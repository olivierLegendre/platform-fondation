#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRODUCTION_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PLATFORM_FOUNDATION_ROOT="$(cd "${PRODUCTION_DIR}/../.." && pwd)"
IOT_SERVICES_ROOT="$(cd "${PLATFORM_FOUNDATION_ROOT}/.." && pwd)"
MANIFEST_FILE="${MANIFEST_FILE:-${PRODUCTION_DIR}/ghcr-service-images.manifest}"
IMAGE_TAG="${IMAGE_TAG:-v0.2.0}"

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "missing required env var: ${name}" >&2
    exit 1
  fi
}

require_env GHCR_USERNAME
require_env GHCR_TOKEN

if [[ ! -f "${MANIFEST_FILE}" ]]; then
  echo "manifest file not found: ${MANIFEST_FILE}" >&2
  exit 1
fi

echo "Logging in to ghcr.io as ${GHCR_USERNAME}"
printf '%s' "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USERNAME}" --password-stdin >/dev/null

echo "Publishing images with IMAGE_TAG=${IMAGE_TAG}"
while IFS='|' read -r service repo_dir image_repo; do
  [[ -z "${service}" || "${service}" =~ ^# ]] && continue
  image_repo="$(printf '%s' "${image_repo}" | tr '[:upper:]' '[:lower:]')"

  repo_path="${IOT_SERVICES_ROOT}/${repo_dir}"
  dockerfile_path="${repo_path}/Dockerfile"

  if [[ ! -f "${dockerfile_path}" ]]; then
    echo "[ERROR] ${service}: missing Dockerfile at ${dockerfile_path}" >&2
    exit 1
  fi

  image_tagged="${image_repo}:${IMAGE_TAG}"
  image_sha="${image_repo}:sha-$(git -C "${repo_path}" rev-parse --short=12 HEAD)"

  echo "[BUILD] ${service} -> ${image_tagged}"
  docker build -f "${dockerfile_path}" -t "${image_tagged}" -t "${image_sha}" "${repo_path}"

  echo "[PUSH] ${image_tagged}"
  docker push "${image_tagged}"
  echo "[PUSH] ${image_sha}"
  docker push "${image_sha}"

done < "${MANIFEST_FILE}"

echo "Done."
