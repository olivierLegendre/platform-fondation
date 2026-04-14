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
MANIFEST_SET="${1:-$ROOT_DIR/nodered/policy/w6_topology_release_gate.manifests.txt}"
OUT_REPORT="${2:-$ROOT_DIR/nodered/reports/w6_topology_release_gate_report.json}"

if [[ ! -f "$MANIFEST_SET" ]]; then
  echo "manifest set not found: $MANIFEST_SET" >&2
  exit 2
fi

mapfile -t MANIFESTS < <(grep -vE '^\s*#|^\s*$' "$MANIFEST_SET")
if [[ ${#MANIFESTS[@]} -eq 0 ]]; then
  echo "manifest set is empty after filtering comments/blanks: $MANIFEST_SET" >&2
  exit 2
fi

for manifest in "${MANIFESTS[@]}"; do
  if [[ ! -f "$manifest" ]]; then
    echo "manifest not found: $manifest" >&2
    exit 2
  fi
done

CMD=("$PYTHON_BIN" "$ROOT_DIR/nodered/scripts/verify_nodered_topology_retired.py")
for manifest in "${MANIFESTS[@]}"; do
  CMD+=(--manifest "$manifest")
done
CMD+=(--out "$OUT_REPORT")

"${CMD[@]}"

echo "wrote report: $OUT_REPORT"
