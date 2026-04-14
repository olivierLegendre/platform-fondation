#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRODUCTION_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${PRODUCTION_DIR}/compose/postgres-shared.compose.yaml"
ENV_FILE="${POSTGRES_SHARED_ENV_FILE:-${SCRIPT_DIR}/postgres-shared.env}"

if [[ -f "${ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
fi

VOLUME_NAME="${POSTGRES_MANAGED_VOLUME_NAME:-pf_postgres_data_managed}"
SUPERUSER="${POSTGRES_SUPERUSER:-postgres}"
SERVICE_NAME="postgres-shared"
COMPOSE_ENV_ARGS=()
if [[ -f "${ENV_FILE}" ]]; then
  COMPOSE_ENV_ARGS=(--env-file "${ENV_FILE}")
fi

run_compose() {
  docker compose \
    "${COMPOSE_ENV_ARGS[@]}" \
    -f "${COMPOSE_FILE}" \
    "$@"
}

usage() {
  cat <<'EOF'
Usage:
  run_shared_postgres_cluster.sh up
  run_shared_postgres_cluster.sh down
  run_shared_postgres_cluster.sh status
  run_shared_postgres_cluster.sh logs
  run_shared_postgres_cluster.sh destroy-data

Notes:
  - The managed Postgres volume is external and is never removed by "down".
  - "destroy-data" is destructive and requires ALLOW_DESTRUCTIVE_VOLUME_DELETE=true.
EOF
}

wait_ready() {
  for _ in {1..60}; do
    if docker exec platform-foundation-postgres pg_isready -U "${SUPERUSER}" -d postgres >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "shared postgres cluster did not become ready in time" >&2
  return 1
}

cmd="${1:-}"
case "${cmd}" in
  up)
    docker volume create "${VOLUME_NAME}" >/dev/null
    run_compose up -d "${SERVICE_NAME}"
    wait_ready
    ;;
  down)
    run_compose down
    ;;
  status)
    run_compose ps
    ;;
  logs)
    run_compose logs --tail=100 "${SERVICE_NAME}"
    ;;
  destroy-data)
    if [[ "${ALLOW_DESTRUCTIVE_VOLUME_DELETE:-false}" != "true" ]]; then
      echo "Refusing destructive delete. Set ALLOW_DESTRUCTIVE_VOLUME_DELETE=true to proceed." >&2
      exit 1
    fi
    run_compose down
    docker volume rm -f "${VOLUME_NAME}"
    ;;
  *)
    usage
    exit 1
    ;;
esac
