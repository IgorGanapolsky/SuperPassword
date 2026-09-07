#!/usr/bin/env bash
# Thin wrapper kept for Claude Code installs that prefer .claude/hooks/*.
# Canonical entrypoint: scripts/agent_rose_lite/autowire.py
# Fail-open: a missing or failing autowire must never block the agent session.
set -u
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$ROOT" || exit 0
SCRIPT="scripts/agent_rose_lite/autowire.py"
if [[ ! -f "$SCRIPT" ]]; then
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"ROSE-lite not verified (autowire missing)"}}'
  exit 0
fi
python3 "$SCRIPT" --mode session-start --runtime claude --hook-event SessionStart \
  || printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"ROSE-lite not verified (autowire failed)"}}'
exit 0
