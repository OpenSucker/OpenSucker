"""Unit tests for the Agent Network adapter.

No live daemon is required — ``anet.svc.SvcClient`` is monkeypatched with a
fake that records calls and returns canned responses. This mirrors the
smoke-test pattern already used in ``test_domains/test_skills.py``.
"""
from __future__ import annotations

from typing import Any

import pytest

from app.core import agentnet as mod
from app.core.config import settings


class FakeSvcClient:
    """Records ``.register``/``.unregister``/``.list``/``.discover`` calls."""

    instances: list["FakeSvcClient"] = []

    def __init__(self, *, base_url: str = "http://127.0.0.1:3998", token: str | None = None, timeout: float = 30.0):
        self.base_url = base_url
        self.token = token
        self.timeout = timeout
        self.closed = False
        self.calls: list[tuple[str, dict]] = []
        self._registered: dict[str, dict] = {}
        FakeSvcClient.instances.append(self)

    def close(self) -> None:
        self.closed = True

    def register(self, **kwargs: Any) -> dict:
        self.calls.append(("register", kwargs))
        self._registered[kwargs["name"]] = kwargs
        return {
            "name": kwargs["name"],
            "ans": {"published": True},
            "meta_probe": {"attempted": False},
        }

    def unregister(self, name: str) -> dict:
        self.calls.append(("unregister", {"name": name}))
        self._registered.pop(name, None)
        return {"unregistered": name}

    def list(self) -> list[dict]:  # noqa: A003 — matches SDK
        self.calls.append(("list", {}))
        return [{"name": n, **v} for n, v in self._registered.items()]

    def health(self) -> list[dict]:
        self.calls.append(("health", {}))
        return [{"name": n, "status": "healthy", "code": 200} for n in self._registered]

    def discover(self, *, skill: str | None = None, peer_id: str | None = None, limit: int | None = None) -> Any:
        self.calls.append(("discover", {"skill": skill, "peer_id": peer_id, "limit": limit}))
        return [{"peer_id": "12D3Koo-fake", "owner_did": "did:key:fake", "services": [{"name": settings.anet_service_name}]}]


@pytest.fixture
def fake_sdk(monkeypatch):
    """Patch ``anet.svc`` so AnetClient uses the fake."""
    FakeSvcClient.instances.clear()
    import anet.svc as real_svc

    monkeypatch.setattr(real_svc, "SvcClient", FakeSvcClient)
    # Re-import safety: mod imports inside __init__, so patching the module
    # attribute is sufficient.
    yield
    FakeSvcClient.instances.clear()


def test_register_uses_configured_defaults(fake_sdk):
    client = mod.AnetClient()
    result = client.register_skill_distill()
    client.close()

    assert result.name == settings.anet_service_name
    assert result.ans_published is True

    (fake,) = FakeSvcClient.instances
    kinds = [c[0] for c in fake.calls]
    # force=True unregisters first, then registers
    assert kinds == ["unregister", "register"]

    reg_kwargs = fake.calls[1][1]
    assert reg_kwargs["name"] == settings.anet_service_name
    assert reg_kwargs["endpoint"] == settings.anet_service_endpoint
    assert reg_kwargs["free"] is True
    assert reg_kwargs["health_check"] == "/api/v1/health"
    assert "/api/v1/skills" in reg_kwargs["paths"]


def test_register_tags_parsed_from_settings(fake_sdk):
    client = mod.AnetClient()
    client.register_skill_distill()
    client.close()

    reg_kwargs = FakeSvcClient.instances[0].calls[1][1]
    assert "skill-distillation" in reg_kwargs["tags"]
    assert "investor-perspective" in reg_kwargs["tags"]


def test_register_force_false_skips_prior_unregister(fake_sdk):
    client = mod.AnetClient()
    client.register_skill_distill(force=False)
    client.close()

    kinds = [c[0] for c in FakeSvcClient.instances[0].calls]
    assert kinds == ["register"]


def test_unregister(fake_sdk):
    client = mod.AnetClient()
    client.register_skill_distill()
    client.unregister_skill_distill()
    client.close()

    kinds = [c[0] for c in FakeSvcClient.instances[0].calls]
    assert kinds[-1] == "unregister"


def test_discover_returns_peers(fake_sdk):
    client = mod.AnetClient()
    peers = client.discover(skill="skill-distillation")
    client.close()

    assert isinstance(peers, list)
    assert peers[0]["peer_id"].startswith("12D3Koo")


def test_unavailable_when_auth_missing(monkeypatch):
    """AnetClient() should raise AnetUnavailable when the SDK can't find a token."""
    import anet.svc as real_svc

    class NoAuthSvcClient:
        def __init__(self, **_: Any):
            raise real_svc.AuthMissingError("fake: no token")

    monkeypatch.setattr(real_svc, "SvcClient", NoAuthSvcClient)
    with pytest.raises(mod.AnetUnavailable):
        mod.AnetClient()


def test_probe_when_disabled(monkeypatch):
    """probe() should not require a daemon when ANET_ENABLED is false."""
    from app.services import anet_register

    monkeypatch.setattr(settings, "anet_enabled", False)

    # probe() still runs — it only returns {"available": False} without a daemon.
    # (We just want no exception here.)
    import anet.svc as real_svc

    class FailingSvcClient:
        def __init__(self, **_: Any):
            raise real_svc.AuthMissingError("no token")

    monkeypatch.setattr(real_svc, "SvcClient", FailingSvcClient)
    result = anet_register.probe()
    assert result["available"] is False
