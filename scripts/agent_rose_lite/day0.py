"""Day-0 model bringup protocol (Perplexity GPT-OSS Day-0 adapted).

Stages mirrored from ROSE bringup:
1. weight_map / capability inventory
2. tp1_smoke (single-path forward equivalent)
3. parallelism_or_fallback (local MLX/Ollama vs cloud)
4. cost_matrix under $20/mo hard cap
5. promote_or_hold
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Day0BringupReport:
    model_id: str
    stages: Dict[str, str]
    estimated_monthly_usd: float
    within_budget: bool
    promote: bool
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "stages": self.stages,
            "estimated_monthly_usd": self.estimated_monthly_usd,
            "within_budget": self.within_budget,
            "promote": self.promote,
            "notes": self.notes,
        }


def run_day0_bringup(
    model_id: str,
    probes: Dict[str, bool],
    monthly_budget_usd: float = 20.0,
) -> Day0BringupReport:
    stages: Dict[str, str] = {}
    notes: List[str] = []

    # 1. Weight / capability map
    stages["weight_map"] = "ok" if model_id else "fail"
    if not model_id:
        notes.append("missing model_id")

    # 2. TP=1 smoke: tokenizer + one forward-equivalent probe
    if probes.get("harmony_tokenizer") or probes.get("local_mlx_or_ollama"):
        stages["tp1_smoke"] = "ok"
    else:
        stages["tp1_smoke"] = "hold"
        notes.append("no local tokenizer/runtime probe; hold cloud until verified")

    # 3. Parallelism / hardware path (FP8 analog: prefer quantized local)
    if probes.get("local_mlx_or_ollama"):
        stages["parallelism_or_fallback"] = "local_zero_cost"
        estimated = 0.0
    elif probes.get("fp8_or_int4"):
        stages["parallelism_or_fallback"] = "quantized_eval_only"
        estimated = 0.0  # eval harness is free; paid serving requires CEO approval
        notes.append("quantized path recorded; paid GPU serving not auto-started ($20 cap)")
    else:
        stages["parallelism_or_fallback"] = "hold"
        estimated = 0.0
        notes.append("no local or quantized path; do not spend")

    # 4. Cost matrix under hard cap
    within = estimated <= monthly_budget_usd
    stages["cost_matrix"] = "within_cap" if within else "exceeds_cap"

    # 5. Promote only if smoke ok and within budget
    promote = stages.get("tp1_smoke") == "ok" and within and stages["weight_map"] == "ok"
    stages["promote_or_hold"] = "promote" if promote else "hold"

    return Day0BringupReport(
        model_id=model_id,
        stages=stages,
        estimated_monthly_usd=estimated,
        within_budget=within,
        promote=promote,
        notes=notes,
    )
