"""GitHub canvas steal: persist workflow state. Fail closed. No Copilot app."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset({"tokens", "pr_velocity", "daily_messages", "canvas_ux"})
METERED_SURFACES = frozenset(
    {"copilot_app", "create_canvas", "copilot_pro", "github_copilot", "awesome_copilot"}
)
CHAT_SURFACES = frozenset({"chat_only", "chat_scroll", "transcript", "chat_transcript"})
IAP_WEIGHT = 10
TASK_WEIGHT = 5


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str
    addresses: tuple[str, ...] = ()


def _norm(value: str) -> str:
    return (value or "").strip().lower().replace("-", "_").replace(".", "_")


def evaluate_surface(*, surface: str) -> ControlDecision:
    name = _norm(surface)
    if name in {"local_canvas", "markdown_canvas", "durable_canvas"}:
        return ControlDecision(
            action="allow_local_canvas",
            ok=True,
            reason="persist stages and drafts outside the chat scroll",
        )
    if name in CHAT_SURFACES or "chat" in name or "transcript" in name:
        return ControlDecision(
            action="block_chat_scroll",
            ok=False,
            reason="chat is intent; the canvas is the source of truth",
        )
    if name in METERED_SURFACES or "copilot" in name:
        return ControlDecision(
            action="block_metered",
            ok=False,
            reason="Copilot app and /create-canvas are outside the monthly cap",
        )
    return ControlDecision(
        action="block_metered",
        ok=False,
        reason="unknown canvas surface is denied",
    )


def persist_canvas(*, canvas: Mapping[str, object]) -> ControlDecision:
    stages = canvas.get("stages") or []
    drafts = canvas.get("drafts") or {}
    addresses: list[str] = []
    if isinstance(stages, Sequence):
        for raw in stages:
            if not isinstance(raw, Mapping):
                continue
            stage_id = str(raw.get("id") or "").strip()
            if stage_id:
                addresses.append(f"stage:{stage_id}")
    if isinstance(drafts, Mapping):
        for key, value in drafts.items():
            if str(key).strip() and str(value).strip():
                addresses.append(f"draft:{key}")
    if addresses:
        return ControlDecision(
            action="allow_persist",
            ok=True,
            reason="workflow state is durable on the canvas",
            addresses=tuple(addresses),
        )
    return ControlDecision(
        action="block_empty_canvas",
        ok=False,
        reason="a canvas with no stages or drafts is just another chat",
    )


def evaluate_source(*, source: str) -> ControlDecision:
    name = _norm(source)
    if name in {"canvas", "local_canvas", "durable_canvas"}:
        return ControlDecision(
            action="allow_canvas_source",
            ok=True,
            reason="read the persisted canvas, not the transcript",
        )
    return ControlDecision(
        action="block_chat_scroll",
        ok=False,
        reason="do not reconstruct work from chat history",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_canvas",
            ok=True,
            reason="cite sits on persisted canvas state",
        )
    return ControlDecision(
        action="block_off_canvas",
        ok=False,
        reason="cite is not on the durable canvas",
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


def require_canvas_controls(
    *,
    has_surface: bool,
    has_canvas: bool,
    has_source: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_surface and has_canvas and has_source and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="surface, canvas, source, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing surface, canvas, source, or cite",
    )


def _load_canvas(path: str) -> dict[str, object]:
    if not path:
        return {}
    raw = Path(path)
    if not raw.is_file():
        return {}
    payload = json.loads(raw.read_text())
    return dict(payload) if isinstance(payload, Mapping) else {}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Local durable canvas (no Copilot app).")
    parser.add_argument("--surface", default="")
    parser.add_argument("--canvas", default="")
    parser.add_argument("--source", default="")
    parser.add_argument("--cite", default="")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    has_surface = bool(args.surface)
    if has_surface:
        surface = evaluate_surface(surface=args.surface)
        payload["surface"] = {k: v for k, v in surface.__dict__.items() if k != "addresses"}
        ok = ok and surface.ok

    canvas = _load_canvas(args.canvas)
    has_canvas = bool(args.canvas)
    addresses: list[str] = []
    if has_canvas:
        persisted = persist_canvas(canvas=canvas)
        payload["persist"] = {
            "action": persisted.action,
            "ok": persisted.ok,
            "reason": persisted.reason,
            "addresses": list(persisted.addresses),
        }
        addresses = list(persisted.addresses)
        ok = ok and persisted.ok

    has_source = bool(args.source)
    if has_source:
        sourced = evaluate_source(source=args.source)
        payload["source"] = {k: v for k, v in sourced.__dict__.items() if k != "addresses"}
        ok = ok and sourced.ok

    has_cite = bool(args.cite)
    if has_cite:
        grounded = evaluate_claim(cite=args.cite, addresses=addresses)
        payload["cite"] = {k: v for k, v in grounded.__dict__.items() if k != "addresses"}
        ok = ok and grounded.ok

    completeness = require_canvas_controls(
        has_surface=has_surface,
        has_canvas=has_canvas,
        has_source=has_source,
        has_cite=has_cite,
    )
    payload["completeness"] = {
        k: v for k, v in completeness.__dict__.items() if k != "addresses"
    }
    ok = ok and completeness.ok
    print(json.dumps(payload, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
