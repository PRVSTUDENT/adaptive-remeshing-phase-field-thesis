#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package118_re_equilibrated_transfer.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Maps authentic Re-equilibrated Increment 79 donor state from Package 117
(C3 same-mesh control: RF2 = 185.318 N, E_tot = 0.212455 mJ, d_max = 0.433395)
onto Candidate C4 (4,422 quads, 4,588 physical nodes) nonmatching mesh:
1. Exact shape-function interpolation with slit flank awareness (y=0.050 mm, x <= 0.040 mm).
2. Gauss-point history H and damage lower bound d0 transfer.
3. Computes initial mapped Bourdin fracture energy, elastic strain energy, and mechanical reaction force.
4. Generates Abaqus input deck, UEL, PBS script, manifests, and lower-bound CSV files for Package 118.
5. Saves audit JSON to results/validation/c4_inc79_from_p117_mapping_audit.json.
"""

from __future__ import print_function, division
import os
import sys
import math
import json
import shutil
import hashlib
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

C3_INP = REPO_ROOT / "models/pandey_kumar_mode1/117_c3_samemesh_am_control/M1_C3_SAMEMESH_AM_CONTROL.inp"
C3_NODAL_U_CSV = REPO_ROOT / "models/pandey_kumar_mode1/117_c3_samemesh_am_control/p117_terminal_nodal_u.csv"
C3_NODAL_D_CSV = REPO_ROOT / "models/pandey_kumar_mode1/117_c3_samemesh_am_control/p117_terminal_nodal_d.csv"
C3_ELEM_GP_CSV = REPO_ROOT / "models/pandey_kumar_mode1/117_c3_samemesh_am_control/p117_terminal_elem_gp.csv"
C3_SUMMARY_JSON = REPO_ROOT / "models/pandey_kumar_mode1/117_c3_samemesh_am_control/c3_samemesh_inc79_control_summary.json"

C4_TEMPLATE_INP = REPO_ROOT / "models/pandey_kumar_mode1/115_c4_inc79_direct_transfer/M1_C4_INC79_DIRECT_TRANSFER.inp"
OUT_DIR = REPO_ROOT / "models/pandey_kumar_mode1/118_c4_inc79_from_p117_transfer"
OUT_AUDIT_JSON = REPO_ROOT / "results/validation/c4_inc79_from_p117_mapping_audit.json"

TARGET_U_RP = 0.001842500000000000
P117_TARGET_RF2 = 185.31826138
P117_TARGET_E_TOT = 0.21245454
P117_TARGET_E_ELAS = 0.17072821
P117_TARGET_E_FRAC = 0.04172633
P117_TARGET_D_MAX = 0.43339499

def shape_functions(xi, eta):
    N = np.array([
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta)
    ])
    dNdxi = np.array([-0.25 * (1.0 - eta),  0.25 * (1.0 - eta), 0.25 * (1.0 + eta), -0.25 * (1.0 + eta)])
    dNdeta = np.array([-0.25 * (1.0 - xi), -0.25 * (1.0 + xi),  0.25 * (1.0 + xi),  0.25 * (1.0 - xi)])
    return N, dNdxi, dNdeta

def load_inp_mesh(inp_path):
    nodes = {}
    elements = {}
    reading = None
    with open(inp_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            u = l.upper()
            if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                reading = "NODE"
                continue
            elif u.startswith("*ELEMENT"):
                if "TYPE=U1" in u or "TYPE=U2" in u or "TYPE=CPE4" in u or "TYPE=CPS4" in u:
                    reading = "ELEM"
                else:
                    reading = None
                continue
            elif u.startswith("*"):
                reading = None
                continue
            if reading == "NODE":
                p = [x.strip() for x in l.split(",")]
                if len(p) >= 3 and p[0].isdigit():
                    nid = int(p[0])
                    if nid != 999999:
                        nodes[nid] = np.array([float(p[1]), float(p[2])])
            elif reading == "ELEM":
                p = [x.strip() for x in l.split(",")]
                if len(p) >= 5 and p[0].isdigit():
                    eid = int(p[0])
                    if eid <= 4422:
                        elements[eid] = [int(x) for x in p[1:5]]

    node_to_elems = {nid: [] for nid in nodes}
    for eid, conn in elements.items():
        for n in conn:
            node_to_elems[n].append(eid)

    flank = {}
    for nid, pt in nodes.items():
        if abs(pt[1] - 0.050) < 1e-6 and pt[0] <= 0.040 + 1e-6:
            centroids_y = [np.mean([nodes[n][1] for n in elements[eid]]) for eid in node_to_elems[nid]]
            if all(cy > 0.050 for cy in centroids_y):
                flank[nid] = "upper"
            elif all(cy < 0.050 for cy in centroids_y):
                flank[nid] = "lower"
            else:
                flank[nid] = "slit_tip"
        else:
            flank[nid] = "intact"

    return {"nodes": nodes, "elements": elements, "flank": flank, "node_to_elems": node_to_elems}

def run_mapping():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("[PACKAGE 118 MAPPER] Loading C3 donor mesh and C4 receiver mesh...")
    c3_mesh = load_inp_mesh(C3_INP)
    c4_mesh = load_inp_mesh(C4_TEMPLATE_INP)

    print("[PACKAGE 118 MAPPER] C3 Donor mesh: %d nodes, %d elements" % (len(c3_mesh["nodes"]), len(c3_mesh["elements"])))
    print("[PACKAGE 118 MAPPER] C4 Receiver mesh: %d nodes, %d elements" % (len(c4_mesh["nodes"]), len(c4_mesh["elements"])))

    # Load Package 117 converged nodal displacements
    import csv
    p117_u = {}
    with open(C3_NODAL_U_CSV, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            p117_u[int(r["node_id"])] = (float(r["u1"]), float(r["u2"]))

    # Load Package 117 converged nodal damage
    p117_d = {}
    with open(C3_NODAL_D_CSV, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            p117_d[int(r["node_id"])] = float(r["d"])

    # Load Package 117 committed GP history
    p117_gp_h = {}
    p117_gp_d = {}
    with open(C3_ELEM_GP_CSV, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            eid = int(r["eid"])
            gp = int(r["gp"])
            if eid not in p117_gp_h:
                p117_gp_h[eid] = {}
                p117_gp_d[eid] = {}
            p117_gp_h[eid][gp] = float(r["h0"])
            p117_gp_d[eid][gp] = float(r["d0"])

    print("[PACKAGE 118 MAPPER] Loaded Package 117 state: %d nodes U/D, %d elements GP history" %
          (len(p117_u), len(p117_gp_h)))
    print("[PACKAGE 118 MAPPER] Package 117 peak nodal damage: %.8f" % max(p117_d.values()))

    # C3 grid interpolation functions (40x40 quads, h=0.0025 mm)
    def interpolate_c3_field(x, y, flank, field_dict):
        x = max(0.0, min(0.1, x))
        y = max(0.0, min(0.1, y))
        col = min(39, max(0, int(x / 0.0025)))
        if x >= 0.1: col = 39

        if y < 0.050:
            row = min(19, max(0, int(y / 0.0025)))
        elif y > 0.050:
            row = min(39, max(20, int(y / 0.0025)))
        else:
            if flank == "lower":
                row = 19
            elif flank == "upper":
                row = 20
            else:
                row = 20 if (x > 0.040 or flank == "upper") else 19

        eid = row * 40 + col + 1
        conn = c3_mesh["elements"][eid]
        pts = [c3_mesh["nodes"][n] for n in conn]
        x_min, y_min = pts[0][0], pts[0][1]

        xi = max(-1.0, min(1.0, 2.0 * (x - x_min) / 0.0025 - 1.0))
        eta = max(-1.0, min(1.0, 2.0 * (y - y_min) / 0.0025 - 1.0))
        N, _, _ = shape_functions(xi, eta)

        vals = [field_dict[n] for n in conn]
        if isinstance(vals[0], tuple):
            v1 = sum(N[i] * vals[i][0] for i in range(4))
            v2 = sum(N[i] * vals[i][1] for i in range(4))
            return (float(v1), float(v2))
        else:
            return float(sum(N[i] * vals[i] for i in range(4)))

    def interpolate_c3_history(x, y, flank):
        x = max(0.0, min(0.1, x))
        y = max(0.0, min(0.1, y))
        col = min(39, max(0, int(x / 0.0025)))
        if x >= 0.1: col = 39

        if y < 0.050:
            row = min(19, max(0, int(y / 0.0025)))
        elif y > 0.050:
            row = min(39, max(20, int(y / 0.0025)))
        else:
            row = 20 if (x > 0.040 or flank == "upper") else 19

        eid = row * 40 + col + 1
        x_min = col * 0.0025
        y_min = row * 0.0025
        xi0 = max(-1.0, min(1.0, 2.0 * (x - x_min) / 0.0025 - 1.0))
        eta0 = max(-1.0, min(1.0, 2.0 * (y - y_min) / 0.0025 - 1.0))

        s3 = math.sqrt(3.0)
        xi_gp = max(-1.0, min(1.0, xi0 * s3))
        eta_gp = max(-1.0, min(1.0, eta0 * s3))
        N, _, _ = shape_functions(xi_gp, eta_gp)
        h_vals = [p117_gp_h[eid][gp] for gp in range(1, 5)]
        return float(sum(N[i] * h_vals[i] for i in range(4)))

    print("[PACKAGE 118 MAPPER] Transferring Package 117 fields onto Candidate C4 nodes and elements...")
    c4_nodal_u = {}
    c4_nodal_d = {}

    for nid, pt in c4_mesh["nodes"].items():
        fl = c4_mesh["flank"][nid]
        c4_nodal_u[nid] = interpolate_c3_field(pt[0], pt[1], fl, p117_u)
        c4_nodal_d[nid] = max(0.0, min(1.0, interpolate_c3_field(pt[0], pt[1], fl, p117_d)))

    c4_elem_d0 = {}
    c4_elem_h0 = {}
    for eid, conn in c4_mesh["elements"].items():
        pts = np.array([c4_mesh["nodes"][n] for n in conn])
        c4_elem_d0[eid] = []
        c4_elem_h0[eid] = []
        for kpt in range(4):
            xi, eta = UEL_GP_COORDS[kpt]
            N, _, _ = shape_functions(xi, eta)
            gp_x = float(np.dot(N, pts[:, 0]))
            gp_y = float(np.dot(N, pts[:, 1]))
            fl = "upper" if gp_y >= 0.050 else "lower"

            # Damage lower bound at GP
            gp_d0 = float(np.dot(N, [c4_nodal_d[n] for n in conn]))
            c4_elem_d0[eid].append(max(0.0, min(1.0, gp_d0)))

            # History transfer
            gp_h0 = interpolate_c3_history(gp_x, gp_y, fl)
            c4_elem_h0[eid].append(max(0.0, gp_h0))

    # Evaluate mapped C4 energies
    c4_at2_ef = 0.0
    c4_elas_e = 0.0
    for eid, conn in c4_mesh["elements"].items():
        pts = np.array([c4_mesh["nodes"][n] for n in conn])
        ue = np.array([c4_nodal_u[n] for n in conn]).flatten()
        de = np.array([c4_nodal_d[n] for n in conn])
        d_avg = float(np.mean(de))
        deg = (1.0 - d_avg)**2 + K_DEGRAD
        c_mech = C0 * deg

        for kpt in range(4):
            xi, eta = UEL_GP_COORDS[kpt]
            N, dNdxi, dNdeta = shape_functions(xi, eta)
            J = np.vstack([dNdxi, dNdeta]) @ pts
            detJ = float(np.linalg.det(J))
            invJ = np.linalg.inv(J)
            dNdx = invJ @ np.vstack([dNdxi, dNdeta])

            d_val = float(np.dot(N, de))
            grad_d = np.dot(dNdx, de)
            grad_d_sq = float(np.dot(grad_d, grad_d))
            psi_f = (GC / (2.0 * ELL0)) * (d_val**2 + (ELL0**2) * grad_d_sq)
            c4_at2_ef += psi_f * detJ * UEL_WEIGHTS[kpt]

            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]   = dNdx[0, i]
                B[1, 2*i+1] = dNdx[1, i]
                B[2, 2*i]   = dNdx[1, i]
                B[2, 2*i+1] = dNdx[0, i]
            eps = B.dot(ue)
            psi_e = 0.5 * eps.dot(c_mech).dot(eps)
            c4_elas_e += psi_e * detJ * UEL_WEIGHTS[kpt]

    c4_elas_mJ = c4_elas_e * 1000.0
    c4_frac_mJ = c4_at2_ef * 1000.0
    c4_tot_mJ = c4_elas_mJ + c4_frac_mJ

    print("\n[PACKAGE 118 MAPPER] Initial Mapped C4 Energies from Re-equilibrated Package 117:")
    print("  E_elas: %.8f mJ (P117: %.8f mJ, diff %+.4f%%)" %
          (c4_elas_mJ, P117_TARGET_E_ELAS, 100.0 * (c4_elas_mJ - P117_TARGET_E_ELAS) / P117_TARGET_E_ELAS))
    print("  E_frac: %.8f mJ (P117: %.8f mJ, diff %+.4f%%)" %
          (c4_frac_mJ, P117_TARGET_E_FRAC, 100.0 * (c4_frac_mJ - P117_TARGET_E_FRAC) / P117_TARGET_E_FRAC))
    print("  E_tot:  %.8f mJ (P117: %.8f mJ, diff %+.4f%%)" %
          (c4_tot_mJ, P117_TARGET_E_TOT, 100.0 * (c4_tot_mJ - P117_TARGET_E_TOT) / P117_TARGET_E_TOT))
    print("  Peak nodal d: %.8f (P117: %.8f)" % (max(c4_nodal_d.values()), P117_TARGET_D_MAX))

    # Write Package 118 d_lower_bounds.csv
    bounds_csv_path = OUT_DIR / "d_lower_bounds.csv"
    with open(bounds_csv_path, "w") as f:
        f.write("EID, D0_1, D0_2, D0_3, D0_4, H0_1, H0_2, H0_3, H0_4\n")
        for eid in sorted(c4_mesh["elements"].keys()):
            d_vals = c4_elem_d0[eid]
            h_vals = c4_elem_h0[eid]
            f.write("%d, %.10e, %.10e, %.10e, %.10e, %.10e, %.10e, %.10e, %.10e\n" %
                    (eid, d_vals[0], d_vals[1], d_vals[2], d_vals[3],
                     h_vals[0], h_vals[1], h_vals[2], h_vals[3]))
    print("[PACKAGE 118 MAPPER] Written bounds to: %s" % bounds_csv_path)

    # Write stage_a_all_d0_boundary_cards.inc
    stage_a_path = OUT_DIR / "stage_a_all_d0_boundary_cards.inc"
    with open(stage_a_path, "w") as f:
        f.write("** Stage A Initial All-D0 Boundary Cards for Package 118 Direct Transfer\n")
        f.write("** Format: node_id, 3, 3, d_value\n")
        for nid in sorted(c4_mesh["nodes"].keys()):
            f.write("%d, 3, 3, %.8f\n" % (nid, c4_nodal_d[nid]))
    print("[PACKAGE 118 MAPPER] Written Stage A boundary cards to: %s" % stage_a_path)

    # Copy active_set_boundary_cards.inc initially from stage_a
    active_cards_path = OUT_DIR / "active_set_boundary_cards.inc"
    shutil.copyfile(stage_a_path, active_cards_path)

    # Write initial nodal displacements CSV for driver initialization
    disp_csv_path = OUT_DIR / "nodal_displacements_initial.csv"
    with open(disp_csv_path, "w") as f:
        f.write("NID, U1, U2\n")
        for nid in sorted(c4_mesh["nodes"].keys()):
            u1, u2 = c4_nodal_u[nid]
            f.write("%d, %.10e, %.10e\n" % (nid, u1, u2))
    print("[PACKAGE 118 MAPPER] Written initial displacements to: %s" % disp_csv_path)

    # Copy C4 INP deck as M1_C4_P117_DIRECT_TRANSFER.inp
    inp_dest = OUT_DIR / "M1_C4_P117_DIRECT_TRANSFER.inp"
    with open(C4_TEMPLATE_INP, "r") as fin, open(inp_dest, "w") as fout:
        for line in fin:
            if "Candidate C4 Stage C1-1 Direct State-Transfer Control (Inc 79)" in line:
                fout.write("** Candidate C4 Package 118 Direct State-Transfer from Re-equilibrated P117 C3\n")
            elif "Step, name=C1-2-Inc79" in line:
                fout.write("*Step, name=P117-Transfer-Inc79, nlgeom=NO, inc=200\n")
            else:
                fout.write(line)
    print("[PACKAGE 118 MAPPER] Generated INP deck: %s" % inp_dest)

    # Copy UEL subroutine
    uel_src = REPO_ROOT / "models/pandey_kumar_mode1/117_c3_samemesh_am_control/f42_unified_12dof_active_set_uel.for"
    uel_dest = OUT_DIR / "f42_unified_12dof_active_set_uel.for"
    shutil.copyfile(uel_src, uel_dest)
    print("[PACKAGE 118 MAPPER] Copied unified 12-DOF UEL to: %s" % uel_dest)

    # Copy job_notifications.sh
    shutil.copyfile(REPO_ROOT / "scripts/hpc/notifications/job_notifications.sh", OUT_DIR / "job_notifications.sh")

    # Generate driver_c4_p117_direct_transfer.py
    driver_src = REPO_ROOT / "models/pandey_kumar_mode1/115_c4_inc79_direct_transfer/driver_c4_inc79_direct_transfer.py"
    driver_dest = OUT_DIR / "driver_c4_p117_direct_transfer.py"
    with open(driver_src, "r") as fin, open(driver_dest, "w") as fout:
        content = fin.read()
        content = content.replace("Package 115: Isolated Increment-79 Direct State-Transfer Control on Candidate C4",
                                  "Package 118: C4 Direct State-Transfer from Re-equilibrated C3 (Package 117)")
        content = content.replace("c4_inc79_direct_transfer_summary.json",
                                  "c4_inc79_from_p117_summary.json")
        content = content.replace("M1_C4_INC79_DIRECT_TRANSFER.inp",
                                  "M1_C4_P117_DIRECT_TRANSFER.inp")
        content = content.replace('job_name = "M1_C4_INC79_CYC%d_MECH" % cycle',
                                  'job_name = "M1_C4_P117_CYC%d_MECH" % cycle')
        content = content.replace('target_rf2_ref = 186.067909',
                                  'target_rf2_ref = 185.31826138')
        content = content.replace('authentic_donor_energy_mJ = 0.212448',
                                  'authentic_donor_energy_mJ = 0.21245454')
        content = content.replace('"PACKAGE_115_C4_INC79_DIRECT_TRANSFER"',
                                  '"PACKAGE_118_C4_INC79_FROM_P117_TRANSFER"')
        fout.write(content)
    print("[PACKAGE 118 MAPPER] Generated AM driver: %s" % driver_dest)

    # Generate submit_M1_C4_P117_DIRECT_TRANSFER.pbs
    pbs_content = """#!/bin/bash
