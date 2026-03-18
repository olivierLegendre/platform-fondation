#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def render_service_env(service: str, values: dict[str, str], outdir: Path) -> Path:
    if not isinstance(values, dict):
        raise ValueError(f"service payload must be object: {service}")

    lines: list[str] = []
    for key in sorted(values.keys()):
        value = values[key]
        if not isinstance(value, str):
            raise ValueError(f"secret value must be string: {service}.{key}")
        lines.append(f"{key}={value}")

    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{service}.env"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render service .env files from Vault-exported JSON payload"
    )
    parser.add_argument("--input", required=True, type=Path, help="Path to Vault export JSON")
    parser.add_argument(
        "--outdir",
        required=True,
        type=Path,
        help="Output directory for generated .env files",
    )
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("input JSON must be an object keyed by service")

    written: list[Path] = []
    for service, values in payload.items():
        if not isinstance(service, str):
            raise SystemExit("service keys must be strings")
        path = render_service_env(service=service, values=values, outdir=args.outdir)
        written.append(path)

    print(f"wrote {len(written)} env file(s)")
    for path in written:
        print(f" - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
