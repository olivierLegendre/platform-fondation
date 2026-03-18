#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json root must be object: {path}")
    return payload


def _check_manifest_namespace(path: Path, namespace_prefix: str) -> tuple[bool, list[str]]:
    findings: list[str] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) != 3:
            findings.append(f"invalid manifest format line {line_no}: {raw}")
            continue
        image_repo = parts[2].strip()
        if not image_repo.startswith(namespace_prefix):
            findings.append(
                f"manifest image not in namespace at line {line_no}: {image_repo}"
            )
    return (len(findings) == 0, findings)


def _check_compose_namespace(paths: list[Path], namespace_prefix: str) -> tuple[bool, list[str]]:
    findings: list[str] = []
    for path in paths:
        for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw.strip()
            if not line.startswith("image:"):
                continue
            image_ref = line.split("image:", 1)[1].strip()
            if image_ref.startswith("hashicorp/"):
                continue
            if not image_ref.startswith(namespace_prefix):
                findings.append(
                    f"compose image not in namespace {path}:{line_no}: {image_ref}"
                )
    return (len(findings) == 0, findings)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Wave 8 namespace readiness")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--compose", action="append", required=True, type=Path)
    parser.add_argument("--topology", required=True, type=Path)
    parser.add_argument("--retirement", required=True, type=Path)
    parser.add_argument("--pullability", required=False, type=Path)
    parser.add_argument("--namespace-prefix", default="ghcr.io/olivierlegendre/")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    findings: list[str] = []

    manifest_ok, manifest_findings = _check_manifest_namespace(args.manifest, args.namespace_prefix)
    findings.extend(manifest_findings)

    compose_ok, compose_findings = _check_compose_namespace(args.compose, args.namespace_prefix)
    findings.extend(compose_findings)

    topology = _read_json(args.topology)
    topology_status = topology.get("status")
    if topology_status != "PASS":
        findings.append(f"topology gate not PASS: {topology_status}")

    retirement = _read_json(args.retirement)
    retirement_decision = retirement.get("decision")
    if retirement_decision != "READY_FOR_W6_10_CLOSURE":
        findings.append(f"retirement readiness decision not READY_FOR_W6_10_CLOSURE: {retirement_decision}")

    pullability_status = "SKIPPED"
    if args.pullability is not None and args.pullability.exists():
        pull = _read_json(args.pullability)
        pullability_status = str(pull.get("status", "UNKNOWN"))
        if pullability_status != "PASS":
            findings.append(f"pullability not PASS: {pullability_status}")

    status = "PASS" if not findings else "FAIL"
    report = {
        "status": status,
        "finding_count": len(findings),
        "findings": findings,
        "checks": {
            "manifest_namespace": "PASS" if manifest_ok else "FAIL",
            "compose_namespace": "PASS" if compose_ok else "FAIL",
            "topology_gate": str(topology_status),
            "retirement_decision": str(retirement_decision),
            "pullability": pullability_status,
        },
        "inputs": {
            "manifest": str(args.manifest),
            "compose": [str(p) for p in args.compose],
            "topology": str(args.topology),
            "retirement": str(args.retirement),
            "pullability": str(args.pullability) if args.pullability else None,
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"status={status} findings={len(findings)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
