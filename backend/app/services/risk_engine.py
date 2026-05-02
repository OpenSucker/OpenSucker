from __future__ import annotations

from collections import Counter

import numpy as np

from app.models.schemas import CompositeRiskRequest, NewsRiskRequest, RiskAnalysisResponse, RiskFactor


NEGATIVE_KEYWORDS = {
    "调查": 18,
    "处罚": 20,
    "暴跌": 22,
    "减持": 12,
    "违约": 24,
    "异常": 10,
    "风险": 12,
    "诉讼": 15,
    "造假": 28,
    "问询": 16,
    "停牌": 16,
    "澄清": 6,
}

POSITIVE_KEYWORDS = {
    "增长": 8,
    "回购": 10,
    "中标": 8,
    "盈利": 10,
    "突破": 6,
    "合作": 5,
}


def _to_level(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def _clip(score: float) -> float:
    return float(max(0.0, min(100.0, round(score, 2))))


def analyze_market(symbol: str, price_series: list, order_book: list) -> RiskAnalysisResponse:
    prices = np.array([point.price for point in price_series], dtype=float)
    volumes = np.array([point.volume for point in price_series], dtype=float)
    bid_ask_spreads = np.array([item.best_ask - item.best_bid for item in order_book], dtype=float)
    cancel_ratios = np.array([item.cancel_ratio for item in order_book], dtype=float)
    large_order_ratios = np.array([item.large_order_ratio for item in order_book], dtype=float)
    bid_volumes = np.array([item.bid_volume for item in order_book], dtype=float)
    ask_volumes = np.array([item.ask_volume for item in order_book], dtype=float)

    returns = np.diff(prices) / prices[:-1]
    volatility = float(np.std(returns) * 1000) if len(returns) > 0 else 0.0
    volume_spike = float(volumes[-1] / max(np.mean(volumes[:-1]), 1.0)) if len(volumes) > 1 else 1.0
    spread_ratio = float(np.mean(bid_ask_spreads) / max(np.mean(prices), 1.0) * 10000)
    cancel_ratio = float(np.mean(cancel_ratios) * 100)
    large_order_ratio = float(np.mean(large_order_ratios) * 100)
    imbalance = float(abs(np.mean(bid_volumes) - np.mean(ask_volumes)) / max(np.mean(bid_volumes + ask_volumes), 1.0) * 100)

    factors = [
        RiskFactor(
            name="price_volatility",
            score=_clip(volatility * 1.8),
            level=_to_level(_clip(volatility * 1.8)),
            detail=f"最近价格波动强度为 {volatility:.2f}。",
        ),
        RiskFactor(
            name="volume_spike",
            score=_clip((volume_spike - 1) * 35),
            level=_to_level(_clip((volume_spike - 1) * 35)),
            detail=f"最新成交量相对均值放大倍数为 {volume_spike:.2f}。",
        ),
        RiskFactor(
            name="spread_widening",
            score=_clip(spread_ratio * 2.2),
            level=_to_level(_clip(spread_ratio * 2.2)),
            detail=f"买卖价差相对价格平均基点为 {spread_ratio:.2f}。",
        ),
        RiskFactor(
            name="cancel_pressure",
            score=_clip(cancel_ratio),
            level=_to_level(_clip(cancel_ratio)),
            detail=f"撤单占比均值为 {cancel_ratio:.2f}%。",
        ),
        RiskFactor(
            name="large_order_pressure",
            score=_clip(large_order_ratio * 0.9),
            level=_to_level(_clip(large_order_ratio * 0.9)),
            detail=f"大单占比均值为 {large_order_ratio:.2f}%。",
        ),
        RiskFactor(
            name="order_book_imbalance",
            score=_clip(imbalance * 1.3),
            level=_to_level(_clip(imbalance * 1.3)),
            detail=f"盘口量能失衡度为 {imbalance:.2f}%。",
        ),
    ]

    risk_score = _clip(sum(f.score for f in factors) / len(factors))
    return RiskAnalysisResponse(
        symbol=symbol,
        risk_score=risk_score,
        risk_level=_to_level(risk_score),
        summary=f"{symbol} 的市场微观结构风险评分为 {risk_score:.2f}。",
        factors=factors,
    )


def analyze_news(request: NewsRiskRequest) -> RiskAnalysisResponse:
    keyword_counter: Counter[str] = Counter()
    total_negative = 0
    total_positive = 0

    for item in request.news:
        text = f"{item.title} {item.summary}"
        for keyword, weight in NEGATIVE_KEYWORDS.items():
            if keyword in text:
                keyword_counter[keyword] += 1
                total_negative += weight
        for keyword, weight in POSITIVE_KEYWORDS.items():
            if keyword in text:
                total_positive += weight

    intensity_score = _clip(total_negative - total_positive * 0.35)
    concentration_penalty = _clip(sum(count for _, count in keyword_counter.items()) * 3.5)
    total_score = _clip(intensity_score * 0.75 + concentration_penalty * 0.25)

    matched_keywords = ", ".join(sorted(keyword_counter.keys())) if keyword_counter else "无"
    factors = [
        RiskFactor(
            name="negative_news_intensity",
            score=intensity_score,
            level=_to_level(intensity_score),
            detail=f"负面新闻强度评估完成，命中关键词：{matched_keywords}。",
        ),
        RiskFactor(
            name="negative_news_concentration",
            score=concentration_penalty,
            level=_to_level(concentration_penalty),
            detail=f"近期新闻中重复出现的风险关键词数量为 {sum(keyword_counter.values())}。",
        ),
    ]

    return RiskAnalysisResponse(
        symbol=request.symbol,
        risk_score=total_score,
        risk_level=_to_level(total_score),
        summary=f"{request.symbol} 的新闻风险评分为 {total_score:.2f}。",
        factors=factors,
    )


def analyze_composite(request: CompositeRiskRequest) -> RiskAnalysisResponse:
    market_result = analyze_market(
        symbol=request.market.symbol,
        price_series=request.market.price_series,
        order_book=request.market.order_book,
    )
    news_result = analyze_news(request.news)

    merged_factors = market_result.factors + news_result.factors
    total_score = _clip(market_result.risk_score * 0.6 + news_result.risk_score * 0.4)

    return RiskAnalysisResponse(
        symbol=request.market.symbol,
        risk_score=total_score,
        risk_level=_to_level(total_score),
        summary=(
            f"{request.market.symbol} 的综合风险评分为 {total_score:.2f}，"
            f"其中市场信号占 60%，新闻信号占 40%。"
        ),
        factors=merged_factors,
    )
