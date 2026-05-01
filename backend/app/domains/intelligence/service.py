from app.domains.intelligence.schemas import SentimentItem, SentimentReport

NEGATIVE_KEYWORDS = ["调查", "处罚", "暴跌", "减持", "违约", "异常", "风险", "诉讼", "造假", "问询", "停牌"]
POSITIVE_KEYWORDS = ["增长", "回购", "中标", "盈利", "突破", "合作"]


def analyze_sentiment(symbol: str, texts: list[dict]) -> SentimentReport:
    items = []
    negative_count = 0
    for t in texts:
        text = f"{t.get('title', '')} {t.get('summary', '')}"
        matched_negative = [kw for kw in NEGATIVE_KEYWORDS if kw in text]
        matched_positive = [kw for kw in POSITIVE_KEYWORDS if kw in text]
        if matched_negative:
            sentiment = "negative"
            confidence = min(len(matched_negative) * 0.25 + 0.3, 1.0)
            negative_count += 1
        elif matched_positive:
            sentiment = "positive"
            confidence = min(len(matched_positive) * 0.2 + 0.3, 1.0)
        else:
            sentiment = "neutral"
            confidence = 0.5
        items.append(
            SentimentItem(
                source=t.get("source", "unknown"),
                text=text,
                sentiment=sentiment,
                confidence=confidence,
                risk_keywords=matched_negative,
            )
        )
    total = len(items) if items else 1
    negative_ratio = negative_count / total
    overall = "negative" if negative_ratio > 0.4 else "neutral" if negative_ratio > 0.15 else "positive"
    return SentimentReport(
        symbol=symbol,
        overall_sentiment=overall,
        negative_ratio=negative_ratio,
        items=items,
        summary=f"{symbol} 舆情分析完成，负面占比 {negative_ratio*100:.1f}%。",
    )
