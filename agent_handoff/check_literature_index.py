#!/usr/bin/env python3
"""Check that literature index entries point to existing PDFs, notes, and maps."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=Path("references/notes/literature_index.json"))
    parser.add_argument("--workspace", type=Path, default=Path("."))
    parser.add_argument("--dry-run", action="store_true", help="Check only; never writes files")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    with args.index.open("r", encoding="utf-8") as stream:
        index: dict[str, Any] = json.load(stream)

    errors: list[str] = []
    ids: set[str] = set()
    for source in index.get("sources", []):
        source_id = source.get("id")
        if not source_id:
            errors.append("source without id")
            continue
        if source_id in ids:
            errors.append(f"duplicate source id: {source_id}")
        ids.add(source_id)
        for field in ("path", "note"):
            value = source.get(field)
            if not value:
                errors.append(f"{source_id} missing {field}")
                continue
            candidate = workspace / value
            if not candidate.exists():
                errors.append(f"{source_id} missing {field}: {value}")

    for map_path in index.get("maps", []):
        if not (workspace / map_path).exists():
            errors.append(f"missing map: {map_path}")

    if len(index.get("sources", [])) != 5:
        errors.append("literature index must contain exactly the five supplied sources")

    if errors:
        print("Literature index check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    mode = "dry-run " if args.dry_run else ""
    print(f"Literature index check passed ({mode}no files written): {args.index}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
