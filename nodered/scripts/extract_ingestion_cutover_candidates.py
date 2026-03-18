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
INGEST_MQTT_TOPICS = {
    "zigbee2mqtt/#",
    "application/+/device/+/event/up",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def collect_candidates(flows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {str(n.get("id")): n for n in flows if n.get("id")}

    seeds: set[str] = set()
    for node in flows:
        node_id = str(node.get("id", ""))
        node_type = str(node.get("type", ""))
        name = str(node.get("name", ""))
        topic = str(node.get("topic", ""))

        if node_type == "mqtt in" and topic in INGEST_MQTT_TOPICS:
            seeds.add(node_id)
            continue

        if node_type == "function" and (
            name.startswith(INGEST_FN_PREFIX) or name in INGEST_FN_EXACT
        ):
            seeds.add(node_id)

    selected: set[str] = set(seeds)

    # Pull one- and two-hop runtime neighbors from seed nodes to catch SQL executor nodes.
    frontier = list(seeds)
    for _ in range(2):
        nxt: list[str] = []
        for current in frontier:
            node = by_id.get(current)
            if not node:
                continue
            wires = node.get("wires")
            if not isinstance(wires, list):
                continue
            for outputs in wires:
                if not isinstance(outputs, list):
                    continue
                for target in outputs:
                    tid = str(target)
                    if tid and tid in by_id and tid not in selected:
                        selected.add(tid)
                        nxt.append(tid)
        frontier = nxt

    # Add config nodes referenced by selected runtime nodes.
    config_refs: set[str] = set()
    for node_id in list(selected):
        node = by_id.get(node_id)
        if not node:
            continue
        for value in node.values():
            if isinstance(value, str) and value in by_id:
                cfg = by_id[value]
                if not cfg.get("z"):
                    config_refs.add(value)

    selected |= config_refs

    items: list[dict[str, Any]] = []
    for node_id in sorted(selected):
        node = by_id[node_id]
        items.append(
            {
                "id": node_id,
                "type": node.get("type"),
                "name": node.get("name", ""),
                "topic": node.get("topic", ""),
                "tab": node.get("z", ""),
            }
        )

    type_counts: dict[str, int] = {}
    for item in items:
        typ = str(item.get("type", ""))
        type_counts[typ] = type_counts.get(typ, 0) + 1

    return {
        "seed_rule": {
            "mqtt_in_topics": sorted(INGEST_MQTT_TOPICS),
            "function_name_prefix": INGEST_FN_PREFIX,
            "function_name_exact": sorted(INGEST_FN_EXACT),
            "neighbor_hops": 2,
        },
        "seed_count": len(seeds),
        "candidate_count": len(items),
        "candidate_type_counts": dict(sorted(type_counts.items(), key=lambda kv: kv[0])),
        "candidates": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract Node-RED ingestion cutover candidates from a flows.json file."
    )
    parser.add_argument("--flows", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    raw = load_json(args.flows)
    if not isinstance(raw, list):
        raise SystemExit("flows file must contain a JSON list")

    result = collect_candidates(raw)
    payload = {
        "flows": str(args.flows),
        "seed_count": result["seed_count"],
        "candidate_count": result["candidate_count"],
        "candidate_type_counts": result["candidate_type_counts"],
        "seed_rule": result["seed_rule"],
        "candidates": result["candidates"],
    }

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(
        f"seed_count={payload['seed_count']} candidate_count={payload['candidate_count']}"
    )
    for typ, count in payload["candidate_type_counts"].items():
        print(f" - {typ}: {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
