# Production Deployment Scaffold

This directory hosts the production topology manifest set used by the Wave 6 retirement gate.

Current status:
- scaffolded baseline for service topology checks;
- Node-RED intentionally absent from all manifests;
- image tags and runtime details are placeholders and must be replaced before real deployment.
- Wave 8 namespace migration baseline applied for `ghcr.io/olivierlegendre/...`.

## Files

- `compose/reference-api.compose.yaml`
- `compose/device-ingestion.compose.yaml`
- `compose/channel-policy-router.compose.yaml`
- `compose/vault-secrets-runtime.compose.yaml`
- `ghcr-service-images.manifest`
- `scripts/publish_service_images_to_ghcr.sh`
- `scripts/verify_ghcr_images_pullable.sh`
- `scripts/run_ghcr_publish_proof.sh`
- `scripts/run_wave8_namespace_readiness.sh`
- `scripts/evaluate_wave8_namespace_readiness.py`

## How this is used

`nodered/policy/w6_topology_release_gate.manifests.txt` points to these files.
The gate verifies Node-RED runtime absence from production manifests.

Wave 7 note:
- `partner-integration-layer` deploy artifacts are intentionally not in this manifest set yet;
- they will be added in Wave 7 once adapter security/tenancy and runbook controls are validated.

## Before go-live

1. Replace placeholder images/tags with real production artifacts.
2. Add real networking, secrets injection, and health checks.
3. Validate the same manifest set in CI/CD release pipeline.

Image/tag policy reference: `plateform-meta-iot/docs/container-image-tagging-policy.md`

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
