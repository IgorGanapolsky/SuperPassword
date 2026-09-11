# Agent Universal Orchestration (Decisions-inspired, $0)

Adapted from Decisions’ [Universal Orchestration](https://decisions.com/ebooks/universal-orchestration-what-it-is-why-it-matters-and-how-to-achieve-it) ebook + [agentic orchestration](https://decisions.com/platform/agentic-orchestration) control-plane framing. Steal the **governance method**, not a paid BPM/SaaS seat.

| Source construct | Random-Timer control plane |
| --- | --- |
| Enterprise control layer vs agent sprawl | `evaluate_control_layer` |
| Rules-first over prompt-only | `evaluate_rules_first` |
| Authorized-action guardrails | `evaluate_guardrails` |
| HITL before irreversible action | `evaluate_human_in_loop` |
| Audit: rules/inputs/outputs/handoffs | `evaluate_audit_trail` |
| No handoff black hole | `evaluate_handoff` |
| Readiness + focused first use case | `evaluate_readiness` |
| Shadow-test before live | `evaluate_shadow_test` |
| Observability + exceptions | `evaluate_visibility` |
| Three UO capability pillars | `evaluate_capability_pillars` |
| Instructions ≠ control (hard perms) | `evaluate_hard_permissioning` |
| Process state outside agent context | `evaluate_process_state` |
| Shadow AI outside approved process | `evaluate_shadow_ai` |
| Cost/performance under $20 cap | `evaluate_agent_cost_telemetry` |
| Five enterprise outcomes | `evaluate_five_outcomes` |

## Mapped to our product (not Decisions SaaS)

Example control layer for Play publish:

1. Complexity signal: multi-agent store work (privacy → review → publish → public verify)
2. Rules-first: production track only; no prompt-only “just ship it”
3. Guardrails: authorized = production publish after gates; unauthorized = open testing without CEO request
4. HITL: managed publish is irreversible → approval / environment sign-off
5. Hard permissioning: production reach needs hard perms + approval + intervention (not prompt text alone)
6. Process state: authoritative record outside any single agent context window
7. Handoff: each step persists evidence and routes next job
8. Shadow: dry-run / API read-back before claiming live; no shadow AI outside approved surfaces
9. Audit + visibility + cost telemetry: log rule/inputs/outputs/handoffs; surface exceptions; stay under operating cap

## What we deliberately did *not* copy

- Decisions SaaS / enterprise seats under the **$20/month** cap.
- Counting agent/workflow counts or ebook downloads as product progress.
- Boiling the ocean (enterprise-wide transform) before a focused first use case.

## Fail-closed CLI

```bash
python3 scripts/agent_universal_orchestration.py \
  --platform ops_control_layer \
  --flows scripts/tests/fixtures/agent_universal_orchestration.json \
  --cite uor:play-publish-control-layer \
  --has-control-layer 1 --deterministic-policy 1 \
  --authorized-actions-defined 1 --unauthorized-blocked 1 \
  --irreversible-action 1 --approval-point 1 \
  --rules-logged 1 --inputs-logged 1 --outputs-logged 1 --handoffs-logged 1 \
  --next-step-routed 1 --result-persisted 1 \
  --complexity-signals 1 --readiness-assessed 1 --focused-first-use-case 1 \
  --shadow-tested 1 --going-live 1 \
  --real-time-observability 1 --exceptions-surfaced 1
```

## Live evidence (project 299775, trailing 7d, 2026-09-11)

WQTU `5`. Ranker puts store/IAP control-layer work ahead of agent-count vanity.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- Sanity CDN PDF (ebook asset): `cdn.sanity.io/files/a9zf4mro/production/3a1a4f21b38cef8a635d7f6487d7bfa95fb05de2.pdf`
- https://decisions.com/ebooks/universal-orchestration-what-it-is-why-it-matters-and-how-to-achieve-it
- https://decisions.com/ebooks/is-your-organization-ready-for-universal-orchestration
- https://decisions.com/platform/agentic-orchestration
