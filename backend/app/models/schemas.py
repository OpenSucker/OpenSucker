from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str


class PricePoint(BaseModel):
    timestamp: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    volume: float = Field(..., ge=0)


class OrderBookSnapshot(BaseModel):
    timestamp: str = Field(..., min_length=1)
    best_bid: float = Field(..., gt=0)
    best_ask: float = Field(..., gt=0)
    bid_volume: float = Field(..., ge=0)
    ask_volume: float = Field(..., ge=0)
    cancel_ratio: float = Field(..., ge=0, le=1)
    large_order_ratio: float = Field(..., ge=0, le=1)


class MarketSignalRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    price_series: list[PricePoint] = Field(..., min_length=5)
    order_book: list[OrderBookSnapshot] = Field(..., min_length=3)


class NewsItem(BaseModel):
    timestamp: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    summary: str = Field(default="")


class NewsRiskRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    news: list[NewsItem] = Field(..., min_length=1)


class CompositeRiskRequest(BaseModel):
    market: MarketSignalRequest
    news: NewsRiskRequest


class RiskFactor(BaseModel):
    name: str
    score: float = Field(..., ge=0, le=100)
    level: Literal["low", "medium", "high", "critical"]
    detail: str


class RiskAnalysisResponse(BaseModel):
    symbol: str
    risk_score: float = Field(..., ge=0, le=100)
    risk_level: Literal["low", "medium", "high", "critical"]
    summary: str
    factors: list[RiskFactor]


class SampleScenarioResponse(BaseModel):
    name: str
    market: MarketSignalRequest
    news: NewsRiskRequest
