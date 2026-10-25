#!/usr/bin/env python3
"""
create_package108_r6.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 131)
Protocol Version: 2

Constructs Package 108 Revision 6: Candidate C3 Multi-Increment Staggered Continuation (R6).
Corrects the Abaqus boundary condition syntax defect identified in R5:
Avoids mixing OP=NEW and OP=MOD in any step.
In Inc1-Mech1: Uses OP=MOD (*Boundary, fixed on N_ALL 3, 3; *Boundary on N_RP, 2, 2, u1) matching R4 Step 2.
In Inc{2..5}-Mech1: Uses single OP=MOD (*Boundary on N_RP, 2, 2, u_i) carrying over fixed phase from Mech2.
In Inc{1..5}-Phase1: Uses single OP=NEW (*Boundary, op=NEW, fixed on N_ALL 1, 2 and boundaries).
In Inc{1..5}-Mech2: Uses single OP=NEW (*Boundary, op=NEW, fixed on N_ALL 3, 3 and boundaries).

Steps (16 total):
  Step 1: Stage-A Same-Load Re-equilibration at u = 0.00196510735 mm
  Increments 1..5:
    Step 3i-1: Inc{i}-Mech1: +1 nm forward loading to u_{i} (Phase DOF 3 FIXED, RP advanced)
    Step 3i:   Inc{i}-Phase1: Phase relaxation (Displacement DOFs 1,2 FIXED, Phase free)
    Step 3i+1: Inc{i}-Mech2: Mechanical re-equilibration (Phase DOF 3 FIXED, RP at u_{i})
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
    r4_dir = repo_root / "models" / "pandey_kumar_mode1" / "108_r4_c3_staggered_continuation"
    r6_dir = repo_root / "models" / "pandey_kumar_mode1" / "108_r6_c3_multi_increment_continuation"
    r6_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy shared assets
    for name in ["d_lower_bounds.csv", "job_notifications.sh"]:
        shutil.copy2(r4_dir / name, r6_dir / name)

    # Copy f42_experimental_irreversible_uel.for and verify hash e72e00d3...
    uel_src = r4_dir / "f42_experimental_irreversible_uel.for"
    uel_dst = r6_dir / "f42_experimental_irreversible_uel.for"
    shutil.copy2(uel_src, uel_dst)
    uel_hash = compute_sha256(uel_dst)
    expected_uel_hash = "e72e00d338e355b370fc5ebabfe6679f49bc07458d333b642b593c6710b16dad"
    if uel_hash != expected_uel_hash:
        raise ValueError(f"UEL hash mismatch! Expected {expected_uel_hash}, got {uel_hash}")
    print(f"Verified UEL hash: {uel_hash}")

    # 2. Read R4 input deck up to end of Step 1 (Stage-A)
    r4_inp_path = r4_dir / "M1_C3_STAGGERED_R4_CONTINUATION.inp"
    r4_lines = r4_inp_path.read_text(encoding="utf-8").splitlines()

    stage_a_end_idx = None
    in_stage_a = False
    for idx, line in enumerate(r4_lines):
        if line.strip().lower().startswith("*step") and "stage-a" in line.lower():
            in_stage_a = True
        elif in_stage_a and line.strip().lower().startswith("*end step"):
            stage_a_end_idx = idx + 1
            break

    if stage_a_end_idx is None:
        raise ValueError("Could not find *End Step for Stage-A in R4 input deck!")

    base_header = "\n".join(r4_lines[:stage_a_end_idx]) + "\n"
    print(f"Extracted base mesh and Stage-A from R4 (lines 1 to {stage_a_end_idx})")

    # 3. Construct the 15 forward steps (Increments 1 to 5) with zero OP=NEW / OP=MOD mixing
    u_base = 0.00196510735
    delta_u = 0.000001  # 1 nm
    forward_steps = []

    for inc in range(1, 6):
        u_inc = u_base + inc * delta_u
        u_str = f"{u_inc:.9f}"

        # Substep 1: Mech 1 (Phase fixed, RP advanced to u_inc)
        if inc == 1:
            # First increment after Stage-A: add Phase fix and advance RP using OP=MOD (matching R4 Step 2)
            step_mech1 = f"""** ================================================================
** STEP 2: Inc1-Mech1 (+1 nm loading to u = {u_str} mm, Phase FIXED)
** ================================================================
*Step, name=Inc1-Mech1, nlgeom=NO, inc=20
*Static
1.0, 1.0, 1.0E-5, 1.0
*Boundary, fixed
N_ALL, 3, 3
*Boundary
N_RP, 2, 2, {u_str}
*Output, field, frequency=1
*Node Output
U, RF
*Element Output, elset=VIS_QUADS
SDV, S, E
*Output, history, frequency=1
*Energy Output
ALLSE, ALLIE, ALLWK, ALLFD, ALLCD, ALLVD, ALLPD, ALLAE, ETOTAL
*End Step"""
        else:
            # Increments 2..5 after Mech2: Phase is already fixed, boundaries active, interior free; modify N_RP with OP=MOD
            step_mech1 = f"""** ================================================================
** STEP {3*inc - 1}: Inc{inc}-Mech1 (+1 nm loading to u = {u_str} mm, Phase FIXED)
** ================================================================
*Step, name=Inc{inc}-Mech1, nlgeom=NO, inc=20
*Static
1.0, 1.0, 1.0E-5, 1.0
*Boundary
N_RP, 2, 2, {u_str}
*Output, field, frequency=1
*Node Output
U, RF
*Element Output, elset=VIS_QUADS
SDV, S, E
*Output, history, frequency=1
*Energy Output
ALLSE, ALLIE, ALLWK, ALLFD, ALLCD, ALLVD, ALLPD, ALLAE, ETOTAL
*End Step"""

        # Substep 2: Phase 1 (Displacement fixed at u_inc, Phase free to relax)
        step_phase1 = f"""** ================================================================
