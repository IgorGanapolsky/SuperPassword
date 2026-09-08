# Agent compounding ROI (PlayerZero-inspired, $0)

Adapted from PlayerZero's *Engineering Leader's Operational Guide to Compounding ROI with AI* (2026). Steal the **method**, not the product.

| PlayerZero | Random-Timer control plane |
| --- | --- |
| Mice vs hawks | Single-player session AI vs a shared lifecycle graph |
| Phase 2 world model | Persistent `code + telemetry + deploys + resolution_history` |
| Recovery vs prevention | Every resolved incident must encode a watch/gate |
| Velocity dashboards | Rejected; require WQTU, paywall attempt→success, recurrence, escape rate |
| Agents spin humans for cleanup | Fail; humans are spun in for **judgment** only |

## What we deliberately did *not* copy

- PlayerZero SaaS, paid production-engineering platforms, or any new metered service.
- Board slides that treat PR velocity or token spend as ROI.

## Fail-closed CLI

```bash
python3 scripts/compounding_roi.py \
  --source-stage sre \
  --target-stages quality,review,planning \
  --context-id incident-paywall-dismiss-20260908 \
  --metrics wqtu,paywall_attempt_success,incident_recurrence \
  --resolved \
  --pattern 'paywall_view with zero purchase_attempt' \
  --gate 'scripts/compounding_roi.py' \
  --cycle quality_to_simulation,simulation_to_prevention,prevention_to_triage,triage_to_knowledge,knowledge_to_simulation \
  --sources code,telemetry,deploys,resolution_history \
  --persists
```

Allow only when every JSON `ok` is true (process exit 0). Incomplete inputs exit 2.

## Rank work

`rank_work` scores `(paywall_attempts * 10 + wqtu_delta * 5) / effort` and zeros vanity metrics. Live PostHog (project 299775, trailing 7d, 2026-09-08): WQTU `3`, `paywall_view` 12/6 users, `paywall_dismissed` 9/5, **zero** purchase attempts. That leak outranks faster PRs.

`paywall_purchase_success` is telemetry, not ledger revenue (`docs/OPERATIONAL_RELIABILITY.md`).

## Sources

- https://hs.playerzero.ai/hubfs/PlayerZero%20-%20Guide%20To%20Compounding%20ROI%20with%20AI.pdf
