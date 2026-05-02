"""Thin adapter around anet-sdk's SvcClient (P2P Service Gateway).

Usage:

    from app.core.agentnet import AnetClient

    client = AnetClient()
    client.register_skill_distill()   # idempotent
    client.unregister_skill_distill()

The adapter fails soft when the daemon is unreachable so the FastAPI app
can still boot in environments without ANet installed.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.core.config import settings


log = logging.getLogger(__name__)


class AnetUnavailable(RuntimeError):
    """Raised when the local anet daemon cannot be reached or authenticated."""


@dataclass
class RegistrationResult:
    name: str
    ans_published: bool
    meta_attempted: bool
    raw: dict[str, Any]


class AnetClient:
    """Wraps anet.svc.SvcClient with OpenSucker-specific defaults.

    Reads connection settings from `app.core.config.settings`:
      * ANET_DAEMON_URL            — daemon REST base URL (default http://127.0.0.1:3998)
      * ANET_API_TOKEN             — bearer token; falls back to $HOME/.anet/api_token
      * ANET_SERVICE_NAME          — local service name (default opensucker-skill-distill)
      * ANET_SERVICE_ENDPOINT      — OpenSucker FastAPI URL the daemon will proxy to
      * ANET_SERVICE_TAGS          — comma-separated discovery tags
      * ANET_SERVICE_DESCRIPTION   — human-readable description

    Required paths exposed to peers (prefix matching in the daemon):
      * /api/v1/skills/distill     — POST, start a distillation job
      * /api/v1/skills/jobs        — GET, poll job status / download SKILL.md / research
      * /api/v1/health             — health check
    """

    # Prefix matching — daemon routes anything under these to our FastAPI.
    SKILL_PATHS: tuple[str, ...] = (
        "/api/v1/skills",
        "/api/v1/health",
    )

    def __init__(
        self,
        *,
        daemon_url: str | None = None,
        token: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        try:
            from anet.svc import AuthMissingError, SvcClient
        except ImportError as exc:  # pragma: no cover - SDK missing
            raise AnetUnavailable(
                "anet-sdk is not installed; run `pip install anet-sdk`"
            ) from exc

        self._AuthMissingError = AuthMissingError
        resolved_token = token if token is not None else (settings.anet_api_token or None)
        base_url = daemon_url or settings.anet_daemon_url

        try:
            self._svc = SvcClient(
                base_url=base_url,
                token=resolved_token,
                timeout=timeout,
            )
        except AuthMissingError as exc:
            raise AnetUnavailable(
                "no ANet API token: set ANET_API_TOKEN, or let the daemon create "
                "~/.anet/api_token on first boot"
            ) from exc

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._svc.close()

    def __enter__(self) -> "AnetClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # registration — the whole point of this adapter
    # ------------------------------------------------------------------

    def register_skill_distill(
        self,
        *,
        name: str | None = None,
        endpoint: str | None = None,
        tags: list[str] | None = None,
        description: str | None = None,
        free: bool = True,
        force: bool = True,
    ) -> RegistrationResult:
        """Register OpenSucker's distill surface as a P2P service.

        ``force=True`` will unregister any previous entry with the same name
        first, so the call is idempotent across daemon restarts.
        """
        name = name or settings.anet_service_name
        endpoint = endpoint or settings.anet_service_endpoint
        description = description or settings.anet_service_description or name
        if tags is None:
            raw = settings.anet_service_tags
            tags = [t.strip() for t in raw.split(",") if t.strip()]

        if force:
            try:
                self._svc.unregister(name)
            except Exception:  # noqa: BLE001  — best-effort cleanup
                pass

        resp = self._svc.register(
            name=name,
            endpoint=endpoint,
            paths=list(self.SKILL_PATHS),
            modes=["rr"],
            free=free,
            tags=tags,
            description=description,
            health_check="/api/v1/health",
        )
        log.info(
            "ANet: registered service %s → %s (tags=%s)",
            name,
            endpoint,
            ",".join(tags),
        )
        ans = resp.get("ans") if isinstance(resp, dict) else None
        meta = resp.get("meta_probe") if isinstance(resp, dict) else None
        return RegistrationResult(
            name=resp.get("name", name) if isinstance(resp, dict) else name,
            ans_published=bool(ans and ans.get("published")),
            meta_attempted=bool(meta and meta.get("attempted")),
            raw=resp if isinstance(resp, dict) else {},
        )

    def unregister_skill_distill(self, *, name: str | None = None) -> None:
        name = name or settings.anet_service_name
        try:
            self._svc.unregister(name)
            log.info("ANet: unregistered service %s", name)
        except Exception as exc:  # noqa: BLE001
            log.warning("ANet: unregister %s failed: %s", name, exc)

    def list_services(self) -> list[dict]:
        return self._svc.list()

    def health(self) -> list[dict]:
        return self._svc.health()

    def discover(self, *, skill: str, limit: int | None = None) -> Any:
        """Look up peers that expose a given skill (ANS-backed)."""
        return self._svc.discover(skill=skill, limit=limit)

    # ------------------------------------------------------------------
    # convenience — callers on the *client* side (e.g. a demo script that
    # invokes a remote OpenSucker peer) can use this instead of driving
    # SvcClient.call directly.
    # ------------------------------------------------------------------

    def call_peer_distill(
        self,
        peer_id: str,
        name: str,
        *,
        service_name: str | None = None,
        locale: str = "zh-CN",
    ) -> dict:
        service_name = service_name or settings.anet_service_name
        return self._svc.call(
            peer_id,
            service_name,
            "/api/v1/skills/distill",
            method="POST",
            body={"name": name, "locale": locale},
        )

    def call_peer_job_status(
        self,
        peer_id: str,
        job_id: str,
        *,
        service_name: str | None = None,
    ) -> dict:
        service_name = service_name or settings.anet_service_name
        return self._svc.call(
            peer_id,
            service_name,
            f"/api/v1/skills/jobs/{job_id}",
            method="GET",
        )

    def call_peer_download_skill(
        self,
        peer_id: str,
        job_id: str,
        *,
        service_name: str | None = None,
    ) -> dict:
        service_name = service_name or settings.anet_service_name
        return self._svc.call(
            peer_id,
            service_name,
            f"/api/v1/skills/jobs/{job_id}/skill",
            method="GET",
        )
