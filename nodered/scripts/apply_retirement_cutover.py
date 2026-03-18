#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def as_str(value: Any) -> str:
    return value if isinstance(value, str) else ""


def match_any(patterns: list[str], value: str) -> bool:
    return any(re.match(pattern, value) for pattern in patterns)


def runtime_reasons(node: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    reasons: list[str] = []

    node_type = as_str(node.get("type"))
    node_name = as_str(node.get("name"))
    node_topic = as_str(node.get("topic"))

    allowed_runtime = set(policy.get("allowed_runtime_node_types", []))
    forbidden_runtime = set(policy.get("forbidden_runtime_node_types", []))

    forbidden_prefixes = [as_str(v) for v in policy.get("forbidden_name_prefixes", [])]
    forbidden_contains = [as_str(v).lower() for v in policy.get("forbidden_name_contains", [])]

    allowed_mqtt_in = [as_str(v) for v in policy.get("allowed_mqtt_in_topic_patterns", [])]
    allowed_mqtt_out = [as_str(v) for v in policy.get("allowed_mqtt_out_topic_patterns", [])]

    if node_type in forbidden_runtime:
        reasons.append(f"forbidden_runtime_type:{node_type}")

    if node_type not in allowed_runtime:
        reasons.append(f"runtime_type_not_allowlisted:{node_type}")

    for prefix in forbidden_prefixes:
        if prefix and node_name.startswith(prefix):
            reasons.append(f"forbidden_name_prefix:{prefix}")
            break

    lowered_name = node_name.lower()
    for fragment in forbidden_contains:
        if fragment and fragment in lowered_name:
            reasons.append(f"forbidden_name_contains:{fragment}")
            break

    if node_type == "mqtt in" and node_topic:
        if not match_any(allowed_mqtt_in, node_topic):
            reasons.append(f"mqtt_in_topic_not_allowlisted:{node_topic}")

    if node_type == "mqtt out" and node_topic:
        if not match_any(allowed_mqtt_out, node_topic):
            reasons.append(f"mqtt_out_topic_not_allowlisted:{node_topic}")

    return reasons


def apply_retirement(
    flows: list[dict[str, Any]],
    policy: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    allowed_config = set(policy.get("allowed_config_node_types", []))

    output: list[dict[str, Any]] = []
    disabled_runtime: list[dict[str, Any]] = []
    removed_config: list[dict[str, Any]] = []

    for node in flows:
        node_type = as_str(node.get("type"))
        node_id = as_str(node.get("id"))
        node_name = as_str(node.get("name"))
        on_tab = bool(node.get("z"))

        if not node_type:
            output.append(node)
            continue

        if not on_tab:
            if node_type not in allowed_config:
                removed_config.append({
                    "id": node_id,
                    "type": node_type,
                    "name": node_name,
                })
                continue
            output.append(node)
            continue

        reasons = runtime_reasons(node, policy)
        if reasons:
            node_copy = dict(node)
            node_copy["d"] = True
            output.append(node_copy)
            disabled_runtime.append(
                {
                    "id": node_id,
                    "type": node_type,
                    "name": node_name,
                    "reasons": reasons,
                }
            )
            continue

        output.append(node)

    report = {
        "total_input_nodes": len(flows),
        "total_output_nodes": len(output),
        "disabled_runtime_count": len(disabled_runtime),
        "removed_config_count": len(removed_config),
        "disabled_runtime": sorted(disabled_runtime, key=lambda item: item["id"]),
        "removed_config": sorted(removed_config, key=lambda item: item["id"]),
    }
    return output, report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply W6-10 Node-RED retirement cutover preview using bridge-only policy"
    )
    parser.add_argument("--flows", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--out-flows", required=True, type=Path)
    parser.add_argument("--out-report", required=True, type=Path)
    args = parser.parse_args()

    raw_flows = load_json(args.flows)
    if not isinstance(raw_flows, list):
        raise SystemExit("flows must be a JSON list")

    policy = load_json(args.policy)
    if not isinstance(policy, dict):
        raise SystemExit("policy must be a JSON object")

    out_flows, summary = apply_retirement(raw_flows, policy)

    args.out_flows.parent.mkdir(parents=True, exist_ok=True)
    args.out_flows.write_text(json.dumps(out_flows, indent=2) + "\n", encoding="utf-8")

    result = {
        "source_flows": str(args.flows),
        "policy": str(args.policy),
        "output_flows": str(args.out_flows),
        **summary,
    }
    args.out_report.parent.mkdir(parents=True, exist_ok=True)
    args.out_report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(
        "disabled_runtime_count="
        f"{result['disabled_runtime_count']} removed_config_count={result['removed_config_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
