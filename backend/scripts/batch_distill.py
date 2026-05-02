#!/usr/bin/env python3
"""
Batch skill distillation CLI — thin wrapper around SkillDistillService.

Usage:
    python scripts/batch_distill.py                          # all in people.json
    python scripts/batch_distill.py --people "彼得·林奇,雷·达里奥"
    python scripts/batch_distill.py --config scripts/people.json
    python scripts/batch_distill.py --people "彼得·林奇" --force
    python scripts/batch_distill.py --dry-run

Run from project root (OpenSucker/) so .claude/skills/ resolves correctly.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running as  python backend/scripts/batch_distill.py  from project root
_SCRIPTS_DIR = Path(__file__).resolve().parent   # backend/scripts/
_BACKEND_DIR = _SCRIPTS_DIR.parent               # backend/
sys.path.insert(0, str(_BACKEND_DIR))

from app.services.skill_distill import SkillDistillService


def load_people(config_path: Path) -> list[dict[str, str]]:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"people.json must be a JSON array, got {type(data).__name__}")
    return [
        item if isinstance(item, dict) else {"name": str(item)}
        for item in data
    ]


def parse_people_arg(arg: str) -> list[dict[str, str]]:
    return [{"name": n.strip()} for n in arg.split(",") if n.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch distill investment legends into Claude Code SKILL.md files"
    )
    src = parser.add_mutually_exclusive_group()
    src.add_argument("--people", type=str, metavar="NAMES",
                     help='Comma-separated, e.g. "彼得·林奇,雷·达里奥"')
    src.add_argument("--config", type=Path, metavar="PATH",
                     default=_SCRIPTS_DIR / "people.json",
                     help="JSON config (default: scripts/people.json)")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing SKILL.md files")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print people list and exit, no Claude Code calls")
    parser.add_argument("--claude-cmd", default="claude", metavar="CMD",
                        help="Claude Code binary path (default: claude)")
    parser.add_argument("--timeout", type=int, default=600, metavar="SEC",
                        help="Max seconds per person (default: 600)")
    args = parser.parse_args()

    if args.people:
        people = parse_people_arg(args.people)
    else:
        if not args.config.exists():
            print(f"Config not found: {args.config}")
            print("Tip: create scripts/people.json or use --people 'Name1,Name2'")
            sys.exit(1)
        people = load_people(args.config)

    if not people:
        print("No people to process.")
        sys.exit(0)

    print(f"People ({len(people)}): {[p['name'] for p in people]}")

    if args.dry_run:
        print("[dry-run] Exiting.")
        return

    svc = SkillDistillService(claude_cmd=args.claude_cmd, timeout_s=args.timeout)
    svc.distill_batch(people, force=args.force)


if __name__ == "__main__":
    main()
