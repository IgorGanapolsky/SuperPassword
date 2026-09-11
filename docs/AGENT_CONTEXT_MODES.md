# Agent Context Modes (LangChain-inspired, $0)

Adapted from LangChain’s [Organizing Context in a Multi-Agent Harness](https://www.langchain.com/blog/organizing-context-in-a-multi-agent-harness). Steal **isolated vs fork** context routing, not a LangSmith seat.

| Source construct | Random-Timer control plane |
| --- | --- |
| Worker continues diagnosed work → `fork` | `evaluate_context_mode` (worker) |
| Verifier independent review → `isolated` | `evaluate_context_mode` (verifier) |
| Researcher self-contained Q → `isolated` | `evaluate_context_mode` (researcher) |
| Memory needs conversation → `fork` | `evaluate_context_mode` (memory) |
| Avoid rediscovery waste | `evaluate_waste` |
| Supervisor gets outcome only | `evaluate_return_shape` |
| Parallel research stays isolated | `evaluate_parallel_research` |
| Specialize permissions | `evaluate_permissions` |
| No all-fork / all-isolated monoculture | `evaluate_monoculture` |

## Mapped to our product

Example IAP / store diagnosis harness:

1. Supervisor traces catalog empty → evidence in thread
2. **Fixer** (`fork`): implement telemetry/fix using that diagnosis
3. **Reviewer** (`isolated`): independent check of the diff vs criteria
4. Parallel **researchers** (`isolated`): Play API docs vs PostHog schema questions
5. **Memorizer** (`fork`, write-restricted): persist durable decision into GSD JSON

## What we deliberately did *not* copy

- LangSmith paid seats / hosted Deep Agents over the **$20/month** cap.
- Counting spans or subagent count as product progress.
- Forcing one context mode for every subagent.

## Fail-closed CLI

```bash
python3 scripts/agent_context_modes.py \
  --platform supervisor_subagent_harness \
  --harnesses scripts/tests/fixtures/agent_context_modes.json \
  --cite acm:iap-fixer-fork \
  --role fixer --mode fork \
  --supervisor-already-gathered-context 1 \
  --supervisor-receives-final-only 1 \
  --write-paths-restricted 1
```

## Live evidence (project 299775, trailing 7d, 2026-09-11)

WQTU `4`. Ranker puts IAP context-reuse harnesses ahead of LangSmith span vanity.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://www.langchain.com/blog/organizing-context-in-a-multi-agent-harness
