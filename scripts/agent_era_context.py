"""Local ops context for Random Timer (Era Context ideas, zero external cost).

Gives agents MoM category deltas, recurring inventory, and silent-increase
rules against the hard $20/month operating cap — without Era/Context SaaS.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

MONTHLY_CAP_USD = 20.0
FORGOTTEN_AFTER_DAYS = 30

ALLOWED_PLATFORMS = frozenset(
    {
        "local_ops_context",
        "agent_era_context",
        "local_financial_context",
    }
)
DENIED_MARKERS = (
    "era_app",
    "era_context_cloud",
    "context_saas",
    "external_ops_context_vendor",
)


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str


@dataclass(frozen=True)
class CategoryDelta:
    category: str
    previous_usd: float
    current_usd: float
    delta_usd: float
    why: str


@dataclass(frozen=True)
class MomReport:
    deltas: tuple[CategoryDelta, ...]
    up_categories: tuple[str, ...]
    down_categories: tuple[str, ...]
    total_previous_usd: float
    total_current_usd: float
    total_delta_usd: float
    within_cap: bool


@dataclass(frozen=True)
class RecurringInventory:
    active_count: int
    monthly_total_usd: float
    forgotten_names: tuple[str, ...]
    within_cap: bool
    over_cap_usd: float


@dataclass(frozen=True)
class IncreaseAlert:
    name: str
    previous_usd: float
    current_usd: float
    delta_usd: float


@dataclass(frozen=True)
class PromptRecipe:
    id: str
    prompt: str


@dataclass(frozen=True)
class LedgerSummary:
    mtd_usd: float
    remaining_usd: float
    mom: MomReport
    recurring: RecurringInventory
    increase_alerts: tuple[IncreaseAlert, ...]


def _norm(value: str) -> str:
    return (
        (value or "")
        .strip()
        .lower()
        .replace("-", "_")
        .replace(".", "_")
        .replace(" ", "_")
    )


def evaluate_platform(*, platform: str) -> ControlDecision:
    name = _norm(platform)
    if name in ALLOWED_PLATFORMS:
        return ControlDecision(
            action="allow_local_ops_context",
            ok=True,
            reason="local ops context under operating cap",
        )
    if any(marker in name for marker in DENIED_MARKERS):
        return ControlDecision(
            action="block_external_ops_context_vendor",
            ok=False,
            reason="external Context/Era-style vendor denied",
        )
    return ControlDecision(
        action="block_external_ops_context_vendor",
        ok=False,
        reason="unknown platform denied",
    )


def remaining_cap(*, mtd_usd: float, cap_usd: float = MONTHLY_CAP_USD) -> float:
    return max(0.0, round(cap_usd - float(mtd_usd), 2))


def compare_categories(
    *,
    previous: Mapping[str, float],
    current: Mapping[str, float],
    cap_usd: float = MONTHLY_CAP_USD,
) -> MomReport:
    keys = sorted(set(previous) | set(current))
    deltas: list[CategoryDelta] = []
    up: list[str] = []
    down: list[str] = []
    for key in keys:
        prev = float(previous.get(key) or 0.0)
        curr = float(current.get(key) or 0.0)
        delta = round(curr - prev, 2)
        if delta > 0:
            why = f"{key} up ${delta:.2f} vs prior month"
            up.append(key)
        elif delta < 0:
            why = f"{key} down ${abs(delta):.2f} vs prior month"
            down.append(key)
        else:
            why = f"{key} flat vs prior month"
        deltas.append(
            CategoryDelta(
                category=key,
                previous_usd=prev,
                current_usd=curr,
                delta_usd=delta,
                why=why,
            )
        )
    total_prev = round(sum(float(v) for v in previous.values()), 2)
    total_curr = round(sum(float(v) for v in current.values()), 2)
    return MomReport(
        deltas=tuple(deltas),
        up_categories=tuple(up),
        down_categories=tuple(down),
        total_previous_usd=total_prev,
        total_current_usd=total_curr,
        total_delta_usd=round(total_curr - total_prev, 2),
        within_cap=total_curr <= cap_usd,
    )


def inventory_recurring(
    *,
    items: Sequence[Mapping[str, Any]],
    cap_usd: float = MONTHLY_CAP_USD,
    forgotten_after_days: int = FORGOTTEN_AFTER_DAYS,
) -> RecurringInventory:
    active = [dict(item) for item in items if bool(item.get("active"))]
    total = round(sum(float(item.get("monthly_usd") or 0.0) for item in active), 2)
    forgotten = tuple(
        str(item.get("name"))
        for item in active
        if int(item.get("last_seen_days") or 0) >= forgotten_after_days
    )
    over = round(max(0.0, total - cap_usd), 2)
    return RecurringInventory(
        active_count=len(active),
        monthly_total_usd=total,
        forgotten_names=forgotten,
        within_cap=total <= cap_usd,
        over_cap_usd=over,
    )


def apply_increase_rules(
    *,
    previous: Mapping[str, float],
    current: Mapping[str, float],
    watched: Sequence[str],
) -> list[IncreaseAlert]:
    alerts: list[IncreaseAlert] = []
    for name in watched:
        prev = float(previous.get(name) or 0.0)
        curr = float(current.get(name) or 0.0)
        delta = round(curr - prev, 2)
        if delta > 0:
            alerts.append(
                IncreaseAlert(
                    name=name,
                    previous_usd=prev,
                    current_usd=curr,
                    delta_usd=delta,
                )
            )
    return alerts


def assistant_prompt_recipes() -> tuple[PromptRecipe, ...]:
    return (
        PromptRecipe(
            id="mom_categories",
            prompt=(
                "Am I above last month on operating outlay? Which categories went up? "
                "Use marketing/data/operating_budget_ledger.json and remaining_cap."
            ),
        ),
        PromptRecipe(
            id="recurring_inventory",
            prompt=(
                "List every active recurring subscription or SaaS charge in the ledger. "
                "How much is that per month total, and which look forgotten?"
            ),
        ),
        PromptRecipe(
            id="increase_rule",
            prompt=(
                "Create a rule that flags any watched recurring charge that increased "
                "since last month, then report alerts against the $20 operating cap."
            ),
        ),
    )


def summarize_ledger(
    ledger: Mapping[str, Any],
    *,
    current_month: str,
    previous_month: str,
) -> LedgerSummary:
    months = dict(ledger.get("months") or {})
    current = {k: float(v) for k, v in dict(months.get(current_month) or {}).items()}
    previous = {k: float(v) for k, v in dict(months.get(previous_month) or {}).items()}
    cap = float(ledger.get("cap_usd") or MONTHLY_CAP_USD)
    mom = compare_categories(previous=previous, current=current, cap_usd=cap)
    recurring = inventory_recurring(items=list(ledger.get("recurring") or []), cap_usd=cap)
    mtd = mom.total_current_usd
    watched: list[str] = []
    prev_recurring: dict[str, float] = {}
    curr_recurring: dict[str, float] = {}
    for item in ledger.get("recurring") or []:
        name = str(item.get("name") or "")
        if not name:
            continue
        watched.append(name)
        curr_val = float(item["monthly_usd"]) if "monthly_usd" in item else 0.0
        if "previous_monthly_usd" in item:
            prev_val = float(item["previous_monthly_usd"])
        else:
            prev_val = curr_val
        curr_recurring[name] = curr_val
        prev_recurring[name] = prev_val
    alerts = apply_increase_rules(
        previous=prev_recurring,
        current=curr_recurring,
        watched=watched,
    )
    return LedgerSummary(
        mtd_usd=mtd,
        remaining_usd=remaining_cap(mtd_usd=mtd, cap_usd=cap),
        mom=mom,
        recurring=recurring,
        increase_alerts=tuple(alerts),
    )


__all__ = [
    "CategoryDelta",
    "ControlDecision",
    "FORGOTTEN_AFTER_DAYS",
    "IncreaseAlert",
    "LedgerSummary",
    "MONTHLY_CAP_USD",
    "MomReport",
    "PromptRecipe",
    "RecurringInventory",
    "apply_increase_rules",
    "assistant_prompt_recipes",
    "compare_categories",
    "evaluate_platform",
    "inventory_recurring",
    "remaining_cap",
    "summarize_ledger",
]
