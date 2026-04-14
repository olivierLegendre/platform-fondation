# Production Deployment Scaffold

This directory hosts the production topology manifest set used by the Wave 6 retirement gate.

Current status:
- scaffolded baseline for service topology checks;
- Node-RED intentionally absent from all manifests;
- image tags and runtime details are placeholders and must be replaced before real deployment.
- Wave 8 namespace migration baseline applied for `ghcr.io/olivierlegendre/...`.
- shared PostgreSQL ownership is managed here (cluster lifecycle, provisioning, and DB operations policy).

## Files

- `compose/reference-api.compose.yaml`
- `compose/device-ingestion.compose.yaml`
- `compose/channel-policy-router.compose.yaml`
- `compose/vault-secrets-runtime.compose.yaml`
- `compose/postgres-shared.compose.yaml`
- `ghcr-service-images.manifest`
- `scripts/publish_service_images_to_ghcr.sh`
- `scripts/verify_ghcr_images_pullable.sh`
- `scripts/run_ghcr_publish_proof.sh`
- `scripts/run_wave1_vault_runtime_baseline.sh`
- `scripts/run_wave1_observability_baseline.sh`
- `scripts/run_wave8_namespace_readiness.sh`
- `scripts/evaluate_wave8_namespace_readiness.py`
- `scripts/postgres-shared.env.example`
- `scripts/run_shared_postgres_cluster.sh`
- `scripts/provision_shared_postgres.sh`

## How this is used

`nodered/policy/w6_topology_release_gate.manifests.txt` points to these files.
The gate verifies Node-RED runtime absence from production manifests.

Wave 7 note:
- `partner-integration-layer` deploy artifacts are intentionally not in this manifest set yet;
- they will be added in Wave 7 once adapter security/tenancy and runbook controls are validated.

## Shared PostgreSQL Ownership (Foundation-managed)

This deployment area owns PostgreSQL infrastructure and lifecycle for service databases.

Target contract:

1. One shared cluster for platform services.
2. One logical database per service.
3. Least-privilege service roles only (no PostgreSQL `SUPERUSER` for service accounts).
4. Cross-service data access must use APIs, never direct DB-to-DB reads.

### Runtime commands

Bring up the shared cluster:

```bash
cd /home/olivier/work/iot_services/platform-foundation
cp deploy/production/scripts/postgres-shared.env.example deploy/production/scripts/postgres-shared.env
./deploy/production/scripts/run_shared_postgres_cluster.sh up
```

Provision all service databases and roles:

```bash
cd /home/olivier/work/iot_services/platform-foundation
./deploy/production/scripts/provision_shared_postgres.sh
```

Reset and reprovision one service DB (test use):

```bash
cd /home/olivier/work/iot_services/platform-foundation
./deploy/production/scripts/provision_shared_postgres.sh --service reference-api-service --reset-db
```

### Managed volume guardrail

The Postgres data volume is an external managed volume (`pf_postgres_data_managed` by default).
Normal teardown does not delete data:

```bash
./deploy/production/scripts/run_shared_postgres_cluster.sh down
```

Destructive data deletion is intentionally explicit and gated:

```bash
ALLOW_DESTRUCTIVE_VOLUME_DELETE=true ./deploy/production/scripts/run_shared_postgres_cluster.sh destroy-data
```

### Backup and restore status

Backup/restore implementation is foundation-owned and tracked as a TODO item.
Service teams must provide restore-validation evidence at application level once operational backup pipelines are in place.

## Before go-live

1. Replace placeholder images/tags with real production artifacts.
2. Add real networking, secrets injection, and health checks.
3. Validate the same manifest set in CI/CD release pipeline.

Image/tag policy reference: `plateform-meta-iot/docs/specs/container-image-tagging-policy.md`

## GHCR Publish Proof Scaffold

Purpose: provide a platform-level operational action to publish and verify service images as Wave 6 closure evidence.

Ownership split:
- Service repos own Dockerfile build behavior and CI publish workflows.
- `platform-foundation` owns cross-repo operational proof execution and evidence commands.

### Inputs

1. `ghcr-service-images.manifest` contains service->repo->image mappings.
2. Environment variables:
- `GHCR_USERNAME`
- `GHCR_TOKEN` (PAT with package publish rights)
- optional `IMAGE_TAG` (default: `v0.2.0`)

### Publish command

```bash
cd /home/olivier/work/iot_services/platform-foundation
GHCR_USERNAME=<github-user> \
GHCR_TOKEN=<token> \
IMAGE_TAG=v0.2.0 \
./deploy/production/scripts/publish_service_images_to_ghcr.sh
```

### Pullability verification command

```bash
cd /home/olivier/work/iot_services/platform-foundation
IMAGE_TAG=v0.2.0 \
./deploy/production/scripts/verify_ghcr_images_pullable.sh
```

### One-command proof runner (recommended)

```bash
cd /home/olivier/work/iot_services/platform-foundation
./deploy/production/scripts/run_ghcr_publish_proof.sh
```

Behavior:
1. optionally loads `deploy/production/scripts/ghcr-publish.env` if present;
2. prompts for any missing `GHCR_USERNAME`, `GHCR_TOKEN`, `IMAGE_TAG`;
3. runs publish then pullability verification.

## Wave 8 Namespace Readiness

Purpose: validate namespace migration readiness (`ghcr.io/olivierlegendre/...`) with manifest checks, topology gate rerun, retirement decision rerun, and pullability check integration.

Runner:

```bash
cd /home/olivier/work/iot_services/platform-foundation
./deploy/production/scripts/run_wave8_namespace_readiness.sh
```

Output report:
- `deploy/production/reports/wave8-namespace-readiness-report.json`

Optional local mode (skip pullability until migrated images/permissions are available):

```bash
cd /home/olivier/work/iot_services/platform-foundation
SKIP_PULLABILITY=true ./deploy/production/scripts/run_wave8_namespace_readiness.sh
```

## Wave 1 Vault Runtime Baseline

Purpose: execute the non-dev runtime secret baseline proof for Wave 1 (`render -> validate -> report`).

Runner:

```bash
cd /home/olivier/work/iot_services/platform-foundation
./deploy/production/scripts/run_wave1_vault_runtime_baseline.sh
```

Output report:
- `vault/reports/w1-vault-runtime-baseline-report.json`

## Wave 1 Observability Baseline

Purpose: execute the Wave 1 observability baseline proof (wiring verification + synthetic healthy/breach behavior checks).

Runner:

```bash
cd /home/olivier/work/iot_services/platform-foundation
./deploy/production/scripts/run_wave1_observability_baseline.sh
```

Output reports:
- `observability/reports/w1-observability-wiring-verification.json`
- `observability/reports/w1-observability-baseline-report.json`
