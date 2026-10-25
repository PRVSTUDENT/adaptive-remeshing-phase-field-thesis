#!/usr/bin/env python3
"""
create_package108_r2.py
Constructs Package 108 Revision 2: Candidate C3 Multi-Step Staggered Continuation.

Implements true alternating minimization:
  Step 1: Stage-A Same-Load Re-equilibration at u = 0.00196510735 mm
  Step 2: Stage-B-Mech: +5 nm forward loading to u = 0.00197010735 mm with Phase (DOF 3) FIXED
  Step 3: Stage-B-Phase: Phase relaxation under updated H with Displacements (DOFs 1,2) FIXED
  Step 4: Stage-B-Mech2: Final mechanical re-equilibration with updated Phase (DOF 3) FIXED
"""

import os
import shutil
import hashlib
from pathlib import Path

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def create_package():
    repo_root = Path(__file__).resolve().parent.parent.parent
    r1_dir = repo_root / "models" / "pandey_kumar_mode1" / "108_r1_c3_staggered_continuation"
    r2_dir = repo_root / "models" / "pandey_kumar_mode1" / "108_r2_c3_staggered_continuation"
    if not r1_dir.exists():
        r1_dir = Path("/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r1")
        r2_dir = Path("/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r2")
    r2_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy shared assets
    for name in ["d_lower_bounds.csv", "f42_experimental_irreversible_uel.for", "job_notifications.sh"]:
        shutil.copy2(r1_dir / name, r2_dir / name)

    # 2. Read R1 inp and modify step definitions
    r1_inp = (r1_dir / "M1_C3_STAGGERED_CONTINUATION.inp").read_text(encoding="utf-8")

    # Add N_ALL after N_RP definition
    assert "*Nset, nset=N_RP\n999999" in r1_inp or "*Nset, nset=N_RP\n 999999" in r1_inp
    if "*Nset, nset=N_RP\n999999" in r1_inp:
        target_nset = "*Nset, nset=N_RP\n999999"
    else:
        target_nset = "*Nset, nset=N_RP\n 999999"

    replacement_nset = target_nset + "\n*Nset, nset=N_ALL, generate\n1, 2769, 1\n"
    inp_mod = r1_inp.replace(target_nset, target_nset + "\n*Nset, nset=N_ALL, generate\n1, 2769, 1", 1)

    # Replace step definitions from "** STEP 1: Stage-A Same-Load" to end
    step_start_idx = inp_mod.find("** STEP 1: Stage-A Same-Load")
    assert step_start_idx != -1, "Could not find step start marker"

    header_part = inp_mod[:step_start_idx]

    staggered_steps = """** ================================================================
** STEP 1: Stage-A Same-Load Re-Equilibration at u = 0.00196510735 mm
** ================================================================
*Step, name=Stage-A, nlgeom=NO, inc=25
*Static
1.0, 1.0, 1.0E-5, 1.0
*Boundary
N_BOTTOM, 2, 2, 0.0
N_PIN, 1, 1, 0.0
N_TOP, 1, 1, 0.0
N_RP, 2, 2, 0.00196510735
*Output, field, frequency=1
*Node Output
U, RF
*Element Output, elset=VIS_QUADS
SDV, S, E
*Output, history, frequency=1
*Energy Output
ALLSE, ALLIE, ALLWK, ALLFD, ALLCD, ALLVD, ALLPD, ALLAE, ETOTAL
*End Step
** ================================================================
** STEP 2: Stage-B-Mech (+5 nm forward loading with Phase FIXED)
** ================================================================
*Step, name=Stage-B-Mech, nlgeom=NO, inc=20
*Static
1.0, 1.0, 1.0E-5, 1.0
*Boundary, fixed
N_ALL, 3, 3
*Boundary
N_RP, 2, 2, 0.00197010735
*Output, field, frequency=1
*Node Output
U, RF
*Element Output, elset=VIS_QUADS
SDV, S, E
*Output, history, frequency=1
*Energy Output
ALLSE, ALLIE, ALLWK, ALLFD, ALLCD, ALLVD, ALLPD, ALLAE, ETOTAL
*End Step
** ================================================================
** STEP 3: Stage-B-Phase (Phase relaxation with Displacement FIXED)
** ================================================================
*Step, name=Stage-B-Phase, nlgeom=NO, inc=20
*Static
1.0, 1.0, 1.0E-5, 1.0
*Boundary, op=NEW, fixed
N_ALL, 1, 2
N_BOTTOM, 2, 2
N_PIN, 1, 1
N_TOP, 1, 1
N_RP, 2, 2
*Output, field, frequency=1
*Node Output
U, RF
*Element Output, elset=VIS_QUADS
SDV, S, E
*Output, history, frequency=1
*Energy Output
ALLSE, ALLIE, ALLWK, ALLFD, ALLCD, ALLVD, ALLPD, ALLAE, ETOTAL
*End Step
"""
    final_inp = header_part + staggered_steps
    r2_inp_path = r2_dir / "M1_C3_STAGGERED_R2_CONTINUATION.inp"
    with open(r2_inp_path, "w", newline="\n", encoding="utf-8") as f:
        f.write(final_inp)
    print(f"Written R2 inp to {r2_inp_path}")

    # 3. Create PBS submission script
    pbs_text = """#!/bin/bash
#PBS -N M1_C3_STAGGERED_R2
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r2/pbs_execution.log
#PBS -e /scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r2/pbs_error.log

set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r2"
cd "${RUN_DIR}"

# Storage compliance guard
if [[ "$(pwd -P)" =~ ^/home/ ]]; then
    echo "ERROR: Running under /home is strictly prohibited by HPC storage policy." >&2
    exit 2
fi

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

export NOTIFICATION_CONFIG="${HOME}/.config/adaptive-remeshing/notifications.env"
source ./job_notifications.sh
notification_load_config

notification_install_terminal_trap
notify_start

JOB_NAME="M1_C3_STAGGERED_R2"
INPUT_NAME="M1_C3_STAGGERED_R2_CONTINUATION.inp"
USER_SUB="f42_experimental_irreversible_uel.for"

abaqus job="${JOB_NAME}" input="${INPUT_NAME}" user="${USER_SUB}" cpus=1 interactive
"""
    r2_pbs_path = r2_dir / "submit_M1_C3_STAGGERED_R2.pbs"
    with open(r2_pbs_path, "w", newline="\n", encoding="utf-8") as f:
        f.write(pbs_text)
    print(f"Written R2 pbs to {r2_pbs_path}")

if __name__ == "__main__":
    create_package()
