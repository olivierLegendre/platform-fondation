#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRODUCTION_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
MANIFEST_FILE="${MANIFEST_FILE:-${PRODUCTION_DIR}/ghcr-service-images.manifest}"
IMAGE_TAG="${IMAGE_TAG:-v0.2.0}"

if [[ ! -f "${MANIFEST_FILE}" ]]; then
  echo "manifest file not found: ${MANIFEST_FILE}" >&2
  exit 1
fi

failed=0
while IFS='|' read -r service _repo_dir image_repo; do
  [[ -z "${service}" || "${service}" =~ ^# ]] && continue
  image_repo="$(printf '%s' "${image_repo}" | tr '[:upper:]' '[:lower:]')"
  ref="${image_repo}:${IMAGE_TAG}"
  if docker manifest inspect "${ref}" >/dev/null 2>&1; then
    echo "[OK] ${service} ${ref}"
  else
    echo "[FAIL] ${service} ${ref}" >&2
    failed=1
  fi
done < "${MANIFEST_FILE}"

exit ${failed}
