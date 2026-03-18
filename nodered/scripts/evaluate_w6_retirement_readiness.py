#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def _load_report(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"report must be a JSON object: {path}")
    return payload


def _status(report: dict[str, Any]) -> str:
    value = report.get("status")
    return value if isinstance(value, str) else "UNKNOWN"


def _finding_count(report: dict[str, Any]) -> int:
    value = report.get("finding_count")
    return value if isinstance(value, int) else 0


def _read_manifest_set(path: Path) -> list[Path]:
    items: list[Path] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        items.append(Path(line))
    return items


def _scan_placeholder_images(paths: list[Path]) -> bool:
    for path in paths:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        services = payload.get("services")
        if not isinstance(services, dict):
            continue
        for service in services.values():
            if not isinstance(service, dict):
                continue
            image = service.get("image")
            if isinstance(image, str):
                lowered = image.lower()
                if "replace-me" in lowered or "ghcr.io/example/" in lowered:
                    return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate W6-10 Node-RED retirement readiness from gate reports"
    )
    parser.add_argument("--managed", required=True, type=Path, help="Managed manifest gate report")
    parser.add_argument("--legacy", required=True, type=Path, help="Legacy PoC gap report")
    parser.add_argument("--manifest-set", required=False, type=Path, help="Release gate manifest set file")
    parser.add_argument("--out", required=True, type=Path, help="Output readiness report JSON")
    args = parser.parse_args()

    managed = _load_report(args.managed)
    legacy = _load_report(args.legacy)

    blockers: list[str] = []
    warnings: list[str] = []

    managed_status = _status(managed)
    legacy_status = _status(legacy)

    if managed_status != "PASS":
        blockers.append(
            f"managed_topology_gate_not_passed status={managed_status} findings={_finding_count(managed)}"
        )

    # Legacy PoC is expected to fail until migration/retirement is complete.
    if legacy_status != "FAIL":
        warnings.append(
            f"legacy_gap_signal_missing expected_FAIL_got={legacy_status} findings={_finding_count(legacy)}"
        )

    manifest_set_confirmed = False
    manifest_paths: list[Path] = []

    if args.manifest_set is not None and args.manifest_set.exists():
        manifest_paths = _read_manifest_set(args.manifest_set)
        if manifest_paths and all("/deploy/production/" in str(path) for path in manifest_paths):
            manifest_set_confirmed = True

    if not manifest_set_confirmed:
        blockers.append("production_manifest_set_not_confirmed_for_release_gate")

    if manifest_paths and _scan_placeholder_images(manifest_paths):
        blockers.append("production_manifests_contain_placeholder_images")

    decision = "READY_FOR_W6_10_CLOSURE" if not blockers else "NOT_READY"

    report = {
        "decision": decision,
        "managed_gate": {
            "path": str(args.managed),
            "status": managed_status,
            "finding_count": _finding_count(managed),
        },
        "legacy_gap": {
            "path": str(args.legacy),
            "status": legacy_status,
            "finding_count": _finding_count(legacy),
        },
        "manifest_set": str(args.manifest_set) if args.manifest_set is not None else None,
        "manifest_set_confirmed": manifest_set_confirmed,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "blockers": blockers,
        "warnings": warnings,
        "required_next_actions": [
            "replace manifest set with production deployment manifests",
            "replace placeholder images/tags with real production artifacts",
            "run one-command release gate against production manifests",
            "remove Node-RED runtime from production topology",
            "record service-owner sign-off",
        ],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        f"decision={report['decision']} blockers={report['blocker_count']} warnings={report['warning_count']}"
    )
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
