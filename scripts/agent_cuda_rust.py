"""NVIDIA CUDA Rust steal: Tile-first ownership + launch contracts for ops. Fail closed."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset(
    {
        "gpu_tflops",
        "cuda_kernel_count",
        "press_mentions",
        "crates_downloads",
        "nightly_toolchain_age",
    }
)
DENIED_PLATFORMS = frozenset(
    {
        "cuda_cloud_gpu_rental",
        "hf_paid_gpu",
        "nvidia_foundry_cloud",
        "a100_spot_fleet",
        "cutile_cloud_ci",
        "oxide_nightly_ci_spend",
    }
)
ALLOWED_PLATFORMS = frozenset(
    {
        "local_cuda_rust_controls",
        "agent_cuda_rust",
        "tile_first_ops",
        "simt_explicit_ops",
        "ops_ownership_gate",
    }
)
DOMAIN_METRICS = frozenset(
    {
        "iap_attempt",
        "wqtu",
        "timer_completed",
        "paywall_attempt",
        "store_version_verify",
        "alias_reject",
        "launch_contract_pass",
    }
)
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
            action="allow_local_cuda_rust_controls",
            ok=True,
            reason="run Tile/SIMT ownership gates locally under the monthly cap",
        )
    if name in DENIED_PLATFORMS or "gpu_rental" in name or "a100" in name:
        return ControlDecision(
            action="block_gpu_spend",
            ok=False,
            reason="CUDA cloud / paid GPU rental stays denied under the monthly cap",
        )
    return ControlDecision(
        action="block_gpu_spend",
        ok=False,
        reason="unknown CUDA Rust platform is denied",
    )


def evaluate_track_preference(
    *,
    prefer_tile: bool,
    simt_selected: bool,
    explicit_control_needed: bool,
) -> ControlDecision:
    if prefer_tile and not simt_selected:
        return ControlDecision(
            action="allow_tile_first",
            ok=True,
            reason="prefer Tile (high-level safe defaults) before SIMT",
        )
    if simt_selected and explicit_control_needed:
        return ControlDecision(
            action="allow_simt_with_need",
            ok=True,
            reason="SIMT allowed only when explicit thread/memory control is required",
        )
    if simt_selected and not explicit_control_needed:
        return ControlDecision(
            action="block_simt_without_need",
            ok=False,
            reason="do not drop to SIMT/unsafe control when Tile is enough",
        )
    return ControlDecision(
        action="block_simt_without_need",
        ok=False,
        reason="pick Tile first or justify SIMT with an explicit-control need",
    )


def evaluate_aliasing(
    *,
    input_ids: Sequence[str],
    output_ids: Sequence[str],
) -> ControlDecision:
    inputs = {str(x).strip() for x in input_ids if str(x).strip()}
    outputs = {str(x).strip() for x in output_ids if str(x).strip()}
    overlap = inputs & outputs
    if overlap:
        return ControlDecision(
            action="block_aliasing",
            ok=False,
            reason=f"plan-time alias reject: shared buffers {sorted(overlap)}",
        )
    if not inputs or not outputs:
        return ControlDecision(
            action="block_aliasing",
            ok=False,
            reason="inputs and outputs must both be declared before launch",
        )
    return ControlDecision(
        action="allow_no_alias",
        ok=True,
        reason="no input/output buffer aliasing at plan time",
    )


def evaluate_disjoint_ownership(
    *,
    exclusive_write_slots: bool,
    shared_mutable: bool,
) -> ControlDecision:
    if exclusive_write_slots and not shared_mutable:
        return ControlDecision(
            action="allow_disjoint_writes",
            ok=True,
            reason="parallel workers get exclusive write slots (DisjointSlice analog)",
        )
    return ControlDecision(
        action="block_shared_mutable",
        ok=False,
        reason="shared mutable ownership across parallel agents is denied",
    )


def evaluate_launch_contract(
    *,
    contract_declared: bool,
    config_validated: bool,
) -> ControlDecision:
    if contract_declared and config_validated:
        return ControlDecision(
            action="allow_launch_contract",
            ok=True,
            reason="launch shape declared and validated before safe launch",
        )
    return ControlDecision(
        action="block_unvalidated_launch",
        ok=False,
        reason="launch without declared+validated contract is denied",
    )


def evaluate_doctor(*, doctor_pass: bool) -> ControlDecision:
    if doctor_pass:
        return ControlDecision(
            action="allow_doctor_pass",
            ok=True,
            reason="prereq doctor passed (cargo oxide doctor analog)",
        )
    return ControlDecision(
        action="block_doctor_fail",
        ok=False,
        reason="run doctor and fix prereqs before scaffolding or launch",
    )


def evaluate_lazy_sync(
    *,
    chain_recorded: bool,
    synced: bool,
    ownership_returned: bool,
) -> ControlDecision:
    if chain_recorded and not synced:
        return ControlDecision(
            action="allow_lazy_plan",
            ok=True,
            reason="ops recorded as lazy chain; nothing executes until sync",
        )
    if chain_recorded and synced and ownership_returned:
        return ControlDecision(
            action="allow_synced_chain",
            ok=True,
            reason="sync executed and ownership of artifacts returned to host",
        )
    if synced and not ownership_returned:
        return ControlDecision(
            action="block_sync_without_return",
            ok=False,
            reason="sync must return ownership of tensors/artifacts to the host",
        )
    return ControlDecision(
        action="block_blind_execute",
        ok=False,
        reason="do not execute without a recorded lazy chain",
    )


def evaluate_readiness(
    *,
    maturity: str,
    claim_production: bool,
) -> ControlDecision:
    stage = _norm(maturity)
    if claim_production and stage in {"alpha", "early_alpha", "experimental"}:
        return ControlDecision(
            action="block_alpha_as_production",
            ok=False,
            reason="alpha CUDA Rust tooling is not confirmed for production claims",
        )
    if claim_production and stage in {"stable", "ga", "production"}:
        return ControlDecision(
            action="allow_production_claim",
            ok=True,
            reason="production claim only when maturity is GA/stable with evidence",
        )
    if not claim_production:
        return ControlDecision(
            action="allow_alpha_local_use",
            ok=True,
            reason="local alpha use allowed without production claims",
        )
    return ControlDecision(
        action="block_alpha_as_production",
        ok=False,
        reason="maturity unknown — fail closed on production claims",
    )


def evaluate_interop(
    *,
    lock_in: bool,
    shared_contract: bool,
) -> ControlDecision:
    if lock_in:
        return ControlDecision(
            action="block_tool_lockin",
            ok=False,
            reason="do not lock agent ops into one language/path without interop",
        )
    if shared_contract:
        return ControlDecision(
            action="allow_interop",
            ok=True,
            reason="multi-track interop with a shared launch/ownership contract",
        )
    return ControlDecision(
        action="block_tool_lockin",
        ok=False,
        reason="interop requires an explicit shared contract across tracks",
    )


def _kernel_clears(raw: Mapping[str, object]) -> bool:
    return evaluate_platform(platform=str(raw.get("platform") or "")).ok


def pick_kernel(*, kernels: Sequence[Mapping[str, object]]) -> ControlDecision:
    for raw in kernels:
        kid = str(raw.get("id") or "").strip()
        if kid and _kernel_clears(raw):
            return ControlDecision(
                action="allow_local_kernel",
                ok=True,
                reason="local CUDA Rust ownership kernel cleared",
                addresses=(f"crs:{kid}",),
            )
    return ControlDecision(
        action="block_no_local_kernel",
        ok=False,
        reason="no kernel cleared local CUDA Rust gates",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_cuda_rust",
            ok=True,
            reason="cite is the local CUDA Rust kernel address",
        )
    return ControlDecision(
        action="block_off_cuda_rust",
        ok=False,
        reason="cite is not the local CUDA Rust address",
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


def require_cuda_rust_controls(
    *,
    has_platform: bool,
    has_kernels: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_platform and has_kernels and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="platform, kernels, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing platform, kernels, or cite",
    )


def _load_kernels(path: str) -> list[dict[str, object]]:
    if not path:
        return []
    raw = Path(path)
    if not raw.is_file():
        return []
    payload = json.loads(raw.read_text())
    items = payload.get("kernels", payload) if isinstance(payload, Mapping) else payload
    return [dict(item) for item in items if isinstance(item, Mapping)]


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _csv(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip()]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Local CUDA Rust ownership/launch controls (no GPU cloud spend)."
    )
    parser.add_argument("--platform", default="")
    parser.add_argument("--kernels", default="")
    parser.add_argument("--cite", default="")
    parser.add_argument("--prefer-tile", default="")
    parser.add_argument("--simt-selected", default="0")
    parser.add_argument("--explicit-control-needed", default="0")
    parser.add_argument("--input-ids", default="")
    parser.add_argument("--output-ids", default="")
    parser.add_argument("--exclusive-write-slots", default="")
    parser.add_argument("--shared-mutable", default="0")
    parser.add_argument("--contract-declared", default="")
    parser.add_argument("--config-validated", default="0")
    parser.add_argument("--doctor-pass", default="")
    parser.add_argument("--chain-recorded", default="")
    parser.add_argument("--synced", default="0")
    parser.add_argument("--ownership-returned", default="0")
    parser.add_argument("--maturity", default="")
    parser.add_argument("--claim-production", default="0")
    parser.add_argument("--lock-in", default="")
    parser.add_argument("--shared-contract", default="0")
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

    kernels = _load_kernels(args.kernels)
    has_kernels = bool(args.kernels)
    addresses: list[str] = []
    if has_kernels:
        picked = pick_kernel(kernels=kernels)
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

    if args.prefer_tile != "":
        track = evaluate_track_preference(
            prefer_tile=_truthy(args.prefer_tile),
            simt_selected=_truthy(args.simt_selected),
            explicit_control_needed=_truthy(args.explicit_control_needed),
        )
        payload["track"] = {k: v for k, v in track.__dict__.items() if k != "addresses"}
        ok = ok and track.ok

    if args.input_ids != "" or args.output_ids != "":
        alias = evaluate_aliasing(
            input_ids=_csv(args.input_ids),
            output_ids=_csv(args.output_ids),
        )
        payload["aliasing"] = {
            k: v for k, v in alias.__dict__.items() if k != "addresses"
        }
        ok = ok and alias.ok

    if args.exclusive_write_slots != "":
        disjoint = evaluate_disjoint_ownership(
            exclusive_write_slots=_truthy(args.exclusive_write_slots),
            shared_mutable=_truthy(args.shared_mutable),
        )
        payload["disjoint"] = {
            k: v for k, v in disjoint.__dict__.items() if k != "addresses"
        }
        ok = ok and disjoint.ok

    if args.contract_declared != "":
        contract = evaluate_launch_contract(
            contract_declared=_truthy(args.contract_declared),
            config_validated=_truthy(args.config_validated),
        )
        payload["launch_contract"] = {
            k: v for k, v in contract.__dict__.items() if k != "addresses"
        }
        ok = ok and contract.ok

    if args.doctor_pass != "":
        doctor = evaluate_doctor(doctor_pass=_truthy(args.doctor_pass))
        payload["doctor"] = {
            k: v for k, v in doctor.__dict__.items() if k != "addresses"
        }
        ok = ok and doctor.ok

    if args.chain_recorded != "":
        lazy = evaluate_lazy_sync(
            chain_recorded=_truthy(args.chain_recorded),
            synced=_truthy(args.synced),
            ownership_returned=_truthy(args.ownership_returned),
        )
        payload["lazy_sync"] = {
            k: v for k, v in lazy.__dict__.items() if k != "addresses"
        }
        ok = ok and lazy.ok

    if args.maturity != "":
        ready = evaluate_readiness(
            maturity=args.maturity,
            claim_production=_truthy(args.claim_production),
        )
        payload["readiness"] = {
            k: v for k, v in ready.__dict__.items() if k != "addresses"
        }
        ok = ok and ready.ok

    if args.lock_in != "":
        interop = evaluate_interop(
            lock_in=_truthy(args.lock_in),
            shared_contract=_truthy(args.shared_contract),
        )
        payload["interop"] = {
            k: v for k, v in interop.__dict__.items() if k != "addresses"
        }
        ok = ok and interop.ok

    completeness = require_cuda_rust_controls(
        has_platform=has_platform,
        has_kernels=has_kernels,
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
