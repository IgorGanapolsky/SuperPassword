# Agent AI Factory (NVIDIA/Palantir-inspired, $0)

Adapted from The New Stack coverage of **Nvidia + Palantir** fine-tuning a **30B Nemotron** on Nvidia’s own supply-chain decisions (domain specialization beat a ~18× larger generalist on that task). Steal the **method**, not Foundry seats, DGX Cloud spend, or “bigger model” vanity.

| Source construct | Random-Timer control plane |
| --- | --- |
| Sovereign AI (data/weights/inference controlled) | `evaluate_sovereignty` |
| Ontology as live ops map | `evaluate_ontology` |
| Specialization over size | `evaluate_specialization` |
| Post-train on ops decision logs | `evaluate_decision_log_training` |
| Scarce-part allocation (cuOpt analog) | `evaluate_scarce_allocation` |
| Own ops as proving ground | `evaluate_proving_ground` |
| Honesty: specialization ≠ universal | `evaluate_specialization_honesty` |
| Local cite | `--cite aif:<id>` |

## What we deliberately did *not* copy

- Paid Palantir Foundry / AIP managed seats.
- Nemotron cloud fine-tunes or DGX Cloud under the **$20/month** cap.
- Ranking work by parameter count / frontier leaderboards.
- Claiming domain post-training also solves forecasting / every attached problem.

## Fail-closed CLI

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

Allow only when every JSON `ok` is true (process exit 0).

## Live evidence (project 299775, trailing 7d, 2026-09-10)

WQTU `5`. Ranker puts domain allocation accuracy / IAP path ahead of parameter-count vanity.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://thenewstack.io/ai-factories-are-among-the-most-complex-systems-ever-built-nvidia-and-palantir-turn-nvidias-supply-chain-into-a-proving-ground-for-sovereign-ai/
