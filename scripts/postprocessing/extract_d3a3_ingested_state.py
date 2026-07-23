#!/usr/bin/env python3
"""Extract D3A3 ingested/released state from an ODB after the PBS job."""

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--odb", type=Path, required=True)
    parser.add_argument("--package-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/package"))
    parser.add_argument("--out-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion"))
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    status = {
        "classification": "stage_d3a3_extraction_placeholder",
        "odb": str(args.odb),
        "note": "Run under Abaqus Python after D3A3 completes; extract SDV15/SDV16, RF-U, and frame comparisons.",
    }
    (args.out_dir / "D3A3_EXTRACT_REQUEST.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
