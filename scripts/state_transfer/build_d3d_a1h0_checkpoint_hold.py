#!/usr/bin/env python3
"""Build the isolated two-step D3D-A1H0 fixed-phase checkpoint hold."""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.build_d3a3_r4_compatible_hold import (
    generate_inp,
    write_csv_runtime,
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer"))
    parser.add_argument("--package-dir", type=Path, default=Path("runs/hpc/stage_d3/fracture_continuation/package_d3d_a1_checkpoint_r1"))
    parser.add_argument("--r4-dir", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer/executable_r4_compatible_r2"))
    parser.add_argument("--out-dir", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer/executable_d3d_a1_checkpoint_hold_r1"))
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    temporary = args.out_dir / "_temporary_r4_shape.inp"
    membership = generate_inp(temporary, args.model_dir, args.package_dir)
    text = temporary.read_text(encoding="utf-8")
    text = text.split("*Step, name=ACTIVE_SET_R2_RELEASE_HOLD", 1)[0].rstrip() + "\n"
    text = text.replace("INGEST_COMPATIBLE_R2", "INGEST_D3D_A1_CANDIDATE")
    text = text.replace("CHECKPOINT_EQUILIBRATION_COMPATIBLE_R2_FIXED", "D3D_A1_MECHANICAL_CHECKPOINT_EQUILIBRATION")
    text = text.replace("D3A3-R4 compatible R2 active-set release hold.", "D3D-A1H0 fixed-phase mechanical checkpoint hold.")
    text = text.replace("Compatible nodal d and H from package_compatible_r2 (D3A5 actual-history reprojection).", "Corrected nodal d and unchanged actual F3 H from package_d3d_a1_checkpoint_r1.")
    deck = args.out_dir / "D3D_A1H0_checkpoint_hold.inp"
    deck.write_text(text, encoding="utf-8")
    temporary.unlink()
    src_fortran = args.r4_dir / "d3_transfer_uel.for"
    dst_fortran = args.out_dir / "d3_transfer_uel.for"
    shutil.copyfile(src_fortran, dst_fortran)
    rows = write_csv_runtime(args.package_dir / "D3_TRANSFERRED_IP_H.csv", args.out_dir / "d3_transfer_h.dat")
    active = len(membership["active_nodes"])
    free = len(membership["free_nodes"])
    if (active, free, len(rows)) != (6374, 227, 25600):
        raise SystemExit("candidate counts/runtime H coverage mismatch")
    audit = {
        "classification": "stage_d3d_a1h0_input_prepared",
        "source_package": str(args.package_dir),
        "steps": ["INGEST_D3D_A1_CANDIDATE", "D3D_A1_MECHANICAL_CHECKPOINT_EQUILIBRATION"],
        "phase_fixed_nodes_each_step": 6601,
        "active_nodes": active,
        "free_nodes": free,
        "runtime_H_records": len(rows),
        "runtime_H_modification_count": 0,
        "fortran_sha256": sha256(dst_fortran),
        "accepted_r4_fortran_sha256": sha256(src_fortran),
        "fortran_byte_identical_to_r4": sha256(dst_fortran) == sha256(src_fortran),
        "phase_release_step_present": False,
        "continuation_step_present": False,
        "datacheck_authorized": False,
        "solver_submission_authorized": False,
    }
    (args.out_dir / "D3D_A1H0_INPUT_PROVENANCE.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
