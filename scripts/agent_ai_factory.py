"""NVIDIA/Palantir AI-factory steal: sovereign local ops ontology. Fail closed."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset(
    {
        "model_parameter_count",
        "frontier_leaderboard",
        "gpu_hours",
        "tokens",
        "foundry_seats",
        "nemotron_size",
    }
)
MANAGED_PLATFORMS = frozenset(
    {
        "palantir_foundry_cloud",
        "palantir_aip_managed",
        "nemotron_cloud_finetune",
        "nvidia_dgx_cloud_paid",
        "hugging_face_enterprise_spend",
    }
)
ALLOWED_PLATFORMS = frozenset(
    {
        "local_ai_factory",
        "agent_ai_factory",
        "sovereign_local",
        "local_ops_ontology",
    }
)
DOMAIN_METRICS = frozenset(
    {
        "domain_allocation_accuracy",
        "iap_attempt",
        "wqtu",
        "timer_completed",
        "paywall_attempt",
        "ops_decision_accuracy",
    }
)
REQUIRED_ONTOLOGY_ENTITIES = frozenset({"wqtu", "paywall", "release", "agent_slot"})
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
    if name in ALLOWED_PLATFORMS:
        return ControlDecision(
            action="allow_local_ai_factory",
            ok=True,
            reason="run sovereign AI-factory controls locally under the monthly cap",
        )
    if name in MANAGED_PLATFORMS or "foundry" in name or "nemotron_cloud" in name:
        return ControlDecision(
            action="block_managed_ai_factory",
            ok=False,
            reason="Palantir Foundry / Nemotron cloud spend stays denied",
        )
    return ControlDecision(
        action="block_managed_ai_factory",
        ok=False,
        reason="unknown AI-factory platform is denied",
    )


def evaluate_sovereignty(
    *,
    data_local: bool,
    weights_local: bool,
    inference_local: bool,
    proprietary_exported: bool,
) -> ControlDecision:
    if proprietary_exported or not (data_local and weights_local and inference_local):
        return ControlDecision(
            action="block_proprietary_export",
            ok=False,
            reason="keep ops data, weights, and inference under local control",
        )
    return ControlDecision(
        action="allow_sovereign_local",
        ok=True,
        reason="sovereign local path: data, weights, and inference stay controlled",
    )


def evaluate_ontology(
    *,
    ontology_live: bool,
    entities: Sequence[str],
) -> ControlDecision:
    normalized = {_norm(item) for item in entities if str(item).strip()}
    if (
        ontology_live
        and REQUIRED_ONTOLOGY_ENTITIES.issubset(normalized)
        and len(normalized) >= 4
    ):
        return ControlDecision(
            action="allow_live_ontology",
            ok=True,
            reason="live ontology links WQTU, paywall, release, and agent slots",
        )
    return ControlDecision(
        action="block_missing_ontology",
        ok=False,
        reason="AI factory needs a live map of ops entities before recommending work",
    )


def evaluate_specialization(
    *,
    domain_post_trained: bool,
    domain_eval_beats_general: bool,
    chose_bigger_without_domain_eval: bool,
) -> ControlDecision:
    if chose_bigger_without_domain_eval:
        return ControlDecision(
            action="block_size_over_domain",
            ok=False,
            reason="do not pick a larger model without a domain evaluation",
        )
    if domain_post_trained and domain_eval_beats_general:
        return ControlDecision(
            action="allow_domain_specialization",
            ok=True,
            reason="prefer domain-specialized models that beat generalists on the task",
        )
    return ControlDecision(
        action="block_size_over_domain",
        ok=False,
        reason="domain post-training plus domain eval evidence is required",
    )


def evaluate_decision_log_training(
    *,
    trained_on_ops_decisions: bool,
    generic_chat_only: bool,
) -> ControlDecision:
    if trained_on_ops_decisions and not generic_chat_only:
        return ControlDecision(
            action="allow_decision_log_training",
            ok=True,
            reason="specialize on real ops decision logs / GSD artifacts",
        )
    return ControlDecision(
        action="block_generic_chat_training",
        ok=False,
        reason="generic chat fine-tunes are not ops decision specialization",
    )


def evaluate_scarce_allocation(
    *,
    budget_remaining_usd: float,
    concurrent_slots: int,
    max_slots: int,
    allocation_evidenced: bool,
) -> ControlDecision:
    if (
        budget_remaining_usd > 0
        and 0 < concurrent_slots <= max_slots
        and allocation_evidenced
    ):
        return ControlDecision(
            action="allow_scarce_allocation",
            ok=True,
            reason="scarce agent/budget slots allocated with evidence under the cap",
        )
    return ControlDecision(
        action="block_unbounded_allocation",
        ok=False,
        reason="unbounded concurrent agents or zero remaining budget is denied",
    )


def evaluate_proving_ground(
    *,
    own_ops_validated: bool,
    export_before_proof: bool,
) -> ControlDecision:
    if own_ops_validated and not export_before_proof:
        return ControlDecision(
            action="allow_proving_ground",
            ok=True,
            reason="validate the pattern on our own ops before exporting it",
        )
    return ControlDecision(
        action="block_export_before_proof",
        ok=False,
        reason="do not export an AI-factory pattern before own-ops proof",
    )


def evaluate_specialization_honesty(
    *,
    scoped_task_claim: bool,
    claims_universal_capability: bool,
) -> ControlDecision:
    if scoped_task_claim and not claims_universal_capability:
        return ControlDecision(
            action="allow_scoped_specialization_claim",
            ok=True,
            reason="specialization gains are scoped to the post-trained decision task",
        )
    return ControlDecision(
        action="block_universal_specialization_claim",
        ok=False,
        reason="do not claim specialization solves forecasting or every attached problem",
    )


def _factory_clears(raw: Mapping[str, object]) -> bool:
    return evaluate_platform(platform=str(raw.get("platform") or "")).ok


def pick_factory(
    *,
    factories: Sequence[Mapping[str, object]],
) -> ControlDecision:
    for raw in factories:
        factory_id = str(raw.get("id") or "").strip()
        if factory_id and _factory_clears(raw):
            return ControlDecision(
                action="allow_local_factory",
                ok=True,
                reason="local AI-factory experiment cleared",
                addresses=(f"aif:{factory_id}",),
            )
    return ControlDecision(
        action="block_no_local_factory",
        ok=False,
        reason="no factory cleared local sovereign gates",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_ai_factory",
            ok=True,
            reason="cite is the local AI-factory address",
        )
    return ControlDecision(
        action="block_off_ai_factory",
        ok=False,
        reason="cite is not the local AI-factory address",
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


def require_ai_factory_controls(
    *,
    has_platform: bool,
    has_factories: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_platform and has_factories and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="platform, factories, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing platform, factories, or cite",
    )


def _load_factories(path: str) -> list[dict[str, object]]:
    if not path:
        return []
    raw = Path(path)
    if not raw.is_file():
        return []
    payload = json.loads(raw.read_text())
    items = payload.get("factories", payload) if isinstance(payload, Mapping) else payload
    return [dict(item) for item in items if isinstance(item, Mapping)]


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _split_entities(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Local sovereign AI-factory controls (no Foundry/Nemotron cloud)."
    )
    parser.add_argument("--platform", default="")
    parser.add_argument("--factories", default="")
    parser.add_argument("--cite", default="")
    parser.add_argument("--data-local", default="")
    parser.add_argument("--weights-local", default="0")
    parser.add_argument("--inference-local", default="0")
    parser.add_argument("--proprietary-exported", default="0")
    parser.add_argument("--ontology-live", default="")
    parser.add_argument("--entities", default="")
    parser.add_argument("--domain-post-trained", default="")
    parser.add_argument("--domain-eval-beats-general", default="0")
    parser.add_argument("--chose-bigger-without-domain-eval", default="0")
    parser.add_argument("--trained-on-ops-decisions", default="")
    parser.add_argument("--generic-chat-only", default="0")
    parser.add_argument("--budget-remaining-usd", default="")
    parser.add_argument("--concurrent-slots", default="0")
    parser.add_argument("--max-slots", default="0")
    parser.add_argument("--allocation-evidenced", default="0")
    parser.add_argument("--own-ops-validated", default="")
    parser.add_argument("--export-before-proof", default="0")
    parser.add_argument("--scoped-task-claim", default="")
    parser.add_argument("--claims-universal-capability", default="0")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    has_platform = bool(args.platform)
    if has_platform:
        platform = evaluate_platform(platform=args.platform)
        payload["platform"] = {
            k: v for k, v in platform.__dict__.items() if k != "addresses"
        }
        ok = ok and platform.ok

    factories = _load_factories(args.factories)
    has_factories = bool(args.factories)
    addresses: list[str] = []
    if has_factories:
        picked = pick_factory(factories=factories)
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
        payload["cite"] = {
            k: v for k, v in grounded.__dict__.items() if k != "addresses"
        }
        ok = ok and grounded.ok

    if args.data_local != "" or _truthy(args.proprietary_exported):
        sovereignty = evaluate_sovereignty(
            data_local=_truthy(args.data_local),
            weights_local=_truthy(args.weights_local),
            inference_local=_truthy(args.inference_local),
            proprietary_exported=_truthy(args.proprietary_exported),
        )
        payload["sovereignty"] = {
            k: v for k, v in sovereignty.__dict__.items() if k != "addresses"
        }
        ok = ok and sovereignty.ok

    if args.ontology_live != "":
        ontology = evaluate_ontology(
            ontology_live=_truthy(args.ontology_live),
            entities=_split_entities(args.entities),
        )
        payload["ontology"] = {
            k: v for k, v in ontology.__dict__.items() if k != "addresses"
        }
        ok = ok and ontology.ok

    if args.domain_post_trained != "":
        specialization = evaluate_specialization(
            domain_post_trained=_truthy(args.domain_post_trained),
            domain_eval_beats_general=_truthy(args.domain_eval_beats_general),
            chose_bigger_without_domain_eval=_truthy(
                args.chose_bigger_without_domain_eval
            ),
        )
        payload["specialization"] = {
            k: v for k, v in specialization.__dict__.items() if k != "addresses"
        }
        ok = ok and specialization.ok

    if args.trained_on_ops_decisions != "":
        training = evaluate_decision_log_training(
            trained_on_ops_decisions=_truthy(args.trained_on_ops_decisions),
            generic_chat_only=_truthy(args.generic_chat_only),
        )
        payload["decision_log"] = {
            k: v for k, v in training.__dict__.items() if k != "addresses"
        }
        ok = ok and training.ok

    if args.budget_remaining_usd != "":
        allocation = evaluate_scarce_allocation(
            budget_remaining_usd=float(args.budget_remaining_usd),
            concurrent_slots=int(args.concurrent_slots or 0),
            max_slots=int(args.max_slots or 0),
            allocation_evidenced=_truthy(args.allocation_evidenced),
        )
        payload["allocation"] = {
            k: v for k, v in allocation.__dict__.items() if k != "addresses"
        }
        ok = ok and allocation.ok

    if args.own_ops_validated != "":
        proving = evaluate_proving_ground(
            own_ops_validated=_truthy(args.own_ops_validated),
            export_before_proof=_truthy(args.export_before_proof),
        )
        payload["proving_ground"] = {
            k: v for k, v in proving.__dict__.items() if k != "addresses"
        }
        ok = ok and proving.ok

    if args.scoped_task_claim != "":
        honesty = evaluate_specialization_honesty(
            scoped_task_claim=_truthy(args.scoped_task_claim),
            claims_universal_capability=_truthy(args.claims_universal_capability),
        )
        payload["honesty"] = {
            k: v for k, v in honesty.__dict__.items() if k != "addresses"
        }
        ok = ok and honesty.ok

    completeness = require_ai_factory_controls(
        has_platform=has_platform,
        has_factories=has_factories,
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