#PBS -N M1_C4_P117_DIRECT_TRANSFER
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_c4_p117_direct_transfer/pbs_execution.log
#PBS -e /scratch9/pr21vyci/runs/mode1_c4_p117_direct_transfer/pbs_error.log

set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_c4_p117_direct_transfer"
cd "${RUN_DIR}"

if [[ "$(pwd -P)" =~ ^/home/ ]]; then
    echo "ERROR: Running under /home is strictly prohibited by HPC storage policy." >&2
    exit 2
fi

export XDG_RUNTIME_DIR="/tmp/runtime-pr21vyci"
mkdir -p "${XDG_RUNTIME_DIR}" 2>/dev/null || true

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

abaqus python driver_c4_p117_direct_transfer.py
"""
    pbs_dest = OUT_DIR / "submit_M1_C4_P117_DIRECT_TRANSFER.pbs"
    with open(pbs_dest, "w") as f:
        f.write(pbs_content)
    print("[PACKAGE 118 MAPPER] Generated PBS script: %s" % pbs_dest)

    # Generate run_c4_p117_transfer_datacheck.sh
    dc_content = """#!/bin/bash
set -euo pipefail

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi

module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

cd /scratch9/pr21vyci/runs/mode1_c4_p117_direct_transfer
abaqus datacheck job=M1_C4_P117_DC input=M1_C4_P117_DIRECT_TRANSFER.inp user=f42_unified_12dof_active_set_uel.for interactive
"""
    dc_dest = OUT_DIR / "run_c4_p117_transfer_datacheck.sh"
    with open(dc_dest, "w") as f:
        f.write(dc_content)
    print("[PACKAGE 118 MAPPER] Generated datacheck script: %s" % dc_dest)

    # Compute file hashes for manifests
    def get_sha256(path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk: break
                h.update(chunk)
        return h.hexdigest().upper()

    # Generate PACKAGE_MANIFEST.json
    manifest = {
        "package_name": "PACKAGE_118_C4_INC79_FROM_P117_TRANSFER",
        "created_at": "2026-10-27T11:15:00+01:00",
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "protocol_version": 2,
        "model": "pandey_kumar_mode1",
        "solver": "Abaqus/Standard 2023 with Intel Fortran ifort (active-set alternating minimization)",
        "mesh": {
            "name": "Candidate C4",
            "quad_count": 4422,
            "node_count": 4588,
            "h_min_mm": 0.000609,
            "h_min_over_l0": 0.0812
        },
        "donor": {
            "source": "PACKAGE_117_C3_SAMEMESH_AM_CONTROL",
            "model": "Candidate C3 (1600 quads, 1698 physical nodes)",
            "physical_endpoint_u_rp_mm": TARGET_U_RP,
            "re_equilibrated_rf2_N": P117_TARGET_RF2,
            "re_equilibrated_e_tot_mJ": P117_TARGET_E_TOT,
            "re_equilibrated_e_elas_mJ": P117_TARGET_E_ELAS,
            "re_equilibrated_e_frac_mJ": P117_TARGET_E_FRAC,
            "re_equilibrated_d_max": P117_TARGET_D_MAX
        },
        "files": {
            "input_deck": "M1_C4_P117_DIRECT_TRANSFER.inp",
            "input_deck_sha256": get_sha256(inp_dest),
            "user_subroutine": "f42_unified_12dof_active_set_uel.for",
            "user_subroutine_sha256": get_sha256(uel_dest),
            "driver_script": "driver_c4_p117_direct_transfer.py",
            "driver_script_sha256": get_sha256(driver_dest),
            "pbs_script": "submit_M1_C4_P117_DIRECT_TRANSFER.pbs",
            "pbs_script_sha256": get_sha256(pbs_dest),
            "d_lower_bounds": "d_lower_bounds.csv",
            "d_lower_bounds_sha256": get_sha256(bounds_csv_path),
            "stage_a_cards": "stage_a_all_d0_boundary_cards.inc",
            "stage_a_cards_sha256": get_sha256(stage_a_path)
        }
    }
    manifest_dest = OUT_DIR / "PACKAGE_MANIFEST.json"
    with open(manifest_dest, "w") as f:
        json.dump(manifest, f, indent=2)
    print("[PACKAGE 118 MAPPER] Generated PACKAGE_MANIFEST.json: %s" % manifest_dest)

    # Generate M1_C4_P117_TRANSFER_AUTHORIZATION.json
    auth_doc = {
        "schema": 1,
        "authorization_id": "AUTH-F1597-MODE1-PACKAGE118-C4-P117-TRANSFER-001",
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "created_at": "2026-10-27T11:15:00+01:00",
        "scope": "SERIAL_MODE1_PRODUCTION",
        "target_hpc_cluster": "tu_freiberg",
        "execution_mode": "SERIAL_1CPU",
        "queue": "entry_imfdfkmq",
        "walltime": "08:00:00",
        "memory": "16gb",
        "jobs": [
            {
                "job_name": "M1_C4_P117_DIRECT_TRANSFER",
                "pbs_script": "models/pandey_kumar_mode1/118_c4_inc79_from_p117_transfer/submit_M1_C4_P117_DIRECT_TRANSFER.pbs",
                "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c4_p117_direct_transfer",
                "expected_deliverables": [
                    "c4_inc79_from_p117_summary.json",
                    "pbs_execution.log"
                ],
                "acceptance_criteria": {
                    "exit_code": 0,
                    "max_walltime_seconds": 28800,
                    "max_consecutive_delta_rf2_N": 0.1,
                    "max_consecutive_delta_d": 0.001,
                    "zero_damage_healing": True
                }
            }
        ],
        "dual_channel_notifications": {
            "pbs_mail": {
                "directives": ["#PBS -m abe", "#PBS -M pr21vyci@mailserver.tu-freiberg.de"],
                "recipient": "pr21vyci@mailserver.tu-freiberg.de"
            },
            "telegram": {
                "config_path": "~/.config/adaptive-remeshing/notifications.env",
                "events": ["SUBMITTED", "STARTED", "COMPLETED", "FAILED", "TERMINATED"]
            }
        }
    }
    auth_dest = OUT_DIR / "M1_C4_P117_TRANSFER_AUTHORIZATION.json"
    with open(auth_dest, "w") as f:
        json.dump(auth_doc, f, indent=2)
    print("[PACKAGE 118 MAPPER] Generated authorization document: %s" % auth_dest)

    # Generate Audit Record
    audit_record = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "package": "PACKAGE_118_C4_INC79_FROM_P117_TRANSFER",
        "objective": "C4 Direct State-Transfer Control from Re-equilibrated C3 Donor (Package 117)",
        "donor_reference": {
            "model": "Candidate C3 Re-equilibrated Control (Package 117)",
            "quads": 1600,
            "nodes": 1698,
            "prescribed_u_rp_mm": TARGET_U_RP,
            "re_equilibrated_rf2_N": P117_TARGET_RF2,
            "re_equilibrated_e_elas_mJ": P117_TARGET_E_ELAS,
            "re_equilibrated_e_frac_mJ": P117_TARGET_E_FRAC,
            "re_equilibrated_e_tot_mJ": P117_TARGET_E_TOT,
            "re_equilibrated_d_max": P117_TARGET_D_MAX
        },
        "receiver_target": {
            "model": "Candidate C4",
            "quads": 4422,
            "nodes": 4588,
            "prescribed_u_rp_mm": TARGET_U_RP
        },
        "initial_mapped_energies_mJ": {
            "e_elas_mJ": c4_elas_mJ,
            "e_frac_mJ": c4_frac_mJ,
            "e_tot_mJ": c4_tot_mJ,
            "delta_elas_pct": 100.0 * (c4_elas_mJ - P117_TARGET_E_ELAS) / P117_TARGET_E_ELAS,
            "delta_frac_pct": 100.0 * (c4_frac_mJ - P117_TARGET_E_FRAC) / P117_TARGET_E_FRAC,
            "delta_tot_pct": 100.0 * (c4_tot_mJ - P117_TARGET_E_TOT) / P117_TARGET_E_TOT
        },
        "comparison_with_package115": {
            "pkg115_mapped_e_frac_mJ": 0.045619,
            "pkg118_mapped_e_frac_mJ": c4_frac_mJ,
            "difference_pct": 100.0 * (c4_frac_mJ - 0.045619) / 0.045619
        },
        "scientific_finding": "Mapped fracture energy on C4 from re-equilibrated C3 donor confirms whether the +11% fracture energy elevation is an intrinsic consequence of nonmatching fine-mesh spatial discretization (h/l0 = 0.333 -> 0.081) or donor state non-equilibrium."
    }

    with open(OUT_AUDIT_JSON, "w") as f:
        json.dump(audit_record, f, indent=2)
    print("[PACKAGE 118 MAPPER] Saved audit to: %s" % OUT_AUDIT_JSON)

if __name__ == "__main__":
    run_mapping()
