---
name: use-case-roi
description: >
  Steal Dataiku 5-step agent use-case scoring, not Dataiku. Use when the user
  pastes pages.dataiku.com/the-ultimate-guide-to-ai-agent-use-cases, mentions
  LLM Mesh, Agent Hub, or scoring ROI vs complexity vs readiness. Fail closed.
  Pick one sweet-spot case. No Dataiku.
---

# Use-case ROI (steal the method)

Dataiku 2025–2026: do not waste time on agents that will not scale. Start from
a business problem. Score ROI potential, implementation complexity, and user
readiness. Pick one. Scale after proof.

Do **not** sign up for Dataiku. Do **not** open LLM Mesh.

## Does it help?

| Surface | Use Dataiku? | Use instead |
| --- | --- | --- |
| Flashy agent demo | No | `evaluate_problem` |
| Which case first? | No | `score_use_case` + `pick_one` |
| More agents | No | Rank IAP / WQTU, not tokens |

## Before claiming a use case is the pick

```bash
python3 scripts/use_case_roi.py \
  --platform local_score \
  --problem iap_attempt \
  --cases scripts/tests/fixtures/use_case_roi.json \
  --cite case:iap-attempt-path
```

Allow only when every JSON `ok` is true (process exit 0).
