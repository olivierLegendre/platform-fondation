# W6-10 Node-RED Retirement Cutover (Preview)

Goal: generate a strict bridge-only retirement preview from legacy Node-RED flows and produce auditable evidence before full runtime removal from production topology.

## Inputs

- Source flow: `/home/olivier/Public/poc/stack/nodered/data/flows.json`
- Policy: `nodered/policy/bridge_allowlist.json`

## Script

- `nodered/scripts/apply_retirement_cutover.py`

Behavior:
- disables all runtime nodes that violate bridge-only policy;
- removes disallowed config nodes from the preview flow;
- emits action report with exact node-level reasons.

## Commands

```bash
python3 -m py_compile nodered/scripts/apply_retirement_cutover.py

python3 nodered/scripts/apply_retirement_cutover.py \
  --flows /home/olivier/Public/poc/stack/nodered/data/flows.json \
  --policy nodered/policy/bridge_allowlist.json \
  --out-flows nodered/flows/poc_retirement_cutover_preview.json \
  --out-report nodered/reports/poc_retirement_cutover_actions.json

python3 nodered/scripts/audit_bridge_policy.py \
  --flows nodered/flows/poc_retirement_cutover_preview.json \
  --policy nodered/policy/bridge_allowlist.json \
  --report nodered/reports/poc_retirement_cutover_bridge_audit.json
```

## Current Baseline Evidence (2026-03-17)

- `total_input_nodes=169`
- `total_output_nodes=145`
- `disabled_runtime_count=134`
- `removed_config_count=24`
- bridge policy audit on active nodes: `violations=0`

Artifacts:
- `nodered/flows/poc_retirement_cutover_preview.json`
- `nodered/reports/poc_retirement_cutover_actions.json`
- `nodered/reports/poc_retirement_cutover_bridge_audit.json`

## Remaining Work To Close W6-10

1. Remove Node-RED service from production compose/topology (not only disable internals).
2. Validate rollback path in runbook and service owner sign-off.
3. Confirm production critical paths run entirely through service stack without Node-RED runtime dependency.
