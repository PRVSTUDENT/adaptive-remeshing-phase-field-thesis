#!/usr/bin/env python3
"""Generate or validate F17 manifests from explicit package allowlists."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST = ROOT / "runs/hpc/stage_f/f17_penalty_activation_and_adaptive_region_repair/F17_MANIFEST_ALLOWLISTS.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_text(path: Path) -> None:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"UTF-8 BOM prohibited: {path}")
    if b"\r" in data:
        raise ValueError(f"non-LF line ending: {path}")
    if not data.endswith(b"\n"):
        raise ValueError(f"final LF missing: {path}")
    data.decode("utf-8")
    if path.suffix == ".json":
        json.loads(data)


def expected_lines(package: Path, entries: list[str]) -> list[str]:
    if len(entries) != len(set(entries)):
        raise ValueError(f"duplicate allowlist entry: {package}")
    if "F17_SHA256SUMS" in entries:
        raise ValueError("manifest must not hash itself")
    lines = []
    for relative in sorted(entries):
        path = package / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.suffix in {".json", ".py", ".sh", ".pbs", ".for", ".inp"} or path.name == ".gitignore":
            validate_text(path)
        lines.append(f"{digest(path)}  {relative}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    allowlists = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    for package_rel, entries in sorted(allowlists.items()):
        package = ROOT / package_rel
        lines = expected_lines(package, entries)
        manifest = package / "F17_SHA256SUMS"
        rendered = "\n".join(lines) + "\n"
        if args.write:
            manifest.write_text(rendered, encoding="utf-8", newline="\n")
        elif manifest.read_bytes() != rendered.encode("utf-8"):
            raise ValueError(f"manifest differs from deterministic rendering: {manifest}")
        print(f"{package_rel}: {len(lines)} entries PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
