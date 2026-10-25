#!/usr/bin/env python3
"""
create_package108_r3.py
Constructs Package 108 Revision 3: Candidate C3 Multi-Step Staggered Continuation.

Implements true closed-loop alternating minimization:
  Step 1: Stage-A Same-Load Re-equilibration at u = 0.00196510735 mm
  Step 2: Stage-B-Mech: +5 nm forward loading to u = 0.00197010735 mm with Phase (DOF 3) FIXED
  Step 3: Stage-B-Phase: Phase relaxation under updated H with Displacements (DOFs 1,2) FIXED
  Step 4: Stage-B-Mech2: Final mechanical re-equilibration with updated Phase (DOF 3) FIXED
"""

import os
import shutil
import hashlib
import json
from pathlib import Path

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def create_package():
    repo_root = Path(__file__).resolve().parent.parent.parent
    r2_dir = repo_root / "models" / "pandey_kumar_mode1" / "108_r2_c3_staggered_continuation"
    r3_dir = repo_root / "models" / "pandey_kumar_mode1" / "108_r3_c3_staggered_continuation"
    is_remote = False
    if not r2_dir.exists():
        r2_dir = Path("/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r2")
        r3_dir = Path("/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r3")
        is_remote = True
    r3_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy shared assets
    for name in ["d_lower_bounds.csv", "f42_experimental_irreversible_uel.for", "job_notifications.sh"]:
        shutil.copy2(r2_dir / name, r3_dir / name)

    # 2. Read R2 inp and append Step 4
    r2_inp_path = r2_dir / "M1_C3_STAGGERED_R2_CONTINUATION.inp"
    r2_inp = r2_inp_path.read_text(encoding="utf-8")

    step4_text = """** ================================================================
** STEP 4: Stage-B-Mech2 (Mechanical re-equilibration with Phase FIXED)
** ================================================================
*Step, name=Stage-B-Mech2, nlgeom=NO, inc=20
*Static
1.0, 1.0, 1.0E-5, 1.0
*Boundary, op=NEW, fixed
N_ALL, 3, 3
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
    final_inp = r2_inp.strip() + "\n" + step4_text
    r3_inp_path = r3_dir / "M1_C3_STAGGERED_R3_CONTINUATION.inp"
    with open(r3_inp_path, "w", newline="\n", encoding="utf-8") as f:
        f.write(final_inp)
    print(f"Written R3 inp to {r3_inp_path}")

    # 3. Create PBS submission script
    pbs_text = """#!/bin/bash
#PBS -N M1_C3_STAGGERED_R3
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r3/pbs_execution.log
#PBS -e /scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r3/pbs_error.log

set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r3"
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

JOB_NAME="M1_C3_STAGGERED_R3"
INPUT_NAME="M1_C3_STAGGERED_R3_CONTINUATION.inp"
USER_SUB="f42_experimental_irreversible_uel.for"

abaqus job="${JOB_NAME}" input="${INPUT_NAME}" user="${USER_SUB}" cpus=1 interactive
"""
    r3_pbs_path = r3_dir / "submit_M1_C3_STAGGERED_R3.pbs"
    with open(r3_pbs_path, "w", newline="\n", encoding="utf-8") as f:
        f.write(pbs_text)
    print(f"Written R3 pbs to {r3_pbs_path}")

    # 4. Generate Manifest / Authorization JSON
    inp_name = "M1_C3_STAGGERED_R3_CONTINUATION.inp"
    uel_name = "f42_experimental_irreversible_uel.for"
    pbs_name = "submit_M1_C3_STAGGERED_R3.pbs"
    bounds_name = "d_lower_bounds.csv"
    notif_name = "job_notifications.sh"

    files_dict = {
        inp_name: compute_sha256(r3_dir / inp_name),
        bounds_name: compute_sha256(r3_dir / bounds_name),
        uel_name: compute_sha256(r3_dir / uel_name),
        pbs_name: compute_sha256(r3_dir / pbs_name),
        notif_name: compute_sha256(r3_dir / notif_name)
    }

    run_dir = "/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r3"
    cmd_prefix = "powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand"
    sub_cmd = "qsub -q entry_imfdfkmq " + run_dir + "/" + pbs_name
    full_cmd = f'{cmd_prefix} "{sub_cmd}"'
    cmd_canonical = " ".join(full_cmd.strip().split())
    cmd_sha256 = hashlib.sha256(cmd_canonical.encode()).hexdigest()

    manifest = {
        "schema": 1,
        "adapter": "mode1-experimental-irrev-v1",
        "scientific_scope": "MODE1",
        "technical_stage": "C1-1",
        "batch_name": "MODE1_C3_STAGGERED_CONTINUATION_R3",
        "configuration": "STAGGERED_IRREVERSIBLE",
        "hypothesis": "Four-step closed-loop alternating minimization (Stage-A -> Stage-B-Mech -> Stage-B-Phase -> Stage-B-Mech2) eliminates artificial holding reactions and restores full mechanical and fracture energy equilibrium on Candidate C3.",
        "automatic_retry": False,
        "max_submissions": 1,
        "remote_run_dir": run_dir,
        "files": files_dict,
        "jobs": [
            {
                "id": "M1_C3_STAGGERED_R3",
                "purpose": "Abaqus 2023 Candidate C3 4-step closed alternating minimization (+5 nm) with verified irreversible UEL (R3)",
                "input": inp_name,
                "user_subroutine": uel_name,
                "pbs": pbs_name,
                "datacheck": "M1_C3_STAGGERED_R3.dat",
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "command": full_cmd,
                "command_sha256": cmd_sha256,
                "depends_on": []
            }
        ],
        "acceptance": {
            "stage_A_same_load": {
                "u_top_target_mm": 0.00196510735,
                "rf2_continuity_vs_c2_equil_pct_max": 5.0,
                "ef_continuity_vs_c2_equil_pct_max": 2.0,
                "healing_magnitude_max": 1e-08,
                "kkt_violations_max": 0
            },
            "stage_B_forward_continuation": {
                "delta_u_mm": 5e-06,
                "u_top_target_mm": 0.00197010735,
                "expected_rf2_N_approx": 179.3,
                "expected_ef_mJ_approx": 0.0624,
                "monotonic_softening_required": True,
                "monotonic_dissipation_required": True,
                "healing_magnitude_max": 1e-08
            }
        }
    }

    out_path = r3_dir / "M1_C3_STAGGERED_R3_AUTHORIZATION.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Successfully generated manifest at {out_path}")

if __name__ == "__main__":
    create_package()
