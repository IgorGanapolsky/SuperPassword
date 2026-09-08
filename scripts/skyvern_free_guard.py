"""Decide whether Skyvern cloud should run. Fail closed. No paid plans."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

MONTHLY_CAP_USD = 20
HOBBY_PLAN_USD = 29
MAX_STEPS_HARD_CAP = 8

ALLOWED_PUBLIC_HOSTS = frozenset(
    {
        "search.sunbiz.org",
        "dos.myflorida.com",
        "icis.corp.delaware.gov",
        "sam.gov",
        "oig.hhs.gov",
        "news.ycombinator.com",
    }
)

PLAY_HOSTS = frozenset({"play.google.com", "apps.apple.com"})
PAID_PLANS = frozenset({"hobby", "pro", "enterprise", "team"})


@dataclass(frozen=True)
class SkyvernDecision:
    action: str
    allow_cloud_run: bool
    max_steps: int
    reason: str


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def decide_skyvern_use(
    *,
    goal: str,
    url: str,
    api_key_present: bool,
    plan: str,
    max_steps: int = MAX_STEPS_HARD_CAP,
) -> SkyvernDecision:
    del goal
    host = _host(url)
    steps = min(max(int(max_steps), 1), MAX_STEPS_HARD_CAP)

    if host in PLAY_HOSTS:
        return SkyvernDecision(
            action="use_local_play_script",
            allow_cloud_run=False,
            max_steps=0,
            reason="Play/App listings already have verify_play_public_listing.py",
        )

    normalized_plan = (plan or "unknown").strip().lower()
    if normalized_plan in PAID_PLANS:
        return SkyvernDecision(
            action="block_paid_plan",
            allow_cloud_run=False,
            max_steps=0,
            reason=f"{normalized_plan} exceeds the {MONTHLY_CAP_USD} USD monthly cap",
        )

    if not api_key_present:
        return SkyvernDecision(
            action="skip_no_key",
            allow_cloud_run=False,
            max_steps=0,
            reason="SKYVERN_API_KEY not present",
        )

    if host not in ALLOWED_PUBLIC_HOSTS:
        return SkyvernDecision(
            action="block_host",
            allow_cloud_run=False,
            max_steps=0,
            reason=f"host {host or 'empty'} is not on the free public allowlist",
        )

    if normalized_plan != "free":
        return SkyvernDecision(
            action="block_paid_plan",
            allow_cloud_run=False,
            max_steps=0,
            reason="plan must be verified free before a cloud run",
        )

    return SkyvernDecision(
        action="allow_cloud_run",
        allow_cloud_run=True,
        max_steps=steps,
        reason="free plan, key present, allowlisted host",
    )


def main() -> int:
    import argparse
    import json
    import os

    parser = argparse.ArgumentParser(description="Skyvern free-tier gate (no cloud call).")
    parser.add_argument("--goal", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--plan", default="unknown")
    parser.add_argument("--max-steps", type=int, default=MAX_STEPS_HARD_CAP)
    args = parser.parse_args()
    decision = decide_skyvern_use(
        goal=args.goal,
        url=args.url,
        api_key_present=bool(os.environ.get("SKYVERN_API_KEY")),
        plan=args.plan,
        max_steps=args.max_steps,
    )
    print(json.dumps(decision.__dict__, indent=2))
    return 0 if decision.action in {"use_local_play_script", "allow_cloud_run", "skip_no_key"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
