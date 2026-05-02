from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CounterInfo(BaseModel):
    counter_type: Literal["normal", "ldp", "uft"]
    name: str
    latency_ms: float
    throughput: int
    supports_quant: bool
    supports_basket: bool
    supports_algorithmic: bool
    cost_level: Literal["free", "medium", "high"]


class CounterComparison(BaseModel):
    counters: list[CounterInfo]
    recommendation: str
