from __future__ import annotations

from typing import TypedDict

from langgraph.graph import StateGraph

from app.models.schemas import CompositeRiskRequest, RiskAnalysisResponse
from app.services.risk_engine import analyze_market, analyze_news


class CompositeRiskState(TypedDict, total=False):
    request: CompositeRiskRequest
    market_result: RiskAnalysisResponse
    news_result: RiskAnalysisResponse
    result: RiskAnalysisResponse


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


def market_analysis_node(state: CompositeRiskState) -> CompositeRiskState:
    request = state["request"]
    market_result = analyze_market(
        symbol=request.market.symbol,
        price_series=request.market.price_series,
        order_book=request.market.order_book,
    )
    return {"market_result": market_result}


def news_analysis_node(state: CompositeRiskState) -> CompositeRiskState:
    request = state["request"]
    news_result = analyze_news(request.news)
    return {"news_result": news_result}


def merge_analysis_node(state: CompositeRiskState) -> CompositeRiskState:
    request = state["request"]
    market_result = state["market_result"]
    news_result = state["news_result"]
    total_score = _clip(market_result.risk_score * 0.6 + news_result.risk_score * 0.4)
    result = RiskAnalysisResponse(
        symbol=request.market.symbol,
        risk_score=total_score,
        risk_level=_to_level(total_score),
        summary=(
            f"{request.market.symbol} 的综合风险评分为 {total_score:.2f}，"
            f"其中市场信号占 60%，新闻信号占 40%。"
        ),
        factors=market_result.factors + news_result.factors,
    )
    return {"result": result}


workflow = StateGraph(CompositeRiskState)
workflow.add_node("market_analysis", market_analysis_node)
workflow.add_node("news_analysis", news_analysis_node)
workflow.add_node("merge_analysis", merge_analysis_node)
workflow.set_entry_point("market_analysis")
workflow.add_edge("market_analysis", "news_analysis")
workflow.add_edge("news_analysis", "merge_analysis")
workflow.set_finish_point("merge_analysis")
composite_risk_graph = workflow.compile()


def run_composite_risk_workflow(request: CompositeRiskRequest) -> RiskAnalysisResponse:
    result = composite_risk_graph.invoke({"request": request})
    return result["result"]
