# Agent orchestration (local)

Source inspiration (ideas only): public enterprise agent-orchestration guide
(2026-05-21) via content hub `agent-orchestration`.

Companion module: `scripts/agent_universal_orchestration.py` covers control-layer
governance. This module covers **pattern selection and runtime guards**.

## What we took

| Practice | Local harness |
|---|---|
| Five patterns (seq / concurrent / group chat / handoff / hierarchical) | `choose_pattern` + `plan_workflow` |
| Inter-step validation (stop silent error propagation) | `validate_step_gate` |
| Max handoffs + loop prevention | `validate_handoff` |
| Group-chat turn cap | `validate_group_chat` |
| Conflict reconciliation (confidence / majority) | `reconcile_concurrent` |
| Vendor-independent control | external orchestration vendors denied |

## Smoke

```bash
PYTHONPATH=scripts python3 -m unittest scripts.tests.test_agent_orchestration -v
```

## Example: sequential ops verify

```python
from agent_orchestration import plan_workflow, validate_step_gate

plan = plan_workflow(
    intent="play_ops_verify",
    agents=("diagnostics", "link_step", "confirm_step", "banner_readback"),
)
# Between each step: validate_step_gate(confidence=..., output_ok=...)
```
