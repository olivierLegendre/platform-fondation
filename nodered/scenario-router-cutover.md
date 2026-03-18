# W6-04 Scenario/Command Routing Cutover (Node-RED -> automation-scenario-service + channel-policy-router)

## Objective

Disable Node-RED scenario evaluation and command-routing logic and move orchestration/routing ownership to:

- `automation-scenario-service` (workflow and decision orchestration)
- `channel-policy-router` (channel policy, dispatch, fallback, reconciliation)

## Inputs

- Legacy flow file: `/home/olivier/Public/poc/stack/nodered/data/flows.json`
- Candidate extraction report: `nodered/reports/poc_scenario_router_cutover_candidates.json`

## Cutover Rules

1. Node-RED must not decide scenario outcomes.
2. Node-RED must not compute command routing/channel policy.
3. Node-RED must not publish actuator commands as the source of truth.
4. Scenario command lifecycle must be traceable through service APIs/events.

## Execution Tooling (Implemented)

Generate cutover preview and action report:

```bash
python3 nodered/scripts/apply_scenario_router_cutover.py \
  --flows /home/olivier/Public/poc/stack/nodered/data/flows.json \
  --candidates nodered/reports/poc_scenario_router_cutover_candidates.json \
  --out-flows nodered/flows/poc_scenario_router_cutover_preview.json \
  --out-report nodered/reports/poc_scenario_router_cutover_actions.json
```

Re-audit bridge policy on preview flow:

```bash
python3 nodered/scripts/audit_bridge_policy.py \
  --flows nodered/flows/poc_scenario_router_cutover_preview.json \
  --policy nodered/policy/bridge_allowlist.json \
  --report nodered/reports/poc_scenario_router_cutover_bridge_audit.json
```

## Current Preview Evidence (2026-03-17)

- Candidate nodes: `15`
- Disabled by cutover rules: `11`
- Skipped candidates (non-target in this step): `4`
- Bridge-policy violations:
  - before preview: `270`
  - after scenario/router preview: `245`

Interpretation:

- Scenario routing and command publish chain are now explicitly disabled in a generated preview flow.
- Remaining violations belong to ingestion/reference/dashboard domains (`W6-02`, `W6-03`, `W6-05`).

## Done Criteria

- Node-RED does not execute scenario decisions or command routing logic.
- `automation-scenario-service` + `channel-policy-router` own the full scenario->command path.
- Wave 6 checkpoint includes evidence and rollback notes.
