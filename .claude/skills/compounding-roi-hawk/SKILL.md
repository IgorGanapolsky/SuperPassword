---
name: compounding-roi-hawk
description: >
  Steal PlayerZero compounding-ROI methods, not the SaaS. Use when the user
  pastes the compounding ROI ebook, mentions mice vs hawks, world models,
  lifecycle handoffs, MTTR vs prevention, or incident recurrence. Fail closed.
  No PlayerZero product, no new metered services.
---

# Compounding ROI hawk (steal the method)

PlayerZero 2026: AI code generation made individuals faster. Team intelligence
did not keep pace. The transferable bits are a **shared lifecycle graph**,
**prevention recipes**, and **hawk metrics** (WQTU, paywall attempt→success,
recurrence, escape rate) — not PR velocity.

Do **not** subscribe to PlayerZero. Do **not** add paid RCA platforms.

## Does it help?

| Surface | Use the paid product? | Use instead |
| --- | --- | --- |
| Production world model | No | Persist code + PostHog + deploys + resolution history |
| Lifecycle handoffs | No | `evaluate_lifecycle_handoff` — shared context id or fail |
| Velocity dashboards | No | `evaluate_hawk_metrics` — WQTU / paywall / recurrence |
| Local incident fix | No | `evaluate_prevention_recipe` — pattern + gate |
| Human mop-up | No | `evaluate_judgment_handoff` — assembled call only |

## Before claiming compounding ROI

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

Allow only when every JSON `ok` is true (process exit 0).

## High-ROI only

- Rank with `rank_work`: paywall attempts and WQTU beat faster PRs.
- Encode every resolved incident as a watch. Recovery without a gate is a mouse.
- Session-only memory is a reset. Phase 2 needs a graph that survives the chat.
- Incomplete controls exit 2. Missing evidence is not approval.
