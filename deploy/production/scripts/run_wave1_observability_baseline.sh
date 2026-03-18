#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

WIRING_REPORT="${WIRING_REPORT:-observability/reports/w1-observability-wiring-verification.json}"
FINAL_REPORT="${FINAL_REPORT:-observability/reports/w1-observability-baseline-report.json}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

python3 -m py_compile \
  observability/scripts/verify_wave6_observability.py \
  observability/scripts/run_synthetic_alert_checks.py

if python3 observability/scripts/verify_wave6_observability.py \
  --mapping observability/metric-name-mapping.yaml \
  --rules observability/prometheus/rules/wave6-critical-path-alerts.yaml \
  --routing observability/alertmanager/wave6-alert-routing.yaml \
  --healthy observability/examples/synthetic-metrics-healthy.json \
  --breach observability/examples/synthetic-metrics-breach.json \
  --out "$WIRING_REPORT" >"$TMP_DIR/wiring.log" 2>&1; then
  wiring_status="PASS"
else
  wiring_status="FAIL"
fi

if python3 observability/scripts/run_synthetic_alert_checks.py \
  --input observability/examples/synthetic-metrics-healthy.json >"$TMP_DIR/healthy.log" 2>&1; then
  healthy_status="PASS"
else
  healthy_status="FAIL"
fi

if python3 observability/scripts/run_synthetic_alert_checks.py \
  --input observability/examples/synthetic-metrics-breach.json >"$TMP_DIR/breach.log" 2>&1; then
  breach_expected_fail="FAIL"
else
  breach_expected_fail="PASS"
fi

python3 - "$FINAL_REPORT" "$WIRING_REPORT" "$TMP_DIR" "$wiring_status" "$healthy_status" "$breach_expected_fail" <<'PY'
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

final_report = Path(sys.argv[1])
wiring_report = Path(sys.argv[2])
tmp_dir = Path(sys.argv[3])
wiring_status = sys.argv[4]
healthy_status = sys.argv[5]
breach_expected_fail = sys.argv[6]

findings: list[str] = []

checks = {
    "wiring_verification": {
        "status": wiring_status,
        "report": str(wiring_report),
        "output_tail": "\n".join((tmp_dir / "wiring.log").read_text(encoding="utf-8").strip().splitlines()[-8:]),
    },
    "synthetic_healthy": {
        "status": healthy_status,
        "output_tail": "\n".join((tmp_dir / "healthy.log").read_text(encoding="utf-8").strip().splitlines()[-8:]),
    },
    "synthetic_breach_expected_fail": {
        "status": breach_expected_fail,
        "output_tail": "\n".join((tmp_dir / "breach.log").read_text(encoding="utf-8").strip().splitlines()[-8:]),
    },
}

if wiring_status != "PASS":
    findings.append("wiring verification failed")
if healthy_status != "PASS":
    findings.append("healthy synthetic check did not pass")
if breach_expected_fail != "PASS":
    findings.append("breach synthetic check did not fail as expected")

status = "PASS" if not findings else "FAIL"

payload = {
    "status": status,
    "finding_count": len(findings),
    "findings": findings,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "checks": checks,
}

final_report.parent.mkdir(parents=True, exist_ok=True)
final_report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(f"wrote report: {final_report}")
print(f"status: {status}")
PY

if [[ ! -f "$FINAL_REPORT" ]]; then
  echo "missing final report: $FINAL_REPORT" >&2
  exit 1
fi

if ! python3 - "$FINAL_REPORT" <<'PY'
from __future__ import annotations
import json
import sys
from pathlib import Path
report = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
raise SystemExit(0 if report.get('status') == 'PASS' else 1)
PY
then
  exit 1
fi
