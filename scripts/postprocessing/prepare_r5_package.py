#!/usr/bin/env python3
"""
F183 Prepare Minimal Scientifically Corrected Same-Mesh Validation R5 Package
Generates M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R5 with:
- Subroutine f44_mixed_uel_restart_stateinit.for (Original authoritative transactional UEL physics)
- Explicit boundary files PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp and PK10R1_INC29_U3_ONLY_BOUNDARY.inp
- Corrected Step 2 INP staging keeping U3 constrained during mechanical equilibration
"""

import os
import shutil
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BASE_DIR = ROOT / "models/generated/mode_ii/production_control_batch"
R5_DIR = BASE_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R5"

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def main():
    R5_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy binary state and subroutine f44
    bin_src = BASE_DIR / "PK10R1_INC29_SOURCE_STATE.bin"
    bin_dst = R5_DIR / "PK10R1_INC29_SOURCE_STATE.bin"
    shutil.copy2(bin_src, bin_dst)

    uel_src = BASE_DIR / "f44_mixed_uel_restart_stateinit.for"
    uel_dst = R5_DIR / "f44_mixed_uel_restart_stateinit.for"
    shutil.copy2(uel_src, uel_dst)

    # 2. Read reference INP deck
    ref_inp_path = BASE_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.inp"
    with open(ref_inp_path, "r") as f:
        text = f.read()

    # Split mesh deck from steps
    mesh_part = text.split("*STEP, NAME=STATE_INIT")[0]

    # Check if primary boundary file exists or create from reference
    bnd_full_src = BASE_DIR / "PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp"
    full_bnd_dst = R5_DIR / "PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp"
    u3_bnd_dst   = R5_DIR / "PK10R1_INC29_U3_ONLY_BOUNDARY.inp"

    if not bnd_full_src.exists():
        # Look in other directories or construct default placeholder
        bnd_full_src = BASE_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R3/PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp"

    if bnd_full_src.exists():
        shutil.copy2(bnd_full_src, full_bnd_dst)
        u3_count = 0
        with open(bnd_full_src, "r") as fin, open(u3_bnd_dst, "w") as fout:
            for line in fin:
                parts = line.strip().split(",")
                if len(parts) >= 4 and parts[1].strip() == "3" and parts[2].strip() == "3":
                    fout.write(line)
                    u3_count += 1
        print(f"Generated U3-only boundary file with {u3_count} node constraints from existing boundary file.")
    else:
        # Create boundary files dynamically from source state json if available
        json_src = BASE_DIR / "PK10R1_INC29_SOURCE_STATE.json"
        if json_src.exists():
            with open(json_src, "r") as f:
                sdata = json.load(f)
            nodal_u = sdata.get("nodal_u", {})
            nodal_d = sdata.get("nodal_d", {})
            u3_count = 0
            full_count = 0
            with open(full_bnd_dst, "w") as f_full, open(u3_bnd_dst, "w") as f_u3:
                for nid_str in sorted(nodal_u.keys(), key=int):
                    nid = int(nid_str)
                    u1, u2 = nodal_u[nid_str]
                    u3 = nodal_d.get(nid_str, 0.0)
                    f_full.write(f"{nid}, 1, 1, {u1:.16e}\n")
                    f_full.write(f"{nid}, 2, 2, {u2:.16e}\n")
                    f_full.write(f"{nid}, 3, 3, {u3:.16e}\n")
                    full_count += 3

                    f_u3.write(f"{nid}, 3, 3, {u3:.16e}\n")
                    u3_count += 1
            print(f"Generated full boundary file ({full_count} lines) and U3-only boundary file ({u3_count} lines) from JSON.")

    # 3. Create R5 INP file with 4-step sequence
    r5_steps = """*STEP, NAME=STATE_INSTALL, NLGEOM=NO, INC=10
*STATIC
1.0, 1.0, 1.0e-5, 1.0
*BOUNDARY, OP=NEW
*BOUNDARY, INPUT=PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_RP
U, RF
*END STEP

*STEP, NAME=MECH_EQUILIBRATION, NLGEOM=NO, INC=100
*STATIC
1.0, 1.0, 1.0e-5, 1.0
*BOUNDARY, OP=NEW
N_BOTTOM, 1, 2, 0.0
N_TOP, 2, 2, 0.0
RP_NODE, 1, 1, 0.010143300518393517
RP_NODE, 2, 2, 0.0
*BOUNDARY, INPUT=PK10R1_INC29_U3_ONLY_BOUNDARY.inp
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_RP
U, RF
*END STEP

*STEP, NAME=PHASE_RELEASE, NLGEOM=NO, INC=100
*STATIC
1.0, 1.0, 1.0e-5, 1.0
*BOUNDARY, OP=NEW
N_BOTTOM, 1, 2, 0.0
N_TOP, 2, 2, 0.0
RP_NODE, 1, 1, 0.010143300518393517
RP_NODE, 2, 2, 0.0
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_RP
U, RF
*END STEP

*STEP, NAME=CONTINUATION, NLGEOM=NO, INC=10000
*STATIC
0.001, 1.0, 1.0e-9, 0.02
*BOUNDARY, OP=MOD
RP_NODE, 1, 1, 0.050000
RP_NODE, 2, 2, 0.0
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_TOP
U, RF
*NODE OUTPUT, NSET=N_BOTTOM
U, RF
*NODE OUTPUT, NSET=N_RP
U, RF
*NODE PRINT, FREQ=1
U, RF
*EL PRINT, FREQ=1, ELSET=E_QUAD_MECH
SDV14, SDV15, SDV16
*END STEP
"""

    inp_dst_path = R5_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R5.inp"
    with open(inp_dst_path, "w") as f:
        f.write(mesh_part + r5_steps)

    # 4. Create PBS launcher for R5
    pbs_path = R5_DIR / "submit_job.pbs"
    pbs_content = """#PBS -N M2R5_SAMEMESH
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q normal_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

cd $PBS_O_WORKDIR
source $HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh
notification_install_terminal_trap

module load abaqus/2023

abaqus job=M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R5 user=f44_mixed_uel_restart_stateinit.for interactive
"""
    with open(pbs_path, "w") as f:
        f.write(pbs_content)

    # Calculate hashes
    inp_hash = get_sha256(inp_dst_path)
    uel_hash = get_sha256(uel_dst)
    pbs_hash = get_sha256(pbs_path)
    bin_hash = get_sha256(bin_dst)

    manifest = {
        "job_name": "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R5",
        "inp_sha256": inp_hash,
        "uel_sha256": uel_hash,
        "pbs_sha256": pbs_hash,
        "bin_sha256": bin_hash,
        "resources": "1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq / Abaqus 2023"
    }

    manifest_path = R5_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    manifest_hash = get_sha256(manifest_path)

    print("================================================================================")
    print("M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R5 PACKAGE PREPARED")
    print("================================================================================")
    print(f"Directory:       {R5_DIR}")
    print(f"INP SHA256:      {inp_hash}")
    print(f"UEL SHA256:      {uel_hash}")
    print(f"PBS SHA256:      {pbs_hash}")
    print(f"BIN SHA256:      {bin_hash}")
    print(f"Manifest SHA256: {manifest_hash}")

if __name__ == "__main__":
    main()
