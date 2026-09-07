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

from agent_rose_lite.intent import (  # noqa: E402
    classify_intent,
    rank_cells,
    render_brief,
    should_reuse_prior,
    synthesize_query,
)
from memory_manager import MemoryManager  # noqa: E402

_UTC = timezone.utc
_CLAUDE_DIR = ".claude"
DEFAULT_ARTIFACT = (
    _REPO_ROOT / _CLAUDE_DIR / "memory" / "rose_lite_session.json"
)
CI_ARTIFACT = (
    _REPO_ROOT / "marketing" / "data" / "rose_lite_autowire.json"
)


def constrain_path(path: Path, allowed_roots: list[Path]) -> Path:
    """Reject paths that escape the repo or the caller-owned memory tree."""
    resolved = path.expanduser().resolve()
    for root in allowed_roots:
        try:
            resolved.relative_to(root.expanduser().resolve())
            return resolved
        except ValueError:
            continue
    raise ValueError(f"path escapes allowed roots: {path}")


def _safe_fs_path(path: Path, allowed_roots: list[Path]) -> str:
    """Rebuild a path inside an allowed root (S8707 sanitizer).

    User-controlled Path objects stay tainted through constrain_path.
    Reconstruct with realpath + join + normpath + prefix check so the
    filesystem sink never receives the original tainted value.
    """
    raw = os.path.realpath(os.fspath(path))
    for root in allowed_roots:
        base = os.path.realpath(os.fspath(root))
        prefix = base + os.sep
        if raw != base and not raw.startswith(prefix):
            continue
        rel = os.path.relpath(raw, base)
        if rel.startswith("..") or os.path.isabs(rel):
            continue
        fullpath = os.path.normpath(os.path.join(base, rel))
        if fullpath == base or fullpath.startswith(prefix):
            return fullpath
    raise ValueError(f"path escapes allowed roots: {path}")


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
    raw = ""
    if explicit and explicit.strip():
        raw = explicit.strip()[:500]
    else:
        raw = _extract_prompt_from_stdin(stdin_text)
    if raw:
        return synthesize_query(raw, branch_hint=_git_branch_hint())
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


def _load_prior(artifact_path: Path) -> Optional[dict]:
    if not artifact_path.exists():
        return None
    try:
        data = json.loads(artifact_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _claude_hook_stdout(event: str, additional: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": additional,
        }
    }


def _cursor_hook_stdout(additional: str) -> dict[str, Any]:
    return {"additional_context": additional}


def _hook_for(runtime: str, hook_event: Optional[str], context: str) -> dict[str, Any]:
    if runtime == "claude" and hook_event:
        return _claude_hook_stdout(hook_event, context)
    if runtime == "cursor":
        return _cursor_hook_stdout(context)
    return {}


def _write_artifact(path: Path, payload: dict[str, Any], allowed: list[Path]) -> Path:
    fullpath = _safe_fs_path(path, allowed)
    os.makedirs(os.path.dirname(fullpath), exist_ok=True)
    text = json.dumps(payload, indent=2) + "\n"
    with open(fullpath, "w", encoding="utf-8") as handle:
        handle.write(text)
    return Path(fullpath)


def _maintain(mgr: MemoryManager, do_ingest: bool, do_maintain: bool) -> tuple[int, int, int]:
    ingested = pruned = merged = 0
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
            pruned = merged = 0
    return ingested, pruned, merged


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
    allowed = [_REPO_ROOT, memory_dir, memory_dir.parent]
    memory_dir = constrain_path(memory_dir, allowed)
    artifact_path = constrain_path(artifact_path, allowed)
    resolved = resolve_query(query, stdin_text=stdin_text, env=env)
    prior = _load_prior(artifact_path)
    if mode == "prompt-context" and should_reuse_prior(prior, resolved):
        context = str((prior or {}).get("context") or "")
        return {
            "query": resolved,
            "artifact_path": str(artifact_path),
            "payload": {**(prior or {}), "reused": True, "query": resolved},
            "hook_stdout": _hook_for(runtime, hook_event, context),
        }

    mgr = MemoryManager(memory_dir=memory_dir)
    decision = classify_intent(resolved)
    ingested, pruned, merged = _maintain(mgr, do_ingest, do_maintain)

    if sync_claude_hooks and mode in ("session-start", "ci"):
        try:
            from agent_rose_lite.apply_claude_hooks import apply as apply_hooks

            apply_hooks(check_only=False)
        except Exception:
            pass

    try:
        pool = mgr.recall(scene=None, query=resolved, limit=max(limit * 3, 16))
    except TypeError:
        pool = mgr.recall(scene=None, limit=max(limit * 3, 16))
    cells = rank_cells(pool, decision, now_iso=_now_iso(), limit=limit)
    context = render_brief(decision, cells)
    payload: dict[str, Any] = {
        "generated_at": _now_iso(),
        "mode": mode,
        "runtime": runtime,
        "query": resolved,
        "intent": decision.intent,
        "scene": decision.scene,
        "confidence": decision.confidence,
        "ingested": ingested,
        "pruned": pruned,
        "merged": merged,
        "recalled": len(cells),
        "reused": False,
        "cells": [
            {
                "id": c.get("id"),
                "scene": c.get("scene"),
                "cell_type": c.get("cell_type"),
                "salience": c.get("salience"),
                "score": c.get("score"),
                "content": c.get("content"),
            }
            for c in cells
        ],
        "stats": mgr.stats(),
        "context": context,
    }
    written = _write_artifact(artifact_path, payload, allowed)
    return {
        "query": resolved,
        "artifact_path": str(written),
        "payload": payload,
        "hook_stdout": _hook_for(runtime, hook_event, context),
    }


