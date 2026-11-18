# -*- coding: utf-8 -*-
"""
scripts/remeshing/prepare_f1855_lpanel_fracture_job1.py
======================================================
Prepares the authentic coarse phase-field Job-1 simulation on the L-panel geometry
for Task F1855:
1. Validates PK_F1846_LPANEL_COARSE.inp (340 physical elements: 328 CPE4, 12 CPE3).
2. Builds 3-layer Method A deck PK_F1855_LPANEL_COARSE_JOB1.inp (1,020 layered elements)
   with Step-1 (u2=0.1 mm) and Step-2 (u2=0.2 mm), requesting native S, MISESERI,
   MISESAVG, EVOL, E, and SDV on the companion set.
3. Verifies line-wrapping compliance on all *NSET cards (<=16 entries per line).
4. Stages models/pandey_kumar_mode1/284_f1855_lpanel_fracture_job1/.
5. Copies f42_native_miseseri_interface_v1.for (verifying SHA E5C98B6F...).
6. Prepares dual-channel PBS execution script submit_f1855_lpanel_job1.pbs.
7. Writes staging receipt PK_F1855_LPANEL_JOB1_RECEIPT.json.
"""
from __future__ import print_function
import os
import sys
import shutil
import hashlib
import json
import math

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
STAGING_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "284_f1855_lpanel_fracture_job1")

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

from scripts.remeshing.reusable_2d_adaptive_framework import MeshQualityAuditEngine

def parse_physical_inp(inp_path):
    return MeshQualityAuditEngine.parse_physical_inp(inp_path)

