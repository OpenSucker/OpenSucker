from __future__ import annotations

from pydantic import BaseModel, Field


class SentimentItem(BaseModel):
    source: str
    text: str
    sentiment: str = Field(..., description="positive/negative/neutral")
    confidence: float = Field(..., ge=0, le=1)
    risk_keywords: list[str] = Field(default_factory=list)


class SentimentReport(BaseModel):
    symbol: str
    overall_sentiment: str
    negative_ratio: float = Field(..., ge=0, le=1)
    items: list[SentimentItem]
    summary: str
