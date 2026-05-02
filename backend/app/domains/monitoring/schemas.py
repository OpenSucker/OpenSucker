from __future__ import annotations

from pydantic import BaseModel, Field


class AbnormalSignal(BaseModel):
    signal_type: str = Field(..., description="异常类型")
    severity: str = Field(..., description="严重程度: low/medium/high/critical")
    description: str
    confidence: float = Field(..., ge=0, le=1)


class MonitoringReport(BaseModel):
    symbol: str
    signals: list[AbnormalSignal]
    overall_risk_level: str
    summary: str
