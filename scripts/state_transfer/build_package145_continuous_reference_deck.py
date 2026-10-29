#!/usr/bin/env python3
"""
Generator and Preflight Qualification Script for Package 145:
Candidate C4 Continuous Reference Simulation (M1_C4_PACKAGE145_CONTINUOUS_REFERENCE).

Scientific Purpose:
Provides the essential Candidate B continuous Mode-I reference anchor on Candidate C4 mesh
(4,422 physical quads, 4,588 nodes, h_tip = 0.6 um) starting from virgin initial conditions (u=0, d=0, H=0).
Uses the two-step monotonic displacement loading schedule targeting exact Frame-77 landing
at u_RP = 0.0018003125442191958 mm (matching Package 143 Frame 77) and continuing through u = 0.0020 mm.

Decouples intrinsic mesh-discretization energy differences from state transfer / initialization defects:
  Delta_mesh = (E_B - E_A) / E_A
  Delta_transfer = (E_C - E_B) / E_B
where:
  E_A: Candidate A (C3-Intermediate continuous donor, Package 143 Frame 77: E_tot = 0.208752 mJ, RF2 = 188.4570 N)
  E_B: Candidate B (C4 continuous reference, Package 145 Step 1 Increment 76)
  E_C: Candidate C (C4 transferred clamped, Package 142: E_tot = 0.213833 mJ, RF2 = 194.1213 N)
"""

import os
import sys
import hashlib
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
PRODUCTION_UEL_PATH = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
C4_BASE_TEMPLATE_PATH = REPO_ROOT / "models/pandey_kumar_mode1/94_c4_package94_authentic_transfer/M1_C4_PACKAGE94_TRANSFER.inp"
PKG143_NOTIFICATIONS_PATH = REPO_ROOT / "models/pandey_kumar_mode1/143_c3_int_donor_monitored/job_notifications.sh"

PACKAGE_NUM = 145
MODEL_NAME = "M1_C4_PACKAGE145_CONTINUOUS_REFERENCE"
OUTPUT_DIR = REPO_ROOT / f"models/pandey_kumar_mode1/{PACKAGE_NUM}_c4_continuous_reference"
REMOTE_RUN_DIR = f"/scratch9/pr21vyci/runs/mode1_c4_package{PACKAGE_NUM}_continuous_reference"

