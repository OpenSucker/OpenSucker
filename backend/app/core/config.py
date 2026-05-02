from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


SearchProvider = Literal["tavily", "duckduckgo", "serper"]


def _load_dotenv() -> None:
    """Minimal .env loader, no external dep. Safe no-op if file missing."""
    for candidate in (
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / ".env",  # backend/.env
        Path(__file__).resolve().parents[3] / ".env",  # repo-root/.env
    ):
        if not candidate.exists():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        break


_load_dotenv()


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    return value if value not in (None, "") else default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_compat(canonical: str, *aliases: str, default: str | None = None) -> str | None:
    """Return the first non-empty value among canonical + legacy aliases."""
    value = os.getenv(canonical)
    if value not in (None, ""):
        return value
    for alias in aliases:
        v = os.getenv(alias)
        if v not in (None, ""):
            return v
    return default


def _normalize_database_url(raw: str | None) -> str:
    """Translate legacy DB_PATH=/abs/file.db into a SQLAlchemy URL."""
    if not raw:
        return "sqlite:///backend/data/opensucker.db"
    if "://" in raw:
        return raw
    return f"sqlite:///{raw}"


class Settings(BaseModel):
    app_name: str = "OpenSucker Risk Analysis API"
    app_version: str = "0.2.0"
    api_prefix: str = "/api/v1"
    debug: bool = False

    # ── LLM ────────────────────────────────────────────────────────────
    llm_base_url: str = _env_compat("LLM_BASE_URL", "LLM_API_BASE", default="https://api.openai.com/v1") or ""
    llm_api_key: str = _env("LLM_API_KEY", "") or ""
    model_cheap: str = _env("MODEL_CHEAP", "gpt-4o-mini") or "gpt-4o-mini"
    model_strong: str = _env("MODEL_STRONG", "gpt-4o") or "gpt-4o"
    llm_timeout_seconds: int = _env_int("LLM_TIMEOUT_SECONDS", 120)

    # Matrix Agent primary model (chat + intent routing). Defaults to MATRIX_MODEL,
    # falls back to legacy LLM_API_MODEL, then to MODEL_STRONG.
    matrix_model: str = (
        _env_compat(
            "MATRIX_MODEL",
            "LLM_API_MODEL",
            default=_env("MODEL_STRONG", "gpt-4o"),
        )
        or "gpt-4o"
    )

    # ── Search / research ──────────────────────────────────────────────
    search_provider: SearchProvider = (_env("SEARCH_PROVIDER", "duckduckgo") or "duckduckgo")  # type: ignore[assignment]
    tavily_api_key: str = _env("TAVILY_API_KEY", "") or ""
    serper_api_key: str = _env("SERPER_API_KEY", "") or ""
    search_top_k: int = _env_int("SEARCH_TOP_K", 8)
    search_snippet_chars: int = _env_int("SEARCH_SNIPPET_CHARS", 400)

    # ── Filesystem / data ──────────────────────────────────────────────
    data_dir: Path = Path(_env("DATA_DIR", "backend/data") or "backend/data")
    cache_ttl_days: int = _env_int("CACHE_TTL_DAYS", 30)

    # ── Persistence (SQLAlchemy) ───────────────────────────────────────
    database_url: str = _normalize_database_url(_env_compat("DATABASE_URL", "DB_PATH"))

    # ── CORS ───────────────────────────────────────────────────────────
    cors_origins_raw: str = _env("CORS_ORIGINS", "*") or "*"

    # ── Agent Network (ANet) P2P Service Gateway ──────────────────────
    anet_enabled: bool = (_env("ANET_ENABLED", "false") or "false").lower() in ("1", "true", "yes")
    anet_daemon_url: str = _env("ANET_DAEMON_URL", "http://127.0.0.1:3998") or "http://127.0.0.1:3998"
    anet_api_token: str = _env("ANET_API_TOKEN", "") or ""
    anet_service_name: str = _env("ANET_SERVICE_NAME", "opensucker-skill-distill") or "opensucker-skill-distill"
    anet_service_endpoint: str = _env("ANET_SERVICE_ENDPOINT", "http://127.0.0.1:8000") or "http://127.0.0.1:8000"
    anet_service_tags: str = _env("ANET_SERVICE_TAGS", "skill-distillation,investor-perspective,mental-model") or ""
    anet_service_description: str = (
        _env("ANET_SERVICE_DESCRIPTION", "OpenSucker 投资大师 Skill 蒸馏：输入人名，输出决策系统 SKILL.md") or ""
    )

    @property
    def jobs_dir(self) -> Path:
        return self.data_dir / "jobs"

    @property
    def research_cache_dir(self) -> Path:
        return self.data_dir / "research_cache"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def skills_dir(self) -> Path:
        return self.data_dir / "skills"

    @property
    def matrix_db_dir(self) -> Path:
        return self.data_dir

    @property
    def cors_origins(self) -> list[str]:
        raw = (self.cors_origins_raw or "").strip()
        if not raw or raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    # Convenience for legacy callers that expect a flat dict.
    def matrix_llm_config(self) -> dict[str, str]:
        return {
            "api_key": self.llm_api_key,
            "base_url": self.llm_base_url,
            "model": self.matrix_model,
        }


settings = Settings()
