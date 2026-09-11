---
name: agent-universal-orchestration
description: Fail-closed multi-agent control-layer controls adapted from Decisions Universal Orchestration (rules-first, guardrails, HITL, audit, handoffs). Deny vendor SaaS spend.
---

# Agent Universal Orchestration

Use when coordinating multiple agents/automation paths (store publish chains, IAP diagnosis + CI + Maestro) so work stays governed, visible, and accountable.

## Instructions

1. Put agents under one **control layer** — deny sprawl.
2. Lock final decisions to **deterministic policy**, not prompt-only.
3. Define **authorized actions** and block the rest.
4. Gate **irreversible** actions with approval/escalation *before* execute.
5. Keep an **audit trail**: rules, inputs, outputs, handoffs.
6. Route every completion to a **next step** (no handoff black hole).
7. Assess readiness; start with one **focused** use case.
8. **Shadow-test** against rules before going live.
9. Require observability and surfaced exceptions.
10. Deny Decisions SaaS / enterprise BPM spend under the monthly cap.

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

## Examples

- Allow: Play production publish with rules, approval, audit, and routed verify step.
- Deny: “LLM decided to open testing”; “agent finished with no next job”; unpaid SaaS seat.

## Performance Notes

- Zero external spend path.
- Ranker zeros agent-count / ebook vanity metrics.

## Troubleshooting

- Exit `2`: inspect `control_layer`, `rules_first`, `hitl`, `handoff`, `shadow` keys.
- See `docs/AGENT_UNIVERSAL_ORCHESTRATION.md`.
