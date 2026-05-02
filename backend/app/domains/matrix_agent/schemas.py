"""Typed state + request/response models for the Matrix Agent."""
from __future__ import annotations

from operator import add
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field


# ── LangGraph state ────────────────────────────────────────────────────


class UserEntity(TypedDict, total=False):
    """Cross-session financial profile for the user."""

    risk_preference: Optional[str]      # conservative / moderate / aggressive
    investment_style: Optional[str]     # value / growth / speculative
    capital_size: Optional[str]         # small / medium / large
    cognitive_level: Optional[int]      # 1-5
    holdings: Optional[List[Dict[str, Any]]]
    last_trade: Optional[Dict[str, Any]]
    historical_lessons: Optional[List[str]]
    watchlist: Optional[List[str]]
    api_trading_enabled: bool
    paper_trading_mode: bool


class SuckerState(TypedDict, total=False):
    """Global flow state for the X×Y matrix."""

    session_id: str
    message: str
    model_version: str
    user: UserEntity
    x_axis: str
    y_axis: str
    intent: str
    intent_cn: str
    task_chain: List[str]
    risk_level: int
    risk_reason: Optional[str]
    risk_redirected: bool
    response_message: str
    skill_used: str
    debug_steps: Annotated[List[str], add]
    tools_called: Annotated[List[Dict[str, Any]], add]
    history: List[Dict[str, Any]]
    _cached_intent: Dict[str, Any]


# ── HTTP contracts ────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str
    model_version: str = "api"


class AgentResponse(BaseModel):
    message: str
    intent: str
    x_axis: str
    y_axis: str
    skill_used: str = ""
    user: Optional[Dict[str, Any]] = None
    tools: List[Dict[str, Any]] = Field(default_factory=list)
    debug: Dict[str, Any] = Field(default_factory=dict)


# Mapping from raw intent string to a Chinese display label.
INTENT_CN: Dict[str, str] = {
    "greeting": "打招呼",
    "chitchat": "闲聊",
    "market_analysis": "大盘分析",
    "stock_scan": "选股扫描",
    "trade_execution": "交易执行",
    "portfolio_audit": "持仓诊断",
    "risk_warning": "风险预警",
    "psychology_care": "情绪安抚",
    "confirm": "确认操作",
    "reset": "重置状态",
    "committee": "矩阵委员会",
}