TARGET_DISP_STEP1_MM = 0.0018003125442191958
TARGET_DISP_STEP2_MM = 0.0020000000000000000


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def build_package145():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Building Package {PACKAGE_NUM} in {OUTPUT_DIR}...")

    # 1. Verify and copy production UEL
    assert PRODUCTION_UEL_PATH.exists(), f"Production UEL missing at {PRODUCTION_UEL_PATH}"
    uel_hash = compute_sha256(PRODUCTION_UEL_PATH)
    assert uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch! Expected {FROZEN_UEL_HASH}, got {uel_hash}"
    target_uel = OUTPUT_DIR / "f42_mixed_uel.for"
    shutil.copyfile(PRODUCTION_UEL_PATH, target_uel)
    print(f"Verified and copied production UEL: {target_uel.name} ({uel_hash})")

    # 2. Copy job_notifications.sh
    assert PKG143_NOTIFICATIONS_PATH.exists(), f"job_notifications.sh missing at {PKG143_NOTIFICATIONS_PATH}"
    target_notif = OUTPUT_DIR / "job_notifications.sh"
    shutil.copyfile(PKG143_NOTIFICATIONS_PATH, target_notif)
    print(f"Copied notification script: {target_notif.name}")

    # 3. Read base mesh cards from C4 template
    assert C4_BASE_TEMPLATE_PATH.exists(), f"C4 base template missing at {C4_BASE_TEMPLATE_PATH}"
    base_lines = []
    with open(C4_BASE_TEMPLATE_PATH, "r") as f:
        for idx, line in enumerate(f):
            # Extract lines 7 to 18134 (0-indexed)
            if 7 <= idx <= 18134:
                base_lines.append(line)

    assert len(base_lines) > 10000, f"Unexpected short base_lines count: {len(base_lines)}"
    print(f"Extracted {len(base_lines)} base mesh lines from C4 template.")

    # 4. Generate Master Input Deck
    inp_path = OUTPUT_DIR / f"{MODEL_NAME}.inp"
    with open(inp_path, "w", newline="\n") as f:
        f.write("*Heading\n")
        f.write("** Candidate C4 Continuous Monotonic Mode-I Reference Simulation\n")
        f.write("** Elements: 4422 Quads, Nodes: 4588 physical + RP 999999\n")
        f.write("** Geometry: 0.1 x 0.1 mm, sharp slit at y=0.05 mm, a0=0.04 mm\n")
        f.write("** Parameters: E=210.0 kN/mm^2, nu=0.3, Gc=0.0027 kN/mm, l0=0.0075 mm, k=1e-07\n")
        f.write(f"** Two-step continuous loading: Step 1 lands exactly on Frame 77 (u = {TARGET_DISP_STEP1_MM:.10f} mm)\n")
        f.write("*Preprint, echo=NO, model=NO, history=NO, contact=NO\n")

        # Write C4 base mesh cards
        for line in base_lines:
            f.write(line)

        # RP constraints in initial boundary
        f.write("N_RP, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, 0.0\n")

        # STEP 1: Monotonic loading to Frame-77 landing
        f.write("** ==========================================================\n")
        f.write(f"** STEP 1: Monotonic Loading to Frame 77 (u = {TARGET_DISP_STEP1_MM:.10f} mm)\n")
        f.write("** ==========================================================\n")
        f.write("*Step, name=Step-1, nlgeom=NO, inc=2000\n")
        f.write("*Static\n")
        f.write("1.0e-3, 0.36006251, 1.0e-8, 5.0e-3\n")
        f.write("*Boundary\n")
        f.write(f"N_RP, 2, 2, {TARGET_DISP_STEP1_MM:.16f}\n")
        f.write("** Output requests\n")
        f.write("*Output, field, frequency=1\n")
        f.write("*Node Output\n")
        f.write("U, RF\n")
        f.write("*Element Output, elset=UMATELEM\n")
        f.write("SDV, S, E\n")
        f.write("*Node Print, frequency=1000\n")
        f.write("U, RF\n")
        f.write("*Output, history, frequency=1\n")
        f.write("*Node Output, nset=N_RP\n")
        f.write("U2, RF2\n")
        f.write("*Energy Output\n")
        f.write("ALLSE, ALLWK\n")
        f.write("*Restart, write, frequency=1\n")
        f.write("*End Step\n")

        # STEP 2: Monotonic continuation through u = 0.0020 mm
        f.write("** ==========================================================\n")
        f.write(f"** STEP 2: Monotonic Continuation through u = {TARGET_DISP_STEP2_MM:.4f} mm\n")
        f.write("** ==========================================================\n")
        f.write("*Step, name=Step-2, nlgeom=NO, inc=1000\n")
        f.write("*Static\n")
        f.write("1.0e-3, 0.03993749, 1.0e-8, 5.0e-3\n")
        f.write("*Boundary\n")
        f.write(f"N_RP, 2, 2, {TARGET_DISP_STEP2_MM:.16f}\n")
        f.write("** Output requests\n")
        f.write("*Output, field, frequency=1\n")
        f.write("*Node Output\n")
        f.write("U, RF\n")
        f.write("*Element Output, elset=UMATELEM\n")
        f.write("SDV, S, E\n")
        f.write("*Node Print, frequency=1000\n")
        f.write("U, RF\n")
        f.write("*Output, history, frequency=1\n")
        f.write("*Node Output, nset=N_RP\n")
        f.write("U2, RF2\n")
        f.write("*Energy Output\n")
        f.write("ALLSE, ALLWK\n")
        f.write("*Restart, write, frequency=1\n")
        f.write("*End Step\n")

    print(f"Generated master input deck: {inp_path.name} ({inp_path.stat().st_size} bytes)")

    # 5. Generate datacheck script
    dc_script_path = OUTPUT_DIR / "run_datacheck.sh"
    with open(dc_script_path, "w", newline="\n") as f:
        f.write("#!/bin/bash\n")
        f.write("set -e\n")
        f.write(f"cd {REMOTE_RUN_DIR}\n")
        f.write("if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi\n")
        f.write("module purge\n")
        f.write("module load gcc/11.4.0 intel/2024.2.0 abaqus/2023\n")
        f.write(f"rm -f {MODEL_NAME}_DC.*\n")
        f.write(f"abaqus job={MODEL_NAME}_DC input={MODEL_NAME}.inp user=f42_mixed_uel.for datacheck interactive\n")
    print(f"Generated datacheck script: {dc_script_path.name}")

    # 6. Generate PBS submission wrapper
    pbs_path = OUTPUT_DIR / f"submit_{MODEL_NAME}.pbs"
    with open(pbs_path, "w", newline="\n") as f:
        f.write("#!/bin/bash\n")
        f.write(f"#PBS -N M1_C4_P{PACKAGE_NUM}_REF\n")
        f.write("#PBS -l select=1:ncpus=1:mem=16gb\n")
        f.write("#PBS -l walltime=08:00:00\n")
        f.write("#PBS -q entry_imfdfkmq\n")
        f.write("#PBS -j oe\n")
        f.write("#PBS -r n\n")
        f.write(f"#PBS -o {REMOTE_RUN_DIR}/pbs_execution.log\n")
        f.write("#PBS -m abe\n")
        f.write("#PBS -M pr21vyci@mailserver.tu-freiberg.de\n\n")
        f.write("set -euo pipefail\n")
        f.write(f'RUN_DIR="{REMOTE_RUN_DIR}"\n')
        f.write('cd "${RUN_DIR}"\n\n')
        f.write(f'export JOB_NAME="{MODEL_NAME}"\n')
        f.write('export NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-${HOME}/.config/adaptive-remeshing/notifications.env}"\n')
        f.write('source "${RUN_DIR}/job_notifications.sh"\n')
        f.write("notification_load_config\n")
        f.write("notification_install_terminal_trap\n")
        f.write("notify_start\n\n")
        f.write("if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi\n")
        f.write("module purge\n")
        f.write("module load gcc/11.4.0 intel/2024.2.0 abaqus/2023\n")
        f.write("command -v ifort\n\n")
        f.write(f'JOB_NAME="{MODEL_NAME}"\n')
        f.write(f'INP_NAME="{MODEL_NAME}.inp"\n')
        f.write('USER_SUB="f42_mixed_uel.for"\n\n')
        f.write('test ! -e "${JOB_NAME}.lck"\n\n')
        f.write(f'echo "Starting Abaqus/Standard 2023 Continuous C4 Reference (4422 Quads, h=0.6 um)..."\n')
        f.write('abaqus job="${JOB_NAME}" input="${INP_NAME}" user="${USER_SUB}" cpus=1 interactive\n')
        f.write("EXIT_CODE=$?\n\n")
        f.write('echo "Abaqus Finished with Exit Code: ${EXIT_CODE}"\n')
        f.write("exit ${EXIT_CODE}\n")
    print(f"Generated PBS script: {pbs_path.name}")

    # 7. Generate PACKAGE_MANIFEST.json
    manifest_path = OUTPUT_DIR / "PACKAGE_MANIFEST.json"
    files_map = {
        f"{MODEL_NAME}.inp": compute_sha256(inp_path).lower(),
        "f42_mixed_uel.for": compute_sha256(target_uel).lower(),
        "job_notifications.sh": compute_sha256(target_notif).lower(),
        f"submit_{MODEL_NAME}.pbs": compute_sha256(pbs_path).lower(),
    }
    manifest_data = {
        "package_number": PACKAGE_NUM,
        "purpose": (
            "Authentic Mode-I candidate C4 continuous reference simulation with companion UMAT visualization "
            "and *NODE PRINT monitoring (4422 quads, h=0.6 um, 4588 nodes, f42_mixed_uel.for) targeting exact "
            f"Frame-77 displacement (u = {TARGET_DISP_STEP1_MM:.10f} mm) to establish the true Candidate B reference anchor "
            "and separate mesh discretization effects from transfer defects."
        ),
        "files": files_map
    }
    with open(manifest_path, "w", newline="\n") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"Generated manifest: {manifest_path.name}")

    # 8. Generate AUTHORIZATION.json for Invoke-Mode1Execution
    auth_path = OUTPUT_DIR / f"{MODEL_NAME}_AUTHORIZATION.json"
    qsub_cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq {REMOTE_RUN_DIR}/submit_{MODEL_NAME}.pbs"'
    cmd_sha256 = hashlib.sha256(qsub_cmd.encode("utf-8")).hexdigest().lower()
    auth_data = {
        "batch_name": f"MODE1_PACKAGE{PACKAGE_NUM}_C4_CONTINUOUS_REFERENCE",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "hours_valid": 24,
        "automatic_retry": False,
        "remote_run_dir": REMOTE_RUN_DIR,
        "files": {
            f"{MODEL_NAME}.inp": files_map[f"{MODEL_NAME}.inp"],
            "f42_mixed_uel.for": files_map["f42_mixed_uel.for"],
            "job_notifications.sh": files_map["job_notifications.sh"],
            f"submit_{MODEL_NAME}.pbs": files_map[f"submit_{MODEL_NAME}.pbs"],
            "PACKAGE_MANIFEST.json": compute_sha256(manifest_path).lower(),
        },
        "jobs": [
            {
                "id": MODEL_NAME,
                "pbs": f"submit_{MODEL_NAME}.pbs",
                "command": qsub_cmd,
                "command_sha256": cmd_sha256,
                "max_submissions": 1,
                "depends_on": [],
                "purpose": (
                    f"Abaqus 2023 Candidate C4 continuous reference calculation (4422 quads, h=0.6 um, 4588 nodes, f42_mixed_uel.for) "
                    f"targeting exact Frame-77 landing u = {TARGET_DISP_STEP1_MM:.10f} mm and continuing through u = 0.0020 mm"
                ),
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "queue": "entry_imfdfkmq",
                "execution": "single-rank serial",
                "input": f"{MODEL_NAME}.inp",
                "datacheck": f"{MODEL_NAME}_DC.dat"
            }
        ],
        "acceptance": {
            MODEL_NAME: (
                "Exit code 0; monotonic damage growth and fracture energy dissipation; "
                f"Step 1 completes at exact target displacement u = {TARGET_DISP_STEP1_MM:.10f} mm."
            )
        }
    }
    with open(auth_path, "w", newline="\n") as f:
        json.dump(auth_data, f, indent=2)
    print(f"Generated authorization: {auth_path.name}")

    return {
        "inp": inp_path,
        "manifest": manifest_path,
        "auth": auth_path,
        "pbs": pbs_path,
        "files_map": files_map
    }


if __name__ == "__main__":
    build_package145()
