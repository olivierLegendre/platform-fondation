#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_DEV_SECRET = "dev-wave6-change-me-32-byte-minimum-key"
REQUIRED_BY_SERVICE: dict[str, tuple[str, ...]] = {
    "reference-api-service": (
        "REFERENCE_API_POSTGRES_DSN",
    ),
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
FORBIDDEN_REFERENCE_API_DSN = "postgresql://postgres:postgres@localhost:5432/reference_api"


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"invalid env line in {path}: {raw_line}")
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"empty env key in {path}: {raw_line}")
        values[key] = value
    return values


def validate_service_env(path: Path, service: str) -> list[str]:
    errors: list[str] = []
    data = parse_env_file(path)
    required = REQUIRED_BY_SERVICE.get(service)
    if required is None:
        errors.append(f"unknown service: {service}")
        return errors

    for key in required:
        if not data.get(key):
            errors.append(f"{service}: missing required key {key}")

    if service == "reference-api-service":
        dsn = data.get("REFERENCE_API_POSTGRES_DSN", "")
        if dsn and not dsn.startswith("postgresql://"):
            errors.append(
                f"{service}: REFERENCE_API_POSTGRES_DSN must start with postgresql://"
            )
        if dsn == FORBIDDEN_REFERENCE_API_DSN:
            errors.append(
                f"{service}: REFERENCE_API_POSTGRES_DSN uses forbidden local dev default"
            )

    jwt_secret = data.get("AUTH_JWT_SECRET", "")
    if jwt_secret == DEFAULT_DEV_SECRET:
        errors.append(f"{service}: AUTH_JWT_SECRET uses forbidden default dev secret")
    if jwt_secret and len(jwt_secret) < 32:
        errors.append(f"{service}: AUTH_JWT_SECRET is shorter than 32 chars")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate generated runtime env files for non-dev deployment"
    )
    parser.add_argument(
        "--env-dir",
        required=True,
        type=Path,
        help="Directory containing <service>.env files",
    )
    parser.add_argument(
        "--services",
        nargs="*",
        default=sorted(REQUIRED_BY_SERVICE.keys()),
        help="Service names to validate",
    )
    args = parser.parse_args()

    all_errors: list[str] = []
    for service in args.services:
        env_path = args.env_dir / f"{service}.env"
        if not env_path.exists():
            all_errors.append(f"{service}: missing env file: {env_path}")
            continue
        all_errors.extend(validate_service_env(path=env_path, service=service))

    if all_errors:
        print("runtime env validation failed")
        for error in all_errors:
            print(f" - {error}")
        return 1

    print("runtime env validation passed")
    for service in args.services:
        print(f" - {service}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