** STEP {3*inc}: Inc{inc}-Phase1 (Phase relaxation under u = {u_str} mm, Displacement FIXED)
** ================================================================
*Step, name=Inc{inc}-Phase1, nlgeom=NO, inc=20
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
*End Step"""

        # Substep 3: Mech 2 (Phase fixed at new relaxed damage, Displacement re-equilibrated at u_inc)
        step_mech2 = f"""** ================================================================
** STEP {3*inc + 1}: Inc{inc}-Mech2 (Mechanical re-equilibration under Inc{inc} damage, Phase FIXED)
** ================================================================
*Step, name=Inc{inc}-Mech2, nlgeom=NO, inc=20
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
*End Step"""

        forward_steps.extend([step_mech1, step_phase1, step_mech2])

    final_inp_content = base_header + "\n".join(forward_steps) + "\n"

    r6_inp_path = r6_dir / "M1_C3_STAGGERED_R6_CONTINUATION.inp"
    with open(r6_inp_path, "w", newline="\n", encoding="utf-8") as f:
        f.write(final_inp_content)
    print(f"Written R6 input deck to {r6_inp_path}")

    # 4. Construct PBS submission script
    pbs_text = """#!/bin/bash
#PBS -N M1_C3_STAGGERED_R6
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r6/pbs_execution.log
#PBS -e /scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r6/pbs_error.log

set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r6"
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

JOB_NAME="M1_C3_STAGGERED_R6"
INPUT_NAME="M1_C3_STAGGERED_R6_CONTINUATION.inp"
USER_SUB="f42_experimental_irreversible_uel.for"

abaqus job="${JOB_NAME}" input="${INPUT_NAME}" user="${USER_SUB}" cpus=1 interactive
"""
    r6_pbs_path = r6_dir / "submit_M1_C3_STAGGERED_R6.pbs"
    with open(r6_pbs_path, "w", newline="\n", encoding="utf-8") as f:
        f.write(pbs_text)
    print(f"Written R6 pbs script to {r6_pbs_path}")

    # 5. Construct datacheck script
    datacheck_sh = """#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r6"
cd "${RUN_DIR}"
if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus job=M1_C3_STAGGERED_R6 input=M1_C3_STAGGERED_R6_CONTINUATION.inp user=f42_experimental_irreversible_uel.for datacheck interactive
"""
    r6_datacheck_path = r6_dir / "run_pkg108_r6_datacheck.sh"
    with open(r6_datacheck_path, "w", newline="\n", encoding="utf-8") as f:
        f.write(datacheck_sh)
    print(f"Written datacheck script to {r6_datacheck_path}")

    # 6. Construct Governed Manifest / Authorization JSON
    inp_name = "M1_C3_STAGGERED_R6_CONTINUATION.inp"
    uel_name = "f42_experimental_irreversible_uel.for"
    pbs_name = "submit_M1_C3_STAGGERED_R6.pbs"
    bounds_name = "d_lower_bounds.csv"
    notif_name = "job_notifications.sh"

    files_dict = {
        inp_name: compute_sha256(r6_dir / inp_name),
        bounds_name: compute_sha256(r6_dir / bounds_name),
        uel_name: compute_sha256(r6_dir / uel_name),
        pbs_name: compute_sha256(r6_dir / pbs_name),
        notif_name: compute_sha256(r6_dir / notif_name)
    }

    run_dir = "/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r6"
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
        "batch_name": "MODE1_C3_STAGGERED_CONTINUATION_R6",
        "configuration": "STAGGERED_IRREVERSIBLE",
        "hypothesis": "Separating fixed holding constraints (*Boundary, op=NEW, fixed) from the moving reference node boundary (*Boundary with explicit N_RP displacement) restores authentic forward load incrementation (5x1 nm), resolving R5 stationary damage escalation and converging terminal fracture energy within the +-2% gate tolerance.",
        "automatic_retry": False,
        "max_submissions": 1,
        "remote_run_dir": run_dir,
        "files": files_dict,
        "jobs": [
            {
                "id": "M1_C3_STAGGERED_R6",
                "purpose": "Abaqus 2023 Candidate C3 16-step 5x1nm multi-increment continuation with corrected displacement boundary syntax and verified irreversible UEL (R6)",
                "input": inp_name,
                "user_subroutine": uel_name,
                "pbs": pbs_name,
                "datacheck": "M1_C3_STAGGERED_R6.dat",
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
                "num_sub_increments": 5,
                "sub_increment_delta_u_mm": 1e-06,
                "u_top_target_mm": 0.00197010735,
                "expected_rf2_N_approx": 179.3,
                "rf2_tolerance_pct": 5.0,
                "expected_ef_mJ_approx": 0.062404,
                "ef_tolerance_pct": 2.0,
                "ef_acceptance_window_mJ": [0.06115592, 0.06365208],
                "expected_dmax_approx": 0.675399,
                "dmax_tolerance_pct": 2.0,
                "monotonic_softening_required": True,
                "monotonic_dissipation_required": True,
                "healing_magnitude_max": 1e-08
            }
        }
    }

    manifest_path = r6_dir / "M1_C3_STAGGERED_R6_AUTHORIZATION.json"
    with open(manifest_path, "w", newline="\n", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Written R6 manifest to {manifest_path}")

    return manifest_path

if __name__ == "__main__":
    create_package()
