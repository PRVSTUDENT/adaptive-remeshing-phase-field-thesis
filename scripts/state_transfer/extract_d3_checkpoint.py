#!/usr/bin/env python3
"""Prepare a D3 checkpoint extraction manifest.

This script intentionally does not run Abaqus. It records the requested
checkpoint contract so a later, explicitly authorized extraction can be tied to
the same metrics and displacement target.
"""

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/state_transfer/d3_interrupted_transfer.yaml"))
    parser.add_argument("--odb", type=Path, required=True, help="Future H0 diagnostic ODB path to extract from.")
    parser.add_argument("--out", type=Path, required=True, help="Manifest path to write.")
    args = parser.parse_args()

    manifest = {
        "classification": "stage_d3_checkpoint_manifest_only",
        "solver_job_submitted": False,
        "config": str(args.config),
        "odb": str(args.odb),
        "checkpoint_displacement_mm": 0.003,
        "fields": ["SDV15", "SDV16", "U", "RF", "ALLIE", "ALLSE", "ALLWK"],
        "note": "Extraction implementation requires an existing authorized checkpoint ODB.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
