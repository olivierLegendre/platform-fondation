# W6-03 Reference/Mapping API Cutover (Node-RED -> reference-api-service)

## Objective

Disable Node-RED HTTP reference/mapping endpoints and route all reference/mapping API traffic through `reference-api-service`.

## Inputs

- Legacy flow file: `/home/olivier/Public/poc/stack/nodered/data/flows.json`
- Candidate extraction report: `nodered/reports/poc_reference_api_cutover_candidates.json`

## Cutover Rules

1. Node-RED must not expose service-owned reference/mapping HTTP endpoints.
2. Node-RED must not execute reference/mapping validation or SQL query construction logic.
3. `reference-api-service` owns CRUD/list/link/mapping behavior and contracts.
4. During transition, compatibility routing may forward calls but must not duplicate business logic.

## Execution Tooling (Implemented)

Generate cutover preview and action report:

```bash
python3 nodered/scripts/apply_reference_api_cutover.py \
  --flows /home/olivier/Public/poc/stack/nodered/data/flows.json \
  --candidates nodered/reports/poc_reference_api_cutover_candidates.json \
  --out-flows nodered/flows/poc_reference_api_cutover_preview.json \
  --out-report nodered/reports/poc_reference_api_cutover_actions.json
```

Re-audit bridge policy on preview flow:

```bash
python3 nodered/scripts/audit_bridge_policy.py \
  --flows nodered/flows/poc_reference_api_cutover_preview.json \
  --policy nodered/policy/bridge_allowlist.json \
  --report nodered/reports/poc_reference_api_cutover_bridge_audit.json
```

## Current Preview Evidence (2026-03-17)

- Candidate nodes: `61`
- Disabled by cutover rules: `55`
- Skipped candidates (non-target in this step): `6`
- Bridge-policy violations:
  - before preview: `270`
  - after reference API preview: `174`

Interpretation:

- Reference/mapping API routes and main execution chain are now explicitly disabled in a generated preview flow.
- Remaining violations mostly belong to ingestion/scenario/dashboard domains (`W6-02`, `W6-04`, `W6-05`).

## Done Criteria

- No active Node-RED `http in` endpoint serves reference/mapping APIs.
- `reference-api-service` is the only production endpoint for reference/mapping APIs.
- Wave 6 checkpoint includes cutover evidence and rollback notes.
