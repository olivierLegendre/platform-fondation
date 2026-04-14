#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_BIN="$PYTHON_BIN"
elif [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

FLOWS_PATH="${1:-${NODERED_FLOWS_PATH:-/home/olivier/Public/poc/stack/nodered/data/flows.json}}"
POLICY_PATH="${2:-${NODERED_BRIDGE_POLICY_PATH:-$ROOT_DIR/nodered/policy/bridge_allowlist.json}}"
REPORT_PATH="${3:-${NODERED_BRIDGE_REPORT_PATH:-$ROOT_DIR/nodered/reports/bridge_policy_gate_report.json}}"

if [[ ! -f "$FLOWS_PATH" ]]; then
  echo "flows file not found: $FLOWS_PATH" >&2
  exit 2
fi

if [[ ! -f "$POLICY_PATH" ]]; then
  echo "policy file not found: $POLICY_PATH" >&2
  exit 2
fi

"$PYTHON_BIN" "$ROOT_DIR/nodered/scripts/audit_bridge_policy.py" \
  --flows "$FLOWS_PATH" \
  --policy "$POLICY_PATH" \
  --report "$REPORT_PATH" \
  --enforce

printf '\nBridge policy gate passed. Report: %s\n' "$REPORT_PATH"
