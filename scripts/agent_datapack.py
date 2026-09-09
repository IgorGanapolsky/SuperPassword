"""Meko steal: local datapack + decision traces. Fail closed. No mekodata cloud."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset({"tokens", "token_savings", "agent_count", "memory_mb"})
MEKO_PLATFORMS = frozenset(
    {
        "meko",
        "meko_cloud",
        "mekodata",
        "mekodata_ai",
        "mcp_mekodata_ai",
        "cloud_mekodata",
        "yugabyte_meko",
        "mem0_hosted",
    }
)
ALLOWED_PLATFORMS = frozenset(
    {"local_datapack", "agent_datapack", "local_memory_pack", "decision_trace_local"}
)
ALLOWED_LAYERS = frozenset({"memory", "knowledge", "conversation", "trace", "decision_trace"})
ALLOWED_STORAGE = frozenset(
    {"local_json", "marketing_data", "claude_memory", "repo_json", "local_file"}
)
REMOTE_STORAGE = frozenset(
    {
        "mcp_mekodata_ai",
        "meko_mcp",
        "cloud_mekodata",
        "remote_mcp",
        "yugabyte_hosted",
        "mem0_cloud",
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
            action="allow_local_datapack",
            ok=True,
            reason="keep shared context in a local datapack under the monthly cap",
        )
    if name in MEKO_PLATFORMS or "meko" in name or "mekodata" in name:
        return ControlDecision(
            action="block_meko_cloud",
            ok=False,
            reason="Meko cloud / mcp.mekodata.ai signup stays denied under the $20 cap",
        )
    return ControlDecision(
        action="block_meko_cloud",
        ok=False,
        reason="unknown datapack platform is denied",
    )


def evaluate_layer(*, layer: str, storage: str) -> ControlDecision:
    layer_name = _norm(layer)
    storage_name = _norm(storage)
    if storage_name in REMOTE_STORAGE or "meko" in storage_name or "mcp" in storage_name:
        return ControlDecision(
            action="block_remote_layer",
            ok=False,
            reason="remote MCP / Meko storage is denied; use local JSON packs",
        )
    if layer_name in ALLOWED_LAYERS and storage_name in ALLOWED_STORAGE:
        return ControlDecision(
            action="allow_local_layer",
            ok=True,
            reason="memory, knowledge, conversations, and traces stay local",
        )
    return ControlDecision(
        action="block_remote_layer",
        ok=False,
        reason="unknown layer or storage is denied",
    )


def evaluate_promote(*, promoted: bool, verified: bool) -> ControlDecision:
    if promoted and verified:
        return ControlDecision(
            action="allow_promote_verified",
            ok=True,
            reason="promote memory to shared knowledge only after verification",
        )
    if promoted and not verified:
        return ControlDecision(
            action="block_promote_unverified",
            ok=False,
            reason="unverified memories must not become shared knowledge",
        )
    return ControlDecision(
        action="allow_private_memory",
        ok=True,
        reason="private memory may stay unpromoted",
    )


def evaluate_recall(*, queried_local: bool, reprocess_frontier: bool) -> ControlDecision:
    if queried_local and not reprocess_frontier:
        return ControlDecision(
            action="allow_local_recall",
            ok=True,
            reason="query the local pack before re-burning frontier tokens",
        )
    if queried_local and reprocess_frontier:
        return ControlDecision(
            action="allow_local_recall",
            ok=True,
            reason="local recall already ran; frontier reprocess is intentional",
        )
    if reprocess_frontier and not queried_local:
        return ControlDecision(
            action="block_reprocess_without_recall",
            ok=False,
            reason="do not reprocess through a frontier model without local recall first",
        )
    return ControlDecision(
        action="block_reprocess_without_recall",
        ok=False,
        reason="local recall is required before claiming shared context",
    )


def _pack_clears(pack: Mapping[str, object]) -> bool:
    layer = evaluate_layer(
        layer=str(pack.get("layer") or ""),
        storage=str(pack.get("storage") or ""),
    )
    promoted = bool(pack.get("promoted"))
    verified = bool(pack.get("verified"))
    promote = evaluate_promote(promoted=promoted, verified=verified)
    return layer.ok and promote.ok


def pick_pack(*, packs: Sequence[Mapping[str, object]]) -> ControlDecision:
    for raw in packs:
        pack_id = str(raw.get("id") or "").strip()
        if pack_id and _pack_clears(raw):
            return ControlDecision(
                action="allow_local_pack",
                ok=True,
                reason="keep local knowledge packs with verified cites",
                addresses=(f"pack:{pack_id}",),
            )
    return ControlDecision(
        action="block_no_local_pack",
        ok=False,
        reason="no pack cleared local datapack controls",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_datapack",
            ok=True,
            reason="cite is the local datapack decision address",
        )
    return ControlDecision(
        action="block_off_datapack",
        ok=False,
        reason="cite is not the local datapack address",
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


def require_datapack_controls(
    *,
    has_platform: bool,
    has_packs: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_platform and has_packs and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="platform, packs, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing platform, packs, or cite",
    )


def _load_packs(path: str) -> list[dict[str, object]]:
    if not path:
        return []
    raw = Path(path)
    if not raw.is_file():
        return []
    payload = json.loads(raw.read_text())
    items = payload.get("packs", payload) if isinstance(payload, Mapping) else payload
    return [dict(item) for item in items if isinstance(item, Mapping)]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Local agent datapack + decision traces (no Meko cloud)."
    )
    parser.add_argument("--platform", default="")
    parser.add_argument("--packs", default="")
    parser.add_argument("--cite", default="")
    parser.add_argument("--queried-local", default="")
    parser.add_argument("--reprocess-frontier", default="0")
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

    packs = _load_packs(args.packs)
    has_packs = bool(args.packs)
    addresses: list[str] = []
    if has_packs:
        picked = pick_pack(packs=packs)
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

    if args.queried_local != "":
        queried = str(args.queried_local).strip().lower() in {"1", "true", "yes"}
        reprocess = str(args.reprocess_frontier).strip().lower() in {"1", "true", "yes"}
        recall = evaluate_recall(queried_local=queried, reprocess_frontier=reprocess)
        payload["recall"] = {
            k: v for k, v in recall.__dict__.items() if k != "addresses"
        }
        ok = ok and recall.ok

    completeness = require_datapack_controls(
        has_platform=has_platform,
        has_packs=has_packs,
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
