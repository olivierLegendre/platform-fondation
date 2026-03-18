# W6-05 Dashboard Read-Path Cutover (Node-RED -> operator-ui + Grafana)

## Objective

Retire Node-RED dashboard SQL/formatting logic and move read paths to service-owned APIs and approved observability/analytics views.

## Inputs

- Legacy flow file: `/home/olivier/Public/poc/stack/nodered/data/flows.json`
- Candidate extraction report: `nodered/reports/poc_dashboard_cutover_candidates.json`

## Cutover Rules

1. Node-RED must not own dashboard/business read aggregation.
2. SQL read models for operations views must be service-owned or Grafana-backed.
3. Operator UI reads from service APIs only.
4. Dashboard visual logic must not block operational command path.

## Execution Tooling (Implemented)

Generate cutover preview and action report:

```bash
python3 nodered/scripts/apply_dashboard_cutover.py \
  --flows /home/olivier/Public/poc/stack/nodered/data/flows.json \
  --candidates nodered/reports/poc_dashboard_cutover_candidates.json \
  --out-flows nodered/flows/poc_dashboard_cutover_preview.json \
  --out-report nodered/reports/poc_dashboard_cutover_actions.json
```

Re-audit bridge policy on preview flow:

```bash
python3 nodered/scripts/audit_bridge_policy.py \
  --flows nodered/flows/poc_dashboard_cutover_preview.json \
  --policy nodered/policy/bridge_allowlist.json \
  --report nodered/reports/poc_dashboard_cutover_bridge_audit.json
```

## Current Preview Evidence (2026-03-17)

- Candidate nodes: `92`
- Disabled by cutover rules: `83`
- Skipped candidates (non-target in this step): `9`
- Bridge-policy violations:
  - before preview: `270`
  - after dashboard preview: `130`

Interpretation:

- Dashboard visual + SQL chains are now explicitly disabled in a generated preview flow.
- Remaining violations are mainly non-dashboard domains (ingestion/reference/scenario chains still active in this isolated preview run).

## Done Criteria

- Node-RED dashboard and dashboard SQL chains are retired from production path.
- Operator dashboard views are served via service APIs/Grafana.
- Evidence captured in Wave 6 checkpoint.
