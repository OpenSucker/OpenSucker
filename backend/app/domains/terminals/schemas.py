from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TerminalInfo(BaseModel):
    terminal_type: Literal["mobile", "pc", "vip"]
    name: str
    avg_latency_ms: float
    max_throughput: int
    supports_script: bool
    supports_vip_channel: bool
    geo_limitation: bool
    maintenance_cost: float


class TerminalComparison(BaseModel):
    terminals: list[TerminalInfo]
    recommendation: str
