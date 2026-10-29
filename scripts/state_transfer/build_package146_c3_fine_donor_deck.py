#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package146_c3_fine_donor_deck.py
Mode-I Method C: Package 146 Continuous C3-Fine Donor Generator and Preflight.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Hypothesis: H54 - Narrower Mesh-Resolution Jump Donor Qualification
Protocol Version: 2

Scientific Purpose:
Generates the distinct Candidate C3-Fine donor simulation (Package 146) with a target crack-tip
element resolution of h_tip ~ 0.81 um (5,112 physical quads, 5,290 nodes) to test whether a
narrower donor-to-C4 mesh-resolution jump (ratio ~ 1.07 vs original 1.38) reduces the Stage C1-1
energy continuity mismatch below the 2.0% acceptance threshold without altering frozen physics.

Mesh Architecture:
- Discretization: 5,112 physical quads, 5,290 physical nodes + RP 999999
- Refinement Corridor: h_tip = 0.8095 um x 0.8095 um around crack tip (0.040, 0.050)
- Slit Topology: Exact coincident seam split along y = 0.050 mm for x <= 0.040 mm
- Layer 1: Phase-Field UEL Quads (U1, DOF 3, EIDs 1..5112)
- Layer 2: Mechanical UEL Quads (U2, DOFs 1,2, EIDs 5113..10224)
- Layer 3: Companion UMAT Overlay (CPE4, EIDs 10225..15336)
- Loading: Two-step monotonic loading schedule landing exactly on Frame 77 at
  u_RP = 0.0018003125442191958 mm (Step 1) and continuing through u_RP = 0.0020 mm (Step 2).
