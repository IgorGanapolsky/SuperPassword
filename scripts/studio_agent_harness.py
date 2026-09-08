"""AI Studio Agents steal: local harness. Fail closed. No Gemini API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

PROXY_METRICS = frozenset({"tokens", "pr_velocity", "daily_messages"})
DENIED_TOOLS = frozenset(
    {"open_network", "antigravity_hosted", "gemini_sandbox_exec", "aistudio_agents"}
)
IAP_WEIGHT = 10
TASK_WEIGHT = 5


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str


def _norm(value: str) -> str:
    return (value or "").strip().lower().replace("-", "_")


def _csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in (value or "").split(",") if part.strip())


def evaluate_harness_files(*, has_agents_md: bool, has_skill_md: bool) -> ControlDecision:
    if has_agents_md and has_skill_md:
        return ControlDecision(
            action="allow_harness",
            ok=True,
            reason="AGENTS.md plus SKILL.md define persona and workflow",
        )
    return ControlDecision(
        action="block_incomplete_harness",
        ok=False,
        reason="AI Studio templates ship both AGENTS.md and SKILL.md",
    )


def evaluate_tool_allowlist(
    *,
    requested: Sequence[str],
    allowed: Sequence[str],
) -> ControlDecision:
    asked = [_norm(item) for item in requested if str(item).strip()]
    permit = {_norm(item) for item in allowed if str(item).strip()}
    if not asked:
        return ControlDecision(
            action="block_undeclared_tools",
            ok=False,
            reason="tools must be declared; empty is not least privilege",
        )
    denied = [item for item in asked if item in DENIED_TOOLS or item not in permit]
    if denied:
        return ControlDecision(
            action="block_tool",
            ok=False,
            reason="unknown or hosted tools are denied",
        )
    return ControlDecision(
        action="allow_tools",
        ok=True,
        reason="requested tools are a subset of the allowlist",
    )


def evaluate_network_allowlist(
    *,
    domains: Sequence[str],
    open_network: bool,
    needs_network: bool,
) -> ControlDecision:
    if open_network:
        return ControlDecision(
            action="block_open_network",
            ok=False,
            reason="sandbox traffic must be an explicit domain allowlist",
        )
    named = [item.strip() for item in domains if str(item).strip()]
    if needs_network and not named:
        return ControlDecision(
            action="block_open_network",
            ok=False,
            reason="network work needs named domains",
        )
    return ControlDecision(
        action="allow_network",
        ok=True,
        reason="no open egress; domains named or network unused",
    )


def evaluate_termination(*, stop_condition: str) -> ControlDecision:
    if (stop_condition or "").strip():
        return ControlDecision(
            action="allow_bounded",
            ok=True,
            reason="stop condition bounds the agent loop",
        )
    return ControlDecision(
        action="block_unbounded",
        ok=False,
        reason="one prompt can loop; name the stop condition",
    )


def evaluate_sandbox(*, isolation: str) -> ControlDecision:
    if _norm(isolation) == "worktree":
        return ControlDecision(
            action="allow_sandbox",
            ok=True,
            reason="writes stay in an ephemeral worktree",
        )
    return ControlDecision(
        action="block_checkout",
        ok=False,
        reason="do not write on the user checkout",
    )


def evaluate_verified_execution(*, tests_passed: bool, read_back: bool) -> ControlDecision:
    if tests_passed and read_back:
        return ControlDecision(
            action="allow_verified",
            ok=True,
            reason="tests and read-back before claiming done",
        )
    return ControlDecision(
        action="block_unverified",
        ok=False,
        reason="human oversight: verify outputs before deploy",
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


def require_harness_controls(
    *,
    has_harness: bool,
    has_tools: bool,
    has_network: bool,
    has_termination: bool,
    has_sandbox: bool,
    has_verified: bool,
) -> ControlDecision:
    if (
        has_harness
        and has_tools
        and has_network
        and has_termination
        and has_sandbox
        and has_verified
    ):
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="harness, tools, network, stop, sandbox, and verify evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing harness, tools, network, stop, sandbox, or verify",
    )


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="AI Studio-inspired local harness (no SaaS).")
    parser.add_argument("--agents-md", action="store_true")
    parser.add_argument("--skill-md", action="store_true")
    parser.add_argument("--tools", default="")
    parser.add_argument("--allowed-tools", default="")
    parser.add_argument("--domains", default="")
    parser.add_argument("--open-network", action="store_true")
    parser.add_argument("--needs-network", action="store_true")
    parser.add_argument("--stop", default="")
    parser.add_argument("--isolation", default="")
    parser.add_argument("--tests-passed", action="store_true")
    parser.add_argument("--read-back", action="store_true")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    has_harness = bool(args.agents_md or args.skill_md)
    if has_harness:
        harness = evaluate_harness_files(
            has_agents_md=bool(args.agents_md),
            has_skill_md=bool(args.skill_md),
        )
        payload["harness"] = harness.__dict__
        ok = ok and harness.ok

    has_tools = bool(args.tools or args.allowed_tools)
    if has_tools:
        tools = evaluate_tool_allowlist(
            requested=_csv(args.tools),
            allowed=_csv(args.allowed_tools),
        )
        payload["tools"] = tools.__dict__
        ok = ok and tools.ok

    has_network = bool(args.domains or args.open_network or args.needs_network)
    if has_network:
        network = evaluate_network_allowlist(
            domains=_csv(args.domains),
            open_network=bool(args.open_network),
            needs_network=bool(args.needs_network) or bool(args.domains),
        )
        payload["network"] = network.__dict__
        ok = ok and network.ok

    has_termination = args.stop != ""
    if has_termination:
        termination = evaluate_termination(stop_condition=args.stop)
        payload["termination"] = termination.__dict__
        ok = ok and termination.ok

    has_sandbox = bool(args.isolation)
    if has_sandbox:
        sandbox = evaluate_sandbox(isolation=args.isolation)
        payload["sandbox"] = sandbox.__dict__
        ok = ok and sandbox.ok

    has_verified = bool(args.tests_passed or args.read_back)
    if has_verified:
        verified = evaluate_verified_execution(
            tests_passed=bool(args.tests_passed),
            read_back=bool(args.read_back),
        )
        payload["verified"] = verified.__dict__
        ok = ok and verified.ok

    completeness = require_harness_controls(
        has_harness=has_harness,
        has_tools=has_tools,
        has_network=has_network,
        has_termination=has_termination,
        has_sandbox=has_sandbox,
        has_verified=has_verified,
    )
    payload["completeness"] = completeness.__dict__
    ok = ok and completeness.ok

    print(json.dumps(payload, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
