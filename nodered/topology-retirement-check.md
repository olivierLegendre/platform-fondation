# W6-10 Topology Retirement Verification

Goal: provide an executable check that fails when deployment manifests still reference Node-RED runtime.

## Script

- `nodered/scripts/verify_nodered_topology_retired.py`

Checks performed per manifest service entry:
- service name containing `nodered`/`node-red`
- image containing `nodered`/`node-red`
- container_name containing `nodered`/`node-red`
- depends_on referencing `nodered`/`node-red`

## Baseline Verification Command (2026-03-17)

```bash
python3 -m py_compile nodered/scripts/verify_nodered_topology_retired.py

python3 nodered/scripts/verify_nodered_topology_retired.py \
  --manifest /home/olivier/work/iot_services/reference-api-service/docker-compose.postgres.yml \
  --manifest /home/olivier/work/iot_services/device-ingestion-service/docker-compose.postgres.yml \
  --manifest /home/olivier/work/iot_services/channel-policy-router/docker-compose.postgres.yml \
  --manifest /home/olivier/work/iot_services/platform-foundation/vault/examples/docker-compose.secrets.override.yaml \
  --out nodered/reports/w6_topology_retirement_verification.json
```

## Baseline Result

- `status=PASS`
- `manifest_count=4`
- `checked_service_count=5`
- `finding_count=0`

Artifact:
- `nodered/reports/w6_topology_retirement_verification.json`


## Legacy PoC Gap Check (2026-03-17)

```bash
python3 nodered/scripts/verify_nodered_topology_retired.py   --manifest /home/olivier/Public/poc/stack/docker-compose.yml   --out nodered/reports/poc_topology_retirement_gap_report.json
```

Result:
- `status=FAIL`
- `manifest_count=1`
- `checked_service_count=8`
- `finding_count=2`
- findings include Node-RED service presence in PoC compose topology.

Artifact:
- `nodered/reports/poc_topology_retirement_gap_report.json`


## One-Command Release Gate

```bash
./nodered/scripts/run_w6_topology_release_gate.sh
```

Default manifest set:
- `nodered/policy/w6_topology_release_gate.manifests.txt` (production scaffold baseline)

Scaffold manifests:
- `deploy/production/compose/reference-api.compose.yaml`
- `deploy/production/compose/device-ingestion.compose.yaml`
- `deploy/production/compose/channel-policy-router.compose.yaml`
- `deploy/production/compose/vault-secrets-runtime.compose.yaml`

Default report output:
- `nodered/reports/w6_topology_release_gate_report.json`

Baseline result (2026-03-17):
- `status=PASS`
- `manifest_count=4`
- `checked_service_count=5`
- `finding_count=0`


## Readiness Evaluation Gate

```bash
python3 -m py_compile nodered/scripts/evaluate_w6_retirement_readiness.py

python3 nodered/scripts/evaluate_w6_retirement_readiness.py \
  --managed nodered/reports/w6_topology_release_gate_report.json \
  --legacy nodered/reports/poc_topology_retirement_gap_report.json \
  --out nodered/reports/w6_retirement_readiness_report.json
```

Baseline result (2026-03-17):
- `decision=READY_FOR_W6_10_CLOSURE`
- `blocker_count=0`
- `blocker_count=0`
- `warning_count=0`

Artifact:
- `nodered/reports/w6_retirement_readiness_report.json`

## Limitations

This check validates only manifests provided to it. Wave 6 closure still requires running the same gate against production deployment manifests as part of release verification.