"""

from __future__ import print_function, division
import os
import sys
import json
import shutil
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.remeshing.generate_crack_band_mesh import generate_graded_1d, build_quad_mesh

PRODUCTION_UEL_PATH = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
NOTIFICATIONS_SRC = REPO_ROOT / "models/pandey_kumar_mode1/143_c3_int_donor_monitored/job_notifications.sh"

PACKAGE_NUM = 146
MODEL_NAME = "M1_C3_FINE_PACKAGE146_DONOR"
OUTPUT_DIR = REPO_ROOT / f"models/pandey_kumar_mode1/{PACKAGE_NUM}_c3_fine_donor"
REMOTE_RUN_DIR = f"/scratch9/pr21vyci/runs/mode1_c3_fine_package{PACKAGE_NUM}_donor"

TARGET_DISP_STEP1_MM = 0.0018003125442191958
TARGET_DISP_STEP2_MM = 0.0020000000000000000


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def build_package146():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("================================================================================")
    print(f"BUILDING PACKAGE {PACKAGE_NUM}: {MODEL_NAME}")
    print("================================================================================")

    # 1. Verify frozen production UEL
    assert PRODUCTION_UEL_PATH.exists(), f"Production UEL missing at {PRODUCTION_UEL_PATH}"
    uel_hash = compute_sha256(PRODUCTION_UEL_PATH)
    assert uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch! Expected {FROZEN_UEL_HASH}, got {uel_hash}"
    target_uel = OUTPUT_DIR / "f42_mixed_uel.for"
    shutil.copyfile(PRODUCTION_UEL_PATH, target_uel)
    print(f"Verified frozen UEL: f42_mixed_uel.for ({uel_hash})")

    # 2. Copy notification script
    assert NOTIFICATIONS_SRC.exists(), f"Notifications script missing at {NOTIFICATIONS_SRC}"
    target_notif = OUTPUT_DIR / "job_notifications.sh"
    shutil.copyfile(NOTIFICATIONS_SRC, target_notif)
    print("Verified dual-channel notification script.")

    # 3. Generate C3-Fine Specimen Mesh
    y_coords = generate_graded_1d(
        x_min=0.0,
        x_max=0.100,
        x_center=0.050,
        band_half_width=0.017,
        h_fine=0.00085,
        growth_ratio=1.14,
        max_h=0.0035
    )
    x_coords = generate_graded_1d(
        x_min=0.0,
        x_max=0.100,
        x_center=0.040,
        band_half_width=0.017,
        h_fine=0.00085,
        growth_ratio=1.14,
        max_h=0.0035,
        key_points=[0.040]
    )
    mesh = build_quad_mesh(x_coords, y_coords, slit_y=0.050, slit_a0=0.040)
    n_phys_nodes = mesh["n_nodes"]
    n_phys_elems = mesh["n_elements"]
    print(f"Generated mesh: {n_phys_nodes} nodes, {n_phys_elems} quads (nx={mesh['nx']}, ny={mesh['ny']})")

    # 4. Assemble Abaqus Input Deck
    inp_path = OUTPUT_DIR / f"{MODEL_NAME}.inp"
    with open(inp_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("*Heading\n")
        f.write(f"** Continuous C3-Fine Mode-I Donor Simulation (Package {PACKAGE_NUM})\n")
        f.write(f"** Elements: {n_phys_elems} Quads, Nodes: {n_phys_nodes} physical + RP 999999\n")
        f.write("** Geometry: 0.1 x 0.1 mm, sharp slit at y=0.05 mm, a0=0.04 mm\n")
        f.write("** Parameters: E=210.0 kN/mm^2, nu=0.3, Gc=0.0027 kN/mm, l0=0.0075 mm, k=1e-07\n")
        f.write(f"** Two-step continuous loading: Step 1 lands exactly on Frame 77 (u = {TARGET_DISP_STEP1_MM:.10f} mm)\n")
        f.write("*Preprint, echo=NO, model=NO, history=NO, contact=NO\n")
        f.write("** ==========================================================\n")
        f.write(f"*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n")
        f.write("3\n")
        f.write(f"*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n")
        f.write("1, 2\n")
        f.write("** ==========================================================\n")
        f.write("** NODES\n")
        f.write("** ==========================================================\n")
        f.write("*Node\n")
        for nid in sorted(mesh["nodes"].keys()):
            pt = mesh["nodes"][nid]
            f.write(f"{nid}, {pt[0]:.10f}, {pt[1]:.10f}\n")

        f.write("** ==========================================================\n")
        f.write(f"** LAYER 1: Phase-Field UEL Elements (U1: DOF 3, 1..{n_phys_elems})\n")
        f.write("** ==========================================================\n")
        f.write("*Element, type=U1, elset=PHASE_QUADS\n")
        for eid in sorted(mesh["elements"].keys()):
            conn = mesh["elements"][eid]
            f.write(f"{eid}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}\n")

        f.write("** ==========================================================\n")
        f.write(f"** LAYER 2: Mechanical UEL Elements (U2: DOFs 1,2, {n_phys_elems+1}..{2*n_phys_elems})\n")
        f.write("** ==========================================================\n")
        f.write("*Element, type=U2, elset=MECH_QUADS\n")
        for eid in sorted(mesh["elements"].keys()):
            conn = mesh["elements"][eid]
            f.write(f"{eid + n_phys_elems}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}\n")

        f.write("** ==========================================================\n")
        f.write(f"** LAYER 3: Visualization Overlay Elements (CPE4, {2*n_phys_elems+1}..{3*n_phys_elems})\n")
        f.write("** ==========================================================\n")
        f.write("*Element, type=CPE4, elset=umatelem\n")
        for eid in sorted(mesh["elements"].keys()):
            conn = mesh["elements"][eid]
            f.write(f"{eid + 2*n_phys_elems}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}\n")

        # Element Properties
        f.write("** ==========================================================\n")
        f.write("** ELEMENT PROPERTIES\n")
        f.write("** ==========================================================\n")
        f.write("*UEL PROPERTY, ELSET=PHASE_QUADS\n")
        f.write(f"0.0075, 0.0027, 210.0, 0.3, 1.0e-07, {n_phys_elems}\n")
        f.write("*UEL PROPERTY, ELSET=MECH_QUADS\n")
        f.write(f"0.0075, 0.0027, 210.0, 0.3, 1.0e-07, {n_phys_elems}\n")
        f.write("*Solid Section, elset=umatelem, material=VIS_MATERIAL\n")
        f.write("1.0\n")
        f.write("*Material, name=VIS_MATERIAL\n")
        f.write("*User Material, constants=3\n")
        f.write(f"210.0, 0.3, {n_phys_elems}\n")
        f.write("*Depvar\n")
        f.write("20\n")

        # Node sets
        f.write("** ==========================================================\n")
        f.write("** NODE SETS\n")
        f.write("** ==========================================================\n")
        # N_TOP
        f.write("*Nset, nset=N_TOP\n")
        for i in range(0, len(mesh["top_nodes"]), 10):
            f.write(", ".join(str(n) for n in mesh["top_nodes"][i:i+10]) + "\n")
        # N_BOTTOM
        f.write("*Nset, nset=N_BOTTOM\n")
        for i in range(0, len(mesh["bottom_nodes"]), 10):
            f.write(", ".join(str(n) for n in mesh["bottom_nodes"][i:i+10]) + "\n")
        # N_PIN
        f.write("*Nset, nset=N_PIN\n")
        f.write(f"{mesh['pin_nodes'][0]}\n")
        # N_RP
        f.write("*Nset, nset=N_RP\n")
        f.write(f"{mesh['rp_nid']}\n")

        # Kinematic Coupling Equations: tie all top nodes to N_RP in DOF 2
        f.write("** ==========================================================\n")
        f.write("** EQUATIONS: Tie all top nodes to RP in DOF 2 (u_y)\n")
        f.write("** ==========================================================\n")
        for n in mesh["top_nodes"]:
            f.write("*EQUATION\n")
            f.write("2\n")
            f.write(f"{n}, 2, 1.0, {mesh['rp_nid']}, 2, -1.0\n")

        # Initial boundary conditions
        f.write("** ==========================================================\n")
        f.write("** INITIAL BOUNDARY CONDITIONS\n")
        f.write("** ==========================================================\n")
        f.write("*Boundary\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_TOP, 1, 1, 0.0\n")
        f.write("N_RP, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, 0.0\n")

        # STEP 1: Monotonic loading to Frame 77 landing
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
        f.write("*Element Output, elset=umatelem\n")
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
        f.write("*Element Output, elset=umatelem\n")
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
        f.write(f"#PBS -N M1_C3_P{PACKAGE_NUM}_DON\n")
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
        f.write(f'echo "Starting Abaqus/Standard 2023 Continuous C3-Fine Donor ({n_phys_elems} Quads, h=0.81 um)..."\n')
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
            f"Authentic Mode-I candidate C3-Fine continuous donor simulation with companion UMAT visualization "
            f"and *NODE PRINT monitoring ({n_phys_elems} quads, h=0.81 um, {n_phys_nodes} nodes, f42_mixed_uel.for) targeting exact "
            f"Frame-77 displacement (u = {TARGET_DISP_STEP1_MM:.10f} mm) to provide a narrower mesh-jump donor candidate "
            "for testing whether reduced resolution ratio lowers raw Stage C1-1 energy continuity mismatch below 2%."
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
        "batch_name": f"MODE1_PACKAGE{PACKAGE_NUM}_C3_FINE_DONOR",
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
                "purpose": f"Abaqus 2023 Candidate C3-Fine continuous donor calculation ({n_phys_elems} quads, h=0.81 um, {n_phys_nodes} nodes, f42_mixed_uel.for) with *NODE PRINT to capture authentic nodal phase field (DOF 3) at Frame-77 for reduced mesh-jump state transfer",
                "input": f"{MODEL_NAME}.inp",
                "datacheck": f"{MODEL_NAME}_DC.dat",
                "pbs": f"submit_{MODEL_NAME}.pbs",
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "depends_on": [],
                "command": qsub_cmd,
                "command_sha256": cmd_sha256,
            }
        ],
        "acceptance": {
            MODEL_NAME: (
                "Exit code 0; monotonic damage growth and fracture energy dissipation; "
                f"Step 1 completes at exact target displacement u = {TARGET_DISP_STEP1_MM:.16f} mm "
                "with authentic nodal phase field (DOF 3) recorded in .dat file via *NODE PRINT; "
                f"Step 2 continues through u = {TARGET_DISP_STEP2_MM:.4f} mm."
            )
        }
    }
    with open(auth_path, "w", newline="\n") as f:
        json.dump(auth_data, f, indent=2)
    print(f"Generated authorization: {auth_path.name}")

    return {
        "inp_path": inp_path,
        "manifest_path": manifest_path,
        "auth_path": auth_path,
        "pbs_path": pbs_path,
        "files_map": files_map
    }


if __name__ == "__main__":
    build_package146()
