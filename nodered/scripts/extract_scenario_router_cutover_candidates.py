#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCENARIO_NAME_CONTAINS = ("scenario", "route scenario actions")
COMMAND_TOPIC_HINTS = (
    "/set",
    "command",
)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def collect(flows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {str(n.get("id")): n for n in flows if n.get("id")}

    seeds: set[str] = set()
    for node in flows:
        node_id = str(node.get("id", ""))
        node_type = str(node.get("type", ""))
        name = str(node.get("name", "")).lower()
        topic = str(node.get("topic", "")).lower()

        if node_type == "function" and any(token in name for token in SCENARIO_NAME_CONTAINS):
            seeds.add(node_id)
            continue

        if node_type == "mqtt out" and any(token in topic for token in COMMAND_TOPIC_HINTS):
            seeds.add(node_id)

    selected: set[str] = set(seeds)

    frontier = list(seeds)
    for _ in range(3):
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

    # include reverse neighbors to capture upstream trigger logic
    for node in flows:
        node_id = str(node.get("id", ""))
        wires = node.get("wires")
        if not isinstance(wires, list):
            continue
        for outputs in wires:
            if not isinstance(outputs, list):
                continue
            if any(str(target) in selected for target in outputs):
                selected.add(node_id)

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
    type_counts: dict[str, int] = {}
    for node_id in sorted(selected):
        n = by_id[node_id]
        t = str(n.get("type", ""))
        type_counts[t] = type_counts.get(t, 0) + 1
        items.append(
            {
                "id": node_id,
                "type": t,
                "name": n.get("name", ""),
                "topic": n.get("topic", ""),
                "tab": n.get("z", ""),
            }
        )

    return {
        "seed_count": len(seeds),
        "candidate_count": len(items),
        "candidate_type_counts": dict(sorted(type_counts.items())),
        "seed_name_contains": list(SCENARIO_NAME_CONTAINS),
        "seed_topic_hints": list(COMMAND_TOPIC_HINTS),
        "candidates": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract Node-RED scenario/command-routing cutover candidates from flows.json"
    )
    parser.add_argument("--flows", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    raw = load_json(args.flows)
    if not isinstance(raw, list):
        raise SystemExit("flows file must contain a JSON list")

    result = collect(raw)
    payload = {"flows": str(args.flows), **result}

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
