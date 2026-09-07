#!/usr/bin/env python3
"""Apply tracked ROSE-lite Claude Code hooks into .claude/settings.json.

Runs from CI and agent SessionStart bootstrap. Never requires CEO shell.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).resolve().parent / "claude_hooks.json"
SETTINGS = ROOT / ".claude" / "settings.json"


def merge_hooks(existing: dict, rose: dict) -> dict:
    out = dict(existing) if isinstance(existing, dict) else {}
    hooks = dict(out.get("hooks") or {})
    rose_hooks = rose.get("hooks") or {}
    for event, entries in rose_hooks.items():
        hooks[event] = entries
    out["hooks"] = hooks
    return out


def apply(*, check_only: bool = False) -> int:
    rose = json.loads(MANIFEST.read_text())
    hooks = rose.get("hooks") or {}
    missing = [e for e in ("SessionStart", "UserPromptSubmit") if e not in hooks]
    if missing:
        print(json.dumps({"ok": False, "missing": missing}))
        return 1
    if check_only:
        print(json.dumps({"ok": True, "events": sorted(hooks.keys())}))
        return 0

    existing: dict = {}
    if SETTINGS.exists():
        try:
            existing = json.loads(SETTINGS.read_text())
        except json.JSONDecodeError:
            existing = {}
    merged = merge_hooks(existing, rose)
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(merged, indent=2) + "\n")
    print(json.dumps({"ok": True, "wrote": str(SETTINGS.relative_to(ROOT))}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate manifest only; do not write settings.json",
    )
    args = parser.parse_args(argv)
    return apply(check_only=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
