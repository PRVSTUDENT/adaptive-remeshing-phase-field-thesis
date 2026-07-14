#!/usr/bin/env python3
"""Validate starter run manifests without Abaqus dependencies."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def dotted_get(data: dict[str, Any], key: str) -> Any:
    current: Any = data
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(key)
        current = current[part]
    return current


def validate_manifest(manifest: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for key in schema.get("required", []):
        if key not in manifest:
            errors.append(f"missing top-level field: {key}")

    for parent, children in schema.get("required_nested", {}).items():
        if parent not in manifest or not isinstance(manifest[parent], dict):
            continue
        for child in children:
            value = manifest[parent].get(child)
            if value in (None, ""):
                errors.append(f"missing required field: {parent}.{child}")

    method_type = dotted_get(manifest, "method.type") if "method" in manifest else None
    if method_type and method_type not in schema.get("allowed_method_types", []):
        errors.append(f"unsupported method.type: {method_type}")

    before_run = None
    if "classification" in manifest:
        before_run = manifest["classification"].get("before_run")
    if before_run and before_run not in schema.get("allowed_before_run_classifications", []):
        errors.append(f"unsupported classification.before_run: {before_run}")

    convention = None
    if "physics" in manifest:
        convention = manifest["physics"].get("phase_field_convention")
    if not convention or str(convention).strip().lower() in {"pending", "todo", "unknown"}:
        errors.append("phase_field_convention must be explicit, even for exploratory runs")

    if method_type == "miseseri_pre_refinement":
        remesh_config = manifest.get("method", {}).get("remeshing_config")
        if not remesh_config:
            errors.append("miseseri_pre_refinement requires method.remeshing_config")

    if method_type == "evolving_remesh_state_transfer":
        transfer_config = manifest.get("method", {}).get("state_transfer_config")
        if not transfer_config:
            errors.append("evolving_remesh_state_transfer requires method.state_transfer_config")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Run manifest JSON")
    parser.add_argument("--schema", type=Path, default=Path("configs/run_manifest.schema.json"))
    parser.add_argument("--dry-run", action="store_true", help="Validate only; never writes files")
    args = parser.parse_args()

    schema = load_json(args.schema)
    manifest = load_json(args.manifest)
    errors = validate_manifest(manifest, schema)

    if errors:
        print("Manifest validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    mode = "dry-run " if args.dry_run else ""
    print(f"Manifest validation passed ({mode}no files written): {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
