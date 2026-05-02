"""LanguageModel + SessionManager (in-memory) used by the Matrix Agent.

The original implementation lives in opensucker-backend/backend/modules/llm.py
and modules/user_profile.py — both are domain-internal helpers (not part of
the OpenSucker risk-engine surface), so they live under domains/matrix_agent.

The LanguageModel wraps the openai SDK and adds:
  - a 3-attempt retry loop tolerant to upstream connection / 5xx errors
  - a `mock` fallback when no api key is configured (so the matrix can
    still answer with deterministic stubs in CI / offline dev)
"""
from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from app.core.config import settings


# ── LanguageModel ─────────────────────────────────────────────────────


class LanguageModel:
    """OpenAI-compatible chat client with retries + tool-call support."""

    def __init__(self, api_config: Optional[Dict[str, str]] = None):
        self.api_config = api_config or settings.matrix_llm_config()
        self.mode = "mock"
        self.client = None

        api_key = self.api_config.get("api_key")
        if api_key:
            try:
                from openai import OpenAI

                base_url = self.api_config.get("base_url", "") or ""
                if base_url and not base_url.rstrip("/").endswith("/v1"):
                    base_url = base_url.rstrip("/") + "/v1"
                self.client = OpenAI(api_key=api_key, base_url=base_url)
                self.mode = "api"
            except Exception as exc:  # noqa: BLE001
                print(f"[matrix_agent.runtime] OpenAI init failed: {exc}")

    # ── chat (no tools) ────────────────────────────────────────────────
    def generate(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        if self.mode != "api" or self.client is None:
            return _mock_response(messages)

        last_err: Optional[Exception] = None
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.api_config["model"],
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=60,
                )
                if isinstance(response, str):
                    return f"API 异常返回: {response}"
                return response.choices[0].message.content or ""
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                if not _is_retryable(exc) or attempt == 2:
                    break
                time.sleep(1.5 * (attempt + 1))
        return f"API 调用失败: {last_err}"

    # ── chat with tools ────────────────────────────────────────────────
    def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_choice: str = "auto",
        max_tokens: int = 1500,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        if self.mode != "api" or self.client is None:
            return {
                "content": _mock_response(messages),
                "tool_calls": [],
                "finish_reason": "stop",
            }

        last_err: Optional[Exception] = None
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.api_config["model"],
                    messages=messages,
                    tools=tools,
                    tool_choice=tool_choice,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=60,
                )
                if isinstance(response, str):
                    return {
                        "content": "",
                        "tool_calls": [],
                        "finish_reason": "error",
                        "error": f"API returned plain string: {response[:120]}",
                    }
                msg = response.choices[0].message
                return {
                    "content": msg.content or "",
                    "tool_calls": msg.tool_calls or [],
                    "finish_reason": response.choices[0].finish_reason,
                    "raw": response,
                }
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                if not _is_retryable(exc) or attempt == 2:
                    break
                time.sleep(1.5 * (attempt + 1))
        return {
            "content": "",
            "tool_calls": [],
            "finish_reason": "error",
            "error": str(last_err),
        }


def _is_retryable(exc: Exception) -> bool:
    err_str = str(exc).lower()
    keywords = ("connection", "timeout", "timed out", "reset", "502", "503", "504", "rate")
    return any(k in err_str for k in keywords)


def _mock_response(messages: List[Dict[str, Any]]) -> str:
    last_user = next(
        (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
        "",
    )
    return (
        "（离线模拟回复 · 未配置 LLM_API_KEY）\n"
        f"我已经收到你的消息：「{last_user}」。\n"
        "在离线模式下,矩阵会返回这段占位文本。请在 .env 中配置 LLM_API_KEY 以启用完整功能。"
    )


# ── SessionManager (volatile, in-memory) ──────────────────────────────


class UserSessionState:
    """Light-weight in-memory mirror of the per-user financial profile.

    The SQLite-backed source-of-truth lives in domains/users + domains/sessions;
    this object only caches the fields the LLM router / prompts need to read
    cheaply during a single request.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.cognitive_level: int = 1
        self.risk_preference: str = "moderate"
        self.investment_style: str = "growth"
        self.capital_size: str = "medium"
        self.holdings: List[Dict[str, Any]] = []
        self.historical_lessons: List[str] = []
        self.watchlist: List[str] = []
        self.confirmed: bool = False
        self.selected_symbol: Optional[str] = None
        self.active_recommendations: List[Dict[str, Any]] = []


class SessionManager:
    def __init__(self) -> None:
        self.sessions: Dict[str, UserSessionState] = {}

    def get_or_create(self, session_id: Optional[str] = None) -> UserSessionState:
        sid = session_id or uuid.uuid4().hex[:8]
        if sid not in self.sessions:
            self.sessions[sid] = UserSessionState(sid)
        return self.sessions[sid]

    def get(self, session_id: str) -> Optional[UserSessionState]:
        return self.sessions.get(session_id)


# ── Module-level singletons (lazy-init) ───────────────────────────────


_session_manager: Optional[SessionManager] = None
_llm: Optional[LanguageModel] = None


def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def get_llm() -> LanguageModel:
    global _llm
    if _llm is None:
        _llm = LanguageModel()
    return _llm


def reset_runtime() -> None:
    """Test hook — drop cached singletons so a new settings snapshot is read."""
    global _session_manager, _llm
    _session_manager = None
    _llm = None
