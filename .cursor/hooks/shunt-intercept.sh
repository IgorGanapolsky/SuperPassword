#!/usr/bin/env bash
# Cursor preToolUse / beforeShellExecution wrapper. Fail-open.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || { printf '%s\n' '{"permission":"allow"}'; exit 0; }
python3 scripts/token_shunt.py --hook || printf '%s\n' '{"permission":"allow"}'
exit 0
