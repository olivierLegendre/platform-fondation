# Node-RED Bridge-Only Controls (Wave 6)

This directory contains enforcement artifacts for Wave 6 Node-RED retirement.

## W6-01 Artifacts (Bridge-only policy)

- `policy/bridge_allowlist.json`
- `scripts/audit_bridge_policy.py`
- `scripts/run_bridge_policy_gate.sh`
- `flows/bridge_only_template.json`
- `reports/poc_bridge_policy_report.json`
- `reports/bridge_policy_gate_report.json`

## W6-02 Artifacts (Ingestion cutover execution)

- `scripts/extract_ingestion_cutover_candidates.py`
- `scripts/apply_ingestion_cutover.py`
- `reports/poc_ingestion_cutover_candidates.json`
- `reports/poc_ingestion_cutover_actions.json`
- `flows/poc_ingestion_cutover_preview.json`
- `reports/poc_ingestion_cutover_bridge_audit.json`

## W6-03 Artifacts (Reference API cutover execution)

- `scripts/extract_reference_api_cutover_candidates.py`
- `scripts/apply_reference_api_cutover.py`
- `reports/poc_reference_api_cutover_candidates.json`
- `reports/poc_reference_api_cutover_actions.json`
- `flows/poc_reference_api_cutover_preview.json`
- `reports/poc_reference_api_cutover_bridge_audit.json`

## W6-04 Artifacts (Scenario/router cutover execution)

- `scripts/extract_scenario_router_cutover_candidates.py`
- `scripts/apply_scenario_router_cutover.py`
- `reports/poc_scenario_router_cutover_candidates.json`
- `reports/poc_scenario_router_cutover_actions.json`
- `flows/poc_scenario_router_cutover_preview.json`
- `reports/poc_scenario_router_cutover_bridge_audit.json`

## W6-05 Artifacts (Dashboard read-path cutover execution)

- `scripts/extract_dashboard_cutover_candidates.py`
- `scripts/apply_dashboard_cutover.py`
- `reports/poc_dashboard_cutover_candidates.json`
- `reports/poc_dashboard_cutover_actions.json`
- `flows/poc_dashboard_cutover_preview.json`
- `reports/poc_dashboard_cutover_bridge_audit.json`


## W6-10 Artifacts (Retirement cutover preview)

- `scripts/apply_retirement_cutover.py`
- `flows/poc_retirement_cutover_preview.json`
- `reports/poc_retirement_cutover_actions.json`
- `reports/poc_retirement_cutover_bridge_audit.json`
- `retirement-cutover.md`
- `scripts/verify_nodered_topology_retired.py`
- `reports/w6_topology_retirement_verification.json`
- `reports/poc_topology_retirement_gap_report.json`
- `scripts/run_w6_topology_release_gate.sh`
- `policy/w6_topology_release_gate.manifests.txt`
- `reports/w6_topology_release_gate_report.json`
- `scripts/evaluate_w6_retirement_readiness.py`
- `reports/w6_retirement_readiness_report.json`
- `deploy/production/README.md`
- `deploy/production/compose/reference-api.compose.yaml`
- `deploy/production/compose/device-ingestion.compose.yaml`
- `deploy/production/compose/channel-policy-router.compose.yaml`
- `deploy/production/compose/vault-secrets-runtime.compose.yaml`
- `topology-retirement-check.md`

## Current baseline (2026-03-17)

- Legacy PoC audit: `nodes=169`, `violations=270`
- Managed bridge flow gate: `nodes=7`, `violations=0`
- W6-02 preview: `22` candidates, `7` disabled, `257` violations
- W6-03 preview: `61` candidates, `55` disabled, `174` violations
- W6-04 preview: `15` candidates, `11` disabled, `245` violations
- W6-05 preview: `92` candidates, `83` disabled, `130` violations
- W6-10 preview: `134` runtime nodes disabled, `24` disallowed config nodes removed, `0` active-node violations
- W6-10 topology gate: `manifests=4`, `services=5`, `findings=0`
- W6-10 one-command release gate: `status=PASS`, `manifests=4`, `services=5`, `findings=0`
- W6-10 readiness evaluation: `decision=READY_FOR_W6_10_CLOSURE`, `blockers=0`, `warnings=0`
- W6-10 legacy PoC gap check: `manifests=1`, `services=8`, `findings=2` (`status=FAIL`)

Interpretation:

- Managed bridge baseline is compliant and CI-gated.
- Each cutover domain now has executable preview tooling and evidence artifacts.
- Full closure requires applying cumulative disablement in runtime and validating final service-owned paths.
- W6-10 provides executable retirement preview and topology verification evidence; final closure still requires running the topology gate against production deployment manifests and removing Node-RED runtime from production topology.
