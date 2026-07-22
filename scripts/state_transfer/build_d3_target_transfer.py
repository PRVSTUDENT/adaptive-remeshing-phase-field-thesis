#!/usr/bin/env python3
"""Build a D3 transfer-package manifest without submitting a fracture job."""

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Dict, List


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite(value: str) -> bool:
    try:
        return math.isfinite(float(value))
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-csv", type=Path, required=True)
    parser.add_argument("--target-map", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    checkpoint_rows = read_csv(args.checkpoint_csv)
    target_rows = read_csv(args.target_map)
    manifest = {
        "classification": "stage_d3_transfer_package_manifest_only",
        "solver_job_submitted": False,
        "checkpoint_csv": str(args.checkpoint_csv),
        "target_map": str(args.target_map),
        "checkpoint_rows": len(checkpoint_rows),
        "target_rows": len(target_rows),
        "finite_checkpoint_values": all(
            finite(value)
            for row in checkpoint_rows
            for key, value in row.items()
            if key.lower() in ("d", "h", "sdv15", "sdv16")
        ),
        "required_fields": ["d or SDV15", "H or SDV16", "element", "integration_point", "x", "y"],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
