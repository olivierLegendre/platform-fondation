#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DASHBOARD_NAME_TOKENS = (
    "dashboard",
    "activity",
    "battery",
    "periodic",
    "all_devices",
    "actuator",
    "event_changes",
    "chart",
    "scenario",
)
DASHBOARD_TYPES = {
    "ui-base",
    "ui-page",
    "ui-group",
    "ui-template",
    "ui-chart",
    "ui-dropdown",
    "ui-theme",
}
DISABLE_TYPES = DASHBOARD_TYPES | {"function", "postgresql", "inject"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def has_dashboard_token(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in DASHBOARD_NAME_TOKENS)


def should_disable(node: dict[str, Any]) -> bool:
    node_type = str(node.get("type", ""))
    if node_type not in DISABLE_TYPES:
        return False

    name = str(node.get("name", ""))

    if node_type in DASHBOARD_TYPES:
        return True

    if node_type in {"function", "postgresql", "inject"}:
        return has_dashboard_token(name)

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
        description="Apply W6-05 dashboard cutover preview to Node-RED flows"
    )
    parser.add_argument("--flows", required=True, type=Path, help="Source flows.json path")
    parser.add_argument(
        "--candidates",
        required=True,
        type=Path,
        help="Dashboard candidate report JSON path",
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
            "disable_types": sorted(DISABLE_TYPES),
            "dashboard_name_tokens": list(DASHBOARD_NAME_TOKENS),
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