def build_3layer_lpanel_deck(nodes, quad_elems, tri_elems, config, dst_inp, job_name):
    num_phys_elems = len(quad_elems) + len(tri_elems)
    num_nodes = len(nodes)
    rp_nid = 999999
    rp_coord = (50.0, 100.0)

    # Identify boundary nodes
    tol = 1e-4
    bottom_nodes = []
    top_nodes = []
    pin_node = None
    min_dist_pin = 1e9

    for nid, (x, y) in nodes.items():
        if abs(y) < tol:
            bottom_nodes.append(nid)
        if abs(y - 100.0) < tol:
            top_nodes.append(nid)
        dist = math.hypot(x, y)
        if dist < min_dist_pin:
            min_dist_pin = dist
            pin_node = nid

    with open(dst_inp, "w") as f:
        f.write("** ==========================================================\n")
        f.write("** Abaqus Input Deck - 3-Layer Method A Phase-Field Model\n")
        f.write("** Benchmark: %s\n" % config.get("benchmark_name", "L-Shaped Panel"))
        f.write("** Task: F1855-LPANEL-FRACTURE-JOB1\n")
        f.write("** Subroutine: f42_native_miseseri_interface_v1.for\n")
        f.write("** ==========================================================\n")
        f.write("*HEADING\nMethod A Coarse Phase-Field Model: %s\n" % job_name)
        f.write("*PREPRINT, ECHO=NO, MODEL=NO, HISTORY=NO\n\n")

        # Nodes
        f.write("** ----------------------------------------------------------\n")
        f.write("** NODES\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*NODE, NSET=ALLNODES\n")
        for nid in sorted(nodes.keys()):
            coord = nodes[nid]
            f.write("%d, %.8e, %.8e\n" % (nid, coord[0], coord[1]))
        f.write("%d, %.8e, %.8e\n" % (rp_nid, rp_coord[0], rp_coord[1]))

        # Layer 1: Phase-Field UEL
        f.write("** ----------------------------------------------------------\n")
        f.write("** LAYER 1: Phase-Field User Elements (DOF 3)\n")
        f.write("** ----------------------------------------------------------\n")
        if quad_elems:
            f.write("*USER ELEMENT, NODES=4, TYPE=U1, PROPERTIES=6, COORDINATES=2, VARIABLES=18\n3\n")
            f.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                f.write("%d, %d, %d, %d, %d\n" % (eid, c[0], c[1], c[2], c[3]))

        if tri_elems:
            f.write("*USER ELEMENT, NODES=3, TYPE=U3, PROPERTIES=6, COORDINATES=2, VARIABLES=18\n3\n")
            f.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                f.write("%d, %d, %d, %d\n" % (eid, c[0], c[1], c[2]))

        # Layer 2: Mechanical Displacement UEL
        f.write("** ----------------------------------------------------------\n")
        f.write("** LAYER 2: Mechanical Displacement User Elements (DOF 1, 2)\n")
        f.write("** ----------------------------------------------------------\n")
        offset_disp = num_phys_elems
        if quad_elems:
            f.write("*USER ELEMENT, NODES=4, TYPE=U2, PROPERTIES=6, COORDINATES=2, VARIABLES=18\n1, 2\n")
            f.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                f.write("%d, %d, %d, %d, %d\n" % (eid + offset_disp, c[0], c[1], c[2], c[3]))

        if tri_elems:
            f.write("*USER ELEMENT, NODES=3, TYPE=U4, PROPERTIES=6, COORDINATES=2, VARIABLES=18\n1, 2\n")
            f.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                f.write("%d, %d, %d, %d\n" % (eid + offset_disp, c[0], c[1], c[2]))

        # Layer 3: Companion Continuum Elements
        f.write("** ----------------------------------------------------------\n")
        f.write("** LAYER 3: Companion Visualizer Elements (CPE4 / CPE3)\n")
        f.write("** ----------------------------------------------------------\n")
        offset_vis = 2 * num_phys_elems
        if quad_elems:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=umatelem_quad\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                f.write("%d, %d, %d, %d, %d\n" % (eid + offset_vis, c[0], c[1], c[2], c[3]))

        if tri_elems:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=umatelem_tri\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                f.write("%d, %d, %d, %d\n" % (eid + offset_vis, c[0], c[1], c[2]))

        # Element sets
        f.write("*ELSET, ELSET=All_elem\n")
        if quad_elems and tri_elems:
            f.write("umatelem_quad, umatelem_tri\n")
        elif quad_elems:
            f.write("umatelem_quad\n")
        else:
            f.write("umatelem_tri\n")
        f.write("*ELSET, ELSET=umatelem\nAll_elem\n")

        # Boundary node sets (strictly wrapped <= 10 items per line)
        f.write("** ----------------------------------------------------------\n")
        f.write("** BOUNDARY NODE SETS\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*NSET, NSET=N_BOTTOM\n")
        for i, nid in enumerate(sorted(bottom_nodes)):
            f.write("%d%s" % (nid, ",\n" if (i+1)%10==0 or i==len(bottom_nodes)-1 else ", "))
        f.write("\n*NSET, NSET=N_TOP\n")
        for i, nid in enumerate(sorted(top_nodes)):
            f.write("%d%s" % (nid, ",\n" if (i+1)%10==0 or i==len(top_nodes)-1 else ", "))
        f.write("\n*NSET, NSET=N_PIN\n%d\n" % (pin_node if pin_node else 1))
        f.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)

        # UEL Properties
        mat = config.get("material", {})
        E_mpa = float(mat.get("youngs_modulus_mpa", 210000.0))
        E_kn = E_mpa / 1000.0  # 210.0 kN/mm^2
        nu = float(mat.get("poisson_ratio", 0.3))
        l0 = float(mat.get("length_scale_l0_mm", 1.0))
        Gc = float(mat.get("gc_kn_per_mm", 0.0027))
        k_res = float(mat.get("residual_stiffness_k", 1e-7))
        num_phys_f = float(num_phys_elems)

        if quad_elems:
            f.write("*UEL PROPERTY, ELSET=PHASE_QUAD\n")
            f.write("%.4f, %.4f, %.1f, %.2f, %.1e, %.1f\n" % (l0, Gc, E_kn, nu, k_res, num_phys_f))
            f.write("*UEL PROPERTY, ELSET=DISP_QUAD\n")
            f.write("%.4f, %.4f, %.1f, %.2f, %.1e, %.1f\n" % (l0, Gc, E_kn, nu, k_res, num_phys_f))

        if tri_elems:
            f.write("*UEL PROPERTY, ELSET=PHASE_TRI\n")
            f.write("%.4f, %.4f, %.1f, %.2f, %.1e, %.1f\n" % (l0, Gc, E_kn, nu, k_res, num_phys_f))
            f.write("*UEL PROPERTY, ELSET=DISP_TRI\n")
            f.write("%.4f, %.4f, %.1f, %.2f, %.1e, %.1f\n" % (l0, Gc, E_kn, nu, k_res, num_phys_f))

        # Companion Section & Material
        f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT\n1.0\n")
        f.write("*MATERIAL, NAME=DUMMY_MAT\n")
        f.write("*USER MATERIAL, CONSTANTS=3\n")
        f.write("%.1f, %.2f, %.1f\n" % (E_kn, nu, num_phys_f))
        f.write("*DEPVAR\n20\n")

        # Tie Equations (top edge tied to RP in DOF 2)
        f.write("** ----------------------------------------------------------\n")
        f.write("** EQUATIONS (Rigid top tensile pull tied to RP in DOF 2)\n")
        f.write("** ----------------------------------------------------------\n")
        for nid in sorted(top_nodes):
            f.write("*EQUATION\n2\n")
            f.write("%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_nid))

        # Loading values
        load = config.get("loading", {})
        step1_u2 = float(load.get("step1_precritical_u2", 0.1))
        step2_u2 = float(load.get("step2_fracture_u2", 0.2))

        # Step 1
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 1: Linear Loading to u = %.4f mm\n" % step1_u2)
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=10000\n")
        f.write("*STATIC\n0.02, 1.0, 1.0e-7, 0.02\n")
        f.write("*BOUNDARY\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_TOP, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, %.4f\n" % step1_u2)
        f.write("*RESTART, WRITE, FREQUENCY=1\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=umatelem\nMISESERI, MISESAVG, EVOL, S, E, SDV\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

        # Step 2
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 2: Fracture Propagation to u = %.4f mm\n" % step2_u2)
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=20000\n")
        f.write("*STATIC\n0.002, 1.0, 1.0e-8, 0.002\n")
        f.write("*BOUNDARY\n")
        f.write("N_RP, 2, 2, %.4f\n" % step2_u2)
        f.write("*RESTART, WRITE, FREQUENCY=1\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=umatelem\nMISESERI, MISESAVG, EVOL, S, E, SDV\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

    return {
        "deck_path": dst_inp,
        "physical_elements": num_phys_elems,
        "quad_elements": len(quad_elems),
        "tri_elements": len(tri_elems),
        "layered_elements": 3 * num_phys_elems,
        "nodes": num_nodes,
        "total_nodes": num_nodes + 1,
        "top_nodes": len(top_nodes),
        "bottom_nodes": len(bottom_nodes)
    }

def main():
    print("=" * 80)
    print("TASK F1855: PREPARING L-PANEL COARSE FRACTURE JOB-1 STAGING")
    print("=" * 80)

    if not os.path.exists(STAGING_DIR):
        os.makedirs(STAGING_DIR)

    # 1. Validate inputs
    src_coarse_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "276_f1846_generalized_framework", "l_panel", "PK_F1846_LPANEL_COARSE.inp")
    assert os.path.exists(src_coarse_inp), "Missing coarse mesh: %s" % src_coarse_inp
    coarse_sha = sha256_file(src_coarse_inp)
    print("Source coarse mesh: %s (SHA: %s)" % (src_coarse_inp, coarse_sha))

    config_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1846_unfamiliar_l_panel.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    print("Loaded config: %s" % config_path)

    # 2. Build 3-layer deck
    job_name = "PK_F1855_LPANEL_COARSE_JOB1"
    dst_inp = os.path.join(STAGING_DIR, job_name + ".inp")

    nodes, quad_elems, tri_elems = parse_physical_inp(src_coarse_inp)
    assert len(nodes) == 375, "Expected 375 nodes, found %d" % len(nodes)
    assert len(quad_elems) == 328, "Expected 328 quads, found %d" % len(quad_elems)
    assert len(tri_elems) == 12, "Expected 12 tris, found %d" % len(tri_elems)

    deck_info = build_3layer_lpanel_deck(nodes, quad_elems, tri_elems, config, dst_inp, job_name)
    inp_sha = sha256_file(dst_inp)
    print("Generated 3-layer deck: %s" % dst_inp)
    print("  SHA-256:            %s" % inp_sha)
    print("  Physical elements:  %d (328 CPE4 + 12 CPE3)" % deck_info["physical_elements"])
    print("  Layered elements:   %d" % deck_info["layered_elements"])
    print("  Nodes:              %d (+ RP 999999 = %d)" % (deck_info["nodes"], deck_info["total_nodes"]))

    # Verify NSET line wrapping
    with open(dst_inp, "r") as f:
        in_nset = False
        long_nsets = []
        for i, line in enumerate(f):
            s = line.strip()
            if s.startswith("*"):
                in_nset = s.upper().startswith("*NSET")
                continue
            if in_nset:
                parts = [p.strip() for p in s.split(",") if p.strip()]
                if len(parts) > 16:
                    long_nsets.append((i+1, len(parts)))
    print("NSET violations (>16 entries): %d (100%% line-wrapping PASS)" % len(long_nsets))
    assert len(long_nsets) == 0, "Line wrapping violation found!"

    # 3. Source Fortran subroutine: f42_native_miseseri_interface_v1.for
    src_for = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "271_f1830_stress_output_interface", "f42_native_miseseri_interface_v1.for")
    assert os.path.exists(src_for), "Missing src for: %s" % src_for
    src_for_sha = sha256_file(src_for)
    expected_for_sha = "E5C98B6F601B1CD586571F8E24F357D15ABBD1C5D5487B52903BA249734279B2"
    assert src_for_sha == expected_for_sha, "Subroutine hash mismatch! Found %s, expected %s" % (src_for_sha, expected_for_sha)
    print("Source Subroutine SHA-256 verified: %s" % src_for_sha)

    tgt_for = os.path.join(STAGING_DIR, "f42_native_miseseri_interface_v1.for")
    shutil.copyfile(src_for, tgt_for)
    print("Staged Subroutine: %s" % tgt_for)

    # Also verify frozen UEL exists bitwise
    frozen_uel = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    frozen_uel_sha = sha256_file(frozen_uel)
    expected_uel_sha = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert frozen_uel_sha == expected_uel_sha, "Frozen UEL hash mismatch!"
    print("Frozen Production UEL SHA-256 verified: %s" % frozen_uel_sha)

    # 4. Copy job_notifications.sh
    src_notif = os.path.join(REPO_ROOT, "scripts", "hpc", "notifications", "job_notifications.sh")
    tgt_notif = os.path.join(STAGING_DIR, "job_notifications.sh")
    if os.path.exists(src_notif):
        shutil.copyfile(src_notif, tgt_notif)
    else:
        shutil.copyfile(os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "277_f1838_case2_native_pilot", "job_notifications.sh"), tgt_notif)
    print("Staged Notification Script: %s" % tgt_notif)

    # 5. Create PBS Execution Script
    remote_dir = "/scratch9/pr21vyci/runs/f1855_lpanel_fracture_job1"
    pbs_content = """#!/bin/bash
#PBS -N F1855_LPANEL_J1
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=04:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o %s/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="%s"
cd "${RUN_DIR}"

export JOB_NAME="%s"
export NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-${HOME}/.config/adaptive-remeshing/notifications.env}"
source "${RUN_DIR}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

JOB_NAME="%s"
INP_NAME="%s.inp"
USER_SUB="f42_native_miseseri_interface_v1.for"

test ! -e "${JOB_NAME}.lck"

echo "Starting Abaqus/Standard 2023 L-Panel Coarse Fracture Job-1 Simulation..."
abaqus job="${JOB_NAME}" input="${INP_NAME}" user="${USER_SUB}" cpus=1 interactive
EXIT_CODE=$?

echo "Abaqus Finished with Exit Code: ${EXIT_CODE}"
exit ${EXIT_CODE}
""" % (remote_dir, remote_dir, job_name, job_name, job_name)

    tgt_pbs = os.path.join(STAGING_DIR, "submit_f1855_lpanel_job1.pbs")
    with open(tgt_pbs, "wb") as f:
        f.write(pbs_content.replace("\r\n", "\n").encode("utf-8"))
    tgt_pbs_sha = sha256_file(tgt_pbs)
    print("Staged PBS Script: %s (SHA: %s)" % (tgt_pbs, tgt_pbs_sha))

    # 6. Write Master Staging Receipt
    receipt = {
        "task_id": "F1855-LPANEL-FRACTURE-JOB1",
        "benchmark": "unfamiliar_l_panel",
        "job_name": job_name,
        "remote_run_dir": remote_dir,
        "inputs": {
            "source_coarse_mesh": {
                "path": src_coarse_inp,
                "sha256": coarse_sha,
                "physical_elements": deck_info["physical_elements"],
                "quads": deck_info["quad_elements"],
                "tris": deck_info["tri_elements"],
                "nodes": deck_info["nodes"]
            },
            "config": {
                "path": config_path,
                "step1_u2": 0.1,
                "step2_u2": 0.2
            },
            "frozen_uel": {
                "path": frozen_uel,
                "sha256": frozen_uel_sha
            },
            "native_interface": {
                "path": src_for,
                "sha256": src_for_sha,
                "bytes": 33042
            }
        },
        "staged_artifacts": {
            "input_deck": {
                "path": dst_inp,
                "filename": os.path.basename(dst_inp),
                "sha256": inp_sha,
                "size_bytes": os.path.getsize(dst_inp),
                "physical_elements": deck_info["physical_elements"],
                "layered_elements": deck_info["layered_elements"],
                "total_nodes": deck_info["total_nodes"]
            },
            "user_subroutine": {
                "path": tgt_for,
                "filename": os.path.basename(tgt_for),
                "sha256": src_for_sha
            },
            "pbs_script": {
                "path": tgt_pbs,
                "filename": os.path.basename(tgt_pbs),
                "sha256": tgt_pbs_sha,
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "mem": "16gb",
                "walltime": "04:00:00"
            }
        }
    }

    receipt_path = os.path.join(STAGING_DIR, "PK_F1855_LPANEL_JOB1_RECEIPT.json")
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)
    print("Master Staging Receipt: %s" % receipt_path)
    print("=" * 80)
    print("TASK F1855 STAGING PREPARATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
