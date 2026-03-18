#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

REQUIRED_MAPPING_KEYS = {
    "partner_adapter_error_ratio",
    "partner_adapter_normalize_latency_p95",
    "partner_adapter_governance_handoff_error_ratio",
    "partner_adapter_tenant_scope_reject_ratio",
    "partner_adapter_command_intent_rps",
    "partner_adapter_overload_reject_ratio",
}

REQUIRED_ALERT_NAMES = {
    "PartnerAdapterHighErrorRate",
    "PartnerAdapterNormalizeLatencyHigh",
    "PartnerAdapterGovernanceHandoffErrorRatioHigh",
    "PartnerAdapterTenantScopeRejectRatioHigh",
    "PartnerAdapterCommandIntentThroughputLow",
    "PartnerAdapterOverloadRejectRatioHigh",
}

REQUIRED_RECEIVERS = {"wave7-pager", "wave7-warn"}


def _load_yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify W7 partner observability wiring")
    parser.add_argument("--mapping", required=True, type=Path)
    parser.add_argument("--rules", required=True, type=Path)
    parser.add_argument("--routing", required=True, type=Path)
    parser.add_argument("--healthy", required=True, type=Path)
    parser.add_argument("--breach", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    mapping = _load_yaml(args.mapping)
    rules = _load_yaml(args.rules)
    routing = _load_yaml(args.routing)

    findings: list[str] = []

    mapping_entries = mapping.get("mappings")
    if not isinstance(mapping_entries, dict):
        findings.append("mapping.mappings missing or invalid")
        mapping_entries = {}
    missing_mappings = sorted(REQUIRED_MAPPING_KEYS - set(mapping_entries.keys()))
    if missing_mappings:
        findings.append(f"missing mapping keys: {', '.join(missing_mappings)}")

    alert_names: set[str] = set()
    for group in rules.get("groups", []):
        for rule in group.get("rules", []):
            name = rule.get("alert")
            if isinstance(name, str):
                alert_names.add(name)
    missing_alerts = sorted(REQUIRED_ALERT_NAMES - alert_names)
    if missing_alerts:
        findings.append(f"missing alert rules: {', '.join(missing_alerts)}")

    receivers = routing.get("receivers", [])
    receiver_names = {item.get("name") for item in receivers if isinstance(item, dict)}
    missing_receivers = sorted(name for name in REQUIRED_RECEIVERS if name not in receiver_names)
    if missing_receivers:
        findings.append(f"missing alert receivers: {', '.join(missing_receivers)}")

    healthy = json.loads(args.healthy.read_text(encoding="utf-8"))
    breach = json.loads(args.breach.read_text(encoding="utf-8"))
    for required_key in (
        "partner_adapter_5xx_ratio",
        "partner_adapter_normalize_p95_seconds",
        "partner_adapter_governance_handoff_error_ratio",
        "partner_adapter_tenant_scope_reject_ratio",
        "partner_adapter_command_intent_rps",
        "partner_adapter_overload_reject_ratio",
    ):
        if required_key not in healthy:
            findings.append(f"healthy sample missing key: {required_key}")
        if required_key not in breach:
            findings.append(f"breach sample missing key: {required_key}")

    result = {
        "status": "PASS" if not findings else "FAIL",
        "finding_count": len(findings),
        "findings": findings,
        "checked": {
            "mapping": str(args.mapping),
            "rules": str(args.rules),
            "routing": str(args.routing),
            "healthy": str(args.healthy),
            "breach": str(args.breach),
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(f"verification={result['status']} findings={result['finding_count']}")
    for finding in findings:
        print(f" - {finding}")

    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
