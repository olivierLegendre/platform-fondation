#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

THRESHOLDS = {
    "device_ingestion_5xx_ratio": 0.02,
    "reference_api_5xx_ratio": 0.02,
    "channel_policy_router_queue_depth": 200,
    "channel_policy_router_reconciliation_sla_breach_ratio": 0.01,
    "automation_workflow_start_p95_seconds": 5.0,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run synthetic SLO/alert threshold checks")
    parser.add_argument("--input", type=Path, required=True, help="Synthetic metrics JSON")
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    failures: list[str] = []

    for key, threshold in THRESHOLDS.items():
        value = payload.get(key)
        if value is None:
            failures.append(f"missing metric: {key}")
            continue
        if float(value) > threshold:
            failures.append(f"{key}={value} exceeds threshold {threshold}")

    if failures:
        print("synthetic alert checks: FAILED")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("synthetic alert checks: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
