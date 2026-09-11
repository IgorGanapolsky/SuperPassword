# Agent Blaxel primitives (local, $0)

Source inspiration (ideas only — no paid cloud): [Blaxel is joining Baseten](https://www.baseten.co/blog/blaxel-is-joining-baseten-to-build-the-future-of-agentic-cloud/) (2026-09-10).

## What we stole (mapped)

| Blaxel/Baseten bet | Our $0 implementation |
|---|---|
| Isolated sandboxes (microVM) | `SandboxSession` over git worktrees / temp work dirs |
| Suspend/resume ~25ms, idle ≈ $0 | Checkpoint to `AgentDrive`, clear workdir; local FS roundtrip budget &lt;250ms |
| Agent Drive (durable FS) | Versioned `AgentDrive.put/get` under a durable root |
| Production networking isolation | `evaluate_connectivity` MCP/local allowlist |
| Inference colocated | Prefer local/Hermes loops; deny paid Baseten/Blaxel platforms |
| Win with efficient agents | `rank_agent_efficiency` = outcome/effort × (1+improvement) |

## CLI smoke

```bash
PYTHONPATH=scripts python3 -m unittest scripts.tests.test_agent_blaxel_primitives -v
```

## Budget

Paid `baseten_*` / `blaxel_*` platforms are **denied**. Steal architecture; keep the $20/mo external spend cap.
