#!/usr/bin/env bash
# Thin wrapper kept for Claude Code installs that prefer .claude/hooks/*.
# Canonical entrypoint: scripts/agent_rose_lite/autowire.py
set -euo pipefail
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$ROOT"
exec python3 scripts/agent_rose_lite/autowire.py --mode session-start --runtime claude --hook-event SessionStart
