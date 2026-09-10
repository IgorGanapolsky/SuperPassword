---
name: agent-ai-factory
description: Fail-closed sovereign AI-factory controls adapted from NVIDIA/Palantir supply-chain specialization (local ontology, domain eval over size, scarce slot allocation). Deny Foundry/Nemotron cloud spend.
---

# Agent AI Factory

Use when choosing models, allocating agent slots, or claiming “AI factory” readiness.

## Instructions

1. Prefer **domain-specialized local** paths with an ops ontology (`wqtu`, `paywall`, `release`, `agent_slot`).
2. Keep data, weights, and inference **local/controlled** — do not export proprietary ops to paid Foundry/Nemotron cloud under the monthly cap.
3. Require **decision-log / GSD** specialization evidence; reject generic-chat-only “fine-tunes.”
4. Allocate scarce slots only with budget remaining and evidence.
5. Validate on **our** ops before exporting the pattern.
6. Never claim specialization solves forecasting or every attached problem.

```bash
python3 scripts/agent_ai_factory.py \
  --platform local_ai_factory \
  --factories scripts/tests/fixtures/agent_ai_factory.json \
  --cite aif:local-ops-ontology \
  --data-local 1 --weights-local 1 --inference-local 1 \
  --ontology-live 1 --entities wqtu,paywall,release,agent_slot \
  --domain-post-trained 1 --domain-eval-beats-general 1 \
  --trained-on-ops-decisions 1 \
  --budget-remaining-usd 12 --concurrent-slots 2 --max-slots 3 \
  --allocation-evidenced 1 \
  --own-ops-validated 1 \
  --scoped-task-claim 1
```

Exit `0` only when all controls pass.

## Examples

- Allow: local hermes / LiteLLM with PostHog+GSD ontology and domain eval.
- Deny: “use the 550B because it’s bigger” without domain eval; Foundry cloud export.

## Performance Notes

- Zero external spend path; CLI is pure Python.
- Ranker zeros parameter-count proxies.

## Troubleshooting

- Exit `2`: inspect JSON block keys (`sovereignty`, `ontology`, `specialization`, `allocation`).
- See `docs/AGENT_AI_FACTORY.md`.
