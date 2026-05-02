from fastapi import APIRouter

from app.domains.intelligence.schemas import SentimentReport
from app.domains.intelligence.service import analyze_sentiment

router = APIRouter()


@router.post("/sentiment", response_model=SentimentReport, summary="舆情监控分析")
def analyze_sentiment_endpoint(data: dict) -> SentimentReport:
    symbol = data.get("symbol", "")
    texts = data.get("texts", [])
    return analyze_sentiment(symbol, texts)
