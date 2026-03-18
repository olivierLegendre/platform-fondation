#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

INGEST_FN_PREFIX = "domain.ingest."
INGEST_FN_EXACT = {
    "repo.devices.build_upsert_query",
    "repo.telemetry.build_insert_raw_query",
}
INGEST_SQL_EXEC_PREFIX = (
    "repo.devices.execute_",
    "repo.telemetry.execute_",
)
INGEST_MQTT_TOPICS = {
    "zigbee2mqtt/#",
    "application/+/device/+/event/up",
}
RUNTIME_TYPES_TO_DISABLE = {"mqtt in", "function", "postgresql"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def should_disable(node: dict[str, Any]) -> bool:
    node_type = str(node.get("type", ""))
    if node_type not in RUNTIME_TYPES_TO_DISABLE:
        return False

    name = str(node.get("name", ""))
    topic = str(node.get("topic", ""))

    if node_type == "mqtt in" and topic in INGEST_MQTT_TOPICS:
        return True

    if node_type == "function":
        if name.startswith(INGEST_FN_PREFIX):
            return True
        if name in INGEST_FN_EXACT:
            return True
        return False

    if node_type == "postgresql":
        for prefix in INGEST_SQL_EXEC_PREFIX:
            if name.startswith(prefix):
                return True

    return False


def apply_cutover(flows: list[dict[str, Any]], candidate_ids: set[str]) -> dict[str, Any]:
    disabled: list[dict[str, str]] = []
    skipped_candidates: list[dict[str, str]] = []

    for node in flows:
        node_id = str(node.get("id", ""))
        if not node_id or node_id not in candidate_ids:
            continue

        node_type = str(node.get("type", ""))
        name = str(node.get("name", ""))

        if should_disable(node):
            node["d"] = True
            disabled.append({"id": node_id, "type": node_type, "name": name})
        else:
            skipped_candidates.append({"id": node_id, "type": node_type, "name": name})

    return {
        "disabled": sorted(disabled, key=lambda item: item["id"]),
        "skipped_candidates": sorted(skipped_candidates, key=lambda item: item["id"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply W6-02 ingestion cutover preview to Node-RED flows"
    )
    parser.add_argument("--flows", required=True, type=Path, help="Source flows.json path")
    parser.add_argument(
        "--candidates",
        required=True,
        type=Path,
        help="Ingestion candidate report JSON path",
    )
    parser.add_argument(
        "--out-flows",
        required=True,
        type=Path,
        help="Output cutover-preview flows JSON path",
    )
    parser.add_argument(
        "--out-report",
        required=True,
        type=Path,
        help="Output cutover action report JSON path",
    )
    args = parser.parse_args()

    raw_flows = load_json(args.flows)
    if not isinstance(raw_flows, list):
        raise SystemExit("flows file must contain a JSON list")

    candidate_payload = load_json(args.candidates)
    if not isinstance(candidate_payload, dict):
        raise SystemExit("candidates file must contain a JSON object")

    candidates = candidate_payload.get("candidates")
    if not isinstance(candidates, list):
        raise SystemExit("candidates payload missing list")

    candidate_ids = {
        str(item.get("id"))
        for item in candidates
        if isinstance(item, dict) and item.get("id")
    }

    outcome = apply_cutover(raw_flows, candidate_ids)

    args.out_flows.parent.mkdir(parents=True, exist_ok=True)
    args.out_flows.write_text(json.dumps(raw_flows, indent=2) + "\n", encoding="utf-8")

    report = {
        "source_flows": str(args.flows),
        "candidate_report": str(args.candidates),
        "output_flows": str(args.out_flows),
        "candidate_count": len(candidate_ids),
        "disabled_count": len(outcome["disabled"]),
        "disabled": outcome["disabled"],
        "skipped_candidate_count": len(outcome["skipped_candidates"]),
        "skipped_candidates": outcome["skipped_candidates"],
        "rules": {
            "disable_runtime_types": sorted(RUNTIME_TYPES_TO_DISABLE),
            "function_name_prefix": INGEST_FN_PREFIX,
            "function_name_exact": sorted(INGEST_FN_EXACT),
            "postgresql_name_prefixes": list(INGEST_SQL_EXEC_PREFIX),
            "mqtt_in_topics": sorted(INGEST_MQTT_TOPICS),
        },
    }

    args.out_report.parent.mkdir(parents=True, exist_ok=True)
    args.out_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        f"candidate_count={report['candidate_count']} disabled_count={report['disabled_count']} skipped_candidate_count={report['skipped_candidate_count']}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
