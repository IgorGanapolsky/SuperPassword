"""DeepSeek V4 peak/off-peak router for Random Timer harness.

Ground truth (2026-09-11):
- Official pricing: https://api-docs.deepseek.com/quick_start/pricing
- Peak UTC Mon-Fri: 01:00-04:00 and 06:00-10:00; else off-peak (50% off).
- From 2026-09-14 04:00 UTC (12:00 Beijing): `deepseek-v4-pro` requests are
  served by V4.1 Flash and billed at Flash rates (Pro continuation as alias).
- Email to iganapolsky@gmail.com confirms API service continues after Sep 14.

High-ROI policy under the $20/mo fleet cap:
- Prefer `deepseek-flash` (never pay Pro rates when Flash is better/cheaper).
- Defer non-interactive work out of peak windows.
- Hard DeepSeek sub-cap $10/mo; fail closed to local Hermes when exhausted.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

DEEPSEEK_MONTHLY_CAP_USD = 10.0
FLEET_MONTHLY_CAP_USD = 20.0
LOCAL_FAILOVER_MODEL = "local/hermes-cheap"
FLASH_API_MODEL = "deepseek-flash"
PRO_API_MODEL = "deepseek-v4-pro"
# Pro → Flash routing begins at 12:00 Beijing = 04:00 UTC on 2026-09-14.
PRO_CONTINUATION_CUTOFF_UTC = datetime(2026, 9, 14, 4, 0, tzinfo=timezone.utc)

# USD per 1M tokens (official pricing page, Sep 2026).
RATES = {
    "flash": {
        "off": {"cache_hit": 0.003, "cache_miss": 0.15, "output": 0.6},
        "peak": {"cache_hit": 0.006, "cache_miss": 0.3, "output": 1.2},
    },
    "pro": {
        "off": {"cache_hit": 0.022, "cache_miss": 0.66, "output": 1.98},
        "peak": {"cache_hit": 0.044, "cache_miss": 1.32, "output": 3.96},
    },
}

BillAs = Literal["flash", "pro"]


@dataclass(frozen=True)
class ModelResolution:
    api_model: str
    bill_as: BillAs
    routed_to_flash: bool
    reason: str


@dataclass(frozen=True)
class RouteDecision:
    ok: bool
    action: str
    api_model: str
    bill_as: BillAs
    reason: str
    resume_at_utc: datetime | None = None
    estimated_input_rate_usd_per_m: float = 0.0


def _ensure_aware(now_utc: datetime) -> datetime:
    if now_utc.tzinfo is None:
        return now_utc.replace(tzinfo=timezone.utc)
    return now_utc.astimezone(timezone.utc)


def is_peak_utc(now_utc: datetime) -> bool:
    """Peak only Mon-Fri UTC in [01:00,04:00) U [06:00,10:00)."""
    now = _ensure_aware(now_utc)
    if now.weekday() >= 5:  # Sat/Sun
        return False
    minutes = now.hour * 60 + now.minute
    in_early = 1 * 60 <= minutes < 4 * 60
    in_late = 6 * 60 <= minutes < 10 * 60
    return in_early or in_late


def next_off_peak_utc(now_utc: datetime) -> datetime:
    now = _ensure_aware(now_utc)
    if not is_peak_utc(now):
        return now
    minutes = now.hour * 60 + now.minute
    if 1 * 60 <= minutes < 4 * 60:
        return now.replace(hour=4, minute=0, second=0, microsecond=0)
    if 6 * 60 <= minutes < 10 * 60:
        return now.replace(hour=10, minute=0, second=0, microsecond=0)
    return now


def _norm_model(name: str) -> str:
    return (name or "").strip().lower().replace("_", "-")


def resolve_model_after_pro_continuation(
    *,
    requested: str,
    now_utc: datetime,
) -> ModelResolution:
    now = _ensure_aware(now_utc)
    model = _norm_model(requested)
    wants_pro = "pro" in model and "flash" not in model
    if not wants_pro:
        return ModelResolution(
            api_model=FLASH_API_MODEL,
            bill_as="flash",
            routed_to_flash=False,
            reason="default to deepseek-flash for cost/performance",
        )
    if now >= PRO_CONTINUATION_CUTOFF_UTC:
        return ModelResolution(
            api_model=FLASH_API_MODEL,
            bill_as="flash",
            routed_to_flash=True,
            reason=(
                "Pro continuation after 2026-09-14 04:00 UTC: alias routes to "
                "deepseek-flash and bills at Flash rates"
            ),
        )
    return ModelResolution(
        api_model=PRO_API_MODEL,
        bill_as="pro",
        routed_to_flash=False,
        reason="before cutoff: deepseek-v4-pro still billed as Pro",
    )


def estimate_cost_usd(
    *,
    bill_as: BillAs,
    peak: bool,
    input_tokens: int,
    output_tokens: int,
    cache_hit: bool,
) -> float:
    window = "peak" if peak else "off"
    rates = RATES[bill_as][window]
    input_rate = rates["cache_hit"] if cache_hit else rates["cache_miss"]
    return (input_tokens / 1_000_000.0) * input_rate + (output_tokens / 1_000_000.0) * rates["output"]


def route_request(
    *,
    task: str,
    requested_model: str = FLASH_API_MODEL,
    interactive: bool = True,
    now_utc: datetime | None = None,
    month_spend_usd: float = 0.0,
) -> RouteDecision:
    now = _ensure_aware(now_utc or datetime.now(timezone.utc))
    if month_spend_usd >= DEEPSEEK_MONTHLY_CAP_USD:
        return RouteDecision(
            ok=False,
            action="failover_local",
            api_model=LOCAL_FAILOVER_MODEL,
            bill_as="flash",
            reason=(
                f"DeepSeek sub-cap ${DEEPSEEK_MONTHLY_CAP_USD:.0f}/mo exhausted "
                f"(fleet cap ${FLEET_MONTHLY_CAP_USD:.0f}); use local Hermes"
            ),
        )

    # High-ROI: interactive always prefers Flash; Pro only if explicitly needed
    # AND before cutoff. Background never selects Pro.
    prefer_flash = interactive or "pro" not in _norm_model(requested_model)
    if prefer_flash and "pro" in _norm_model(requested_model):
        # Still resolve continuation for transparency, then force Flash ROI.
        resolved = resolve_model_after_pro_continuation(requested=requested_model, now_utc=now)
        api_model = FLASH_API_MODEL
        bill_as: BillAs = "flash"
        reason = (
            "high-ROI: prefer deepseek-flash over Pro "
            f"(continuation={resolved.routed_to_flash})"
        )
    else:
        resolved = resolve_model_after_pro_continuation(requested=requested_model, now_utc=now)
        api_model = resolved.api_model
        bill_as = resolved.bill_as
        reason = resolved.reason

    peak = is_peak_utc(now)
    input_rate = RATES[bill_as]["peak" if peak else "off"]["cache_miss"]

    if (not interactive) and peak:
        resume = next_off_peak_utc(now)
        return RouteDecision(
            ok=False,
            action="defer_off_peak",
            api_model=api_model,
            bill_as=bill_as,
            reason=f"defer background '{task}' until off-peak for 50% discount",
            resume_at_utc=resume,
            estimated_input_rate_usd_per_m=input_rate,
        )

    return RouteDecision(
        ok=True,
        action="allow_now",
        api_model=api_model,
        bill_as=bill_as,
        reason=reason,
        estimated_input_rate_usd_per_m=input_rate,
    )


def doctor(*, now_utc: datetime | None = None, month_spend_usd: float = 0.0) -> dict:
    now = _ensure_aware(now_utc or datetime.now(timezone.utc))
    peak = is_peak_utc(now)
    return {
        "now_utc": now.isoformat(),
        "peak": peak,
        "window": "peak" if peak else "off-peak",
        "next_off_peak_utc": next_off_peak_utc(now).isoformat(),
        "deepseek_month_spend_usd": month_spend_usd,
        "deepseek_cap_usd": DEEPSEEK_MONTHLY_CAP_USD,
        "remaining_usd": max(DEEPSEEK_MONTHLY_CAP_USD - month_spend_usd, 0.0),
        "pro_continuation_active": now >= PRO_CONTINUATION_CUTOFF_UTC,
        "preferred_model": FLASH_API_MODEL,
        "flash_cache_miss_usd_per_m": RATES["flash"]["peak" if peak else "off"]["cache_miss"],
    }


__all__ = [
    "DEEPSEEK_MONTHLY_CAP_USD",
    "FLEET_MONTHLY_CAP_USD",
    "ModelResolution",
    "RouteDecision",
    "doctor",
    "estimate_cost_usd",
    "is_peak_utc",
    "next_off_peak_utc",
    "resolve_model_after_pro_continuation",
    "route_request",
]


if __name__ == "__main__":
    import json
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "doctor"
    if cmd == "doctor":
        print(json.dumps(doctor(), indent=2))
    elif cmd == "route":
        task = sys.argv[2] if len(sys.argv) > 2 else "interactive"
        interactive = "--background" not in sys.argv
        d = route_request(task=task, interactive=interactive)
        print(
            json.dumps(
                {
                    "ok": d.ok,
                    "action": d.action,
                    "api_model": d.api_model,
                    "bill_as": d.bill_as,
                    "reason": d.reason,
                    "resume_at_utc": d.resume_at_utc.isoformat() if d.resume_at_utc else None,
                },
                indent=2,
            )
        )
    else:
        raise SystemExit("usage: agent_deepseek_v4_router.py [doctor|route <task>] [--background]")
