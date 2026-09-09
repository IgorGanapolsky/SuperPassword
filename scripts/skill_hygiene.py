"""pvncher steal: skill + prompt hygiene. Fail closed. No GPT-6 Astra."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset({"tokens", "pr_velocity", "daily_messages", "agent_count"})
METERED_PLATFORMS = frozenset(
    {
        "gpt6_astra",
        "gpt_6_astra",
        "astra",
        "openai_primary",
        "codex_upgrade",
        "chatgpt_pro",
    }
)
DESCRIPTION_MAX_CHARS = 100
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


def evaluate_platform(*, platform: str) -> ControlDecision:
    name = _norm(platform)
    if name in {"local_hygiene", "skill_hygiene", "prompt_hygiene"}:
        return ControlDecision(
            action="allow_local_hygiene",
            ok=True,
            reason="audit skill and prompt bloat locally",
        )
    if name in METERED_PLATFORMS or "astra" in name or "openai" in name:
        return ControlDecision(
            action="block_metered",
            ok=False,
            reason="GPT-6 Astra and OpenAI-as-primary stay outside the monthly cap",
        )
    return ControlDecision(
        action="block_metered",
        ok=False,
        reason="unknown hygiene platform is denied",
    )


def evaluate_description(*, description: str) -> ControlDecision:
    text = (description or "").strip()
    if not text:
        return ControlDecision(
            action="block_bloated_description",
            ok=False,
            reason="empty skill description cannot be routed",
        )
    if len(text) > DESCRIPTION_MAX_CHARS:
        return ControlDecision(
            action="block_bloated_description",
            ok=False,
            reason="skill descriptions must stay short so they survive truncation",
        )
    lowered = text.lower()
    if "anything" in lowered or "anytime" in lowered or "any " in lowered:
        return ControlDecision(
            action="block_bloated_description",
            ok=False,
            reason="pick-me descriptions pull the wrong skill into context",
        )
    return ControlDecision(
        action="allow_short_description",
        ok=True,
        reason="short trigger description loads cleanly",
    )


def evaluate_disclosure(*, disclosure: str) -> ControlDecision:
    name = _norm(disclosure)
    if name in {"router", "progressive", "progressive_disclosure"}:
        return ControlDecision(
            action="allow_progressive_disclosure",
            ok=True,
            reason="root skill is a minimal router to supporting docs",
        )
    return ControlDecision(
        action="block_over_specific",
        ok=False,
        reason="elaborate itineraries overconstrain stronger models",
    )


def evaluate_always_on(*, bloat: bool) -> ControlDecision:
    if bloat:
        return ControlDecision(
            action="block_always_on_bloat",
            ok=False,
            reason="do not force a full repo map before every edit",
        )
    return ControlDecision(
        action="allow_lean_always_on",
        ok=True,
        reason="always-on instructions stay lean and contextual",
    )


def evaluate_completion(*, defined: bool) -> ControlDecision:
    if defined:
        return ControlDecision(
            action="allow_defined_completion",
            ok=True,
            reason="completion includes run, inspect, and fix before stopping",
        )
    return ControlDecision(
        action="block_early_stop",
        ok=False,
        reason="stopping after the first implementation leaves work unfinished",
    )


def _skill_hygienic(skill: Mapping[str, object]) -> bool:
    description = evaluate_description(description=str(skill.get("description") or ""))
    disclosure = evaluate_disclosure(disclosure=str(skill.get("disclosure") or ""))
    always_on = evaluate_always_on(bloat=bool(skill.get("always_on_bloat")))
    completion = evaluate_completion(defined=bool(skill.get("completion_defined")))
    return description.ok and disclosure.ok and always_on.ok and completion.ok


def pick_hygiene(*, skills: Sequence[Mapping[str, object]]) -> ControlDecision:
    for raw in skills:
        skill_id = str(raw.get("id") or "").strip()
        if skill_id and _skill_hygienic(raw):
            return ControlDecision(
                action="allow_hygienic_skill",
                ok=True,
                reason="keep short, routed skills that define completion",
                addresses=(f"skill:{skill_id}",),
            )
    return ControlDecision(
        action="block_no_hygienic_skill",
        ok=False,
        reason="no skill cleared the hygiene score",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_hygiene",
            ok=True,
            reason="cite is the hygienic skill pick",
        )
    return ControlDecision(
        action="block_off_hygiene",
        ok=False,
        reason="cite is not the hygienic skill pick",
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


def require_hygiene_controls(
    *,
    has_platform: bool,
    has_skills: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_platform and has_skills and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="platform, skills, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing platform, skills, or cite",
    )


def _load_skills(path: str) -> list[dict[str, object]]:
    if not path:
        return []
    raw = Path(path)
    if not raw.is_file():
        return []
    payload = json.loads(raw.read_text())
    items = payload.get("skills", payload) if isinstance(payload, Mapping) else payload
    return [dict(item) for item in items if isinstance(item, Mapping)]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Local skill/prompt hygiene (no Astra).")
    parser.add_argument("--platform", default="")
    parser.add_argument("--skills", default="")
    parser.add_argument("--cite", default="")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    has_platform = bool(args.platform)
    if has_platform:
        platform = evaluate_platform(platform=args.platform)
        payload["platform"] = {k: v for k, v in platform.__dict__.items() if k != "addresses"}
        ok = ok and platform.ok

    skills = _load_skills(args.skills)
    has_skills = bool(args.skills)
    addresses: list[str] = []
    if has_skills:
        picked = pick_hygiene(skills=skills)
        payload["pick"] = {
            "action": picked.action,
            "ok": picked.ok,
            "reason": picked.reason,
            "addresses": list(picked.addresses),
        }
        addresses = list(picked.addresses)
        ok = ok and picked.ok

    has_cite = bool(args.cite)
    if has_cite:
        grounded = evaluate_claim(cite=args.cite, addresses=addresses)
        payload["cite"] = {k: v for k, v in grounded.__dict__.items() if k != "addresses"}
        ok = ok and grounded.ok

    completeness = require_hygiene_controls(
        has_platform=has_platform,
        has_skills=has_skills,
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
