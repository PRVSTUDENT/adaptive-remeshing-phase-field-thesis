#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
map_pkg76_inc88_to_c4.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Maps authentic Increment 88 donor state from Package 76
(u_top = 0.001965107396 mm, RF2 = 185.335442 N, E_tot = 0.23528295 mJ, t = 0.39302149 s)
onto Candidate C4 (4,422 quads, 4,588 physical nodes) nonmatching mesh:
1. Exact shape-function interpolation with slit flank awareness (y=0.050 mm, x <= 0.040 mm).
2. Gauss-point history H and damage lower bound d0 transfer.
3. Generates Abaqus input deck and lower-bound CSV files for Package 120 C4 Increment-88 Holdout Diagnostic.
4. Saves audit JSON to results/validation/c4_inc88_holdout_mapping_audit.json.
"""

from __future__ import print_function, division
import os
import sys
import json
import csv
import math
import hashlib
import shutil
from pathlib import Path
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

GC = 0.0027      # kN/mm (2.7 N/mm)
ELL0 = 0.0075    # mm (7.5 um)
E_MOD = 210.0    # kN/mm^2
NU = 0.3
K_DEGRAD = 1.0e-6

# Plane strain elasticity matrix
LAM = (E_MOD * NU) / ((1.0 + NU) * (1.0 - 2.0 * NU))
MU = E_MOD / (2.0 * (1.0 + NU))
C0 = np.array([
    [LAM + 2.0 * MU, LAM, 0.0],
    [LAM, LAM + 2.0 * MU, 0.0],
    [0.0, 0.0, MU]
])

A_GAUSS = 1.0 / math.sqrt(3.0)
UEL_GP_COORDS = [
    (-A_GAUSS, -A_GAUSS),
    ( A_GAUSS, -A_GAUSS),
    ( A_GAUSS,  A_GAUSS),
    (-A_GAUSS,  A_GAUSS),
]
UEL_WEIGHTS = [1.0, 1.0, 1.0, 1.0]

DONOR_INP = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/candidate_donor_h0025_visual.inp"
DONOR_F88_NODAL_CSV = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_frame88/pkg76_frame88_nodal_u.csv"
DONOR_F88_ELEM_CSV = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_frame88/pkg76_frame88_elem_sdv.csv"

C4_TEMPLATE_INP = REPO_ROOT / "models/pandey_kumar_mode1/115_c4_inc79_direct_transfer/M1_C4_INC79_DIRECT_TRANSFER.inp"
C4_DRIVER_TEMPLATE = REPO_ROOT / "models/pandey_kumar_mode1/115_c4_inc79_direct_transfer/driver_c4_inc79_direct_transfer.py"
OUT_DIR = REPO_ROOT / "models/pandey_kumar_mode1/120_c4_inc88_holdout_diagnostic"
OUT_AUDIT_JSON = REPO_ROOT / "results/validation/c4_inc88_holdout_mapping_audit.json"

TARGET_U_RP = 0.001965107396
TARGET_RF2_DONOR = 185.33544242
TARGET_E_ELAS_DONOR = 0.18210416
TARGET_E_FRAC_DONOR = 0.05317879
TARGET_E_TOT_DONOR = 0.23528295

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def load_mesh_from_inp(inp_path, elem_prefix=None, max_elem_id=None):
    nodes = {}
    elements = {}
    reading = None

    with open(inp_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                    reading = "NODE"
                elif u.startswith("*ELEMENT"):
                    reading = "ELEM"
                elif u.startswith("*"):
                    reading = None
                continue

            if reading == "NODE":
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 3 and parts[0].isdigit():
                    nid = int(parts[0])
                    if nid != 999999:
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = np.array([x, y])

            if reading == "ELEM":
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 5 and parts[0].isdigit():
                    eid = int(parts[0])
                    if max_elem_id and eid > max_elem_id:
                        continue
                    nids = [int(p) for p in parts[1:5]]
                    elements[eid] = nids

    return {"nodes": nodes, "elements": elements}

def shape_functions_2d(xi, eta):
    N = 0.25 * np.array([
        (1.0 - xi) * (1.0 - eta),
        (1.0 + xi) * (1.0 - eta),
        (1.0 + xi) * (1.0 + eta),
        (1.0 - xi) * (1.0 + eta)
    ])
    dNdxi = 0.25 * np.array([
        -(1.0 - eta),
         (1.0 - eta),
         (1.0 + eta),
        -(1.0 + eta)
    ])
    dNdeta = 0.25 * np.array([
        -(1.0 - xi),
        -(1.0 + xi),
         (1.0 + xi),
         (1.0 - xi)
    ])
    return N, dNdxi, dNdeta

def physical_to_parent_quad(x_pt, elem_coords, max_iter=25, tol=1.0e-10):
    xi, eta = 0.0, 0.0
    for _ in range(max_iter):
        N, dNdxi, dNdeta = shape_functions_2d(xi, eta)
        x_calc = np.dot(N, elem_coords)
        res = x_pt - x_calc
        if np.linalg.norm(res) < tol:
            return xi, eta, True
        J = np.vstack([
            np.dot(dNdxi, elem_coords),
            np.dot(dNdeta, elem_coords)
        ])
        detJ = np.linalg.det(J)
        if abs(detJ) < 1.0e-14:
            return xi, eta, False
        J_inv = np.linalg.inv(J)
        delta = np.dot(J_inv, res)
        xi += delta[0]
        eta += delta[1]
        if abs(delta[0]) < tol and abs(delta[1]) < tol:
            return xi, eta, True
    inside = (-1.0001 <= xi <= 1.0001 and -1.0001 <= eta <= 1.0001)
    return xi, eta, inside

def find_containing_element(pt, mesh, slit_flank=None):
    x, y = pt[0], pt[1]
    is_slit_region = (x <= 0.040001 and abs(y - 0.050) < 0.005)
    target_flank = None
    if is_slit_region and slit_flank is not None:
        target_flank = slit_flank

    for eid, conn in mesh["elements"].items():
        coords = np.array([mesh["nodes"][nid] for nid in conn])
        min_x, max_x = np.min(coords[:, 0]), np.max(coords[:, 0])
        min_y, max_y = np.min(coords[:, 1]), np.max(coords[:, 1])

        if not (min_x - 1e-6 <= x <= max_x + 1e-6 and min_y - 1e-6 <= y <= max_y + 1e-6):
            continue

        if target_flank is not None:
            elem_mean_y = np.mean(coords[:, 1])
            elem_flank = "upper" if elem_mean_y >= 0.050 else "lower"
            if elem_flank != target_flank:
                continue

        xi, eta, inside = physical_to_parent_quad(pt, coords)
        if inside and (-1.001 <= xi <= 1.001 and -1.001 <= eta <= 1.001):
            xi = np.clip(xi, -1.0, 1.0)
            eta = np.clip(eta, -1.0, 1.0)
            return eid, xi, eta

    # Fallback nearest search
    best_eid = None
    best_dist = 1.0e9
    best_xi, best_eta = 0.0, 0.0
    for eid, conn in mesh["elements"].items():
        coords = np.array([mesh["nodes"][nid] for nid in conn])
        elem_center = np.mean(coords, axis=0)
        dist = np.linalg.norm(pt - elem_center)
        if dist < best_dist:
            best_dist = dist
            best_eid = eid
            best_xi, best_eta, _ = physical_to_parent_quad(pt, coords)

    best_xi = np.clip(best_xi, -1.0, 1.0)
    best_eta = np.clip(best_eta, -1.0, 1.0)
    return best_eid, best_xi, best_eta

def run_mapping():
    print("=" * 80)
    print("PACKAGE 120: INCREMENT-88 C4 HOLDOUT DIAGNOSTIC MAPPING")
    print("=" * 80)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Donor C3 Mesh
    donor_mesh = load_mesh_from_inp(DONOR_INP, max_elem_id=1600)
    print("Loaded donor C3 mesh: %d nodes, %d elements." %
          (len(donor_mesh["nodes"]), len(donor_mesh["elements"])))

    # 2. Load Receiver C4 Mesh
    c4_mesh = load_mesh_from_inp(C4_TEMPLATE_INP, max_elem_id=4422)
    print("Loaded receiver C4 mesh: %d nodes, %d elements." %
          (len(c4_mesh["nodes"]), len(c4_mesh["elements"])))

    # 3. Load authentic Frame 88 donor states
    donor_f88_u = {}
    with open(DONOR_F88_NODAL_CSV, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            donor_f88_u[int(r["node_id"])] = (float(r["u1"]), float(r["u2"]))
    print("Loaded authentic Frame 88 donor displacements for %d nodes." % len(donor_f88_u))

    donor_elem_d = {}
    donor_elem_h = {}
    with open(DONOR_F88_ELEM_CSV, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            eid = int(r["phys_elem_id"])
            gp = int(r["gp"])
            if eid not in donor_elem_d:
                donor_elem_d[eid] = {}
                donor_elem_h[eid] = {}
            donor_elem_d[eid][gp] = float(r["sdv1_damage"])
            donor_elem_h[eid][gp] = float(r["sdv2_history"])
    print("Loaded authentic Frame 88 element SDVs for %d elements." % len(donor_elem_d))

    # Average nodal damage on donor C3
    donor_nodal_d = {nid: [] for nid in donor_mesh["nodes"]}
    for eid, conn in donor_mesh["elements"].items():
        if eid in donor_elem_d:
            d_elem = np.mean([donor_elem_d[eid][gp] for gp in range(1, 5)])
            for nid in conn:
                donor_nodal_d[nid].append(d_elem)
    donor_nodal_d_avg = {nid: (np.mean(vals) if vals else 0.0) for nid, vals in donor_nodal_d.items()}

    # 4. Map to C4 Nodes
    c4_nodal_u = {}
    c4_nodal_d = {}

    for nid, pt in c4_mesh["nodes"].items():
        flank = None
        if pt[0] <= 0.040001 and abs(pt[1] - 0.050) < 0.005:
            flank = "upper" if pt[1] >= 0.050 else "lower"

        eid, xi, eta = find_containing_element(pt, donor_mesh, slit_flank=flank)
        conn = donor_mesh["elements"][eid]
        N, _, _ = shape_functions_2d(xi, eta)

        u1_interp = sum(N[k] * donor_f88_u[conn[k]][0] for k in range(4))
        u2_interp = sum(N[k] * donor_f88_u[conn[k]][1] for k in range(4))
        d_interp = sum(N[k] * donor_nodal_d_avg[conn[k]] for k in range(4))

        c4_nodal_u[nid] = (u1_interp, u2_interp)
        c4_nodal_d[nid] = max(0.0, min(1.0, d_interp))

    # 5. Map to C4 Element Gauss Points (H0 and d0)
    c4_elem_d0 = {}
    c4_elem_h0 = {}

    for eid, conn in c4_mesh["elements"].items():
        elem_coords = np.array([c4_mesh["nodes"][nid] for nid in conn])
        c4_elem_d0[eid] = []
        c4_elem_h0[eid] = []

        flank = None
        elem_mean_y = np.mean(elem_coords[:, 1])
        elem_mean_x = np.mean(elem_coords[:, 0])
        if elem_mean_x <= 0.040001 and abs(elem_mean_y - 0.050) < 0.005:
            flank = "upper" if elem_mean_y >= 0.050 else "lower"

        for kpt, (xi, eta) in enumerate(UEL_GP_COORDS):
            N, _, _ = shape_functions_2d(xi, eta)
            gp_pt = np.dot(N, elem_coords)

            donor_eid, d_xi, d_eta = find_containing_element(gp_pt, donor_mesh, slit_flank=flank)
            donor_conn = donor_mesh["elements"][donor_eid]

            # Bi-linear interpolation of donor GP history and damage
            h_vals = [donor_elem_h[donor_eid][gp_idx] for gp_idx in range(1, 5)]
            d_vals = [donor_elem_d[donor_eid][gp_idx] for gp_idx in range(1, 5)]
            gp_N, _, _ = shape_functions_2d(d_xi, d_eta)

            h_interp = sum(gp_N[k] * h_vals[k] for k in range(4))
            d_interp = sum(gp_N[k] * d_vals[k] for k in range(4))

            c4_elem_h0[eid].append(max(0.0, h_interp))
            c4_elem_d0[eid].append(max(0.0, min(1.0, d_interp)))

    # 6. Evaluate Initial Mapped C4 Energies
    c4_at2_ef = 0.0
    for eid, conn in c4_mesh["elements"].items():
        elem_coords = np.array([c4_mesh["nodes"][nid] for nid in conn])
        nodal_d = np.array([c4_nodal_d[nid] for nid in conn])

        for kpt, (xi, eta) in enumerate(UEL_GP_COORDS):
            N, dNdxi, dNdeta = shape_functions_2d(xi, eta)
            J = np.vstack([
                np.dot(dNdxi, elem_coords),
                np.dot(dNdeta, elem_coords)
            ])
            detJ = np.linalg.det(J)
            J_inv = np.linalg.inv(J)
            dNdX = np.dot(J_inv, np.vstack([dNdxi, dNdeta]))

            d_val = np.dot(N, nodal_d)
            grad_d = np.dot(dNdX, nodal_d)
            gamma = (d_val**2) / (2.0 * ELL0) + (ELL0 / 2.0) * np.dot(grad_d, grad_d)
            c4_at2_ef += GC * gamma * detJ * UEL_WEIGHTS[kpt]

    c4_frac_mJ = c4_at2_ef # GC in kN/mm, gamma in 1/mm, detJ in mm^2 -> kN*mm = mJ
    print("[PACKAGE 120 MAPPER] Initial Mapped C4 Fracture Energy: %.8f mJ (Donor: %.8f mJ, diff %+.4f%%)" %
          (c4_frac_mJ, TARGET_E_FRAC_DONOR, 100.0 * (c4_frac_mJ - TARGET_E_FRAC_DONOR) / TARGET_E_FRAC_DONOR))

    # 7. Write Package 120 Deliverables
    bounds_csv_path = OUT_DIR / "d_lower_bounds.csv"
    with open(bounds_csv_path, "w") as f:
        f.write("EID, D0_1, D0_2, D0_3, D0_4, H0_1, H0_2, H0_3, H0_4\n")
        for eid in sorted(c4_mesh["elements"].keys()):
            d_vals = c4_elem_d0[eid]
            h_vals = c4_elem_h0[eid]
            f.write("%d, %.10e, %.10e, %.10e, %.10e, %.10e, %.10e, %.10e, %.10e\n" %
                    (eid, d_vals[0], d_vals[1], d_vals[2], d_vals[3],
                     h_vals[0], h_vals[1], h_vals[2], h_vals[3]))
    print("[PACKAGE 120 MAPPER] Written bounds to: %s" % bounds_csv_path)

    stage_a_path = OUT_DIR / "stage_a_all_d0_boundary_cards.inc"
    with open(stage_a_path, "w") as f:
        f.write("** Stage A Initial All-D0 Boundary Cards for Package 120 Holdout Diagnostic\n")
        f.write("** Format: node_id, 3, 3, d_value\n")
        for nid in sorted(c4_mesh["nodes"].keys()):
            f.write("%d, 3, 3, %.8f\n" % (nid, c4_nodal_d[nid]))
    print("[PACKAGE 120 MAPPER] Written Stage A boundary cards to: %s" % stage_a_path)

    active_cards_path = OUT_DIR / "active_set_boundary_cards.inc"
    shutil.copyfile(stage_a_path, active_cards_path)

    disp_csv_path = OUT_DIR / "nodal_displacements_initial.csv"
    with open(disp_csv_path, "w") as f:
        f.write("NID, U1, U2\n")
        for nid in sorted(c4_mesh["nodes"].keys()):
            u1, u2 = c4_nodal_u[nid]
            f.write("%d, %.10e, %.10e\n" % (nid, u1, u2))
    print("[PACKAGE 120 MAPPER] Written initial displacements to: %s" % disp_csv_path)

    # 8. Create Abaqus Deck M1_C4_INC88_HOLDOUT.inp
    with open(C4_TEMPLATE_INP, "r") as f:
        template_text = f.read()

    deck_text = template_text.replace("0.00184250", f"{TARGET_U_RP:.12f}")
    deck_text = deck_text.replace("M1_C4_INC79_DIRECT_TRANSFER", "M1_C4_INC88_HOLDOUT")
    deck_text = deck_text.replace("Package 115", "Package 120")
    deck_path = OUT_DIR / "M1_C4_INC88_HOLDOUT.inp"
    with open(deck_path, "w") as f:
        f.write(deck_text)
    print("[PACKAGE 120 MAPPER] Written deck to: %s" % deck_path)

    # 9. Create AM Driver script driver_c4_inc88_holdout.py
    with open(C4_DRIVER_TEMPLATE, "r") as f:
        driver_text = f.read()

    driver_text = driver_text.replace("PACKAGE_115_C4_INC79_DIRECT_TRANSFER", "PACKAGE_120_C4_INC88_HOLDOUT_DIAGNOSTIC")
    driver_text = driver_text.replace("M1_C4_INC79_DIRECT_TRANSFER", "M1_C4_INC88_HOLDOUT")
    driver_text = driver_text.replace("c4_inc79_direct_transfer_summary.json", "c4_inc88_holdout_summary.json")
    driver_text = driver_text.replace("target_rf2_ref = 185.78857183", f"target_rf2_ref = {TARGET_RF2_DONOR:.6f}")
    driver_text = driver_text.replace("authentic_donor_energy_mJ = 0.212448", f"authentic_donor_energy_mJ = {TARGET_E_TOT_DONOR:.8f}")
    driver_text = driver_text.replace("target_u_top = 0.0018425", f"target_u_top = {TARGET_U_RP:.12f}")
    driver_path = OUT_DIR / "driver_c4_inc88_holdout.py"
    with open(driver_path, "w") as f:
        f.write(driver_text)
    print("[PACKAGE 120 MAPPER] Written driver to: %s" % driver_path)

    # 10. Copy UEL Fortran file and notification script
    src_uel = REPO_ROOT / "models/pandey_kumar_mode1/115_c4_inc79_direct_transfer/f42_unified_12dof_active_set_uel.for"
    dst_uel = OUT_DIR / "f42_unified_12dof_active_set_uel.for"
    shutil.copyfile(src_uel, dst_uel)

    src_notif = REPO_ROOT / "models/pandey_kumar_mode1/115_c4_inc79_direct_transfer/job_notifications.sh"
    dst_notif = OUT_DIR / "job_notifications.sh"
    shutil.copyfile(src_notif, dst_notif)

    # 11. Create PBS Script submit_M1_C4_INC88_HOLDOUT.pbs
    pbs_content = f"""#!/bin/bash
