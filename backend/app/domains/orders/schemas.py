from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    side: Literal["buy", "sell"] = Field(...)
    order_type: Literal["market", "limit", "stop"] = Field(default="limit")
    quantity: float = Field(..., gt=0)
    price: float | None = Field(default=None, gt=0)
    terminal_type: Literal["mobile", "pc", "vip"] = Field(default="pc")
    counter_type: Literal["normal", "ldp", "uft"] = Field(default="normal")


class OrderResponse(BaseModel):
    order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: float | None
    status: str
    terminal_type: str
    counter_type: str
    latency_ms: float
    created_at: str


class OrderLatencyReport(BaseModel):
    terminal_type: str
    counter_type: str
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    order_count: int
