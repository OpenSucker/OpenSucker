"""
意图识别模块 v5 — Sucker Smart Trading Matrix
基于 OpenAI 官方 SDK 的 Router Agent
"""
import json
import os
import time
from enum import Enum
from typing import Optional, Dict, Any
from openai import OpenAI

class Intent(str, Enum):
    GREETING = "greeting"
    CHITCHAT = "chitchat"
    MARKET_ANALYSIS = "market_analysis"
    STOCK_SCAN = "stock_scan"
    TRADE_EXECUTION = "trade_execution"
    PORTFOLIO_AUDIT = "portfolio_audit"
    COMMITTEE = "committee" # 多专家委员会共识模式
    RISK_WARNING = "risk_warning"
    PSYCHOLOGY_CARE = "psychology_care"
    RESET = "reset"
    CONFIRM = "confirm"
    UNKNOWN = "unknown"

LLM_INTENT_PROMPT = """Classify this financial trading message for the 'Sucker' Smart Trading Matrix. 
Identify the intent, the XY-axis coordinates, and the user's apparent cognitive level.

Special Mode: 'committee'
- Trigger this if the user asks for a comprehensive rating, consensus, or a "Should I buy?" style question that requires balancing multiple factors (Sentiment, Technical, Macro).

XY-Axis Mapping:
- X1 (Sentiment): Social media buzz, fear/greed.
- X2 (Technical): Indicators, K-line, RSI, MACD.
- X3 (Tactical): Position sizing, Kelly formula, entry/exit.
- X4 (Macro): Fed, interest rates, sector rotation.
- X5 (Game/Evo): Psychological warfare, pressure tests.

Y-Axis Mapping:
- Y1 (Discovery): Idea browsing.
- Y2 (Audit): Feasibility check.
- Y3 (Execution): Real-time action.
- Y4 (Review): Post-trade review.

Return format:
{{
    "intent": "...",
    "x_axis": "X1/X2/X3/X4/X5",
    "y_axis": "Y1/Y2/Y3/Y4",
    "cognitive_level": 1-5,
    "task_chain": ["XnYm"]
}}
"""

_api_config = None
_client = None

def set_intent_api_config(config: Dict):
    global _api_config, _client
    _api_config = config
    if config and config.get("api_key"):
        base_url = config.get("base_url", "")
        if base_url and not base_url.endswith("/v1") and not base_url.endswith("/v1/"):
            base_url = base_url.rstrip("/") + "/v1"
            
        _client = OpenAI(
            api_key=config["api_key"],
            base_url=base_url
        )
    print(f"  ✅ 意图识别 SDK 已就绪: {config.get('base_url', '?')}")

def _call_llm_intent(message, session, api_config):
    if not _client: return None
    
    cognitive_level = getattr(session, 'cognitive_level', 1)
    prompt = LLM_INTENT_PROMPT + f'\n\nMessage: "{message}"\nCognitive Level: {cognitive_level}'

    try:
        response = _client.chat.completions.create(
            model=api_config.get("model", "gpt-4o"),
            messages=[
                {"role": "system", "content": "You are a Router Agent for a financial AI matrix. Return ONLY valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"}
        )
        
        if isinstance(response, str):
            print(f"  [Intent] API returned string: {response[:100]}")
            return None

        text = response.choices[0].message.content
        return json.loads(text)
    except Exception as e:
        print(f"  [Intent] SDK failed: {e}")
        return None

def _keyword_intent(message, session):
    msg = message.lower().strip()
    if any(w in msg for w in ["你好", "嗨", "hi"]):
        return {"intent": "greeting", "x_axis": "X1", "y_axis": "Y1", "_method": "keyword"}
    if any(w in msg for w in ["大盘", "行情", "涨跌"]):
        return {"intent": "market_analysis", "x_axis": "X1", "y_axis": "Y1", "_method": "keyword"}
    if any(w in msg for w in ["凯利", "仓位", "买", "卖"]):
        return {"intent": "trade_execution", "x_axis": "X3", "y_axis": "Y3", "_method": "keyword"}
    return {"intent": "chitchat", "x_axis": "X1", "y_axis": "Y1", "_method": "keyword"}

def detect_intent_full(message, session, user_profile: Optional[Dict] = None):
    if _client:
        result = _call_llm_intent(message, session, _api_config)
        if result:
            cl = result.get("cognitive_level")
            if cl and hasattr(session, "cognitive_level"):
                session.cognitive_level = cl
            return result
    return _keyword_intent(message, session)

def detect_intent(message, session):
    result = detect_intent_full(message, session)
    intent_str = result.get("intent", "chitchat")
    try:
        return Intent(intent_str)
    except ValueError:
        return Intent.CHITCHAT
