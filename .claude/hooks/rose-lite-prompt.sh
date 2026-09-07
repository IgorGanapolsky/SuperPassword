#!/usr/bin/env bash
# Thin wrapper for UserPromptSubmit. Canonical: scripts/agent_rose_lite/autowire.py
set -euo pipefail
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$ROOT"
exec python3 scripts/agent_rose_lite/autowire.py --mode prompt-context --runtime claude --hook-event UserPromptSubmit
