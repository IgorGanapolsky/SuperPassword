---
name: agent-context-modes
description: Fail-closed isolated-vs-fork subagent context routing adapted from LangChain Deep Agents. Workers/memory fork; verifiers/researchers isolate. Deny LangSmith seats.
---

# Agent Context Modes

Use when spawning subagents from a supervisor (Task tool, worktrees, parallel research) so context is reused or isolated on purpose.

## Instructions

1. **Worker/fixer** after diagnosis → `fork` (reuse supervisor context).
2. **Verifier/reviewer** → `isolated` (independent judgment, no anchoring).
3. **Researcher** (esp. parallel) → `isolated`.
4. **Memory/memorizer** → `fork` + restricted write paths.
5. Do not isolate workers that would redo file reads already done.
6. Return **final outcome only** to the supervisor.
7. Never force all-fork or all-isolated.
8. Deny LangSmith / hosted Deep Agents spend under the monthly cap.

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

## Examples

- Allow: fixer forks after IAP diagnosis; reviewer isolates on the diff.
- Deny: forked parallel researchers; isolated memorizer; LangSmith seat.

## Performance Notes

- Zero external spend path.
- Ranker zeros span/subagent-count vanity.

## Troubleshooting

- Exit `2`: inspect `pairing`, `waste`, `parallel`, `return_shape` keys.
- See `docs/AGENT_CONTEXT_MODES.md`.
