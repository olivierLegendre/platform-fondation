#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

IMAGE_TOKENS = ("node-red", "nodered")


def _as_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return ""


def _has_nodered_token(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in IMAGE_TOKENS)


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return payload


def _scan_manifest(path: Path) -> dict[str, Any]:
    doc = _load_yaml(path)
    services = doc.get("services")

    findings: list[dict[str, str]] = []
    checked_service_count = 0

    if not isinstance(services, dict):
        return {
            "manifest": str(path),
            "checked_service_count": 0,
            "finding_count": 0,
            "findings": [],
            "note": "no services map",
        }

    for service_name, service_payload in services.items():
        if not isinstance(service_payload, dict):
            continue
        checked_service_count += 1
        svc_name = _as_text(service_name)

        if _has_nodered_token(svc_name):
            findings.append(
                {
                    "manifest": str(path),
                    "service": svc_name,
                    "reason": "service_name_contains_nodered",
                }
            )

        image = _as_text(service_payload.get("image"))
        if image and _has_nodered_token(image):
            findings.append(
                {
                    "manifest": str(path),
                    "service": svc_name,
                    "reason": "image_contains_nodered",
                }
            )

        container_name = _as_text(service_payload.get("container_name"))
        if container_name and _has_nodered_token(container_name):
            findings.append(
                {
                    "manifest": str(path),
                    "service": svc_name,
                    "reason": "container_name_contains_nodered",
                }
            )

        depends_on = service_payload.get("depends_on")
        if isinstance(depends_on, list):
            deps = [_as_text(item) for item in depends_on]
        elif isinstance(depends_on, dict):
            deps = [_as_text(item) for item in depends_on.keys()]
        else:
            deps = []

        for dep in deps:
            if dep and _has_nodered_token(dep):
                findings.append(
                    {
                        "manifest": str(path),
                        "service": svc_name,
                        "reason": "depends_on_nodered",
                    }
                )
                break

    return {
        "manifest": str(path),
        "checked_service_count": checked_service_count,
        "finding_count": len(findings),
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify that compose manifests do not include Node-RED runtime dependencies"
    )
    parser.add_argument(
        "--manifest",
        action="append",
        default=[],
        type=Path,
        help="Compose manifest path (repeatable)",
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Output JSON report path",
    )
    args = parser.parse_args()

    manifests = [path.resolve() for path in args.manifest]
    if not manifests:
        raise SystemExit("at least one --manifest is required")

    per_manifest: list[dict[str, Any]] = []
    all_findings: list[dict[str, str]] = []
    checked_services = 0

    for manifest_path in manifests:
        result = _scan_manifest(manifest_path)
        per_manifest.append(result)
        checked_services += int(result.get("checked_service_count", 0))
        all_findings.extend(result.get("findings", []))

    report = {
        "status": "PASS" if not all_findings else "FAIL",
        "manifest_count": len(manifests),
        "checked_service_count": checked_services,
        "finding_count": len(all_findings),
        "findings": all_findings,
        "manifests": per_manifest,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        f"verification={report['status']} manifests={report['manifest_count']} services={report['checked_service_count']} findings={report['finding_count']}"
    )
    return 0 if not all_findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
