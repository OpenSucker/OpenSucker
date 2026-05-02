"""Intent routing for the Matrix Agent.

Three layers, in priority order:

1. Persona Override — if the user explicitly names an investor (e.g. "巴菲特"),
   force-route to the cell that owns that persona. Bypasses the LLM router.

2. LLM Router — call the configured chat model with a strict JSON schema and
   ask it to emit (intent, x_axis, y_axis, cognitive_level, task_chain).

3. Keyword fallback — deterministic offline classifier so the matrix can boot
   and answer even when LLM_API_KEY is empty or the upstream is down.
"""
from __future__ import annotations

import json
import time
from enum import Enum
from typing import Any, Dict, Optional

from app.core.config import settings


class Intent(str, Enum):
    GREETING = "greeting"
    CHITCHAT = "chitchat"
    MARKET_ANALYSIS = "market_analysis"
    STOCK_SCAN = "stock_scan"
    TRADE_EXECUTION = "trade_execution"
    PORTFOLIO_AUDIT = "portfolio_audit"
    COMMITTEE = "committee"
    RISK_WARNING = "risk_warning"
    PSYCHOLOGY_CARE = "psychology_care"
    RESET = "reset"
    CONFIRM = "confirm"
    UNKNOWN = "unknown"


LLM_INTENT_PROMPT = """Classify this financial trading message for the 'Sucker' Smart Trading Matrix.
Identify the intent, the XY-axis coordinates, and the user's apparent cognitive level.

Special Mode: 'committee'
- Trigger this if the user asks for a comprehensive rating, consensus, or a
  "Should I buy?" style question that requires balancing multiple factors
  (Sentiment, Technical, Macro).

XY-Axis Mapping:
- X1 (Sentiment): Social media buzz, fear/greed.
- X2 (Technical): Indicators, K-line, RSI, MACD.
- X3 (Tactical):  Position sizing, Kelly formula, entry/exit.
- X4 (Macro):     Fed, interest rates, sector rotation.
- X5 (Game/Evo):  Psychological warfare, pressure tests.

Y-Axis Mapping:
- Y1 (Discovery): Idea browsing.
- Y2 (Audit):     Feasibility check.
- Y3 (Execution): Real-time action.
- Y4 (Review):    Post-trade review.

Return JSON:
{
    "intent": "...",
    "x_axis": "X1/X2/X3/X4/X5",
    "y_axis": "Y1/Y2/Y3/Y4",
    "cognitive_level": 1-5,
    "task_chain": ["XnYm"]
}
"""


# ── Persona override map ──────────────────────────────────────────────
# (keyword tuple) -> {"explore": cell, "execute": cell}
PERSONA_KEYWORDS: Dict[tuple, Dict[str, str]] = {
    ("巴菲特", "buffett", "warren buffett", "奥马哈"): {"explore": "X4Y1", "execute": "X3Y3"},
    ("芒格", "munger", "查理芒格", "charlie munger"): {"explore": "X5Y2", "execute": "X3Y4"},
    ("格雷厄姆", "graham", "本杰明格雷厄姆"): {"explore": "X3Y2", "execute": "X1Y3"},
    ("彼得林奇", "林奇", "lynch", "peter lynch"): {"explore": "X3Y1", "execute": "X3Y1"},
    ("段永平", "大道无形", "duan"): {"explore": "X3Y1", "execute": "X1Y3"},
    ("索罗斯", "soros", "george soros"): {"explore": "X4Y1", "execute": "X4Y3"},
    ("西蒙斯", "simons", "jim simons", "medallion"): {"explore": "X2Y1", "execute": "X2Y3"},
    ("孙宇晨", "justin sun", "tron", "波场"): {"explore": "X5Y1", "execute": "X5Y3"},
    ("孙正义", "masayoshi son", "softbank", "软银"): {"explore": "X4Y1", "execute": "X3Y1"},
    ("苏世民", "schwarzman", "blackstone", "黑石"): {"explore": "X4Y2", "execute": "X3Y2"},
}

EXECUTE_HINTS = ("买", "卖", "建仓", "清仓", "加仓", "减仓", "下单", "止损", "止盈", "调仓")


def _detect_persona_override(message: str) -> Optional[Dict[str, Any]]:
    msg_lower = message.lower()
    for keywords, cells in PERSONA_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            cell = cells["execute"] if any(h in message for h in EXECUTE_HINTS) else cells["explore"]
            return {
                "intent": "trade_execution" if cell.endswith("Y3") else "market_analysis",
                "x_axis": cell[:2],
                "y_axis": cell[2:],
                "task_chain": [cell],
                "_method": "persona_override",
                "_persona_hit": keywords[0],
            }
    return None


