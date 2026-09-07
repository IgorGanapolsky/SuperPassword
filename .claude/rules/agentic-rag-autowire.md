---
description: Agentic RAG is autowired — agents never hand shell recall/ingest to the CEO.
alwaysApply: true
---

## Agentic RAG (binding, autonomous)

1. **Do not tell the CEO to run** `memory_manager.py` or any recall/ingest CLI.
2. **Session recall** is automatic via ROSE-lite autowire:
   - Claude Code: `scripts/agent_rose_lite/claude_hooks.json` → SessionStart / UserPromptSubmit
   - Cursor: `.cursor/hooks.json` → sessionStart / beforeSubmitPrompt
   - CI: `.github/workflows/rose-lite-autowire.yml` writes `marketing/data/rose_lite_autowire.json`
3. **Agents** read the injected ROSE-lite **brief** (intent + ranked risks + next action), or `.claude/memory/rose_lite_session.json`. If the brief says **not verified**, do not invent memory. Never escalate recall to the CEO.
4. After verified outcomes, ingest via autowire/session hooks; if memory files are empty, state **not verified**.
5. Do not claim external LangSmith/MCP memory unless that gateway is verified in-session.

English only.
