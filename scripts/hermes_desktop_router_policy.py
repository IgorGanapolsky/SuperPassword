"""Pin Desktop tool turns. Steal OpenRouter Ori method, not the paid product."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

PRIMARY_PIN = "hermes-main"
PINNED_TOOL_MODELS = frozenset({"hermes-main", "nous-deepseek", "glm-5.3", "gpt-4o"})
ACP_PROVIDERS = frozenset({"copilot-acp", "acp"})
METERED_PRIMARY_PROVIDERS = frozenset({"openrouter", "openrouter.ai"})
WEAK_MODEL_MARKERS = (
    "hermes-local",
    "qwen2.5:3b",
    "muse-spark",
    "hermes-cheap",
)
REAL_TOOLS = frozenset({"terminal", "browser"})
META_TOOLS = frozenset({"tool_call", "tool_search"})
BABYSIT_RE = re.compile(
    r"pip install|notebooklm|terminal\(\)|step\s*1\s*:",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DesktopRouteDecision:
    action: str
    allow: bool
    resolved_model: str
    reason: str


@dataclass(frozen=True)
class ToolTurnGrade:
    pass_eval: bool
    tools_called: list[str]
    fail_reason: str


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def _is_weak_model(model: str) -> bool:
    lowered = _norm(model)
    return any(marker in lowered for marker in WEAK_MODEL_MARKERS)


def decide_desktop_route(
    *,
    provider: str,
    model: str,
    intent: str,
) -> DesktopRouteDecision:
    del intent
    provider_key = _norm(provider)
    model_key = (model or "").strip()
    model_norm = _norm(model)

    if provider_key in ACP_PROVIDERS:
        return DesktopRouteDecision(
            action="block_acp",
            allow=False,
            resolved_model=model_key,
            reason="copilot-acp tool-bridge sessions do not call terminal/browser",
        )

    if provider_key in METERED_PRIMARY_PROVIDERS:
        return DesktopRouteDecision(
            action="block_metered_primary",
            allow=False,
            resolved_model=model_key,
            reason="OpenRouter is fallback only; do not make it Desktop primary",
        )

    if _is_weak_model(model_key):
        return DesktopRouteDecision(
            action="block_weak_model",
            allow=False,
            resolved_model=model_key,
            reason="3B/local models babysit with fake pip/terminal theater",
        )

    if model_norm == PRIMARY_PIN:
        return DesktopRouteDecision(
            action="pin",
            allow=True,
            resolved_model=PRIMARY_PIN,
            reason="pin proven tool-capable primary",
        )

    if model_norm in PINNED_TOOL_MODELS:
        return DesktopRouteDecision(
            action="route_pinned",
            allow=True,
            resolved_model=model_norm,
            reason="router may pick only from the pinned tool-capable set",
        )

    return DesktopRouteDecision(
        action="block_weak_model",
        allow=False,
        resolved_model=model_key,
        reason="model is not in the pinned tool-capable set",
    )


def grade_tool_turn(
    *,
    tool_names: Iterable[str],
    assistant_text: str,
) -> ToolTurnGrade:
    called = [str(name).strip() for name in tool_names if str(name).strip()]
    text = assistant_text or ""

    if any(_norm(name) in META_TOOLS for name in called):
        return ToolTurnGrade(
            pass_eval=False,
            tools_called=called,
            fail_reason="meta_tool_call",
        )

    if BABYSIT_RE.search(text):
        return ToolTurnGrade(
            pass_eval=False,
            tools_called=called,
            fail_reason="babysit_prose",
        )

    real = [name for name in called if _norm(name) in REAL_TOOLS]
    if not real:
        return ToolTurnGrade(
            pass_eval=False,
            tools_called=called,
            fail_reason="no_tool_called",
        )

    return ToolTurnGrade(
        pass_eval=True,
        tools_called=real,
        fail_reason="",
    )


def summarize_traffic_rows(rows: Iterable[Mapping[str, object]]) -> dict[str, object]:
    by_model: dict[str, dict[str, int]] = {}
    weak_successes = 0
    total = 0
    for row in rows:
        total += 1
        model = str(row.get("model") or "unknown")
        status = str(row.get("status") or "unknown")
        bucket = by_model.setdefault(model, {"success": 0, "failure": 0})
        if status == "success":
            bucket["success"] += 1
            if _is_weak_model(model):
                weak_successes += 1
        elif status == "failure":
            bucket["failure"] += 1
    return {
        "total": total,
        "by_model": by_model,
        "weak_model_successes": weak_successes,
        "source": "local_traffic_jsonl",
    }


def _load_traffic_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Hermes Desktop pin/route + Ori-style tool eval (no OpenRouter API).",
    )
    parser.add_argument("--provider", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--intent", default="tool")
    parser.add_argument("--tools", default="")
    parser.add_argument("--assistant-text", default="")
    parser.add_argument("--traffic-jsonl", default="")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    allow = True

    if args.provider or args.model:
        decision = decide_desktop_route(
            provider=args.provider,
            model=args.model,
            intent=args.intent,
        )
        payload["route"] = decision.__dict__
        allow = allow and decision.allow

    if args.tools or args.assistant_text:
        tools = [part.strip() for part in args.tools.split(",") if part.strip()]
        grade = grade_tool_turn(tool_names=tools, assistant_text=args.assistant_text)
        payload["eval"] = grade.__dict__
        allow = allow and grade.pass_eval

    if args.traffic_jsonl:
        traffic_path = Path(args.traffic_jsonl)
        payload["traffic"] = summarize_traffic_rows(_load_traffic_jsonl(traffic_path))

    if not payload:
        parser.error("provide --provider/--model, --tools/--assistant-text, or --traffic-jsonl")

    print(json.dumps(payload, indent=2))
    return 0 if allow else 2


if __name__ == "__main__":
    raise SystemExit(main())
