#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_BY_SERVICE: dict[str, tuple[str, ...]] = {
    "automation-scenario-service": (
        "AUTH_JWT_SECRET",
        "AUTH_JWT_ISSUER",
        "AUTH_JWT_AUDIENCE",
    ),
    "channel-policy-router": (
        "AUTH_JWT_SECRET",
        "AUTH_JWT_ISSUER",
        "AUTH_JWT_AUDIENCE",
    ),
}


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"invalid env line in {path}: {raw_line}")
        key, value = line.split("=", 1)
        values[key.strip()] = value
    return values


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Wave 1 Vault runtime baseline evidence report"
    )
    parser.add_argument("--env-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    findings: list[str] = []
    services: dict[str, dict[str, object]] = {}

    for service, required_keys in REQUIRED_BY_SERVICE.items():
        env_path = args.env_dir / f"{service}.env"
        record: dict[str, object] = {
            "env_file": str(env_path),
            "present": env_path.exists(),
            "required_keys": list(required_keys),
            "missing_keys": [],
        }
        if not env_path.exists():
            findings.append(f"{service}: missing env file")
            services[service] = record
            continue

        parsed = parse_env_file(env_path)
        missing = [k for k in required_keys if not parsed.get(k)]
        record["missing_keys"] = missing
        if missing:
            findings.append(f"{service}: missing required keys: {', '.join(missing)}")

        services[service] = record

    status = "PASS" if not findings else "FAIL"
    report = {
        "status": status,
        "finding_count": len(findings),
        "findings": findings,
        "services": services,
        "inputs": {
            "env_dir": str(args.env_dir),
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote report: {args.out}")
    print(f"status: {status}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
