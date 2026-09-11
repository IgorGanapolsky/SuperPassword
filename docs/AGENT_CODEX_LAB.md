# Agent Codex Lab (MIT EQuS / OpenAI-inspired, $0)

Adapted from OpenAI’s [Codex quantum computing experiments](https://openai.com/index/codex-quantum-computing-experiments/) (MIT EQuS + GPT‑5.6 Sol). Steal the **lab ops method**, not dilution refrigerators, qubit hardware, or paid Ultra lab spend.

| Source construct | Random-Timer control plane |
| --- | --- |
| Measurement-specific skills (template, prereqs, pass/fail) | `evaluate_measurement_skill` |
| Interdependent calibrations + persist results | `evaluate_interdependent_chain` |
| Clear signal → autonomous; noisy → escalate | `evaluate_signal_quality` |
| Routine vs novel goal width | `evaluate_routine_vs_novel` |
| Overnight run with check-in / steer | `evaluate_unattended_run` |
| Agent owns routine; human owns design/analysis | `evaluate_human_focus` |

## Mapped to our product (not physics)

Example “calibration chain” for Play release:

1. Privacy URL HTTP 200 (prereq)
2. Console field saved (persist)
3. Send for review (measurement)
4. Managed publish (next step uses prior result)
5. Public HTML version verify (success criteria)

Noisy signal example: PostHog vs CEO observation disagreement → escalate (contradiction protocol), do not keep guessing.

## What we deliberately did *not* copy

- Quantum hardware, fridge time, or OpenAI Ultra paid lab runs under the **$20/month** cap.
- Claiming qubit press as product progress.
- Blind overnight agents without progress logs / steer hooks.

## Fail-closed CLI

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

## Live evidence (project 299775, trailing 7d, 2026-09-10)

WQTU `5`. Ranker puts IAP / store verify calibration ahead of qubit-count vanity.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://openai.com/index/codex-quantum-computing-experiments/
- https://cdn.openai.com/pdf/case-study-agentic-calibration-of-superconducting-qubits.pdf
