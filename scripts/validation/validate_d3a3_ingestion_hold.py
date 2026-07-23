#!/usr/bin/env python3
"""Validate D3A3 static preflight or completed ingestion/hold outputs."""

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion"))
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()
    static_path = args.target_dir / "D3A3_STATIC_VALIDATION.json"
    failures = []
    if not static_path.exists():
        failures.append("D3A3_STATIC_VALIDATION.json missing")
        static = {}
    else:
        static = json.loads(static_path.read_text(encoding="utf-8"))
        if static.get("classification") != "stage_d3a3_static_validation_pass":
            failures.append("static validation did not pass")
    if not args.static_only:
        required = [
            "D3A3_STATE_BY_FRAME.csv",
            "D3A3_TRANSFER_VS_ODB.csv",
            "D3A3_INITIAL_VS_EQUILIBRATED.csv",
            "D3A3_EQUILIBRATED_VS_RELEASED.csv",
            "D3A3_RF_U.csv",
            "D3A3_ENERGY_BY_FRAME.json",
            "D3A3_RELEASE_JUMP.json",
        ]
        for name in required:
            if not (args.target_dir / name).exists():
                failures.append(f"{name} missing")
    status = {
        "classification": "stage_d3a3_static_validation_pass" if not failures and args.static_only else ("stage_d3a3_full_target_ingestion_pass" if not failures else "stage_d3a3_state_ingestion_fail"),
        "D3A3_ok": not failures and not args.static_only,
        "static_only": args.static_only,
        "static": static,
        "failures": failures,
    }
    (args.target_dir / "D3A3_STATUS.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
