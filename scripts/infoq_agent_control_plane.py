"""InfoQ steal: agent delivery control plane. Fail closed. No paid webinars or SaaS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

WEAK_MODEL_MARKERS = ("hermes-local", "qwen2.5:3b", "muse-spark", "hermes-cheap")
BILLED_REVIEW = frozenset({"copilot_code_review", "copilot-code-review"})
METERED_SERVICES = frozenset(
    {
        "ori",
        "openrouter_primary",
        "foundry_model_router",
        "harness_paid",
    }
)
ALLOWED_SPEND = frozenset({"local_pytest", "local_gist", "github_actions_minutes"})
NATIVE_MARKERS = ("native-android/", "native-ios/")
REQUIRED_CONTEXT = ("in_scope", "out_scope")
MIN_ACCEPTANCE = 2
LONG_LIVED_KEYS = frozenset({"gcp_sa_json", "service_account_json", "long_lived_pat"})


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def _is_weak(model: str) -> bool:
    lowered = _norm(model)
    return any(marker in lowered for marker in WEAK_MODEL_MARKERS)


def evaluate_gateway_fitness(
    *,
    primary_model: str,
    fallback_models: Iterable[str],
) -> ControlDecision:
    primary = _norm(primary_model)
    fallbacks = [_norm(item) for item in fallback_models if str(item).strip()]
    if not fallbacks:
        return ControlDecision(
            action="block_no_fallback",
            ok=False,
            reason="QCon/Foundry steal: a single primary with no fallback is a SPOF",
        )
    independent = [item for item in fallbacks if item != primary]
    if not independent:
        return ControlDecision(
            action="block_spof",
            ok=False,
            reason="fallback repeats the primary model",
        )
    if any(_is_weak(item) for item in fallbacks):
        return ControlDecision(
            action="block_weak_fallback",
            ok=False,
            reason="3B/local fallbacks babysit and are not a real recovery path",
        )
    return ControlDecision(
        action="allow_route",
        ok=True,
        reason="independent tool-capable fallbacks present",
    )


def evaluate_context_store(
    *,
    sections: Mapping[str, object],
    acceptance_criteria: Iterable[str],
) -> ControlDecision:
    keys = {
        _norm(str(key))
        for key, value in sections.items()
        if str(value).strip()
    }
    missing = [key for key in REQUIRED_CONTEXT if key not in keys]
    acs = [str(item).strip() for item in acceptance_criteria if str(item).strip()]
    if missing or len(acs) < MIN_ACCEPTANCE:
        return ControlDecision(
            action="block_incomplete_context",
            ok=False,
            reason="context engineering requires in_scope, out_scope, and two ACs",
        )
    return ControlDecision(
        action="allow_context",
        ok=True,
        reason="required context sections and ACs present",
    )


def gist_context(sections: Mapping[str, object]) -> dict[str, object]:
    keep = {"in_scope", "out_scope", "acceptance_criteria"}
    return {key: value for key, value in sections.items() if _norm(key) in keep}


def evaluate_token_spend(*, service: str) -> ControlDecision:
    name = _norm(service).replace("-", "_")
    if name in BILLED_REVIEW:
        return ControlDecision(
            action="block_billed_review",
            ok=False,
            reason="Copilot review is billed per review; use existing CI review",
        )
    if name in METERED_SERVICES:
        return ControlDecision(
            action="block_metered",
            ok=False,
            reason="Ori/OpenRouter-primary/Foundry/Harness paid exceed the monthly cap",
        )
    if name in ALLOWED_SPEND:
        return ControlDecision(
            action="allow_local",
            ok=True,
            reason="local or already-paid CI minutes",
        )
    return ControlDecision(
        action="block_metered",
        ok=False,
        reason="unknown service is denied under fail-closed spend",
    )


def evaluate_review_lane(*, changed_paths: Iterable[str]) -> ControlDecision:
    paths = [str(path).replace("\\", "/") for path in changed_paths]
    if any(any(path.startswith(marker) or f"/{marker}" in path for marker in NATIVE_MARKERS) for path in paths):
        return ControlDecision(
            action="require_device_e2e",
            ok=False,
            reason="native app changes need device evidence, not AI-only review",
        )
    if paths and all(path.startswith("scripts/") or path.startswith(".claude/skills/") for path in paths):
        return ControlDecision(
            action="allow_ai_approve",
            ok=True,
            reason="scripts/skills-only change may use existing CI AI review",
        )
    return ControlDecision(
        action="require_device_e2e",
        ok=False,
        reason="mixed or unknown paths stay on the full review lane",
    )


def evaluate_identity(*, credential_kind: str) -> ControlDecision:
    kind = _norm(credential_kind).replace("-", "_")
    if kind in LONG_LIVED_KEYS:
        return ControlDecision(
            action="block_long_lived_key",
            ok=False,
            reason="long-lived SA keys leak; use GitHub OIDC / workload identity",
        )
    if kind == "github_oidc":
        return ControlDecision(
            action="allow_oidc",
            ok=True,
            reason="federated identity, not a forever secret",
        )
    return ControlDecision(
        action="block_long_lived_key",
        ok=False,
        reason="unknown credential kind is denied",
    )


def require_complete_controls(
    *,
    has_context: bool,
    has_spend: bool,
    has_review: bool,
    has_identity: bool,
) -> ControlDecision:
    if has_context and has_spend and has_review and has_identity:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="context, spend, review, and identity were all evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing context, spend, review, or identity input",
    )


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="InfoQ agent control plane (no SaaS call).")
    parser.add_argument("--primary-model", default="hermes-main")
    parser.add_argument("--fallbacks", default="nous-deepseek,glm-5.3")
    parser.add_argument("--in-scope", default="")
    parser.add_argument("--out-scope", default="")
    parser.add_argument("--acs", default="")
    parser.add_argument("--service", default="")
    parser.add_argument("--paths", default="")
    parser.add_argument("--credential", default="")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    fallbacks = [part.strip() for part in args.fallbacks.split(",") if part.strip()]
    gateway = evaluate_gateway_fitness(
        primary_model=args.primary_model,
        fallback_models=fallbacks,
    )
    payload["gateway"] = gateway.__dict__
    ok = ok and gateway.ok

    if args.in_scope or args.out_scope or args.acs:
        acs = [part.strip() for part in args.acs.split("|") if part.strip()]
        context = evaluate_context_store(
            sections={"in_scope": args.in_scope, "out_scope": args.out_scope},
            acceptance_criteria=acs,
        )
        payload["context"] = context.__dict__
        payload["gist"] = gist_context(
            {
                "in_scope": args.in_scope,
                "out_scope": args.out_scope,
                "acceptance_criteria": acs,
            }
        )
        ok = ok and context.ok

    if args.service:
        spend = evaluate_token_spend(service=args.service)
        payload["spend"] = spend.__dict__
        ok = ok and spend.ok

    if args.paths:
        paths = [part.strip() for part in args.paths.split(",") if part.strip()]
        review = evaluate_review_lane(changed_paths=paths)
        payload["review"] = review.__dict__
        ok = ok and review.ok

    if args.credential:
        identity = evaluate_identity(credential_kind=args.credential)
        payload["identity"] = identity.__dict__
        ok = ok and identity.ok

    completeness = require_complete_controls(
        has_context=bool(args.in_scope or args.out_scope or args.acs),
        has_spend=bool(args.service),
        has_review=bool(args.paths),
        has_identity=bool(args.credential),
    )
    payload["completeness"] = completeness.__dict__
    ok = ok and completeness.ok

    print(json.dumps(payload, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
