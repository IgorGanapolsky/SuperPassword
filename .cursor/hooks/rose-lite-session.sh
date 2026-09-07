#!/usr/bin/env bash
# Cursor sessionStart wrapper. Canonical: scripts/agent_rose_lite/autowire.py
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
exec python3 scripts/agent_rose_lite/autowire.py --mode session-start --runtime cursor --hook-event sessionStart
