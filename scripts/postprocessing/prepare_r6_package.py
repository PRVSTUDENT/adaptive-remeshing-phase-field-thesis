#!/usr/bin/env python3
"""
F184 Prepare Corrected Same-Mesh Validation R6 Package
Generates M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6 with:
- Subroutine f44_mixed_uel_restart_stateinit.for (Original authoritative transactional UEL physics)
- Canonical boundary includes generated directly from PK10R1_INC29_PRIMARY_STATE_REPLAY_R1.csv (9,849 physical nodes only)
- Corrected Step 2 INP staging with top U2 FREE, mechanics released before phase, and U3 constrained
- PBS queue #PBS -q entry_imfdfkmq matching manifest declared resource
"""

import os
import shutil
import hashlib
import json
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BASE_DIR = ROOT / "models/generated/mode_ii/production_control_batch"
R6_DIR = BASE_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6"

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def main():
    R6_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy binary state and subroutine f44
    bin_src = BASE_DIR / "PK10R1_INC29_SOURCE_STATE.bin"
    bin_dst = R6_DIR / "PK10R1_INC29_SOURCE_STATE.bin"
    shutil.copy2(bin_src, bin_dst)

    uel_src = BASE_DIR / "f44_mixed_uel_restart_stateinit.for"
    uel_dst = R6_DIR / "f44_mixed_uel_restart_stateinit.for"
    shutil.copy2(uel_src, uel_dst)

    # 2. Build boundary files directly from canonical CSV
    csv_src = BASE_DIR / "PK10R1_INC29_PRIMARY_STATE_REPLAY_R1.csv"
    if not csv_src.exists():
        csv_src = BASE_DIR / "M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1/PK10R1_INC29_PRIMARY_STATE_REPLAY_R1.csv"

    full_bnd_dst = R6_DIR / "PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp"
    u3_bnd_dst   = R6_DIR / "PK10R1_INC29_U3_ONLY_BOUNDARY.inp"

    nodes = {}
    with open(csv_src, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nid = int(row["node_label"])
            u1 = float(row["U1_solver"])
            u2 = float(row["U2_solver"])
            u3 = float(row["U3_phase_solver"])
            nodes[nid] = (u1, u2, u3)

    print(f"Loaded {len(nodes)} physical UEL nodes from canonical CSV ({csv_src.name}).")

    full_count = 0
    u3_count = 0
    with open(full_bnd_dst, "w") as f_full, open(u3_bnd_dst, "w") as f_u3:
        for nid in sorted(nodes.keys()):
            u1, u2, u3 = nodes[nid]
            f_full.write(f"{nid}, 1, 1, {u1:.16e}\n")
            f_full.write(f"{nid}, 2, 2, {u2:.16e}\n")
            f_full.write(f"{nid}, 3, 3, {u3:.16e}\n")
            full_count += 3

            f_u3.write(f"{nid}, 3, 3, {u3:.16e}\n")
            u3_count += 1

    print(f"Generated PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp ({full_count} lines).")
    print(f"Generated PK10R1_INC29_U3_ONLY_BOUNDARY.inp ({u3_count} lines).")

    # 3. Read reference INP deck
    ref_inp_path = BASE_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.inp"
    with open(ref_inp_path, "r") as f:
        text = f.read()

    mesh_part = text.split("*STEP, NAME=STATE_INIT")[0]

    # Corrected 4-step sequence (top U2 FREE in MECH and PHASE steps)
    r6_steps = """*STEP, NAME=STATE_INSTALL, NLGEOM=NO, INC=10
*STATIC
1.0, 1.0, 1.0e-5, 1.0
*BOUNDARY, OP=NEW
*INCLUDE, INPUT=PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_RP
U, RF
*END STEP

*STEP, NAME=MECH_EQUILIBRATION, NLGEOM=NO, INC=100
*STATIC
1.0, 1.0, 1.0e-5, 1.0
*BOUNDARY, OP=NEW
N_BOTTOM, 1, 2, 0.0
N_RP, 1, 1, 0.010143300518393517
N_RP, 2, 2, 0.0
*INCLUDE, INPUT=PK10R1_INC29_U3_ONLY_BOUNDARY.inp
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_RP
U, RF
*END STEP

*STEP, NAME=PHASE_RELEASE, NLGEOM=NO, INC=100
*STATIC
1.0, 1.0, 1.0e-5, 1.0
*BOUNDARY, OP=NEW
N_BOTTOM, 1, 2, 0.0
N_RP, 1, 1, 0.010143300518393517
N_RP, 2, 2, 0.0
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_RP
U, RF
*END STEP

*STEP, NAME=CONTINUATION, NLGEOM=NO, INC=10000
*STATIC
0.001, 1.0, 1.0e-9, 0.02
*BOUNDARY, OP=MOD
N_RP, 1, 1, 0.050000
N_RP, 2, 2, 0.0
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

    inp_dst_path = R6_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6.inp"
    with open(inp_dst_path, "w") as f:
        f.write(mesh_part + r6_steps)

    # 4. Create PBS launcher for R6 matching declared queue entry_imfdfkmq with Unix LF endings
    pbs_path = R6_DIR / "submit_job.pbs"
    pbs_content = """#PBS -N M2R6_SAMEMESH
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

cd $PBS_O_WORKDIR
source $HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh
notification_install_terminal_trap

module load abaqus/2023

abaqus job=M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6 user=f44_mixed_uel_restart_stateinit.for
"""
    with open(pbs_path, "wb") as f:
        f.write(pbs_content.replace("\r\n", "\n").encode("utf-8"))


    # Calculate hashes
    inp_hash = get_sha256(inp_dst_path)
    uel_hash = get_sha256(uel_dst)
    pbs_hash = get_sha256(pbs_path)
    bin_hash = get_sha256(bin_dst)
    full_bnd_hash = get_sha256(full_bnd_dst)
    u3_bnd_hash = get_sha256(u3_bnd_dst)
    csv_hash = get_sha256(csv_src)

    manifest = {
        "job_name": "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6",
        "inp_sha256": inp_hash,
        "uel_sha256": uel_hash,
        "pbs_sha256": pbs_hash,
        "bin_sha256": bin_hash,
        "full_bnd_sha256": full_bnd_hash,
        "u3_bnd_sha256": u3_bnd_hash,
        "csv_sha256": csv_hash,
        "resources": "1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq / Abaqus 2023"
    }

    manifest_path = R6_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    manifest_hash = get_sha256(manifest_path)

    print("================================================================================")
    print("M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6 PACKAGE PREPARED")
    print("================================================================================")
    print(f"Directory:             {R6_DIR}")
    print(f"INP SHA256:            {inp_hash}")
    print(f"UEL SHA256:            {uel_hash}")
    print(f"PBS SHA256:            {pbs_hash}")
    print(f"BIN SHA256:            {bin_hash}")
    print(f"Full Include SHA256:   {full_bnd_hash}")
    print(f"U3-Only Include SHA256:{u3_bnd_hash}")
    print(f"Canonical CSV SHA256:  {csv_hash}")
    print(f"Manifest SHA256:       {manifest_hash}")

if __name__ == "__main__":
    main()
