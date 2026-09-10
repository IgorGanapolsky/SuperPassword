# Agent OpenResearch (alphaXiv-inspired, $0)

Adapted from the alphaXiv digest (**OpenResearch**) and trending **Harness-of-Harness** / Declarative Attention ideas. Steal the **method**, not managed OpenResearch compute, Tinker cloud, or digest vanity metrics.

| Source construct | Random-Timer control plane |
| --- | --- |
| Local-first autoresearch loop | `evaluate_autoresearch_loop` |
| Isolated worktree per experiment arm | `evaluate_worktree_isolation` |
| EVAL.md / evidence artifact | `evaluate_eval_artifact` |
| HoH plan→code→test + independent eval | `evaluate_hoh_loop` |
| Declarative attention scope | `evaluate_declarative_attention` |
| Local cite | `--cite orx:<id>` |

## What we deliberately did *not* copy

- Managed OpenResearch / alphaXiv cloud compute.
- Tinker GPU post-training under the **$20/month** cap.
- Ranking work by paper views from the weekly digest.
- Navier–Stokes / LoRA fine-tune paths as product work.

## Fail-closed CLI

```bash
python3 scripts/agent_openresearch.py \
  --platform local_openresearch \
  --experiments scripts/tests/fixtures/agent_openresearch.json \
  --cite orx:iap-autoresearch \
  --compute local \
  --isolated 1 \
  --has-eval-md 1 \
  --metric iap_attempt \
  --hypothesized 1 --changed-code 1 --ran-experiment 1 \
  --inspected-evidence 1 --decided-next 1 \
  --planned 1 --coded 1 --tested 1 --independent-eval 1 --reused-skills 1 \
  --declared-scope 1
```

Allow only when every JSON `ok` is true (process exit 0).

## Live evidence (project 299775, trailing 7d, 2026-09-10)

WQTU `5`. Ranker puts IAP attempt path ahead of alphaXiv paper-view vanity.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://github.com/alphaXiv/OpenResearch
- https://openresearch.sh/
- https://arxiv.org/abs/2609.01481 (Harness-of-Harness)
- alphaXiv weekly digest email (2026-09-09)
