"""Agent Network diagnostic / control endpoints.

Exposed at ``/api/v1/anet/*``. Gated by ``settings.anet_enabled`` —
when disabled, routes return 503 so the UI can show a clear banner.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.agentnet import AnetClient, AnetUnavailable
from app.core.config import settings
from app.services import anet_register


router = APIRouter()


def _require_enabled() -> None:
    if not settings.anet_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ANet integration disabled; set ANET_ENABLED=true",
        )


@router.get("/status")
def anet_status() -> dict:
    """Snapshot: is the daemon reachable, are we registered, what's our health."""
    if not settings.anet_enabled:
        return {"enabled": False}
    snapshot = anet_register.probe()
    return {"enabled": True, **snapshot}


@router.post("/register")
def anet_register_now() -> dict:
    """Force (re-)register the skill-distill service. Idempotent."""
    _require_enabled()
    try:
        client = AnetClient()
    except AnetUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    try:
        result = client.register_skill_distill()
        return {
            "name": result.name,
            "ans_published": result.ans_published,
            "meta_attempted": result.meta_attempted,
        }
    finally:
        client.close()


@router.post("/unregister")
def anet_unregister_now() -> dict:
    _require_enabled()
    try:
        client = AnetClient()
    except AnetUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    try:
        client.unregister_skill_distill()
        return {"unregistered": settings.anet_service_name}
    finally:
        client.close()


@router.get("/discover")
def anet_discover(skill: str = "skill-distillation", limit: int = 10) -> dict:
    """Find peers on the network that expose a given skill tag."""
    _require_enabled()
    try:
        client = AnetClient()
    except AnetUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    try:
        peers = client.discover(skill=skill, limit=limit)
        return {"skill": skill, "peers": peers}
    finally:
        client.close()
