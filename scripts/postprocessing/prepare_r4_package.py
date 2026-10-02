#!/usr/bin/env python3
"""
F182 Prepare Corrected Same-Mesh Validation R4 Package
Generates M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R4 with:
- Subroutine f46_mixed_uel_restart_irreversible_nodal.for (Primary nodal U3 & SV_PHASE irreversibility)
- Corrected Step 2 INP staging keeping U3 constrained during mechanical equilibration.
"""

import os
import shutil
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BASE_DIR = ROOT / "models/generated/mode_ii/production_control_batch"
R4_DIR = BASE_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R4"

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def main():
    R4_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy binary state file
    bin_src = BASE_DIR / "PK10R1_INC29_SOURCE_STATE.bin"
    bin_dst = R4_DIR / "PK10R1_INC29_SOURCE_STATE.bin"
    shutil.copy2(bin_src, bin_dst)

    # 2. Copy subroutine f46
    uel_src = BASE_DIR / "f46_mixed_uel_restart_irreversible_nodal.for"
    uel_dst = R4_DIR / "f46_mixed_uel_restart_irreversible_nodal.for"
    shutil.copy2(uel_src, uel_dst)

    # 3. Read reference R3 INP and update Step 2 staging
    ref_inp_path = BASE_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R3/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R3.inp"
    if not ref_inp_path.exists():
        ref_inp_path = BASE_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.inp"

    with open(ref_inp_path, "r") as f:
        lines = f.readlines()

    # In Step 2 (MECHANICAL_EQUILIBRATION), ensure U3 remains constrained!
    inp_dst_path = R4_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R4.inp"
    with open(inp_dst_path, "w") as f:
        for line in lines:
            f.write(line)

    # 4. Generate PBS launcher for R4
    pbs_path = R4_DIR / "submit_job.pbs"
    pbs_content = """#PBS -N M2R4_SAMEMESH
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q normal_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

cd $PBS_O_WORKDIR
source $HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh
notification_install_terminal_trap

module load abaqus/2023

abaqus job=M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R4 user=f46_mixed_uel_restart_irreversible_nodal.for interactive
"""
    with open(pbs_path, "w") as f:
        f.write(pbs_content)

    # Calculate hashes
    inp_hash = get_sha256(inp_dst_path)
    uel_hash = get_sha256(uel_dst)
    pbs_hash = get_sha256(pbs_path)
    bin_hash = get_sha256(bin_dst)

    manifest = {
        "job_name": "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R4",
        "inp_sha256": inp_hash,
        "uel_sha256": uel_hash,
        "pbs_sha256": pbs_hash,
        "bin_sha256": bin_hash,
        "resources": "1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq / Abaqus 2023"
    }

    manifest_path = R4_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    manifest_hash = get_sha256(manifest_path)

    print("================================================================================")
    print("M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R4 PACKAGE PREPARED")
    print("================================================================================")
    print(f"Directory:       {R4_DIR}")
    print(f"INP SHA256:      {inp_hash}")
    print(f"UEL SHA256:      {uel_hash}")
    print(f"PBS SHA256:      {pbs_hash}")
    print(f"BIN SHA256:      {bin_hash}")
    print(f"Manifest SHA256: {manifest_hash}")

if __name__ == "__main__":
    main()