# ── LLM router ─────────────────────────────────────────────────────────
_client = None
_model: Optional[str] = None


def _get_client():
    """Lazy-build the OpenAI client from the current settings snapshot."""
    global _client, _model
    if _client is not None:
        return _client, _model
    if not settings.llm_api_key:
        return None, None
    try:
        from openai import OpenAI

        base_url = settings.llm_base_url or ""
        if base_url and not base_url.rstrip("/").endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"
        _client = OpenAI(api_key=settings.llm_api_key, base_url=base_url)
        _model = settings.matrix_model
        return _client, _model
    except Exception as exc:  # noqa: BLE001
        print(f"[matrix_agent.intent] OpenAI client init failed: {exc}")
        return None, None


def _call_llm_intent(message: str, session) -> Optional[Dict[str, Any]]:
    client, model = _get_client()
    if client is None:
        return None

    cognitive_level = getattr(session, "cognitive_level", 1)
    prompt = LLM_INTENT_PROMPT + f'\n\nMessage: "{message}"\nCognitive Level: {cognitive_level}'

    last_err: Optional[Exception] = None
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a Router Agent for a financial AI matrix. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                timeout=30,
            )
            if isinstance(response, str):
                return None
            text = response.choices[0].message.content or "{}"
            return json.loads(text)
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            err_str = str(exc).lower()
            retryable = any(k in err_str for k in ("connection", "timeout", "timed out", "reset", "502", "503", "504", "rate"))
            if not retryable or attempt == 2:
                break
            time.sleep(1.0 * (attempt + 1))
    print(f"[matrix_agent.intent] LLM router failed: {last_err}")
    return None


# ── Keyword fallback ───────────────────────────────────────────────────


def _keyword_intent(message: str, session) -> Dict[str, Any]:
    msg = message.lower().strip()
    if any(w in msg for w in ("你好", "嗨", "hi", "hello")):
        return {"intent": "greeting", "x_axis": "X1", "y_axis": "Y1", "_method": "keyword"}
    if any(w in msg for w in ("大盘", "行情", "涨跌", "市场")):
        return {"intent": "market_analysis", "x_axis": "X1", "y_axis": "Y1", "_method": "keyword"}
    if any(w in msg for w in ("凯利", "仓位", "买", "卖", "建仓", "清仓")):
        return {"intent": "trade_execution", "x_axis": "X3", "y_axis": "Y3", "_method": "keyword"}
    if any(w in msg for w in ("rsi", "macd", "k线", "kdj", "boll")):
        return {"intent": "market_analysis", "x_axis": "X2", "y_axis": "Y1", "_method": "keyword"}
    if any(w in msg for w in ("持仓", "组合", "诊断", "审计")):
        return {"intent": "portfolio_audit", "x_axis": "X3", "y_axis": "Y2", "_method": "keyword"}
    if any(w in msg for w in ("利率", "美联储", "fed", "宏观")):
        return {"intent": "market_analysis", "x_axis": "X4", "y_axis": "Y1", "_method": "keyword"}
    if any(w in msg for w in ("要不要", "应不应该", "建议买")):
        return {"intent": "committee", "x_axis": "X1", "y_axis": "Y2", "_method": "keyword"}
    return {"intent": "chitchat", "x_axis": "X1", "y_axis": "Y1", "_method": "keyword"}


# ── Public entry point ────────────────────────────────────────────────


def detect_intent_full(
    message: str,
    session,
    user_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    # 1. Persona override
    override = _detect_persona_override(message)
    if override:
        if hasattr(session, "cognitive_level"):
            override["cognitive_level"] = session.cognitive_level
        return override

    # 2. LLM router
    result = _call_llm_intent(message, session)
    if result:
        cl = result.get("cognitive_level")
        if cl and hasattr(session, "cognitive_level"):
            try:
                session.cognitive_level = int(cl)
            except (TypeError, ValueError):
                pass
        result.setdefault("_method", "llm")
        return result

    # 3. Fallback
    return _keyword_intent(message, session)


def detect_intent(message: str, session) -> Intent:
    result = detect_intent_full(message, session)
    try:
        return Intent(result.get("intent", "chitchat"))
    except ValueError:
        return Intent.CHITCHAT


def reset_intent_client() -> None:
    """Test hook — drop the cached OpenAI client so settings changes take effect."""
    global _client, _model
    _client = None
    _model = None
