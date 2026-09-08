"""Spotify shunt steal: intercept large reads. Fail closed. No Portal."""

from __future__ import annotations

import json
import os
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

DEFAULT_MIN_LINES = 350
DEFAULT_SLICE_LINES = 80
REASONING_KINDS = frozenset({"reasoning", "debug", "architecture", "safety"})
DELEGABLE_KINDS = frozenset({"boilerplate", "config", "test_scaffold", "large_read"})
METERED_WORKERS = frozenset(
    {"gemini-2.5-flash", "gemini_2_5_flash", "gemini_flash", "portal", "aika"}
)
PROXY_METRICS = frozenset({"tokens", "pr_velocity", "daily_messages"})
IAP_WEIGHT = 10
TASK_WEIGHT = 5
PIPE_TARGET_RE = re.compile(r"\|\s*(grep|rg|awk|sed)\b", re.I)
HEAD_LIMIT_RE = re.compile(r"\b(?:head|tail)\b.*(?:-n|--lines)\b", re.I)
BARE_READER_RE = re.compile(r"^(?:cat|head|tail|less|more)\b", re.I)
HEADING_RE = re.compile(r"^(#{1,6}\s+|class\s+|def\s+|fun\s+|func\s+)", re.M)


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str


def _norm(value: str) -> str:
    return (value or "").strip().lower().replace("-", "_").replace(".", "_")


def evaluate_read_intercept(
    *,
    line_count: int,
    targeted: bool,
    threshold: int = DEFAULT_MIN_LINES,
) -> ControlDecision:
    if int(line_count) > int(threshold) and not targeted:
        return ControlDecision(
            action="block_full_read",
            ok=False,
            reason="untargeted large reads burn frontier tokens; slice or target first",
        )
    return ControlDecision(
        action="allow_read",
        ok=True,
        reason="small file or targeted offset/limit",
    )


def evaluate_task_route(*, task_kind: str, model: str) -> ControlDecision:
    kind = _norm(task_kind)
    worker = _norm(model)
    if kind in REASONING_KINDS:
        if worker in METERED_WORKERS or "flash" in worker or "local_slice" in worker:
            return ControlDecision(
                action="block_delegate_reason",
                ok=False,
                reason="do not delegate debugging or architecture to a cheap worker",
            )
        if "hermes" in worker and "main" in worker:
            return ControlDecision(
                action="allow_frontier",
                ok=True,
                reason="reasoning stays on the capable route",
            )
        return ControlDecision(
            action="block_delegate_reason",
            ok=False,
            reason="reasoning needs hermes-main",
        )
    if kind in DELEGABLE_KINDS:
        if worker in METERED_WORKERS:
            return ControlDecision(
                action="block_metered",
                ok=False,
                reason="Portal and Gemini Flash are outside the monthly cap",
            )
        if worker == "local_slice":
            return ControlDecision(
                action="allow_delegate",
                ok=True,
                reason="boilerplate and large reads use a local slice, not a frontier dump",
            )
    return ControlDecision(
        action="block_metered",
        ok=False,
        reason="unknown task or worker is denied",
    )


def evaluate_context_return(*, source_lines: int, returned_lines: int) -> ControlDecision:
    if int(source_lines) > DEFAULT_MIN_LINES and int(returned_lines) >= int(source_lines):
        return ControlDecision(
            action="block_full_dump",
            ok=False,
            reason="return only the relevant slice to the frontier model",
        )
    return ControlDecision(
        action="allow_slice",
        ok=True,
        reason="frontier context is a slice, not the whole file",
    )


def rank_work(*, candidates: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    scored: list[tuple[float, dict[str, object]]] = []
    for raw in candidates:
        row = dict(raw)
        metric = _norm(str(row.get("metric", "")))
        effort = max(float(row.get("effort") or 1), 1.0)
        if metric in PROXY_METRICS:
            score = 0.0
        else:
            iap = float(row.get("expected_iap_attempts") or 0)
            tasks = float(row.get("expected_completed_tasks") or 0)
            score = (iap * IAP_WEIGHT + tasks * TASK_WEIGHT) / effort
        row["score"] = score
        scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored]


def require_shunt_controls(
    *,
    has_read: bool,
    has_route: bool,
    has_return: bool,
) -> ControlDecision:
    if has_read and has_route and has_return:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="read intercept, route, and slice evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing read intercept, route, or slice",
    )


def is_targeted_bash(command: str) -> bool:
    cmd = (command or "").strip()
    if not cmd:
        return False
    if PIPE_TARGET_RE.search(cmd):
        return True
    if HEAD_LIMIT_RE.search(cmd):
        return True
    if "sed -n" in cmd:
        return True
    return False


def slice_text(*, text: str, query: str = "", max_lines: int = DEFAULT_SLICE_LINES) -> str:
    lines = (text or "").splitlines()
    if not lines:
        return ""
    keep: list[str] = []
    tokens = [tok for tok in re.findall(r"[a-z0-9_]+", (query or "").lower()) if tok]
    if tokens:
        for index, line in enumerate(lines):
            lowered = line.lower()
            if any(token in lowered for token in tokens):
                start = max(0, index - 1)
                end = min(len(lines), index + 2)
                keep.extend(lines[start:end])
    for line in lines:
        if HEADING_RE.match(line):
            keep.append(line)
    if not keep:
        keep = lines[: min(40, len(lines))]
    # Preserve first-seen order without dumping the file.
    seen: set[str] = set()
    unique: list[str] = []
    for line in keep:
        if line in seen:
            continue
        seen.add(line)
        unique.append(line)
        if len(unique) >= int(max_lines):
            break
    return "\n".join(unique)


