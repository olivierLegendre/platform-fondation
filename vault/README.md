# Vault Runtime Secrets Baseline (Wave 1 + W6-07)

This folder defines the runtime secret contract and bootstrap checks used for the Wave 1 foundation/security baseline and reused by later waves.

## Why Vault Is Used Here

Vault is the source of runtime secrets in non-dev environments.
Services must not keep real secrets in git, image layers, or static `.env` files committed to the repo.

In this project, Vault provides values for:

- `REFERENCE_API_POSTGRES_DSN`

- `AUTH_JWT_SECRET`
- `AUTH_JWT_ISSUER`
- `AUTH_JWT_AUDIENCE`

for:

- `reference-api-service`
- `automation-scenario-service`
- `channel-policy-router`

The secret names and required keys are defined in `secrets-contract.yaml`.

## How It Works End-To-End

1. Secret contract is defined:
- `vault/secrets-contract.yaml` declares which keys each service requires.

2. Vault stores real values:
- Ops/security team writes real values in Vault (never in git).

3. Deployment retrieves secrets from Vault:
- Preferred production mode: Vault Agent/Injector/CSI injects env vars or mounted secret files directly.
- Bootstrap compatibility mode: exported JSON is rendered into service env files.

4. Bootstrap render step (if using compatibility mode):
- `render_runtime_env.py` converts Vault-shaped JSON to:
  - `/run/iot-secrets/reference-api-service.env`
  - `/run/iot-secrets/automation-scenario-service.env`
  - `/run/iot-secrets/channel-policy-router.env`

5. Validation gate:
- `validate_runtime_env.py` checks:
  - required keys exist
  - DSN format and dev-default rejection for `reference-api-service`
  - default dev JWT secret is rejected
  - JWT secret length policy (>= 32 chars)

6. Runtime wiring:
- compose/runtime loads env files (example in `examples/docker-compose.secrets.override.yaml`).
- services start with these env vars.

7. Service startup guards:
- in non-dev mode, services reject unsafe default JWT secret and enforce strict JWT verification policy.

## Files

- `secrets-contract.yaml`: required secret names by service.
- `examples/vault-export.example.json`: non-secret payload shape example.
- `scripts/render_runtime_env.py`: renders service `.env` files from Vault-exported JSON.
- `scripts/validate_runtime_env.py`: validates rendered env files for non-dev policy.
- `scripts/evaluate_wave1_vault_runtime_baseline.py`: writes Wave 1 evidence report (`PASS`/`FAIL`).
- `examples/docker-compose.secrets.override.yaml`: example runtime wiring via `env_file`.
- `reports/w1-vault-runtime-baseline-report.json`: Wave 1 runtime baseline evidence artifact.

## Wave 1 One-Command Baseline Proof

Run from `platform-foundation`:

```bash
./deploy/production/scripts/run_wave1_vault_runtime_baseline.sh
```

Default behavior:
1. Renders service env files from `vault/examples/vault-export.example.json`.
2. Validates non-dev secret policy.
3. Produces evidence report at `vault/reports/w1-vault-runtime-baseline-report.json`.

## Usage

Render runtime env files from a Vault-exported JSON payload:

```bash
python3 vault/scripts/render_runtime_env.py \
  --input vault/examples/vault-export.example.json \
  --outdir /run/iot-secrets
```

Validate required keys and reject unsafe defaults:

```bash
python3 vault/scripts/validate_runtime_env.py \
  --env-dir /run/iot-secrets
```

Use the generated env files in compose/runtime wiring:

```bash
docker compose -f docker-compose.yml \
  -f vault/examples/docker-compose.secrets.override.yaml \
  up -d
```

## Rotation Model (Operational)

1. Rotate values in Vault.
2. Re-inject/re-render runtime secrets.
3. Restart affected services.
4. Verify JWT validation and health checks.

No code change is required for normal secret rotation.

## Failure Modes To Expect

- Missing key: validator fails, or service fails startup.
- Default dev secret in non-dev: startup blocked by guard.
- Bad issuer/audience: auth checks reject tokens.
- Vault unavailable during deploy: deployment should fail closed (do not start with empty/fallback secrets).

## Dev vs Non-Dev

- `dev`: relaxed mode possible for local speed.
- non-dev (`APP_ENV != dev`): strict mode expected; Vault-backed secrets required.

## Security Notes

1. Never commit real secret values.
2. Keep secret files in runtime paths only (example: `/run/iot-secrets`).
3. Restrict Vault policies by service/role (least privilege).
4. Prefer short-lived credentials and audited access in production Vault setup.

## Current Project Status (As Of 2026-03-17)

### 1) How to give secrets to Vault

In production, secrets are created directly in your Vault engine/path by an ops/admin account (not through git files).

In this repo, for bootstrap/testing, you simulate the Vault output shape with:

- `vault/examples/vault-export.example.json`

Then you run `render_runtime_env.py` and `validate_runtime_env.py`.

### 2) Which mode do we use: inject or rendered?

Current status:

- Implemented now: **rendered mode** (bootstrap-compatible) using generated env files.
- Target production mode: **inject mode** (Vault Agent/Injector/CSI) is preferred and should replace manual rendering when deployment automation is finalized.

### 3) Is Vault implemented and functional?

- Implemented now: **partially** (bootstrap layer is functional).
- Functional now: yes, for contract validation and runtime env generation/validation.
- Not implemented yet in this repo: full Vault server provisioning, auth method setup, policy provisioning, and automated injector wiring.

Planned completion:

- This is tracked as Wave 6 hardening follow-up (post-baseline automation hardening in deployment path).

### 4) Which Vault implementation are we using?

- Decision baseline: **HashiCorp Vault-compatible model** (Agent/Injector/CSI style integration).
- In-repo implementation today: **provider-agnostic bootstrap tooling** (contract + render + validate), without a concrete Vault cluster module yet.

If you want, next step can lock this to one concrete implementation (`HashiCorp Vault OSS` or `HCP Vault`) and add deployment IaC + policy templates.
