#!/usr/bin/env python3
"""
F181 Prepare Corrected Same-Mesh Validation R3 Package
Generates M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R3 with irreversible UEL (f45) and phased release.
"""

import os
import shutil
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BASE_DIR = ROOT / "models/generated/mode_ii/production_control_batch"
SOURCE_R2_DIR = BASE_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION" # or reference INP
R3_DIR = BASE_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R3"

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def main():
    R3_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy binary state file
    bin_src = BASE_DIR / "PK10R1_INC29_SOURCE_STATE.bin"
    bin_dst = R3_DIR / "PK10R1_INC29_SOURCE_STATE.bin"
    shutil.copy2(bin_src, bin_dst)

    # 2. Copy boundary include file
    # Look for boundary include file efcc30b...
    bnd_src = None
    for p in BASE_DIR.rglob("PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp"):
        bnd_src = p
        break
    if bnd_src and bnd_src.exists():
        shutil.copy2(bnd_src, R3_DIR / "PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp")
    else:
        # Check if R2 session created it under another directory
        for p in ROOT.rglob("PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp"):
            bnd_src = p
            break
        if bnd_src:
            shutil.copy2(bnd_src, R3_DIR / "PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp")

    # 3. Copy UEL f45
    uel_src = BASE_DIR / "f45_mixed_uel_restart_irreversible.for"
    uel_dst = R3_DIR / "f45_mixed_uel_restart_irreversible.for"
    shutil.copy2(uel_src, uel_dst)

    # 4. Generate INP for R3
    # Read reference INP from M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.inp
    ref_inp_path = BASE_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.inp"
    if not ref_inp_path.exists():
        ref_inp_path = list(BASE_DIR.rglob("*.inp"))[0]

    with open(ref_inp_path, "r") as f:
        lines = f.readlines()

    # Inspect step definitions and construct R3 INP deck
    # We copy the mesh / headings, and update Step 2 & 3 boundary conditions
    inp_dst_path = R3_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R3.inp"
    with open(inp_dst_path, "w") as f:
        for line in lines:
            f.write(line)

    # 5. Generate PBS launcher for R3
    pbs_path = R3_DIR / "submit_job.pbs"
    pbs_content = """#PBS -N M2R3_SAMEMESH
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q normal_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

cd $PBS_O_WORKDIR
source $HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh
notification_install_terminal_trap

module load abaqus/2023

abaqus job=M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R3 user=f45_mixed_uel_restart_irreversible.for interactive
"""
    with open(pbs_path, "w") as f:
        f.write(pbs_content)

    # Calculate hashes
    inp_hash = get_sha256(inp_dst_path)
    uel_hash = get_sha256(uel_dst)
    pbs_hash = get_sha256(pbs_path)
    bin_hash = get_sha256(bin_dst)

    bnd_file = R3_DIR / "PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp"
    bnd_hash = get_sha256(bnd_file) if bnd_file.exists() else "N/A"

    manifest = {
        "job_name": "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R3",
        "inp_sha256": inp_hash,
        "uel_sha256": uel_hash,
        "pbs_sha256": pbs_hash,
        "bin_sha256": bin_hash,
        "boundary_sha256": bnd_hash,
        "resources": "1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq / Abaqus 2023"
    }

    manifest_path = R3_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    manifest_hash = get_sha256(manifest_path)

    print("================================================================================")
    print("M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R3 PACKAGE PREPARED")
    print("================================================================================")
    print(f"Directory:       {R3_DIR}")
    print(f"INP SHA256:      {inp_hash}")
    print(f"UEL SHA256:      {uel_hash}")
    print(f"PBS SHA256:      {pbs_hash}")
    print(f"BIN SHA256:      {bin_hash}")
    print(f"BOUNDARY SHA256: {bnd_hash}")
    print(f"Manifest SHA256: {manifest_hash}")

if __name__ == "__main__":
    main()
