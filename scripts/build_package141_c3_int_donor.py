# -*- coding: utf-8 -*-
"""
build_package141_c3_int_donor.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Generates Package 141: Authentic Mode-I Candidate C3-Intermediate Monotonic Donor Simulation
(2,484 quads, h_tip = 1.2 um, 2,610 nodes, f42_mixed_uel.for).
Targets exact Frame-77 displacement (u = 0.0018003125 mm) via two-step continuous loading.
"""

from __future__ import print_function, division
import os
import sys
import shutil
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()

def main():
    pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/141_c3_int_donor_monotonic"
    pkg_dir.mkdir(parents=True, exist_ok=True)

    src_inp = REPO_ROOT / "models/pandey_kumar_mode1/116_r1_c3_int_inc79_direct_transfer/M1_C3_INT_R1_INC79_DIRECT_TRANSFER.inp"
    
    # 1. Parse nodes, elements, nsets, and equations from source C3-Int deck
    nodes = []
    elements = []
    n_top = []
    n_bottom = []
    n_pin = []
    equations = []

    state = None
    with open(src_inp, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            u = l.upper()
            if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                state = "NODE"
                continue
            elif u.startswith("*ELEMENT") and "TYPE=U1" in u:
                state = "ELEM"
                continue
            elif u.startswith("*NSET, NSET=N_TOP"):
                state = "NSET_TOP"
                continue
            elif u.startswith("*NSET, NSET=N_BOTTOM"):
                state = "NSET_BOTTOM"
                continue
            elif u.startswith("*NSET, NSET=N_PIN"):
                state = "NSET_PIN"
                continue
            elif u.startswith("*EQUATION"):
                state = "EQUATION"
                continue
            elif u.startswith("*"):
                state = None
                continue

            if state == "NODE":
                nodes.append(l)
            elif state == "ELEM":
                elements.append(l)
            elif state == "NSET_TOP":
                n_top.extend([int(x.strip()) for x in l.split(",") if x.strip().isdigit()])
            elif state == "NSET_BOTTOM":
                n_bottom.extend([int(x.strip()) for x in l.split(",") if x.strip().isdigit()])
            elif state == "NSET_PIN":
                n_pin.extend([int(x.strip()) for x in l.split(",") if x.strip().isdigit()])
            elif state == "EQUATION":
                equations.append(l)

    n_elems = len(elements)
    print(f"Parsed C3-Int mesh: {len(nodes)} nodes (including RP), {n_elems} quads")
    print(f"Node sets: N_TOP={len(n_top)}, N_BOTTOM={len(n_bottom)}, N_PIN={len(n_pin)}")

    # 2. Build 3-layer input deck
    inp_lines = [
        "*Heading",
        "** Candidate C3-Intermediate Continuous Monotonic Mode-I Donor Simulation",
        f"** Elements: {n_elems} Quads, Nodes: {len(nodes) - 1} physical + RP 999999",
        "** Geometry: 0.1 x 0.1 mm, sharp slit at y=0.05 mm, a0=0.04 mm",
        "** Parameters: E=210.0 kN/mm^2, nu=0.3, Gc=0.0027 kN/mm, l0=0.0075 mm, k=1e-07",
        "** Two-step continuous loading: Step 1 lands exactly on Frame 77 (u = 0.0018003125 mm)",
        "*Preprint, echo=NO, model=NO, history=NO, contact=NO",
        "** ==========================================================",
        f"** USER ELEMENTS (Phase U1: 1..{n_elems}, Mech U2: {n_elems+1}..{2*n_elems})",
        "** ==========================================================",
        "*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM",
        "3",
        "*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM",
        "1, 2",
        "** ==========================================================",
        f"** NODES ({len(nodes) - 1} physical nodes + RP 999999)",
        "** ==========================================================",
        "*Node",
    ]
    inp_lines.extend(nodes)

    # Layer 1: Phase field elements
    inp_lines.append("** ==========================================================")
    inp_lines.append(f"** LAYER 1: Phase-Field UEL Elements (U1: DOF 3, 1..{n_elems})")
    inp_lines.append("** ==========================================================")
    inp_lines.append("*Element, type=U1, elset=PHASE_QUADS")
    for l in elements:
        inp_lines.append(l)

    # Layer 2: Mechanical elements
    inp_lines.append("** ==========================================================")
    inp_lines.append(f"** LAYER 2: Mechanical UEL Elements (U2: DOFs 1,2, {n_elems+1}..{2*n_elems})")
    inp_lines.append("** ==========================================================")
    inp_lines.append("*Element, type=U2, elset=MECH_QUADS")
    for l in elements:
        parts = [x.strip() for x in l.split(",")]
        eid = int(parts[0]) + n_elems
        inp_lines.append(f"{eid}, " + ", ".join(parts[1:]))

    # Layer 3: Companion overlay elements for visualization
    inp_lines.append("** ==========================================================")
    inp_lines.append(f"** LAYER 3: Visualization Overlay Elements (CPE4, {2*n_elems+1}..{3*n_elems})")
    inp_lines.append("** ==========================================================")
    inp_lines.append("*Element, type=CPE4, elset=umatelem")
    for l in elements:
        parts = [x.strip() for x in l.split(",")]
        eid = int(parts[0]) + 2 * n_elems
        inp_lines.append(f"{eid}, " + ", ".join(parts[1:]))

    # Solid section and user material for companion elements
    inp_lines.extend([
        "** ==========================================================",
        "** SOLID SECTION FOR VISUALIZATION OVERLAY",
        "** ==========================================================",
        "*Solid Section, elset=umatelem, material=DUMMY_MAT",
        "1.0,",
        "*Material, name=DUMMY_MAT",
        "*User Material, constants=3",
        f"210.0, 0.3, {n_elems}.0",
        "*Depvar",
        "20",
        "** ==========================================================",
        "** UEL PROPERTIES",
        "** ==========================================================",
        "*UEL PROPERTY, ELSET=PHASE_QUADS",
        f"0.0075, 0.0027, 210.0, 0.3, 1e-07, {n_elems}",
        "*UEL PROPERTY, ELSET=MECH_QUADS",
        f"0.0075, 0.0027, 210.0, 0.3, 1e-07, {n_elems}",
        "** ==========================================================",
        "** NODE SETS & BOUNDARY CONDITIONS",
        "** ==========================================================",
        "*Nset, nset=N_BOTTOM",
    ])
    for i in range(0, len(n_bottom), 16):
        inp_lines.append(", ".join(str(n) for n in n_bottom[i:i + 16]))

    inp_lines.append("*Nset, nset=N_PIN")
    inp_lines.append(", ".join(str(n) for n in n_pin))

    inp_lines.append("*Nset, nset=N_TOP")
    for i in range(0, len(n_top), 16):
        inp_lines.append(", ".join(str(n) for n in n_top[i:i + 16]))

    inp_lines.extend([
        "*Nset, nset=N_RP",
        "999999",
        "** ==========================================================",
        "** EQUATIONS TYING N_TOP TO REFERENCE POINT RP 999999",
        "** ==========================================================",
    ])
    for n in n_top:
        inp_lines.extend([
            "*EQUATION",
            "2",
            f"{n}, 2, 1.0, 999999, 2, -1.0"
        ])

    inp_lines.extend([
        "** ==========================================================",
        "** INITIAL BOUNDARY CONDITIONS",
        "** ==========================================================",
        "*Boundary",
        "N_BOTTOM, 2, 2, 0.0",
        "N_PIN, 1, 1, 0.0",
        "N_RP, 1, 1, 0.0",
        "N_RP, 2, 2, 0.0",
        "** ==========================================================",
        "** STEP 1: Monotonic Loading to Frame 77 (u = 0.0018003125 mm)",
        "** ==========================================================",
        "*Step, name=Step-1, nlgeom=NO, inc=2000",
        "*Static",
        "1.0e-3, 0.36006251, 1.0e-8, 5.0e-3",
        "*Boundary",
        "N_RP, 2, 2, 0.0018003125442191958",
        "** Output requests",
        "*Output, field, frequency=1",
        "*Node Output",
        "U, RF",
        "*Element Output, elset=umatelem",
        "SDV, S, E",
        "*Output, history, frequency=1",
        "*Node Output, nset=N_RP",
        "U2, RF2",
        "*Energy Output",
        "ALLSE, ALLWK",
        "*Restart, write, frequency=1",
        "*End Step",
        "** ==========================================================",
        "** STEP 2: Monotonic Continuation through u = 0.0020 mm",
        "** ==========================================================",
        "*Step, name=Step-2, nlgeom=NO, inc=1000",
        "*Static",
        "1.0e-3, 0.03993749, 1.0e-8, 5.0e-3",
        "*Boundary",
        "N_RP, 2, 2, 0.0020000000000000000",
        "** Output requests",
        "*Output, field, frequency=1",
        "*Node Output",
        "U, RF",
        "*Element Output, elset=umatelem",
        "SDV, S, E",
        "*Output, history, frequency=1",
        "*Node Output, nset=N_RP",
        "U2, RF2",
        "*Energy Output",
        "ALLSE, ALLWK",
        "*Restart, write, frequency=1",
        "*End Step"
    ])

    out_inp = pkg_dir / "M1_C3_INT_DONOR_MONOTONIC.inp"
    with open(out_inp, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(inp_lines) + "\n")
    print(f"Generated input deck: {out_inp}")

    # 3. Copy user subroutine and notifications
    src_uel = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/f42_mixed_uel.for"
    dst_uel = pkg_dir / "f42_mixed_uel.for"
    shutil.copy2(str(src_uel), str(dst_uel))
    print(f"Copied frozen UEL: {dst_uel}")

    src_notif = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/job_notifications.sh"
    dst_notif = pkg_dir / "job_notifications.sh"
    shutil.copy2(str(src_notif), str(dst_notif))
    print(f"Copied notifications script: {dst_notif}")

    # 4. Generate PBS submission wrapper
    pbs_content = """#!/bin/bash
#PBS -N M1_C3_INT_DONOR
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_c3_int_donor_monotonic/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_c3_int_donor_monotonic"
cd "${RUN_DIR}"

export JOB_NAME="M1_C3_INT_DONOR_MONOTONIC"
export NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-${HOME}/.config/adaptive-remeshing/notifications.env}"
source "${RUN_DIR}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

JOB_NAME="M1_C3_INT_DONOR_MONOTONIC"
INP_NAME="M1_C3_INT_DONOR_MONOTONIC.inp"
USER_SUB="f42_mixed_uel.for"

test ! -e "${JOB_NAME}.lck"

echo "Starting Abaqus/Standard 2023 Candidate C3-Intermediate Donor (2484 Quads, h=1.2 um)..."
abaqus job="${JOB_NAME}" input="${INP_NAME}" user="${USER_SUB}" cpus=1 interactive
EXIT_CODE=$?

echo "Abaqus Finished with Exit Code: ${EXIT_CODE}"
exit ${EXIT_CODE}
"""
    out_pbs = pkg_dir / "submit_M1_C3_INT_DONOR_MONOTONIC.pbs"
    with open(out_pbs, "w", encoding="utf-8", newline="\n") as f:
        f.write(pbs_content)
    print(f"Generated PBS script: {out_pbs}")

    # 5. Compute SHA256 hashes of all files in package
    inp_hash = compute_sha256(out_inp)
    uel_hash = compute_sha256(dst_uel)
    notif_hash = compute_sha256(dst_notif)
    pbs_hash = compute_sha256(out_pbs)

    # 6. Generate PACKAGE_MANIFEST.json
    manifest_data = {
        "package_number": 141,
        "purpose": (
            "Authentic Mode-I candidate C3-Intermediate continuous donor simulation with companion "
            "UMAT visualization (2484 quads, h=1.2 um, 2610 nodes, f42_mixed_uel.for) targeting exact "
            "Frame-77 displacement (u = 0.0018003125 mm) to supply the authentic donor state for H37."
        ),
        "files": {
            "M1_C3_INT_DONOR_MONOTONIC.inp": inp_hash,
            "f42_mixed_uel.for": uel_hash,
            "job_notifications.sh": notif_hash,
            "submit_M1_C3_INT_DONOR_MONOTONIC.pbs": pbs_hash
        }
    }
    manifest_path = pkg_dir / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    manifest_hash = compute_sha256(manifest_path)
    print(f"Generated package manifest: {manifest_path}")

    # 7. Generate M1_C3_INT_DONOR_MONOTONIC_AUTHORIZATION.json (for Invoke-Mode1Execution.ps1)
    remote_dir = "/scratch9/pr21vyci/runs/mode1_c3_int_donor_monotonic"
    auth_data = {
        "batch_name": "M1_C3_INT_DONOR_MONOTONIC",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "hours_valid": 24,
        "automatic_retry": False,
        "remote_run_dir": remote_dir,
        "files": {
            "M1_C3_INT_DONOR_MONOTONIC.inp": inp_hash,
            "f42_mixed_uel.for": uel_hash,
            "job_notifications.sh": notif_hash,
            "submit_M1_C3_INT_DONOR_MONOTONIC.pbs": pbs_hash,
            "PACKAGE_MANIFEST.json": manifest_hash
        },
        "jobs": [
            {
                "id": "M1_C3_INT_DONOR_MONOTONIC",
                "pbs": "submit_M1_C3_INT_DONOR_MONOTONIC.pbs",
                "command": f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq {remote_dir}/submit_M1_C3_INT_DONOR_MONOTONIC.pbs"',
                "command_sha256": hashlib.sha256(
                    f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq {remote_dir}/submit_M1_C3_INT_DONOR_MONOTONIC.pbs"'.encode("utf-8")
                ).hexdigest(),
                "max_submissions": 1,
                "depends_on": [],
                "purpose": "Abaqus 2023 Candidate C3-Intermediate continuous donor calculation (2484 quads, h=1.2 um, 2610 nodes, f42_mixed_uel.for) targeting exact Frame-77 displacement (u = 0.0018003125 mm)",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "queue": "entry_imfdfkmq",
                "execution": "single-rank serial",
                "input": "M1_C3_INT_DONOR_MONOTONIC.inp",
                "datacheck": "M1_C3_INT_DONOR_MONOTONIC_DC.dat"
            }
        ],
        "acceptance": {
            "M1_C3_INT_DONOR_MONOTONIC": "Exit code 0; monotonic damage growth and fracture energy dissipation; Step 1 completes at exact target displacement u = 0.0018003125 mm with valid displacement, damage, and history fields recorded in ODB via UMAT companion SDVs."
        }
    }
    auth_path = pkg_dir / "M1_C3_INT_DONOR_MONOTONIC_AUTHORIZATION.json"
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump(auth_data, f, indent=2)
    print(f"Generated authorization manifest: {auth_path}")

if __name__ == "__main__":
    main()