#PBS -N M1_C4_INC88_HOLDOUT
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_c4_inc88_holdout_diagnostic/pbs_execution.log
#PBS -e /scratch9/pr21vyci/runs/mode1_c4_inc88_holdout_diagnostic/pbs_error.log

set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_c4_inc88_holdout_diagnostic"
cd "${{RUN_DIR}}"

if [[ "$(pwd -P)" =~ ^/home/ ]]; then
    echo "ERROR: Running under /home is strictly prohibited by HPC storage policy." >&2
    exit 2
fi

export XDG_RUNTIME_DIR="/tmp/runtime-pr21vyci"
mkdir -p "${{XDG_RUNTIME_DIR}}" 2>/dev/null || true

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

export NOTIFICATION_CONFIG="${{HOME}}/.config/adaptive-remeshing/notifications.env"
source ./job_notifications.sh
notification_load_config

notification_install_terminal_trap
notify_start

abaqus python driver_c4_inc88_holdout.py
"""
    pbs_path = OUT_DIR / "submit_M1_C4_INC88_HOLDOUT.pbs"
    with open(pbs_path, "w", newline="\n") as f:
        f.write(pbs_content)
    print("[PACKAGE 120 MAPPER] Written PBS script to: %s" % pbs_path)

    # 12. Create Datacheck Script run_c4_inc88_holdout_datacheck.sh
    dc_content = """#!/bin/bash
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus datacheck job=M1_C4_INC88_HOLDOUT_DC input=M1_C4_INC88_HOLDOUT.inp user=f42_unified_12dof_active_set_uel.for interactive
"""
    dc_path = OUT_DIR / "run_c4_inc88_holdout_datacheck.sh"
    with open(dc_path, "w", newline="\n") as f:
        f.write(dc_content)
    print("[PACKAGE 120 MAPPER] Written datacheck script to: %s" % dc_path)

    # 13. Create PACKAGE_MANIFEST.json
    manifest_data = {
        "package_name": "PACKAGE_120_C4_INC88_HOLDOUT_DIAGNOSTIC",
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "version": 1,
        "created_date": "2026-10-27",
        "description": "Package 120: Independent Increment-88 C4 Holdout Diagnostic for Mesh-Aware Energy Criterion Validation",
        "mode": "Mode-I",
        "execution_type": "Serial",
        "donor_source": {
            "package": "PACKAGE_76_CANDIDATE_DONOR_H0025_VISUAL",
            "increment": 88,
            "prescribed_u_rp_mm": TARGET_U_RP,
            "rf2_N": TARGET_RF2_DONOR,
            "e_elas_mJ": TARGET_E_ELAS_DONOR,
            "e_frac_mJ": TARGET_E_FRAC_DONOR,
            "e_tot_mJ": TARGET_E_TOT_DONOR
        },
        "receiver_target": {
            "mesh": "Candidate C4",
            "quads": 4422,
            "nodes": 4588,
            "prescribed_u_rp_mm": TARGET_U_RP
        },
        "frozen_prediction_reference": "results/validation/increment_88_frozen_prediction.json",
        "predicted_e_target_mJ": 0.24068166,
        "predicted_delta_e_pct": 2.29456,
        "files": {
            "M1_C4_INC88_HOLDOUT.inp": sha256_file(str(deck_path)),
            "driver_c4_inc88_holdout.py": sha256_file(str(driver_path)),
            "f42_unified_12dof_active_set_uel.for": sha256_file(str(dst_uel)),
            "submit_M1_C4_INC88_HOLDOUT.pbs": sha256_file(str(pbs_path)),
            "d_lower_bounds.csv": sha256_file(str(bounds_csv_path)),
            "active_set_boundary_cards.inc": sha256_file(str(active_cards_path)),
            "stage_a_all_d0_boundary_cards.inc": sha256_file(str(stage_a_path)),
            "nodal_displacements_initial.csv": sha256_file(str(disp_csv_path)),
            "job_notifications.sh": sha256_file(str(dst_notif)),
            "run_c4_inc88_holdout_datacheck.sh": sha256_file(str(dc_path))
        }
    }
    manifest_path = OUT_DIR / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)
    print("[PACKAGE 120 MAPPER] Written manifest to: %s" % manifest_path)

    # 14. Save Audit JSON
    audit_data = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "package": "PACKAGE_120_C4_INC88_HOLDOUT_DIAGNOSTIC",
        "objective": f"Independent Increment-88 Holdout Diagnostic on Candidate C4 (u_RP = {TARGET_U_RP:.8f} mm)",
        "donor_reference": {
            "package": "PACKAGE_76_CANDIDATE_DONOR_H0025_VISUAL",
            "increment": 88,
            "prescribed_u_rp_mm": TARGET_U_RP,
            "rf2_N": TARGET_RF2_DONOR,
            "e_elas_mJ": TARGET_E_ELAS_DONOR,
            "e_frac_mJ": TARGET_E_FRAC_DONOR,
            "e_tot_mJ": TARGET_E_TOT_DONOR
        },
        "receiver_target": {
            "mesh": "Candidate C4",
            "quads": 4422,
            "nodes": 4588,
            "prescribed_u_rp_mm": TARGET_U_RP
        },
        "initial_mapped_energies_mJ": {
            "e_frac_mJ": c4_frac_mJ,
            "delta_frac_pct": 100.0 * (c4_frac_mJ - TARGET_E_FRAC_DONOR) / TARGET_E_FRAC_DONOR
        },
        "frozen_prediction": {
            "predicted_delta_e_mesh_mJ": 0.00539871,
            "predicted_delta_e_mesh_pct": 2.29456,
            "predicted_e_target_mJ": 0.24068166,
            "uncertainty_interval_mJ": [0.24021109, 0.24115223],
            "predeclared_pass_band_pct": 0.25,
            "falsification_threshold_pct": 0.50
        }
    }
    with open(OUT_AUDIT_JSON, "w") as f:
        json.dump(audit_data, f, indent=2)
    print("[PACKAGE 120 MAPPER] Written mapping audit to: %s" % OUT_AUDIT_JSON)

    # 15. Create Authorization JSON
    file_list = [
        "M1_C4_INC88_HOLDOUT.inp",
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "driver_c4_inc88_holdout.py",
        "f42_unified_12dof_active_set_uel.for",
        "job_notifications.sh",
        "nodal_displacements_initial.csv",
        "run_c4_inc88_holdout_datacheck.sh",
        "stage_a_all_d0_boundary_cards.inc",
        "submit_M1_C4_INC88_HOLDOUT.pbs"
    ]
    files_dict = {}
    for fname in file_list:
        fpath = OUT_DIR / fname
        with open(fpath, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().lower()
        files_dict[fname] = h

    remote_dir = "/scratch9/pr21vyci/runs/mode1_c4_inc88_holdout_diagnostic"
    pbs_remote_path = remote_dir + "/submit_M1_C4_INC88_HOLDOUT.pbs"
    command_str = r'powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq ' + pbs_remote_path + '"'
    command_hash = hashlib.sha256(command_str.encode("utf-8")).hexdigest().lower()

    auth_data = {
        "schema": 1,
        "adapter": "mode1-experimental-12dof-v1",
        "scientific_scope": "MODE1",
        "technical_stage": "C1-1",
        "batch_name": "MODE1_C4_INC88_HOLDOUT_DIAGNOSTIC",
        "configuration": "ALTERNATING_MINIMIZATION_SAME_LOAD_HOLDOUT_DIAGNOSTIC",
        "hypothesis": "Second Independent Increment-88 C4 Holdout Diagnostic to test state-dependent mesh-aware energy correction on more strongly localized crack state.",
        "automatic_retry": False,
        "max_submissions": 1,
        "remote_run_dir": remote_dir,
        "files": files_dict,
        "jobs": [
            {
                "id": "M1_C4_INC88_HOLDOUT",
                "purpose": "Abaqus 2023 Candidate C4 Independent Holdout Diagnostic at u = 0.00196511 mm (4,422 quads, 4,588 nodes, up to 15 AM cycles with irreversible history transferred from authentic C3 Increment 88)",
                "input": "M1_C4_INC88_HOLDOUT.inp",
                "user_subroutine": "f42_unified_12dof_active_set_uel.for",
                "pbs": "submit_M1_C4_INC88_HOLDOUT.pbs",
                "datacheck": "M1_C4_INC88_HOLDOUT_DC.dat",
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
        ],
        "acceptance": {
            "stage_C1_1_direct_transfer": {
                "u_top_target_mm": TARGET_U_RP,
                "rf2_expected_N": TARGET_RF2_DONOR,
                "rf2_continuity_pct_max": 5.0,
                "energy_continuity_pct_max": 2.5,
                "kkt_violations_max": 0,
                "free_phase_residual_max_kN_mm": 1e-06,
                "healing_tolerance": 0,
                "stationarity_delta_d_max": 0.001,
                "stationarity_delta_rf2_max_N": 0.1
            }
        },
        "package_name": "120_c4_inc88_holdout_diagnostic"
    }
    auth_path = OUT_DIR / "M1_C4_INC88_HOLDOUT_AUTHORIZATION.json"
    with open(auth_path, "w") as f:
        json.dump(auth_data, f, indent=2)
    print("[PACKAGE 120 MAPPER] Written authorization to: %s" % auth_path)
    print("=" * 80)
    print("PACKAGE 120 MAPPING AND PREPARATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_mapping()