def _tool_name(payload: Mapping[str, object]) -> str:
    return str(
        payload.get("tool_name")
        or payload.get("tool")
        or payload.get("hook_event_name")
        or ""
    ).strip()


def _tool_input(payload: Mapping[str, object]) -> dict[str, object]:
    raw = payload.get("tool_input") or payload.get("input") or payload.get("arguments")
    return dict(raw) if isinstance(raw, Mapping) else {}


def _command(payload: Mapping[str, object], tool_input: Mapping[str, object]) -> str:
    return str(payload.get("command") or tool_input.get("command") or "").strip()


def _read_path(tool_input: Mapping[str, object], command: str) -> str:
    for key in ("path", "file_path", "filePath"):
        value = str(tool_input.get(key) or "").strip()
        if value:
            return value
    if not command:
        return ""
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()
    for token in tokens:
        if token.startswith("-"):
            continue
        if BARE_READER_RE.match(token):
            continue
        candidate = Path(token).expanduser()
        if candidate.is_file():
            return str(candidate)
    return ""


def _line_count(path: str) -> int:
    target = Path(path)
    if not target.is_file():
        return 0
    try:
        with target.open(encoding="utf-8", errors="replace") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def _is_read_event(name: str) -> bool:
    lowered = name.lower()
    return lowered in {"read", "beforereadfile"} or lowered.endswith("read")


def _is_shell_event(name: str, command: str) -> bool:
    lowered = name.lower()
    return lowered in {"shell", "bash", "beforeshellexecution"} or bool(command)


def decide_hook(*, raw: str, threshold: int | None = None) -> dict[str, object]:
    cutoff = int(threshold or os.environ.get("SHUNT_MIN_LINES") or DEFAULT_MIN_LINES)
    try:
        payload = json.loads(raw or "")
        if not isinstance(payload, dict):
            raise ValueError("hook payload must be an object")
    except (json.JSONDecodeError, ValueError):
        return {
            "permission": "allow",
            "action": "fail_open",
            "agent_message": "token-shunt hook failed open on bad stdin",
        }

    tool_input = _tool_input(payload)
    command = _command(payload, tool_input)
    name = _tool_name(payload)
    path = _read_path(tool_input, command)
    lines = _line_count(path) if path else 0

    if _is_read_event(name) or (path and not command):
        targeted = any(tool_input.get(key) not in (None, "", 0) for key in ("offset", "limit"))
        decision = evaluate_read_intercept(
            line_count=lines,
            targeted=targeted,
            threshold=cutoff,
        )
        if decision.ok:
            return {"permission": "allow", "action": "allow_read"}
        rewritten = dict(tool_input)
        key = "file_path" if "file_path" in rewritten else "path"
        if path:
            rewritten[key] = path
        rewritten.setdefault("offset", 1)
        rewritten["limit"] = DEFAULT_SLICE_LINES
        return {
            "permission": "allow",
            "action": "rewrite_read",
            "updated_input": rewritten,
            "agent_message": (
                f"Untargeted read of {lines} lines rewritten to first "
                f"{DEFAULT_SLICE_LINES}. Use offset/limit for edits."
            ),
        }

    if _is_shell_event(name, command) and command:
        if is_targeted_bash(command) or not BARE_READER_RE.match(command):
            return {"permission": "allow", "action": "allow_bash"}
        if lines > cutoff:
            return {
                "permission": "deny",
                "action": "block_bash_read",
                "agent_message": (
                    "Bare cat/head/tail of a large file blocked. Pipe to grep/rg "
                    "or Read with offset/limit."
                ),
            }
        return {"permission": "allow", "action": "allow_bash"}

    return {"permission": "allow", "action": "allow_other"}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Spotify-inspired token shunt (no Portal).")
    parser.add_argument("--hook", action="store_true")
    parser.add_argument("--lines", default="")
    parser.add_argument("--targeted", action="store_true")
    parser.add_argument("--threshold", default=str(DEFAULT_MIN_LINES))
    parser.add_argument("--task-kind", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--source-lines", default="")
    parser.add_argument("--returned-lines", default="")
    args = parser.parse_args()

    if args.hook:
        import sys

        print(json.dumps(decide_hook(raw=sys.stdin.read()), indent=2))
        return 0

    payload: dict[str, object] = {}
    ok = True

    has_read = args.lines != ""
    if has_read:
        read = evaluate_read_intercept(
            line_count=int(args.lines or 0),
            targeted=bool(args.targeted),
            threshold=int(args.threshold or DEFAULT_MIN_LINES),
        )
        payload["read"] = read.__dict__
        ok = ok and read.ok

    has_route = bool(args.task_kind or args.model)
    if has_route:
        route = evaluate_task_route(task_kind=args.task_kind, model=args.model)
        payload["route"] = route.__dict__
        ok = ok and route.ok

    has_return = args.source_lines != "" or args.returned_lines != ""
    if has_return:
        returned = evaluate_context_return(
            source_lines=int(args.source_lines or 0),
            returned_lines=int(args.returned_lines or 0),
        )
        payload["return"] = returned.__dict__
        ok = ok and returned.ok

    completeness = require_shunt_controls(
        has_read=has_read,
        has_route=has_route,
        has_return=has_return,
    )
    payload["completeness"] = completeness.__dict__
    ok = ok and completeness.ok

    print(json.dumps(payload, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
