# platform-foundation

Repository for shared runtime and platform-level operational controls.

## Current focus

- Wave 6 `W6-01`: Node-RED bridge-only freeze controls.
- Wave 6 `W6-07`: Vault bootstrap + runtime secret validation baseline.
- Wave 6 `W6-09`: SLO + alerting activation baseline.
- Wave 7 `W7-06` (planned): observability and runbook baseline for `partner-integration-layer` adapter operations.

## Wave 7 Awareness

`platform-foundation` is a dependency for Wave 7 partner integration rollout:
1. provides runtime/deploy/secret/observability baseline consumed by `partner-integration-layer`;
2. will host adapter-related SLO/alert and incident-recovery runbook controls under `W7-06`;
3. remains policy-neutral relative to adapter business logic ownership.

See:

- `../plateform-meta-iot/docs/project-monitoring/services/platform-foundation/nodered/README.md`
- `nodered/policy/bridge_allowlist.json`
- `nodered/scripts/audit_bridge_policy.py`
- `nodered/reports/poc_bridge_policy_report.json`
- `nodered/scripts/extract_ingestion_cutover_candidates.py`
- `nodered/scripts/apply_ingestion_cutover.py`
- `nodered/reports/poc_ingestion_cutover_candidates.json`
- `nodered/reports/poc_ingestion_cutover_actions.json`
- `nodered/flows/poc_ingestion_cutover_preview.json`
- `nodered/reports/poc_ingestion_cutover_bridge_audit.json`
- `../plateform-meta-iot/docs/project-monitoring/services/platform-foundation/nodered/ingestion-cutover.md`
- `nodered/scripts/extract_reference_api_cutover_candidates.py`
- `nodered/scripts/apply_reference_api_cutover.py`
- `nodered/reports/poc_reference_api_cutover_candidates.json`
- `nodered/reports/poc_reference_api_cutover_actions.json`
- `nodered/flows/poc_reference_api_cutover_preview.json`
- `nodered/reports/poc_reference_api_cutover_bridge_audit.json`
- `../plateform-meta-iot/docs/project-monitoring/services/platform-foundation/nodered/reference-api-cutover.md`
- `nodered/scripts/extract_scenario_router_cutover_candidates.py`
- `nodered/scripts/apply_scenario_router_cutover.py`
- `nodered/reports/poc_scenario_router_cutover_candidates.json`
- `nodered/reports/poc_scenario_router_cutover_actions.json`
- `nodered/flows/poc_scenario_router_cutover_preview.json`
- `nodered/reports/poc_scenario_router_cutover_bridge_audit.json`
- `../plateform-meta-iot/docs/project-monitoring/services/platform-foundation/nodered/scenario-router-cutover.md`
- `nodered/scripts/extract_dashboard_cutover_candidates.py`
- `nodered/scripts/apply_dashboard_cutover.py`
- `nodered/reports/poc_dashboard_cutover_candidates.json`
- `nodered/reports/poc_dashboard_cutover_actions.json`
- `nodered/flows/poc_dashboard_cutover_preview.json`
- `nodered/reports/poc_dashboard_cutover_bridge_audit.json`
- `../plateform-meta-iot/docs/project-monitoring/services/platform-foundation/nodered/dashboard-cutover.md`
- `nodered/scripts/apply_retirement_cutover.py`
- `nodered/flows/poc_retirement_cutover_preview.json`
- `nodered/reports/poc_retirement_cutover_actions.json`
- `nodered/reports/poc_retirement_cutover_bridge_audit.json`
- `../plateform-meta-iot/docs/project-monitoring/services/platform-foundation/nodered/retirement-cutover.md`
- `nodered/scripts/verify_nodered_topology_retired.py`
- `nodered/reports/w6_topology_retirement_verification.json`
- `nodered/reports/poc_topology_retirement_gap_report.json`
- `nodered/scripts/run_w6_topology_release_gate.sh`
- `nodered/policy/w6_topology_release_gate.manifests.txt`
- `nodered/reports/w6_topology_release_gate_report.json`
- `nodered/scripts/evaluate_w6_retirement_readiness.py`
- `nodered/reports/w6_retirement_readiness_report.json`
- `../plateform-meta-iot/docs/project-monitoring/services/platform-foundation/nodered/topology-retirement-check.md`
- `vault/README.md`
- `vault/secrets-contract.yaml`
- `vault/scripts/render_runtime_env.py`
- `vault/scripts/validate_runtime_env.py`
- `vault/examples/docker-compose.secrets.override.yaml`
- `observability/README.md`
- `observability/slo-targets.yaml`
- `observability/prometheus/rules/wave6-critical-path-alerts.yaml`
- `observability/metric-name-mapping.yaml`
- `observability/alertmanager/wave6-alert-routing.yaml`
- `observability/scripts/run_synthetic_alert_checks.py`
- `observability/scripts/verify_wave6_observability.py`
- `observability/reports/wave6-observability-verification.json`
