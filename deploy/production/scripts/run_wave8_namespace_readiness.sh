#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRODUCTION_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PLATFORM_FOUNDATION_ROOT="$(cd "${PRODUCTION_DIR}/../.." && pwd)"

MANIFEST_FILE="${MANIFEST_FILE:-${PRODUCTION_DIR}/ghcr-service-images.manifest}"
TOPOLOGY_REPORT="${TOPOLOGY_REPORT:-${PLATFORM_FOUNDATION_ROOT}/nodered/reports/w6_topology_release_gate_report.json}"
RETIREMENT_REPORT="${RETIREMENT_REPORT:-${PLATFORM_FOUNDATION_ROOT}/nodered/reports/w6_retirement_readiness_report.json}"
PULLABILITY_REPORT="${PULLABILITY_REPORT:-${PRODUCTION_DIR}/reports/wave8-pullability-report.json}"
OUT_REPORT="${OUT_REPORT:-${PRODUCTION_DIR}/reports/wave8-namespace-readiness-report.json}"

COMPOSE_FILES=(
  "${PRODUCTION_DIR}/compose/reference-api.compose.yaml"
  "${PRODUCTION_DIR}/compose/device-ingestion.compose.yaml"
  "${PRODUCTION_DIR}/compose/channel-policy-router.compose.yaml"
  "${PRODUCTION_DIR}/compose/vault-secrets-runtime.compose.yaml"
)

if [[ "${SKIP_PULLABILITY:-false}" != "true" ]]; then
  if "${SCRIPT_DIR}/verify_ghcr_images_pullable.sh"; then
    cat > "${PULLABILITY_REPORT}" <<JSON
{
  "status": "PASS"
}
JSON
  else
    cat > "${PULLABILITY_REPORT}" <<JSON
{
  "status": "FAIL"
}
JSON
  fi
fi

"${PLATFORM_FOUNDATION_ROOT}/nodered/scripts/run_w6_topology_release_gate.sh"
python3 "${PLATFORM_FOUNDATION_ROOT}/nodered/scripts/evaluate_w6_retirement_readiness.py" \
  --managed "${TOPOLOGY_REPORT}" \
  --legacy "${PLATFORM_FOUNDATION_ROOT}/nodered/reports/poc_topology_retirement_gap_report.json" \
  --manifest-set "${PLATFORM_FOUNDATION_ROOT}/nodered/policy/w6_topology_release_gate.manifests.txt" \
  --out "${RETIREMENT_REPORT}"

EVAL_ARGS=(
  --manifest "${MANIFEST_FILE}"
  --topology "${TOPOLOGY_REPORT}"
  --retirement "${RETIREMENT_REPORT}"
  --out "${OUT_REPORT}"
)

for file in "${COMPOSE_FILES[@]}"; do
  EVAL_ARGS+=(--compose "$file")
done

if [[ -f "${PULLABILITY_REPORT}" ]]; then
  EVAL_ARGS+=(--pullability "${PULLABILITY_REPORT}")
fi

python3 "${SCRIPT_DIR}/evaluate_wave8_namespace_readiness.py" "${EVAL_ARGS[@]}"

echo "wrote report: ${OUT_REPORT}"
