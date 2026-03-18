#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _as_str(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _match_any(patterns: list[str], value: str) -> bool:
    return any(re.match(pattern, value) for pattern in patterns)


def audit(
    flows: list[dict[str, Any]],
    policy: dict[str, Any],
    *,
    include_disabled: bool,
) -> tuple[list[str], int]:
    violations: list[str] = []

    allowed_runtime = set(policy.get("allowed_runtime_node_types", []))
    allowed_config = set(policy.get("allowed_config_node_types", []))
    forbidden_runtime = set(policy.get("forbidden_runtime_node_types", []))

    forbidden_prefixes = [str(v) for v in policy.get("forbidden_name_prefixes", [])]
    forbidden_contains = [str(v).lower() for v in policy.get("forbidden_name_contains", [])]

    allowed_mqtt_in = [str(v) for v in policy.get("allowed_mqtt_in_topic_patterns", [])]
    allowed_mqtt_out = [str(v) for v in policy.get("allowed_mqtt_out_topic_patterns", [])]

    skipped_disabled = 0

    for node in flows:
        node_id = _as_str(node.get("id"))
        node_type = _as_str(node.get("type"))
        node_name = _as_str(node.get("name"))
        node_topic = _as_str(node.get("topic"))
        on_tab = bool(node.get("z"))
        disabled = bool(node.get("d"))

        if not node_type:
            continue

        if disabled and not include_disabled:
            skipped_disabled += 1
            continue

        if on_tab:
            if node_type in forbidden_runtime:
                violations.append(
                    f"{node_id}: forbidden runtime node type '{node_type}'"
                )
            elif node_type not in allowed_runtime:
                violations.append(
                    f"{node_id}: runtime node type '{node_type}' not in allowlist"
                )
        else:
            if node_type not in allowed_config:
                violations.append(
                    f"{node_id}: config/global node type '{node_type}' not in allowlist"
                )

        lowered_name = node_name.lower()
        for prefix in forbidden_prefixes:
            if node_name.startswith(prefix):
                violations.append(
                    f"{node_id}: node name '{node_name}' uses forbidden prefix '{prefix}'"
                )
                break

        for fragment in forbidden_contains:
            if fragment and fragment in lowered_name:
                violations.append(
                    f"{node_id}: node name '{node_name}' contains forbidden fragment '{fragment}'"
                )
                break

        if node_type == "mqtt in" and node_topic:
            if not _match_any(allowed_mqtt_in, node_topic):
                violations.append(
                    f"{node_id}: mqtt in topic '{node_topic}' not allowlisted"
                )

        if node_type == "mqtt out" and node_topic:
            if not _match_any(allowed_mqtt_out, node_topic):
                violations.append(
                    f"{node_id}: mqtt out topic '{node_topic}' not allowlisted"
                )

    return violations, skipped_disabled


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit Node-RED flows against bridge-only policy allowlist."
    )
    parser.add_argument("--flows", required=True, type=Path, help="Path to flows.json")
    parser.add_argument("--policy", required=True, type=Path, help="Path to allowlist policy JSON")
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional path to write JSON report",
    )
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Exit non-zero when violations are found",
    )
    parser.add_argument(
        "--include-disabled",
        action="store_true",
        help="Include disabled nodes in violation checks (default skips them)",
    )
    args = parser.parse_args()

    raw_flows = _load_json(args.flows)
    if not isinstance(raw_flows, list):
        print("flows file must contain a JSON list", file=sys.stderr)
        return 2

    policy = _load_json(args.policy)
    if not isinstance(policy, dict):
        print("policy file must contain a JSON object", file=sys.stderr)
        return 2

    violations, skipped_disabled = audit(
        raw_flows,
        policy,
        include_disabled=args.include_disabled,
    )

    report: dict[str, Any] = {
        "flows": str(args.flows),
        "policy": str(args.policy),
        "total_nodes": len(raw_flows),
        "skipped_disabled_nodes": skipped_disabled,
        "include_disabled": args.include_disabled,
        "violation_count": len(violations),
        "violations": violations,
    }

    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        f"nodes={len(raw_flows)} skipped_disabled={skipped_disabled} violations={len(violations)}"
    )
    for item in violations[:50]:
        print(f" - {item}")
    if len(violations) > 50:
        print(f" - ... ({len(violations) - 50} more)")

    if violations and args.enforce:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
