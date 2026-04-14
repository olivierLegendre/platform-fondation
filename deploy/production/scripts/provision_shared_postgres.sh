#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${POSTGRES_SHARED_ENV_FILE:-${SCRIPT_DIR}/postgres-shared.env}"
RUN_CLUSTER_SCRIPT="${SCRIPT_DIR}/run_shared_postgres_cluster.sh"

if [[ -f "${ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
fi

SUPERUSER="${POSTGRES_SUPERUSER:-postgres}"
SUPERUSER_PASSWORD="${POSTGRES_SUPERUSER_PASSWORD:-postgres}"

services=()
reset_db=false

usage() {
  cat <<'EOF'
Usage:
  provision_shared_postgres.sh [--service <service-name>]... [--reset-db]

Services:
  reference-api-service
  device-ingestion-service
  channel-policy-router
  automation-scenario-service

Notes:
  - If no --service is provided, all known services are provisioned.
  - --reset-db drops and recreates the selected service databases.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --service)
      services+=("$2")
      shift 2
      ;;
    --reset-db)
      reset_db=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ ${#services[@]} -eq 0 ]]; then
  services=(
    "reference-api-service"
    "device-ingestion-service"
    "channel-policy-router"
    "automation-scenario-service"
  )
fi

run_psql() {
  local db="$1"
  local sql="$2"
  docker exec -i \
    -e PGPASSWORD="${SUPERUSER_PASSWORD}" \
    platform-foundation-postgres \
    psql -v ON_ERROR_STOP=1 -U "${SUPERUSER}" -d "${db}" <<<"${sql}"
}

run_psql_capture() {
  local db="$1"
  local sql="$2"
  docker exec -i \
    -e PGPASSWORD="${SUPERUSER_PASSWORD}" \
    platform-foundation-postgres \
    psql -v ON_ERROR_STOP=1 -U "${SUPERUSER}" -d "${db}" -tA <<<"${sql}"
}

resolve_service_config() {
  local service="$1"
  case "${service}" in
    reference-api-service)
      DB_NAME="${REFERENCE_API_DB_NAME:-reference_api}"
      APP_ROLE="${REFERENCE_API_APP_ROLE:-svc_reference_api_app}"
      APP_PASSWORD="${REFERENCE_API_APP_PASSWORD:-dev_reference_api_app}"
      MIGRATOR_ROLE="${REFERENCE_API_MIGRATOR_ROLE:-svc_reference_api_migrator}"
      MIGRATOR_PASSWORD="${REFERENCE_API_MIGRATOR_PASSWORD:-dev_reference_api_migrator}"
      ;;
    device-ingestion-service)
      DB_NAME="${DEVICE_INGESTION_DB_NAME:-device_ingestion}"
      APP_ROLE="${DEVICE_INGESTION_APP_ROLE:-svc_device_ingestion_app}"
      APP_PASSWORD="${DEVICE_INGESTION_APP_PASSWORD:-dev_device_ingestion_app}"
      MIGRATOR_ROLE="${DEVICE_INGESTION_MIGRATOR_ROLE:-svc_device_ingestion_migrator}"
      MIGRATOR_PASSWORD="${DEVICE_INGESTION_MIGRATOR_PASSWORD:-dev_device_ingestion_migrator}"
      ;;
    channel-policy-router)
      DB_NAME="${CHANNEL_POLICY_ROUTER_DB_NAME:-channel_policy_router}"
      APP_ROLE="${CHANNEL_POLICY_ROUTER_APP_ROLE:-svc_channel_policy_router_app}"
      APP_PASSWORD="${CHANNEL_POLICY_ROUTER_APP_PASSWORD:-dev_channel_policy_router_app}"
      MIGRATOR_ROLE="${CHANNEL_POLICY_ROUTER_MIGRATOR_ROLE:-svc_channel_policy_router_migrator}"
      MIGRATOR_PASSWORD="${CHANNEL_POLICY_ROUTER_MIGRATOR_PASSWORD:-dev_channel_policy_router_migrator}"
      ;;
    automation-scenario-service)
      DB_NAME="${AUTOMATION_SCENARIO_DB_NAME:-automation_scenario}"
      APP_ROLE="${AUTOMATION_SCENARIO_APP_ROLE:-svc_automation_scenario_app}"
      APP_PASSWORD="${AUTOMATION_SCENARIO_APP_PASSWORD:-dev_automation_scenario_app}"
      MIGRATOR_ROLE="${AUTOMATION_SCENARIO_MIGRATOR_ROLE:-svc_automation_scenario_migrator}"
      MIGRATOR_PASSWORD="${AUTOMATION_SCENARIO_MIGRATOR_PASSWORD:-dev_automation_scenario_migrator}"
      ;;
    *)
      echo "Unknown service: ${service}" >&2
      exit 1
      ;;
  esac
}

"${RUN_CLUSTER_SCRIPT}" up

for service in "${services[@]}"; do
  resolve_service_config "${service}"

  run_psql "postgres" "
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${APP_ROLE}') THEN
    CREATE ROLE ${APP_ROLE} LOGIN PASSWORD '${APP_PASSWORD}' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
  ELSE
    ALTER ROLE ${APP_ROLE} WITH LOGIN PASSWORD '${APP_PASSWORD}' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${MIGRATOR_ROLE}') THEN
    CREATE ROLE ${MIGRATOR_ROLE} LOGIN PASSWORD '${MIGRATOR_PASSWORD}' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
  ELSE
    ALTER ROLE ${MIGRATOR_ROLE} WITH LOGIN PASSWORD '${MIGRATOR_PASSWORD}' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
  END IF;
END
\$\$;
"

  if [[ "${reset_db}" == "true" ]]; then
    run_psql "postgres" "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '${DB_NAME}'
  AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS ${DB_NAME};
"
  fi

  db_exists="$(run_psql_capture "postgres" "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}' LIMIT 1;")"
  if [[ -z "${db_exists}" ]]; then
    run_psql "postgres" "CREATE DATABASE ${DB_NAME} OWNER ${MIGRATOR_ROLE};"
  fi

  run_psql "postgres" "
ALTER DATABASE ${DB_NAME} OWNER TO ${MIGRATOR_ROLE};
GRANT CONNECT, TEMPORARY ON DATABASE ${DB_NAME} TO ${APP_ROLE};
GRANT CONNECT, TEMPORARY ON DATABASE ${DB_NAME} TO ${MIGRATOR_ROLE};
"

  run_psql "${DB_NAME}" "
GRANT USAGE ON SCHEMA public TO ${APP_ROLE};
GRANT USAGE, CREATE ON SCHEMA public TO ${MIGRATOR_ROLE};

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ${APP_ROLE};
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO ${APP_ROLE};
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO ${APP_ROLE};

ALTER DEFAULT PRIVILEGES FOR ROLE ${MIGRATOR_ROLE} IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ${APP_ROLE};
ALTER DEFAULT PRIVILEGES FOR ROLE ${MIGRATOR_ROLE} IN SCHEMA public
  GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO ${APP_ROLE};
ALTER DEFAULT PRIVILEGES FOR ROLE ${MIGRATOR_ROLE} IN SCHEMA public
  GRANT EXECUTE ON FUNCTIONS TO ${APP_ROLE};
"

  echo "Provisioned ${service}: db=${DB_NAME}, app_role=${APP_ROLE}, migrator_role=${MIGRATOR_ROLE}"
done
