#!/usr/bin/env python3
"""
Build Package 116 Revision 1: Intermediate-Resolution State Transfer Control (Corrected UEL Properties)
Package directory: models/pandey_kumar_mode1/116_r1_c3_int_inc79_direct_transfer/

Identified Technical Root Cause in Package 116:
The *UEL PROPERTY card had parameter permutation [E, nu, Gc, l0, k] = [210.0, 0.3, 0.0027, 0.0075, 1.0e-06]
instead of [l0, Gc, E, nu, k] = [0.0075, 0.0027, 210.0, 0.3, 1.0E-07] expected by f42_unified_12dof_active_set_uel.for.
This reduced Young's modulus to E = 0.0027 kN/mm^2 (deficit 77,778x) and inflated l0 to 210.0 mm.

Package 116 Revision 1 applies the exact local repair:
*UEL PROPERTY, ELSET=E_ALL
0.0075, 0.0027, 210.0, 0.3, 1.0E-07
All other files, boundary cards, mesh geometry, and initial mapped state are preserved.
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = REPO_ROOT / "models/pandey_kumar_mode1/116_c3_int_inc79_direct_transfer"
OUT_DIR = REPO_ROOT / "models/pandey_kumar_mode1/116_r1_c3_int_inc79_direct_transfer"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Building Package 116 R1 at: {OUT_DIR}")

    # 1. Read input deck from 116, replace the UEL property card
    src_inp = SRC_DIR / "M1_C3_INT_INC79_DIRECT_TRANSFER.inp"
    dst_inp = OUT_DIR / "M1_C3_INT_R1_INC79_DIRECT_TRANSFER.inp"

    with open(src_inp, "r") as f:
        inp_content = f.read()

    # Verify target property string exists
    old_card = "210.0, 0.3, 0.0027, 0.0075, 1.0e-06"
    new_card = "0.0075, 0.0027, 210.0, 0.3, 1.0E-07"
    if old_card not in inp_content:
        raise ValueError(f"Target property card '{old_card}' not found in {src_inp}")

    inp_content = inp_content.replace(old_card, new_card)
    inp_content = inp_content.replace("** UEL PROPERTIES: E, nu, Gc, l0, k_residual", "** UEL PROPERTIES: l0, Gc, E, nu, k_residual")
    inp_content = inp_content.replace("Candidate C3-Intermediate Stage C1-1 Direct State-Transfer Control (Inc 79)", "Candidate C3-Intermediate Stage C1-1 Direct State-Transfer Control R1 (Inc 79)")

    with open(dst_inp, "w") as f:
        f.write(inp_content)
    print(f"Corrected UEL property card written to {dst_inp}")

    # 2. Copy boundary cards and CSVs directly from SRC_DIR
    files_to_copy = [
        "active_set_boundary_cards.inc",
        "stage_a_all_d0_boundary_cards.inc",
        "d_lower_bounds.csv",
        "nodal_displacements_initial.csv",
        "f42_unified_12dof_active_set_uel.for",
        "job_notifications.sh"
    ]
    for fn in files_to_copy:
        shutil.copy(SRC_DIR / fn, OUT_DIR / fn)

    # 3. Create AM-PDAS driver for R1
    src_driver = SRC_DIR / "driver_c3_int_inc79_direct_transfer.py"
    dst_driver = OUT_DIR / "driver_c3_int_r1_inc79_direct_transfer.py"
    with open(src_driver, "r") as f:
        driver_code = f.read()

    driver_code = driver_code.replace("M1_C3_INT_INC79_DIRECT_TRANSFER.inp", "M1_C3_INT_R1_INC79_DIRECT_TRANSFER.inp")
    driver_code = driver_code.replace("M1_C3_INT_DIR_", "M1_C3_INT_R1_DIR_")
    driver_code = driver_code.replace("c3_int_inc79_direct_transfer_summary.json", "c3_int_r1_inc79_direct_transfer_summary.json")
    driver_code = driver_code.replace("PACKAGE_116_C3_INT_INC79_DIRECT_TRANSFER", "PACKAGE_116_R1_C3_INT_INC79_DIRECT_TRANSFER")

    with open(dst_driver, "w") as f:
        f.write(driver_code)

    # 4. Create datacheck script
    dc_script = OUT_DIR / "run_c3_int_r1_transfer_datacheck.sh"
    with open(dc_script, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("if ! type module >/dev/null 2>&1; then\n")
        f.write("    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true\n")
        f.write("fi\n")
        f.write("module purge\n")
        f.write("module load gcc/11.4.0 intel/2024.2.0 abaqus/2023\n")
        f.write("abaqus job=M1_C3_INT_R1_XFER_DC input=M1_C3_INT_R1_INC79_DIRECT_TRANSFER.inp user=f42_unified_12dof_active_set_uel.for datacheck interactive\n")

    # 5. Create PBS script
    pbs_script = OUT_DIR / "submit_M1_C3_INT_R1_INC79_DIRECT_TRANSFER.pbs"
    with open(pbs_script, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("#PBS -N M1_C3_INT_R1_INC79_TRANSFER\n")
        f.write("#PBS -q entry_imfdfkmq\n")
        f.write("#PBS -m abe\n")
        f.write("#PBS -M pr21vyci@mailserver.tu-freiberg.de\n")
        f.write("#PBS -l select=1:ncpus=1:mem=16gb\n")
        f.write("#PBS -l walltime=08:00:00\n")
        f.write("#PBS -r n\n")
        f.write("#PBS -o /scratch9/pr21vyci/runs/mode1_c3_int_r1_inc79_direct_transfer/pbs_execution.log\n")
        f.write("#PBS -e /scratch9/pr21vyci/runs/mode1_c3_int_r1_inc79_direct_transfer/pbs_error.log\n\n")
        f.write("set -euo pipefail\n\n")
        f.write('RUN_DIR="/scratch9/pr21vyci/runs/mode1_c3_int_r1_inc79_direct_transfer"\n')
        f.write('cd "${RUN_DIR}"\n\n')
        f.write('if [[ "$(pwd -P)" =~ ^/home/ ]]; then\n')
        f.write('    echo "ERROR: Running under /home is strictly prohibited by HPC storage policy." >&2\n')
        f.write('    exit 2\n')
        f.write('fi\n\n')
        f.write('export XDG_RUNTIME_DIR="/tmp/runtime-pr21vyci"\n')
        f.write('mkdir -p "${XDG_RUNTIME_DIR}" 2>/dev/null || true\n\n')
        f.write('if ! type module >/dev/null 2>&1; then\n')
        f.write('    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true\n')
        f.write('fi\n\n')
        f.write('module purge\n')
        f.write('module load gcc/11.4.0 intel/2024.2.0 abaqus/2023\n')
        f.write('command -v ifort\n\n')
        f.write('export NOTIFICATION_CONFIG="${HOME}/.config/adaptive-remeshing/notifications.env"\n')
        f.write('source ./job_notifications.sh\n')
        f.write('notification_load_config\n\n')
        f.write('notification_install_terminal_trap\n')
        f.write('notify_start\n\n')
        f.write('abaqus python driver_c3_int_r1_inc79_direct_transfer.py\n')

    # 6. Hash all package files
    pkg_files = [
        "M1_C3_INT_R1_INC79_DIRECT_TRANSFER.inp",
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "driver_c3_int_r1_inc79_direct_transfer.py",
        "f42_unified_12dof_active_set_uel.for",
        "job_notifications.sh",
        "nodal_displacements_initial.csv",
        "run_c3_int_r1_transfer_datacheck.sh",
        "stage_a_all_d0_boundary_cards.inc",
        "submit_M1_C3_INT_R1_INC79_DIRECT_TRANSFER.pbs"
    ]
    files_hashes = {f: sha256_file(OUT_DIR / f) for f in pkg_files}

    command_str = "powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c3_int_r1_inc79_direct_transfer/submit_M1_C3_INT_R1_INC79_DIRECT_TRANSFER.pbs\""
    command_hash = hashlib.sha256(command_str.encode("utf-8")).hexdigest()

    # 7. Create PACKAGE_MANIFEST.json
    manifest_obj = {
        "schema": 1,
        "package_name": "116_r1_c3_int_inc79_direct_transfer",
        "created_at": "2026-10-27T08:30:00Z",
        "files": files_hashes,
        "jobs": [
            {
                "id": "M1_C3_INT_R1_INC79_TRANSFER",
                "purpose": "Abaqus 2023 Candidate C3-Intermediate Stage C1-1 Direct State-Transfer Control R1 at u = 0.00184250 mm (2,484 quads, 2,610 nodes, h_tip = 1.2 um, corrected UEL properties [0.0075, 0.0027, 210.0, 0.3, 1.0E-07], up to 15 AM cycles with irreversible history transferred from authentic C3 Increment 79)",
                "input": "M1_C3_INT_R1_INC79_DIRECT_TRANSFER.inp",
                "user_subroutine": "f42_unified_12dof_active_set_uel.for",
                "pbs": "submit_M1_C3_INT_R1_INC79_DIRECT_TRANSFER.pbs",
                "datacheck": "M1_C3_INT_R1_XFER_DC.dat",
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "command": command_str,
                "command_sha256": command_hash,
                "depends_on": []
            }
        ]
    }
    with open(OUT_DIR / "PACKAGE_MANIFEST.json", "w") as f:
        json.dump(manifest_obj, f, indent=2)

    # 8. Create M1_C3_INT_R1_TRANSFER_AUTHORIZATION.json
    auth_obj = {
        "schema": 1,
        "adapter": "mode1-experimental-12dof-v1",
        "scientific_scope": "MODE1",
        "technical_stage": "C1-1",
        "batch_name": "MODE1_C3_INT_R1_INC79_DIRECT_TRANSFER",
        "configuration": "ALTERNATING_MINIMIZATION_SAME_LOAD_DIRECT_TRANSFER",
        "hypothesis": "At fixed physical load, correcting the UEL property parameter ordering restores the physical stiffness E = 210.0 kN/mm2 and length scale l0 = 0.0075 mm, allowing genuine evaluation of the intermediate-resolution energy convergence.",
        "automatic_retry": False,
        "max_submissions": 1,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c3_int_r1_inc79_direct_transfer",
        "files": files_hashes,
        "jobs": manifest_obj["jobs"],
        "acceptance": {
            "stage_C1_1_direct_transfer": {
                "u_top_target_mm": 0.0018425,
                "rf2_expected_N": 186.067909,
                "rf2_continuity_pct_max": 5.0,
                "energy_continuity_pct_max": 2.0,
                "kkt_violations_max": 0,
                "free_phase_residual_max_kN_mm": 1.0e-06,
                "healing_tolerance": 0,
                "stationarity_delta_d_max": 0.001,
                "stationarity_delta_rf2_max_N": 0.1
            }
        },
        "package_name": "116_r1_c3_int_inc79_direct_transfer"
    }
    with open(OUT_DIR / "M1_C3_INT_R1_TRANSFER_AUTHORIZATION.json", "w") as f:
        json.dump(auth_obj, f, indent=2)

    print(f"Package 116 R1 successfully created with manifest and authorization.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
