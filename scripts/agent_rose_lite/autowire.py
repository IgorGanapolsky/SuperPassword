#!/usr/bin/env python3
"""ROSE-lite autowire — autonomous ingest/maintain/recall for agent sessions.

Agents and CI invoke this module. Never hand shell commands to the CEO.
Hooks (Claude Code SessionStart/UserPromptSubmit, Cursor sessionStart/
beforeSubmitPrompt) and the rose-lite-autowire GitHub workflow call this.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MEMORY_SCRIPTS = _REPO_ROOT / ".claude" / "scripts" / "memory"
if str(_MEMORY_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_MEMORY_SCRIPTS))
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from memory_manager import MemoryManager, format_recall  # noqa: E402

_UTC = timezone.utc
DEFAULT_ARTIFACT = (
    _REPO_ROOT / ".claude" / "memory" / "rose_lite_session.json"
)
CI_ARTIFACT = (
    _REPO_ROOT / "marketing" / "data" / "rose_lite_autowire.json"
)


def _now_iso() -> str:
    return datetime.now(tz=_UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_branch_hint(cwd: Optional[Path] = None) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(cwd or _REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        branch = (out.stdout or "").strip()
        if branch and branch != "HEAD":
            return branch.replace("/", " ").replace("-", " ").replace("_", " ")
    except (OSError, subprocess.SubprocessError):
        pass
    return ""


def _extract_prompt_from_stdin(stdin_text: str) -> str:
    text = (stdin_text or "").strip()
    if not text:
        return ""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text[:500]
    if not isinstance(payload, dict):
        return text[:500]
    for key in ("prompt", "user_prompt", "message", "content", "query"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()[:500]
    return ""


def resolve_query(
    explicit: Optional[str],
    stdin_text: str = "",
    env: Optional[dict] = None,
) -> str:
    env = env if env is not None else os.environ
    if explicit and explicit.strip():
        return explicit.strip()[:500]
    from_stdin = _extract_prompt_from_stdin(stdin_text)
    if from_stdin:
        return from_stdin
    for key in (
        "ROSE_LITE_QUERY",
        "CLAUDE_SESSION_QUERY",
        "CURSOR_SESSION_QUERY",
    ):
        val = (env.get(key) or "").strip()
        if val:
            return val[:500]
    branch = _git_branch_hint()
    if branch:
        return branch[:500]
    return "Random Timer agent session automation store-publishing debugging"


def _format_context_block(cells: list[dict], query: str, mode: str) -> str:
    header = (
        f"ROSE-lite autowire ({mode}) query={query!r}. "
        "Agents must use these memories; never ask the CEO to run recall/ingest."
    )
    body = format_recall(cells)
    return f"{header}\n{body}"


def _claude_hook_stdout(event: str, additional: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": additional,
        }
    }


def _cursor_hook_stdout(additional: str) -> dict[str, Any]:
    return {"additional_context": additional}


def run_autowire(
    *,
    mode: str,
    query: Optional[str],
    memory_dir: Path,
    artifact_path: Path,
    do_ingest: bool,
    do_maintain: bool,
    runtime: str,
    hook_event: Optional[str],
    stdin_text: str = "",
    env: Optional[dict] = None,
    limit: int = 8,
    sync_claude_hooks: bool = True,
) -> dict[str, Any]:
    env = env if env is not None else os.environ
    resolved = resolve_query(query, stdin_text=stdin_text, env=env)
    mgr = MemoryManager(memory_dir=memory_dir)

    ingested = 0
    pruned = 0
    merged = 0
    if do_ingest:
        try:
            ingested = mgr.ingest_all_unprocessed()
        except OSError:
            ingested = 0
    if do_maintain:
        try:
            pruned = mgr.decay()
            merged = mgr.consolidate()
        except OSError:
            pruned = 0
            merged = 0

    # Keep Claude Code hooks in sync with the tracked manifest (fail-open).
    if sync_claude_hooks and mode in ("session-start", "ci"):
        try:
            from agent_rose_lite.apply_claude_hooks import apply as apply_hooks

            apply_hooks(check_only=False)
        except Exception:
            pass

    scene = None
    scene_match = re.search(
        r"\b(store-publishing|automation|debugging|testing|credentials|"
        r"code-editing|git-operations|animation-parity)\b",
        resolved,
    )
    if scene_match:
        scene = scene_match.group(1)

    cells = mgr.recall(scene=scene, query=resolved, limit=limit)
    context = _format_context_block(cells, resolved, mode)
    stats = mgr.stats()

    payload: dict[str, Any] = {
        "generated_at": _now_iso(),
        "mode": mode,
        "runtime": runtime,
        "query": resolved,
        "scene": scene,
        "ingested": ingested,
        "pruned": pruned,
        "merged": merged,
        "recalled": len(cells),
        "cells": [
            {
                "id": c.get("id"),
                "scene": c.get("scene"),
                "cell_type": c.get("cell_type"),
                "salience": c.get("salience"),
                "content": c.get("content"),
            }
            for c in cells
        ],
        "stats": stats,
        "context": context,
    }

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(payload, indent=2) + "\n")

    hook_stdout: dict[str, Any] = {}
    if runtime == "claude" and hook_event:
        hook_stdout = _claude_hook_stdout(hook_event, context)
    elif runtime == "cursor":
        hook_stdout = _cursor_hook_stdout(context)

    return {
        "query": resolved,
        "artifact_path": str(artifact_path),
        "payload": payload,
        "hook_stdout": hook_stdout,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Autowire ROSE-lite memory for agents/CI (no human CLI)."
    )
    parser.add_argument(
        "--mode",
        choices=("session-start", "prompt-context", "ci", "maintain"),
        required=True,
    )
    parser.add_argument("--query", type=str, default=None)
    parser.add_argument("--runtime", choices=("claude", "cursor", "ci"), default="claude")
    parser.add_argument("--hook-event", type=str, default=None)
    parser.add_argument("--memory-dir", type=str, default=None)
    parser.add_argument("--artifact", type=str, default=None)
    parser.add_argument("--no-ingest", action="store_true")
    parser.add_argument("--no-maintain", action="store_true")
    parser.add_argument("--print-hook-json", action="store_true",
                        help="Emit Claude/Cursor hook JSON on stdout")
    args = parser.parse_args(argv)

    memory_dir = (
        Path(args.memory_dir)
        if args.memory_dir
        else _REPO_ROOT / ".claude" / "memory"
    )

    if args.artifact:
        artifact = Path(args.artifact)
    elif args.mode == "ci":
        artifact = CI_ARTIFACT
    else:
        artifact = DEFAULT_ARTIFACT

    # Prompt hooks stay latency-light: recall only. Session/CI maintain cells.
    if args.mode == "prompt-context":
        do_ingest = False
        do_maintain = False
    else:
        do_ingest = not args.no_ingest
        do_maintain = (
            args.mode in ("session-start", "ci", "maintain") and not args.no_maintain
        )

    hook_event = args.hook_event
    if hook_event is None:
        if args.mode == "session-start" and args.runtime == "claude":
            hook_event = "SessionStart"
        elif args.mode == "prompt-context" and args.runtime == "claude":
            hook_event = "UserPromptSubmit"
        elif args.runtime == "cursor" and args.mode == "session-start":
            hook_event = "sessionStart"
        elif args.runtime == "cursor" and args.mode == "prompt-context":
            hook_event = "beforeSubmitPrompt"

    stdin_text = ""
    if not sys.stdin.isatty():
        stdin_text = sys.stdin.read()

    result = run_autowire(
        mode=args.mode,
        query=args.query,
        memory_dir=memory_dir,
        artifact_path=artifact,
        do_ingest=do_ingest,
        do_maintain=do_maintain,
        runtime=args.runtime,
        hook_event=hook_event,
        stdin_text=stdin_text,
    )

    if args.print_hook_json and result["hook_stdout"]:
        print(json.dumps(result["hook_stdout"], ensure_ascii=True))
    elif args.runtime == "ci" or args.mode == "ci":
        print(json.dumps({"ok": True, "artifact": result["artifact_path"],
                          "recalled": result["payload"]["recalled"]},
                         ensure_ascii=True))
    else:
        # Fail-open for hooks: still print hook JSON when present.
        if result["hook_stdout"]:
            print(json.dumps(result["hook_stdout"], ensure_ascii=True))
        else:
            print(json.dumps({"ok": True, "artifact": result["artifact_path"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
