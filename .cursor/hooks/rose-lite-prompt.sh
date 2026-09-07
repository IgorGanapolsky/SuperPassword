#!/usr/bin/env bash
# Cursor beforeSubmitPrompt wrapper. Canonical: scripts/agent_rose_lite/autowire.py
# Fail-open: a missing or failing autowire must never block the agent session.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 0
SCRIPT="scripts/agent_rose_lite/autowire.py"
if [[ ! -f "$SCRIPT" ]]; then
  printf '%s\n' '{"additional_context":"ROSE-lite not verified (autowire missing)"}'
  exit 0
fi
python3 "$SCRIPT" --mode prompt-context --runtime cursor --hook-event beforeSubmitPrompt \
  || printf '%s\n' '{"additional_context":"ROSE-lite not verified (autowire failed)"}'
exit 0
