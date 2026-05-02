from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.core.config import settings


Tier = Literal["cheap", "strong"]


@dataclass
class LLMConfig:
    base_url: str
    api_key: str
    model: str
    timeout: int


@dataclass
class LLMResult:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    raw: Any | None = None

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


def resolve_config(
    tier: Tier,
    overrides: dict[str, Any] | None = None,
) -> LLMConfig:
    overrides = overrides or {}
    base_url = overrides.get("llm_base_url") or settings.llm_base_url
    api_key = overrides.get("llm_api_key") or settings.llm_api_key
    if tier == "cheap":
        model = overrides.get("model_cheap") or settings.model_cheap
    else:
        model = overrides.get("model_strong") or settings.model_strong
    timeout = overrides.get("llm_timeout_seconds") or settings.llm_timeout_seconds
    return LLMConfig(base_url=base_url, api_key=api_key, model=model, timeout=timeout)


def chat(
    messages: list[dict[str, str]],
    *,
    tier: Tier = "cheap",
    overrides: dict[str, Any] | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.3,
    response_format: dict[str, Any] | None = None,
) -> LLMResult:
    """Call an OpenAI-compatible chat endpoint and return a uniform result.

    Uses the openai SDK if available, otherwise falls back to httpx.
    Either way the only requirement on the upstream is OpenAI-compatible
    /v1/chat/completions semantics.
    """
    config = resolve_config(tier, overrides)
    if not config.api_key:
        raise RuntimeError("LLM api key not configured (LLM_API_KEY or per-request override)")

    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI(base_url=config.base_url, api_key=config.api_key, timeout=config.timeout)
        kwargs: dict[str, Any] = {
            "model": config.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if response_format is not None:
            kwargs["response_format"] = response_format
        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        text = choice.message.content or ""
        usage = getattr(response, "usage", None)
        return LLMResult(
            text=text,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            raw=response,
        )
    except ImportError:
        pass

    import httpx

    payload: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if response_format is not None:
        payload["response_format"] = response_format

    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    url = f"{config.base_url.rstrip('/')}/chat/completions"
    with httpx.Client(timeout=config.timeout) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
    text = data["choices"][0]["message"]["content"] or ""
    usage = data.get("usage") or {}
    return LLMResult(
        text=text,
        prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
        completion_tokens=int(usage.get("completion_tokens", 0) or 0),
        raw=data,
    )
