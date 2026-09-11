---
name: agent-codex-lab
description: Fail-closed ops calibration-loop controls adapted from OpenAI Codex / MIT EQuS qubit lab (measurement skills, interdependent chains, clear-vs-noisy escalate). Deny quantum hardware spend.
---

# Agent Codex Lab

Use when running multi-step release/ops characterization (store publish chains, IAP catalog calibration, overnight CI watches).

## Instructions

1. Give each routine step a **measurement skill**: template, prerequisites, success/fail criteria.
2. Persist each result before the next interdependent step.
3. Autonomous only when signals are **clear**; escalate on noisy/ambiguous evidence.
4. Routine workflows may run long; novel work needs a **narrow goal**.
5. Unattended runs require progress log + check-in + steer hook.
6. Agents own routine; humans own design/interpretation/next-step planning.
7. Deny quantum hardware / paid Ultra lab spend under the monthly cap.

```bash
python3 scripts/agent_codex_lab.py \
  --platform ops_calibration_loop \
  --loops scripts/tests/fixtures/agent_codex_lab.json \
  --cite cxl:play-release-calibration \
  --has-skill 1 --has-prerequisites 1 \
  --has-success-fail-criteria 1 --has-template 1 \
  --prerequisites-complete 1 --result-persisted 1 \
  --signal-clear 1 --routine-workflow 1 \
  --progress-log 1 --check-in-possible 1 --steer-hook 1 \
  --agent-owns-routine 1 --human-owns-design-analysis 1
```

## Examples

- Allow: Play privacy→review→publish→public version verify with persisted evidence.
- Deny: “run overnight with no log”; “novel experiment with unbounded autonomy”; quantum fridge spend.

## Performance Notes

- Zero external spend path.
- Ranker zeros qubit/press vanity metrics.

## Troubleshooting

- Exit `2`: inspect `skill`, `chain`, `signal`, `unattended` keys.
- See `docs/AGENT_CODEX_LAB.md`.
