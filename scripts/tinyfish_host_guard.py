"""Decide whether TinyFish cloud should run. Fail closed. No add-funds path."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

MONTHLY_CAP_USD = 20
MAX_AGENT_STEPS = 3

ALLOWED_FETCH_HOSTS = frozenset(
    {
        "broward.deedauction.net",
        "search.sunbiz.org",
        "dos.myflorida.com",
        "icis.corp.delaware.gov",
    }
)

PLAY_HOSTS = frozenset({"play.google.com", "apps.apple.com"})
BLOCKED_OPERATIONS = frozenset({"top_up", "auto_reload", "upgrade"})


@dataclass(frozen=True)
class TinyfishDecision:
    action: str
    allow_cloud_call: bool
    max_steps: int
    reason: str


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def decide_tinyfish_use(
    *,
    goal: str,
    url: str,
    operation: str,
    api_key_present: bool,
    auto_reload_configured: bool,
    remaining_credit: float,
    max_steps: int = MAX_AGENT_STEPS,
) -> TinyfishDecision:
    del goal
    host = _host(url)
    op = (operation or "").strip().lower()
    steps = min(max(int(max_steps), 1), MAX_AGENT_STEPS)

    if op in BLOCKED_OPERATIONS:
        return TinyfishDecision(
            action="block_add_credit",
            allow_cloud_call=False,
            max_steps=0,
            reason="adding credit and auto-refill are blocked under the monthly cap",
        )

    if host in PLAY_HOSTS:
        return TinyfishDecision(
            action="use_local_play_script",
            allow_cloud_call=False,
            max_steps=0,
            reason="Play/App listings already have verify_play_public_listing.py",
        )

    if auto_reload_configured:
        return TinyfishDecision(
            action="block_auto_refill",
            allow_cloud_call=False,
            max_steps=0,
            reason="auto-refill must stay off so existing credit cannot refill",
        )

    if not api_key_present:
        return TinyfishDecision(
            action="skip_no_key",
            allow_cloud_call=False,
            max_steps=0,
            reason="TinyFish CLI credential not present",
        )

    if float(remaining_credit) <= 0:
        return TinyfishDecision(
            action="skip_no_credit",
            allow_cloud_call=False,
            max_steps=0,
            reason="no remaining TinyFish credit; do not add more",
        )

    if host not in ALLOWED_FETCH_HOSTS:
        return TinyfishDecision(
            action="block_host",
            allow_cloud_call=False,
            max_steps=0,
            reason=f"host {host or 'empty'} is not on the county/entity allowlist",
        )

    if op == "fetch":
        return TinyfishDecision(
            action="allow_fetch",
            allow_cloud_call=True,
            max_steps=0,
            reason="credit present, key present, allowlisted host, fetch only",
        )

    if op == "agent":
        return TinyfishDecision(
            action="allow_agent",
            allow_cloud_call=True,
            max_steps=steps,
            reason="credit present, key present, allowlisted host, agent steps clamped",
        )

    return TinyfishDecision(
        action="block_host",
        allow_cloud_call=False,
        max_steps=0,
        reason=f"operation {op or 'empty'} is not fetch or agent",
    )


def main() -> int:
    import argparse
    import json
    import os

    parser = argparse.ArgumentParser(description="TinyFish host gate (no cloud call).")
    parser.add_argument("--goal", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--operation", default="fetch")
    parser.add_argument("--auto-reload", action="store_true")
    parser.add_argument("--remaining", type=float, default=0.0)
    parser.add_argument("--max-steps", type=int, default=MAX_AGENT_STEPS)
    args = parser.parse_args()
    decision = decide_tinyfish_use(
        goal=args.goal,
        url=args.url,
        operation=args.operation,
        api_key_present=bool(os.environ.get("TINYFISH_API_KEY")),
        auto_reload_configured=args.auto_reload,
        remaining_credit=args.remaining,
        max_steps=args.max_steps,
    )
    print(json.dumps(decision.__dict__, indent=2))
    return 0 if decision.action in {
        "use_local_play_script",
        "allow_fetch",
        "allow_agent",
        "skip_no_key",
        "skip_no_credit",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
