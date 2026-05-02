"""Register OpenSucker's skill-distill capability on the local anet daemon.

This module is intentionally synchronous and side-effect-free on import.
Call :func:`register_on_startup` from a FastAPI lifespan handler, or run
``python -m backend.scripts.anet_register`` as a standalone one-shot.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.agentnet import AnetClient, AnetUnavailable, RegistrationResult
from app.core.config import settings


log = logging.getLogger(__name__)


def register_on_startup() -> RegistrationResult | None:
    """Register the skill-distill service if ANET_ENABLED is true.

    Returns the registration result, or None if the feature is disabled or
    the daemon is unreachable. Does **not** raise — failures are logged so
    the FastAPI app can boot even without ANet.
    """
    if not settings.anet_enabled:
        log.info("ANet integration disabled (ANET_ENABLED=false); skipping register")
        return None

    try:
        client = AnetClient()
    except AnetUnavailable as exc:
        log.warning("ANet unavailable at startup: %s", exc)
        return None

    try:
        result = client.register_skill_distill()
        log.info(
            "ANet ready: name=%s ans.published=%s meta.attempted=%s",
            result.name,
            result.ans_published,
            result.meta_attempted,
        )
        return result
    except Exception as exc:  # noqa: BLE001
        log.warning("ANet registration failed: %s", exc)
        return None
    finally:
        client.close()


def unregister_on_shutdown() -> None:
    if not settings.anet_enabled:
        return
    try:
        client = AnetClient()
    except AnetUnavailable:
        return
    try:
        client.unregister_skill_distill()
    finally:
        client.close()


def probe() -> dict[str, Any]:
    """Return a snapshot of daemon state for diagnostics / /health endpoints."""
    try:
        client = AnetClient()
    except AnetUnavailable as exc:
        return {"available": False, "error": str(exc)}
    try:
        services = client.list_services()
        health = client.health()
        own = next(
            (s for s in services if s.get("name") == settings.anet_service_name),
            None,
        )
        own_health = next(
            (h for h in health if h.get("name") == settings.anet_service_name),
            None,
        )
        return {
            "available": True,
            "daemon_url": settings.anet_daemon_url,
            "service_name": settings.anet_service_name,
            "registered": own is not None,
            "registration": own,
            "health": own_health,
            "all_services": [s.get("name") for s in services],
        }
    except Exception as exc:  # noqa: BLE001
        return {"available": True, "error": str(exc)}
    finally:
        client.close()
