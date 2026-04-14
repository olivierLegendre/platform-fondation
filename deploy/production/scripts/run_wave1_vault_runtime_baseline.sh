#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
VAULT_DIR="$ROOT_DIR/vault"
if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_BIN="$PYTHON_BIN"
elif [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

INPUT_JSON="${INPUT_JSON:-$VAULT_DIR/examples/vault-export.example.json}"
ENV_DIR="${ENV_DIR:-/tmp/iot-wave1-secrets}"
REPORT_PATH="${REPORT_PATH:-$VAULT_DIR/reports/w1-vault-runtime-baseline-report.json}"

mkdir -p "$ENV_DIR"

"$PYTHON_BIN" "$VAULT_DIR/scripts/render_runtime_env.py" \
  --input "$INPUT_JSON" \
  --outdir "$ENV_DIR"

"$PYTHON_BIN" "$VAULT_DIR/scripts/validate_runtime_env.py" \
  --env-dir "$ENV_DIR"

"$PYTHON_BIN" "$VAULT_DIR/scripts/evaluate_wave1_vault_runtime_baseline.py" \
  --env-dir "$ENV_DIR" \
  --out "$REPORT_PATH"

echo "Wave 1 Vault runtime baseline evidence report: $REPORT_PATH"
