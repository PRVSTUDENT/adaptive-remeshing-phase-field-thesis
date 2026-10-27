#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package121_c3_samemesh_control.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Generates Package 121: C3 Increment-88 Same-Mesh AM Control
Isolates whether Increment-88 nonstationarity is specific to C3->C4 refinement
or also occurs when the identical AM-PDAS algorithm re-equilibrates the authentic
C3 donor without remeshing.
"""

import os
import sys
import json
import csv
import shutil
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
DONOR_INP = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/candidate_donor_h0025_visual.inp"
DONOR_F88_NODAL_CSV = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_frame88/pkg76_frame88_nodal_u.csv"
DONOR_F88_ELEM_CSV = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_frame88/pkg76_frame88_elem_sdv.csv"

OUT_DIR = REPO_ROOT / "models/pandey_kumar_mode1/121_c3_inc88_samemesh_control"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_U_RP = 0.001965107396
TARGET_RF2_DONOR = 185.33544242
TARGET_E_TOT_DONOR = 0.23528295
TARGET_E_ELAS_DONOR = 0.18210416
TARGET_E_FRAC_DONOR = 0.05317879

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest().lower()

def main():
    print("[BUILD-P121] 1. Parsing C3 mesh from donor inp...")
    with open(str(DONOR_INP), "r", encoding="utf-8", errors="ignore") as f:
        inp_lines = [l.strip() for l in f]

    nodes = {}
    for idx, l in enumerate(inp_lines[17:1715]):
        p = l.split(",")
        nodes[int(p[0].strip())] = (float(p[1].strip()), float(p[2].strip()))

    elements = {}
    for idx, l in enumerate(inp_lines[1720:3320]):
        p = l.split(",")
        elements[int(p[0].strip())] = [int(x.strip()) for x in p[1:5]]

    print("[BUILD-P121] Loaded %d nodes, %d elements" % (len(nodes), len(elements)))
    assert len(nodes) == 1698
    assert len(elements) == 1600

    print("[BUILD-P121] 2. Loading authentic Frame 88 ODB CSVs...")
    f88_u = {}
    with open(str(DONOR_F88_NODAL_CSV), "r", encoding="utf-8", errors="ignore") as f:
        rdr = csv.reader(f); next(rdr)
        for r in rdr:
            if r:
                f88_u[int(r[0])] = (float(r[1]), float(r[2]))

    f88_elem_d = {}
    f88_elem_h = {}
    with open(str(DONOR_F88_ELEM_CSV), "r", encoding="utf-8", errors="ignore") as f:
        rdr = csv.reader(f); next(rdr)
        for r in rdr:
            if r:
                eid = int(r[0]); gp = int(r[1])
                if eid not in f88_elem_d:
                    f88_elem_d[eid] = {}
                    f88_elem_h[eid] = {}
                f88_elem_d[eid][gp] = float(r[2])
                f88_elem_h[eid][gp] = float(r[3])

    # Direct authentic checkpoint values (no interpolation)
    donor_inc88_u = f88_u
    donor_elem_d = f88_elem_d
    donor_elem_h = f88_elem_h

    # Nodal damage bounds via element averaging
    donor_nodal_d = {nid: [] for nid in nodes}
    for eid, conn in elements.items():
        d_elem = sum(donor_elem_d[eid][gp] for gp in range(1, 5)) / 4.0
        for n in conn:
            donor_nodal_d[n].append(d_elem)
    donor_node_d = {n: float(sum(vals)/len(vals)) if vals else 0.0 for n, vals in donor_nodal_d.items()}

    print("[BUILD-P121] Max nodal d0: %.6f, Max GP d: %.6f, Max GP h: %.6f" %
          (max(donor_node_d.values()),
           max(donor_elem_d[e][gp] for e in donor_elem_d for gp in donor_elem_d[e]),
           max(donor_elem_h[e][gp] for e in donor_elem_h for gp in donor_elem_h[e])))

    print("[BUILD-P121] 3. Writing initial displacements and lower bounds...")
    u_csv = OUT_DIR / "nodal_displacements_initial.csv"
    with open(str(u_csv), "w", newline="\n") as f:
        f.write("node_id,u1,u2\n")
        for nid in sorted(nodes.keys()):
            u1, u2 = donor_inc88_u[nid]
            f.write("%d,%.10e,%.10e\n" % (nid, u1, u2))

    bounds_csv = OUT_DIR / "d_lower_bounds.csv"
    with open(str(bounds_csv), "w", newline="\n") as f:
        f.write("EID, D0_1, D0_2, D0_3, D0_4, H0_1, H0_2, H0_3, H0_4\n")
        for eid in sorted(elements.keys()):
            conn = elements[eid]
            d0_vals = [donor_node_d[n] for n in conn]
            h0_vals = [donor_elem_h[eid][gp] for gp in range(1, 5)]
            f.write("%d, %.10e, %.10e, %.10e, %.10e, %.10e, %.10e, %.10e, %.10e\n" %
                    (eid, d0_vals[0], d0_vals[1], d0_vals[2], d0_vals[3],
                     h0_vals[0], h0_vals[1], h0_vals[2], h0_vals[3]))

    inc_file = OUT_DIR / "active_set_boundary_cards.inc"
    with open(str(inc_file), "w", newline="\n") as f:
        f.write("** Active-Set Boundary Cards for Phase-Field Lower Bounds\n")
        for nid in sorted(nodes.keys()):
            d0 = donor_node_d[nid]
            f.write("%d, 3, 3, %.10e\n" % (nid, d0))
    shutil.copy(str(inc_file), str(OUT_DIR / "stage_a_all_d0_boundary_cards.inc"))

    print("[BUILD-P121] 4. Identifying boundary sets...")
    top_nodes = [nid for nid, pt in nodes.items() if abs(pt[1] - 0.100) < 1e-6]
    bot_nodes = [nid for nid, pt in nodes.items() if abs(pt[1] - 0.000) < 1e-6]
    pin_node = 1
    top_nodes.sort(); bot_nodes.sort()
    assert len(top_nodes) == 41
    assert len(bot_nodes) == 41

    print("[BUILD-P121] 5. Writing Abaqus input deck M1_C3_INC88_SAMEMESH_CONTROL.inp...")
    inp_path = OUT_DIR / "M1_C3_INC88_SAMEMESH_CONTROL.inp"
    with open(str(inp_path), "w", newline="\n") as f:
        f.write("*Heading\n")
        f.write("** Package 121: C3 Increment-88 Same-Mesh AM Control\n")
        f.write("** Elements: %d Quads, Nodes: %d physical + RP 999999\n" % (len(elements), len(nodes)))
        f.write("** DOFs per node: 1:ux, 2:uy, 3:d (Unified 12-DOF UEL)\n")
        f.write("** Step 1 (C1-2-Inc88): Same-mesh re-equilibration at u_RP = %.10f mm\n" % TARGET_U_RP)
        f.write("*Preprint, echo=NO, model=NO, history=NO, contact=NO\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("** UNIFIED 12-DOF USER ELEMENT (Active DOFs 1, 2, 3)\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=5, VARIABLES=8, UNSYMM\n")
        f.write("1, 2, 3\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("*Node\n")
        for nid in sorted(nodes.keys()):
            pt = nodes[nid]
            f.write("%d, %.10f, %.10f\n" % (nid, pt[0], pt[1]))
        f.write("999999, 0.0500000000, 0.1000000000\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("*Element, type=U1, elset=E_ALL\n")
        for eid in sorted(elements.keys()):
            c = elements[eid]
            f.write("%d, %d, %d, %d, %d\n" % (eid, c[0], c[1], c[2], c[3]))
        f.write("** ----------------------------------------------------------------\n")
        f.write("*Nset, nset=N_ALL, generate\n")
        f.write("1, %d, 1\n" % len(nodes))
        f.write("*Nset, nset=N_RP\n999999\n")
        f.write("*Nset, nset=N_TOP\n")
        for i in range(0, len(top_nodes), 16):
            f.write(", ".join(str(n) for n in top_nodes[i:i+16]) + "\n")
        f.write("*Nset, nset=N_BOTTOM\n")
        for i in range(0, len(bot_nodes), 16):
            f.write(", ".join(str(n) for n in bot_nodes[i:i+16]) + "\n")
        f.write("*Nset, nset=N_PIN\n%d\n" % pin_node)
        f.write("** ----------------------------------------------------------------\n")
        f.write("** UEL PROPERTIES: l0, Gc, E, nu, k_residual\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("*UEL PROPERTY, ELSET=E_ALL\n")
        f.write("0.0075, 0.0027, 210.0, 0.3, 1.0E-07\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("** EQUATIONS TYING N_TOP TO REFERENCE POINT RP 999999\n")
        f.write("** ----------------------------------------------------------------\n")
        for nid in top_nodes:
            f.write("*EQUATION\n2\n%d, 2, 1.0, 999999, 2, -1.0\n" % nid)
        f.write("** ----------------------------------------------------------------\n")
        f.write("** INITIAL BOUNDARY CONDITIONS\n")
        f.write("** ----------------------------------------------------------------\n")
        f.write("*Boundary\nN_BOTTOM, 2, 2, 0.0\nN_PIN, 1, 1, 0.0\nN_RP, 1, 1, 0.0\nN_RP, 2, 2, 0.0\n")
        f.write("** ==========================================================\n")
        f.write("** STEP 1: Same-Mesh Re-Equilibration at u = %.10f mm\n" % TARGET_U_RP)
        f.write("** ==========================================================\n")
        f.write("*Step, name=C1-2-Inc88, nlgeom=NO, inc=200\n*Static\n1.0, 1.0, 1.0E-8, 1.0\n")
        f.write("*Boundary\nN_BOTTOM, 2, 2, 0.0\nN_PIN, 1, 1, 0.0\nN_RP, 1, 1, 0.0\nN_RP, 2, 2, %.10f\n" % TARGET_U_RP)
        f.write("*Include, input=active_set_boundary_cards.inc\n")
        f.write("*Output, field, frequency=1\n*Node Output\nU, RF\n")
        f.write("*Output, history, frequency=1\n*Energy Output\n")
        f.write("ALLSE, ALLIE, ALLWK, ALLFD, ALLCD, ALLVD, ALLPD, ALLAE, ETOTAL\n*End Step\n")

    print("[BUILD-P121] 6. Copying unified UEL and verifying hash...")
    uel_src = REPO_ROOT / "models/pandey_kumar_mode1/117_c3_samemesh_am_control/f42_unified_12dof_active_set_uel.for"
    uel_dst = OUT_DIR / "f42_unified_12dof_active_set_uel.for"
    shutil.copy(str(uel_src), str(uel_dst))
    uel_hash = sha256_file(str(uel_dst)).upper()
    assert uel_hash == "AB0A5A71335ECB445E91EC13A645E280FF3310B561A5E78ABA4A49C8E81DD8AC"

    print("[BUILD-P121] 7. Copying job notifications...")
    shutil.copy(str(REPO_ROOT / "models/pandey_kumar_mode1/117_c3_samemesh_am_control/job_notifications.sh"),
                str(OUT_DIR / "job_notifications.sh"))

    print("[BUILD-P121] 8. Creating driver_c3_inc88_samemesh_control.py...")
    driver_src = REPO_ROOT / "models/pandey_kumar_mode1/117_c3_samemesh_am_control/driver_c3_samemesh_am_control.py"
    with open(str(driver_src), "r") as f:
        driver_text = f.read()

    driver_text = driver_text.replace("c3_samemesh_inc79_control_summary.json", "c3_inc88_samemesh_control_summary.json")
    driver_text = driver_text.replace("PACKAGE_117_C3_SAMEMESH_AM_CONTROL", "PACKAGE_121_C3_INC88_SAMEMESH_CONTROL")
    driver_text = driver_text.replace("M1_C3_SM_CYC%d_MECH", "M1_C3_SM_INC88_CYC%d_MECH")
    driver_text = driver_text.replace("M1_C3_SAMEMESH_AM_CONTROL.inp", "M1_C3_INC88_SAMEMESH_CONTROL.inp")
    driver_text = driver_text.replace("target_rf2_ref = 186.067909", "target_rf2_ref = 185.335442")
    driver_text = driver_text.replace("authentic_donor_energy_mJ = 0.212448", "authentic_donor_energy_mJ = 0.23528295")

    with open(str(OUT_DIR / "driver_c3_inc88_samemesh_control.py"), "w", newline="\n") as f:
        f.write(driver_text)

    print("[BUILD-P121] 9. Creating submit_M1_C3_INC88_SAMEMESH_CONTROL.pbs...")
    pbs_path = OUT_DIR / "submit_M1_C3_INC88_SAMEMESH_CONTROL.pbs"
    with open(str(pbs_path), "w", newline="\n") as f:
        f.write("#!/bin/bash\n")
        f.write("#PBS -N M1_C3_SM_INC88_CONTROL\n")
        f.write("#PBS -q entry_imfdfkmq\n")
        f.write("#PBS -m abe\n")
        f.write("#PBS -M pr21vyci@mailserver.tu-freiberg.de\n")
        f.write("#PBS -l select=1:ncpus=1:mem=16gb\n")
        f.write("#PBS -l walltime=08:00:00\n")
        f.write("#PBS -r n\n")
        f.write("#PBS -o /scratch9/pr21vyci/runs/mode1_c3_inc88_samemesh_control/pbs_execution.log\n")
        f.write("#PBS -e /scratch9/pr21vyci/runs/mode1_c3_inc88_samemesh_control/pbs_error.log\n\n")
        f.write("set -euo pipefail\n\n")
        f.write("RUN_DIR=\"/scratch9/pr21vyci/runs/mode1_c3_inc88_samemesh_control\"\n")
        f.write("cd \"${RUN_DIR}\"\n\n")
        f.write("if [[ \"$(pwd -P)\" =~ ^/home/ ]]; then\n")
        f.write("    echo \"ERROR: Running under /home is strictly prohibited by HPC storage policy.\" >&2\n")
        f.write("    exit 2\n")
        f.write("fi\n\n")
        f.write("export XDG_RUNTIME_DIR=\"/tmp/runtime-pr21vyci\"\n")
        f.write("mkdir -p \"${XDG_RUNTIME_DIR}\" 2>/dev/null || true\n\n")
        f.write("if ! type module >/dev/null 2>&1; then\n")
        f.write("    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true\n")
        f.write("fi\n\n")
        f.write("module purge\n")
        f.write("module load gcc/11.4.0 intel/2024.2.0 abaqus/2023\n")
        f.write("command -v ifort\n\n")
        f.write("export NOTIFICATION_CONFIG=\"${HOME}/.config/adaptive-remeshing/notifications.env\"\n")
        f.write("source ./job_notifications.sh\n")
        f.write("notification_load_config\n\n")
        f.write("notification_install_terminal_trap\n")
        f.write("notify_start\n\n")
        f.write("abaqus python driver_c3_inc88_samemesh_control.py\n")

    print("[BUILD-P121] 10. Creating interactive datacheck script...")
    dc_path = OUT_DIR / "run_c3_inc88_samemesh_datacheck.sh"
    with open(str(dc_path), "w", newline="\n") as f:
        f.write("#!/bin/bash\n")
        f.write("cd /scratch9/pr21vyci/runs/mode1_c3_inc88_samemesh_control\n")
        f.write("if ! type module >/dev/null 2>&1; then\n")
        f.write("    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true\n")
        f.write("fi\n")
        f.write("module purge\n")
        f.write("module load gcc/11.4.0 intel/2024.2.0 abaqus/2023\n")
        f.write("abaqus job=M1_C3_SM_INC88_DC input=M1_C3_INC88_SAMEMESH_CONTROL.inp user=f42_unified_12dof_active_set_uel.for datacheck interactive\n")

    print("[BUILD-P121] 11. Computing file hashes and creating manifests...")
    files_to_hash = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "driver_c3_inc88_samemesh_control.py",
        "f42_unified_12dof_active_set_uel.for",
        "job_notifications.sh",
        "M1_C3_INC88_SAMEMESH_CONTROL.inp",
        "nodal_displacements_initial.csv",
        "run_c3_inc88_samemesh_datacheck.sh",
        "stage_a_all_d0_boundary_cards.inc",
        "submit_M1_C3_INC88_SAMEMESH_CONTROL.pbs"
    ]

    file_hashes = {}
    for f in sorted(files_to_hash):
        file_hashes[f] = sha256_file(str(OUT_DIR / f))

    cmd_str = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c3_inc88_samemesh_control/submit_M1_C3_INC88_SAMEMESH_CONTROL.pbs"'
    cmd_hash = hashlib.sha256(cmd_str.encode("utf-8")).hexdigest().lower()

    job_entry = {
        "id": "M1_C3_SM_INC88_CONTROL",
        "purpose": "Abaqus 2023 C3 Increment-88 Same-Mesh AM Control at u = 0.00196511 mm (1,600 quads, 1,698 nodes, h = 2.5 um, UEL properties [0.0075, 0.0027, 210.0, 0.3, 1.0E-07], up to 15 AM cycles with step-frozen history on original donor mesh to isolate nonstationarity mechanism)",
        "input": "M1_C3_INC88_SAMEMESH_CONTROL.inp",
        "user_subroutine": "f42_unified_12dof_active_set_uel.for",
        "pbs": "submit_M1_C3_INC88_SAMEMESH_CONTROL.pbs",
        "datacheck": "M1_C3_SM_INC88_DC.dat",
        "queue": "entry_imfdfkmq",
        "cpus": 1,
        "memory_gb": 16,
        "walltime_hours": 8,
        "execution": "single-rank serial",
        "max_submissions": 1,
        "command": cmd_str,
        "command_sha256": cmd_hash,
        "depends_on": []
    }

    manifest = {
        "schema": 1,
        "package_name": "121_c3_inc88_samemesh_control",
        "created_at": "2026-10-27T13:30:00Z",
        "files": file_hashes,
        "jobs": [job_entry]
    }

    with open(str(OUT_DIR / "PACKAGE_MANIFEST.json"), "w", newline="\n") as f:
        json.dump(manifest, f, indent=2)

    auth = {
        "schema": 1,
        "adapter": "mode1-experimental-12dof-v1",
        "scientific_scope": "MODE1",
        "technical_stage": "C1-1",
        "batch_name": "MODE1_C3_INC88_SAMEMESH_CONTROL",
        "configuration": "ALTERNATING_MINIMIZATION_SAME_MESH_CONTROL",
        "hypothesis": "Hypothesis H2: At authentic Increment 88, the C3 same-mesh AM-PDAS control achieves stationary equilibrium within the original 15-cycle budget, whereas the refined C4 control did not.",
        "automatic_retry": False,
        "max_submissions": 1,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c3_inc88_samemesh_control",
        "files": file_hashes,
        "jobs": [job_entry],
        "acceptance": {
            "stage_C1_1_same_mesh_control": {
                "u_top_target_mm": TARGET_U_RP,
                "rf2_expected_N": TARGET_RF2_DONOR,
                "rf2_continuity_pct_max": 5.0,
                "energy_continuity_pct_max": 2.0,
                "kkt_violations_max": 0,
                "free_phase_residual_max_kN_mm": 1.0e-06,
                "healing_tolerance": 0,
                "stationarity_delta_d_max": 0.001,
                "stationarity_delta_rf2_max_N": 0.1
            }
        },
        "package_name": "121_c3_inc88_samemesh_control"
    }

    with open(str(OUT_DIR / "M1_C3_INC88_SAMEMESH_AUTHORIZATION.json"), "w", newline="\n") as f:
        json.dump(auth, f, indent=2)

    print("[BUILD-P121] Package 121 created successfully in: %s" % OUT_DIR)

if __name__ == "__main__":
    import traceback
    try:
        main()
    except Exception:
        traceback.print_exc()
