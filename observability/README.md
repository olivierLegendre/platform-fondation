# Wave 6 Observability Baseline (W6-09)

This directory contains SLO and alerting scaffolding for critical Wave 6 paths:

- ingestion API
- reference API
- command routing and reconciliation
- workflow orchestration latency

Wave 7 extension (partner adapter baseline):
- partner integration adapter API/error/latency governance metrics
- partner adapter scale/load signals (command-intent throughput and overload reject ratio)

## Files

- `slo-targets.yaml`: declarative SLO targets.
- `prometheus/rules/wave6-critical-path-alerts.yaml`: alert rules baseline.
- `metric-name-mapping.yaml`: platform metric name to rule input mapping.
- `alertmanager/wave6-alert-routing.yaml`: baseline alert routing for warning/page channels.
- `examples/synthetic-metrics-healthy.json`: synthetic healthy metrics payload.
- `examples/synthetic-metrics-breach.json`: synthetic breach metrics payload.
- `scripts/run_synthetic_alert_checks.py`: threshold checker used as acceptance evidence.
- `scripts/verify_wave6_observability.py`: wiring verifier for mapping/rules/routing + synthetic payload coverage.
- `reports/wave6-observability-verification.json`: latest verification report artifact.
- `slo-targets-wave7-partner.yaml`: Wave 7 partner adapter SLO baseline.
- `prometheus/rules/wave7-partner-adapter-alerts.yaml`: Wave 7 partner adapter alert rules.
- `metric-name-mapping-wave7-partner.yaml`: Wave 7 partner metric mapping.
- `alertmanager/wave7-alert-routing.yaml`: Wave 7 alert routing baseline.
- `examples/synthetic-metrics-wave7-healthy.json`: synthetic healthy partner metrics payload.
- `examples/synthetic-metrics-wave7-breach.json`: synthetic breach partner metrics payload.
- `scripts/verify_wave7_partner_observability.py`: Wave 7 partner observability wiring verifier.
- `reports/wave7-partner-observability-verification.json`: latest Wave 7 partner verification report.

## Synthetic Check Usage

```bash
python3 observability/scripts/run_synthetic_alert_checks.py \
  --input observability/examples/synthetic-metrics-healthy.json

python3 observability/scripts/run_synthetic_alert_checks.py \
  --input observability/examples/synthetic-metrics-breach.json
```

Expected:

- healthy payload: pass
- breach payload: fail with explicit threshold violations

## Wiring Verification Usage

```bash
python3 -m py_compile observability/scripts/verify_wave6_observability.py

python3 observability/scripts/verify_wave6_observability.py \
  --mapping observability/metric-name-mapping.yaml \
  --rules observability/prometheus/rules/wave6-critical-path-alerts.yaml \
  --routing observability/alertmanager/wave6-alert-routing.yaml \
  --healthy observability/examples/synthetic-metrics-healthy.json \
  --breach observability/examples/synthetic-metrics-breach.json \
  --out observability/reports/wave6-observability-verification.json
```

Expected:

- verification: `PASS`
- findings: `0`

## Notes

This is a Wave 6 activation baseline. Service teams should align metric names with actual exported telemetry in each repo and wire these rules into the shared monitoring stack.

Wave 7 partner usage:

```bash
python3 -m py_compile observability/scripts/verify_wave7_partner_observability.py

python3 observability/scripts/verify_wave7_partner_observability.py \
  --mapping observability/metric-name-mapping-wave7-partner.yaml \
  --rules observability/prometheus/rules/wave7-partner-adapter-alerts.yaml \
  --routing observability/alertmanager/wave7-alert-routing.yaml \
  --healthy observability/examples/synthetic-metrics-wave7-healthy.json \
  --breach observability/examples/synthetic-metrics-wave7-breach.json \
  --out observability/reports/wave7-partner-observability-verification.json
```
