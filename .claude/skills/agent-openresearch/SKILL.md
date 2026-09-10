---
name: agent-openresearch
description: >
  Steal OpenResearch autoresearch + Harness-of-Harness loops locally, not
  managed alphaXiv compute. Use when the user mentions OpenResearch, orx,
  HoH, declarative attention, or paper-driven agent experiments.
---

# Agent OpenResearch (steal the method)

Local autoresearch only. Isolated worktrees. EVAL evidence required. HoH
plan→code→test with independent eval. Declare attention scope. Do **not**
wire managed OpenResearch / Tinker cloud.

## Before claiming an OpenResearch-style loop

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
