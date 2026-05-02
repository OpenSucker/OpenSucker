"""Standalone entry: register / unregister / probe the OpenSucker skill-distill
service with the local anet daemon.

Run from the ``backend`` directory:

    python -m scripts.anet_register register     # (re)register, idempotent
    python -m scripts.anet_register status       # probe daemon + our service
    python -m scripts.anet_register unregister   # remove our service
    python -m scripts.anet_register discover [skill]   # look for peers

Reads connection settings from env / backend/.env (ANET_* keys). Prints JSON
to stdout so you can pipe into jq.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

# Make the `app.*` package importable when running as a plain script.
HERE = __import__("os").path.dirname(__import__("os").path.abspath(__file__))
BACKEND_ROOT = __import__("os").path.dirname(HERE)
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.core.agentnet import AnetClient, AnetUnavailable  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.services import anet_register  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def _json(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, default=str)


def cmd_register(_args: argparse.Namespace) -> int:
    try:
        client = AnetClient()
    except AnetUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    try:
        result = client.register_skill_distill()
        print(_json({
            "name": result.name,
            "ans_published": result.ans_published,
            "meta_attempted": result.meta_attempted,
            "endpoint": settings.anet_service_endpoint,
            "daemon": settings.anet_daemon_url,
            "paths": list(client.SKILL_PATHS),
        }))
        return 0
    finally:
        client.close()


def cmd_unregister(_args: argparse.Namespace) -> int:
    try:
        client = AnetClient()
    except AnetUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    try:
        client.unregister_skill_distill()
        print(_json({"unregistered": settings.anet_service_name}))
        return 0
    finally:
        client.close()


def cmd_status(_args: argparse.Namespace) -> int:
    print(_json(anet_register.probe()))
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    try:
        client = AnetClient()
    except AnetUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    try:
        peers = client.discover(skill=args.skill, limit=args.limit)
        print(_json({"skill": args.skill, "peers": peers}))
        return 0
    finally:
        client.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="anet_register")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("register", help="(re)register the skill-distill service, idempotent")
    sub.add_parser("unregister", help="remove the skill-distill service")
    sub.add_parser("status", help="probe daemon and our registration")

    p_discover = sub.add_parser("discover", help="find peers that expose a skill tag")
    p_discover.add_argument("skill", nargs="?", default="skill-distillation")
    p_discover.add_argument("--limit", type=int, default=10)

    args = parser.parse_args(argv)

    handlers = {
        "register": cmd_register,
        "unregister": cmd_unregister,
        "status": cmd_status,
        "discover": cmd_discover,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