def _cli_memory_dir(raw: Optional[str]) -> Path:
    if raw:
        return constrain_path(Path(raw), [_REPO_ROOT])
    return _REPO_ROOT / _CLAUDE_DIR / "memory"


def _cli_artifact(raw: Optional[str], mode: str) -> Path:
    """CLI never forwards a user Path to the write sink — fixed artifacts only."""
    target = CI_ARTIFACT if mode == "ci" else DEFAULT_ARTIFACT
    if raw and Path(raw).name != target.name:
        raise ValueError("artifact name not allowed")
    return target


def _cli_flags(mode: str, no_ingest: bool, no_maintain: bool) -> tuple[bool, bool]:
    if mode == "prompt-context":
        return False, False
    do_maintain = mode in ("session-start", "ci", "maintain") and not no_maintain
    return (not no_ingest), do_maintain


def _cli_hook_event(explicit: Optional[str], mode: str, runtime: str) -> Optional[str]:
    if explicit:
        return explicit
    table = {
        ("session-start", "claude"): "SessionStart",
        ("prompt-context", "claude"): "UserPromptSubmit",
        ("session-start", "cursor"): "sessionStart",
        ("prompt-context", "cursor"): "beforeSubmitPrompt",
    }
    return table.get((mode, runtime))


def _emit_result(result: dict[str, Any], *, print_hook_json: bool, runtime: str, mode: str) -> None:
    hook = result["hook_stdout"]
    if print_hook_json and hook:
        print(json.dumps(hook, ensure_ascii=True))
        return
    if runtime == "ci" or mode == "ci":
        print(json.dumps(
            {"ok": True, "artifact": result["artifact_path"],
             "recalled": result["payload"]["recalled"]},
            ensure_ascii=True,
        ))
        return
    print(json.dumps(hook if hook else {"ok": True, "artifact": result["artifact_path"]}))


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

    do_ingest, do_maintain = _cli_flags(args.mode, args.no_ingest, args.no_maintain)
    try:
        stdin_text = sys.stdin.read() if not sys.stdin.isatty() else ""
    except (OSError, ValueError):
        stdin_text = ""
    try:
        result = run_autowire(
            mode=args.mode,
            query=args.query,
            memory_dir=_cli_memory_dir(args.memory_dir),
            artifact_path=_cli_artifact(args.artifact, args.mode),
            do_ingest=do_ingest,
            do_maintain=do_maintain,
            runtime=args.runtime,
            hook_event=_cli_hook_event(args.hook_event, args.mode, args.runtime),
            stdin_text=stdin_text,
        )
    except Exception:
        unverified = "ROSE-lite not verified"
        print(json.dumps(_hook_for(
            args.runtime,
            _cli_hook_event(args.hook_event, args.mode, args.runtime),
            unverified,
        ) or {"ok": False, "verified": False, "reason": unverified}))
        return 0
    _emit_result(
        result,
        print_hook_json=args.print_hook_json,
        runtime=args.runtime,
        mode=args.mode,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit as exc:
        if exc.code not in (0, None):
            raise SystemExit(0)
        raise
    except Exception:
        print(json.dumps({"ok": False, "verified": False, "reason": "ROSE-lite not verified"}))
        raise SystemExit(0)
