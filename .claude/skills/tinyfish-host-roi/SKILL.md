---
name: tinyfish-host-roi
description: >
  Routes TinyFish onboarding vs BrowserOS vs Play listing scripts. Use when the
  user mentions TinyFish, agent.tinyfish.ai/onboarding, @tiny-fish/cli, or asks
  whether TinyFish helps Random Timer. Fail closed on add-credit and auto-refill.
---

# TinyFish host ROI (Random Timer)

Signed-in console (2026-09-08, `iganapolsky@gmail.com`):

- `https://agent.tinyfish.ai/onboarding` redirects to `/home`. Onboarding is already finished.
- Get-started missions: **2 of 4** done (first CLI/MCP call + three uses). Remaining: connect an agent and return after 3 days.
- CLI `0.40.0` doctor: credential present, MCP reachable, authenticated `listRuns`.
- Account status CLI: remaining credit **10**, auto-refill **off**.
- Meter rates (CLI): agent **0.016 per step**, browser **0.002 per minute**.
- `tinyfish connect cursor` would merge a **plaintext API key** into `~/.cursor/mcp.json`. Do not run it. Use the CLI.

agy already owns `scripts/tinyfish_realestate_harvester.py` in RealEstate-lane-agy. Do not duplicate it here.

## Does it help?

| Surface | Use TinyFish? | Use instead |
| --- | --- | --- |
| Random Timer Play/App listing | No | `scripts/verify_play_public_listing.py` |
| Play Console / ASC (logged in) | No | BrowserOS neo + store APIs |
| WQTU / PostHog | No | PostHog MCP `execute-sql` |
| Broward / Sunbiz / Delaware HTML | Fetch only after `tinyfish_host_guard` | agy harvester if it already covers the portal |
| Add credit / auto-refill | Never | Leave existing credit as-is |

## Before any TinyFish cloud call

```bash
npx -y @tiny-fish/cli@latest doctor
python3 scripts/tinyfish_host_guard.py --goal "Broward auction fetch" --url "https://broward.deedauction.net/" --operation fetch --remaining 10
```

Allow only when JSON `allow_cloud_call` is true. Cap agent steps at 3. Never enable auto-refill. Never `connect --all`.
