# W6-02 Ingestion Cutover (Node-RED -> device-ingestion-service)

## Objective

Disable legacy Node-RED ingestion handlers and route ingestion exclusively through `device-ingestion-service`.

## Inputs

- Legacy flow file: `/home/olivier/Public/poc/stack/nodered/data/flows.json`
- Candidate extraction report: `nodered/reports/poc_ingestion_cutover_candidates.json`

## Cutover Rules

1. Node-RED must not parse, normalize, enrich, or persist telemetry.
2. Node-RED must not write to device/telemetry tables.
3. Node-RED may temporarily forward allowed MQTT topics as bridge-only traffic.
4. `device-ingestion-service` is the only owner of ingestion persistence.

## Execution Tooling (Implemented)

Generate cutover preview and action report:

```bash
python3 nodered/scripts/apply_ingestion_cutover.py \
  --flows /home/olivier/Public/poc/stack/nodered/data/flows.json \
  --candidates nodered/reports/poc_ingestion_cutover_candidates.json \
  --out-flows nodered/flows/poc_ingestion_cutover_preview.json \
  --out-report nodered/reports/poc_ingestion_cutover_actions.json
```

Re-audit bridge policy on preview flow:

```bash
python3 nodered/scripts/audit_bridge_policy.py \
  --flows nodered/flows/poc_ingestion_cutover_preview.json \
  --policy nodered/policy/bridge_allowlist.json \
  --report nodered/reports/poc_ingestion_cutover_bridge_audit.json
```

## Current Preview Evidence (2026-03-17)

- Candidate nodes: `22`
- Disabled by cutover rules: `7`
- Skipped candidates (non-ingestion in this step): `15`
- Bridge-policy violations:
  - before preview: `270`
  - after ingestion preview: `257`

Interpretation:

- Ingestion-specific nodes are now explicitly identified and disabled in a generated preview flow.
- Remaining violations belong to other cutover domains (`W6-03..W6-05`).

## Done Criteria

- No active Node-RED node performs ingest normalization or SQL persistence.
- `device-ingestion-service` receives and persists ingest events for production topics.
- Cutover evidence recorded in Wave 6 checkpoint.
