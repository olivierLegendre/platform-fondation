#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRODUCTION_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE_DEFAULT="${SCRIPT_DIR}/ghcr-publish.env"

if [[ -f "${ENV_FILE:-$ENV_FILE_DEFAULT}" ]]; then
  # shellcheck disable=SC1090
  source "${ENV_FILE:-$ENV_FILE_DEFAULT}"
fi

if [[ -z "${GHCR_USERNAME:-}" ]]; then
  read -r -p "GHCR username: " GHCR_USERNAME
fi

if [[ -z "${GHCR_TOKEN:-}" ]]; then
  read -r -s -p "GHCR token: " GHCR_TOKEN
  echo
fi

if [[ -z "${IMAGE_TAG:-}" ]]; then
  read -r -p "Image tag [v0.1.0]: " IMAGE_TAG
  IMAGE_TAG="${IMAGE_TAG:-v0.1.0}"
fi

export GHCR_USERNAME GHCR_TOKEN IMAGE_TAG

echo "Running publish with IMAGE_TAG=${IMAGE_TAG}"
"${SCRIPT_DIR}/publish_service_images_to_ghcr.sh"

echo "Running pullability verification with IMAGE_TAG=${IMAGE_TAG}"
"${SCRIPT_DIR}/verify_ghcr_images_pullable.sh"

echo "GHCR publish proof complete."
