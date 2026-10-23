#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package90_c3_transfer.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Construct Candidate C3 discretization, map Package 89 terminal state
(u = 0.002015107 mm, RF2 = 169.5991 N, d_max = 0.85696), and build
Package 90 4-stage transfer and forward continuation deck M1_C3_PACKAGE90_TRANSFER.inp.
"""

import os
import sys
import math
import hashlib
import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
sys.path.insert(0, str(REPO_ROOT))

from scripts.remeshing.generate_crack_band_mesh import generate_graded_1d, build_quad_mesh

# Physical & Material Constants
GC = 0.0027      # kN/mm (2.7 N/mm)
ELL0 = 0.0075    # mm (7.5 um)
E_MOD = 210.0    # kN/mm^2 (210 GPa)
NU = 0.3
LAMBDA = E_MOD * NU / ((1.0 + NU) * (1.0 - 2.0 * NU))
MU = E_MOD / (2.0 * (1.0 + NU))
K_RES = 1.0e-7

CHECKPOINT_U = 0.00201510735    # Package 89 terminal displacement
CONTINUATION_U = 0.00206510735  # Forward continuation target (+50 nm)

PKG89_NODAL_CSV = REPO_ROOT / "results/validation/mode1_f1597/pkg89_terminal_nodal_state.csv"
PKG89_TABLE_CSV = REPO_ROOT / "models/pandey_kumar_mode1/89_c2_frame88_early_state_transfer/candidate_c2_frame88_mapped_state_table.csv"
C2_BASE_INP = REPO_ROOT / "models/pandey_kumar_mode1/candidate_crack_band_mesh_c2.inp"

OUT_DIR = REPO_ROOT / "models/pandey_kumar_mode1/90_c3_package90_second_cycle_transfer"
OUT_C3_INP = OUT_DIR / "candidate_crack_band_mesh_c3.inp"
OUT_TRANSFER_INP = OUT_DIR / "M1_C3_PACKAGE90_TRANSFER.inp"
OUT_MAPPED_CSV = OUT_DIR / "candidate_c3_frame89_mapped_state_table.csv"
OUT_AUDIT_JSON = REPO_ROOT / "results/validation/mode1_f1597/pkg89_to_c3_transfer_audit.json"

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def shape_functions(xi: float, eta: float):
    N = 0.25 * np.array([
        (1.0 - xi) * (1.0 - eta),
        (1.0 + xi) * (1.0 - eta),
        (1.0 + xi) * (1.0 + eta),
        (1.0 - xi) * (1.0 + eta)
    ])
    dNdxi = 0.25 * np.array([
        -(1.0 - eta),  (1.0 - eta),  (1.0 + eta), -(1.0 + eta)
    ])
    dNdeta = 0.25 * np.array([
        -(1.0 - xi), -(1.0 + xi),  (1.0 + xi),  (1.0 - xi)
    ])
    return N, dNdxi, dNdeta

def spectral_split_psi0(eps11: float, eps22: float, gam12: float) -> float:
    tr_eps = eps11 + eps22
    diff = 0.5 * (eps11 - eps22)
    radius = math.sqrt(diff * diff + 0.25 * gam12 * gam12)
    center = 0.5 * (eps11 + eps22)
    eps1 = center + radius
    eps2 = center - radius
    eps3 = 0.0

    pos_tr = max(0.0, tr_eps)
    pos_eps1 = max(0.0, eps1)
    pos_eps2 = max(0.0, eps2)
    pos_eps3 = max(0.0, eps3)

    psi0_pos = 0.5 * LAMBDA * (pos_tr ** 2) + MU * (pos_eps1**2 + pos_eps2**2 + pos_eps3**2)
    return psi0_pos

def load_donor_c2_state():
    print("Loading Donor C2 mesh and Package 89 terminal state...")
    # Load C2 mesh
    nodes = {}
    elems_u1 = {}
    with open(C2_BASE_INP, "r", encoding="utf-8") as f:
        reading = None
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE") and not u.startswith("*NODE OUTPUT"):
                    reading = "NODE"
                elif u.startswith("*ELEMENT") and "TYPE=U1" in u:
                    reading = "U1"
                elif u.startswith("*"):
                    reading = None
                continue
            parts = [p.strip() for p in l.split(",")]
            if reading == "NODE" and len(parts) >= 3 and parts[0].isdigit():
                nid = int(parts[0])
                if nid != 999999:
                    nodes[nid] = np.array([float(parts[1]), float(parts[2])])
            elif reading == "U1" and len(parts) >= 5 and parts[0].isdigit():
                elems_u1[int(parts[0])] = [int(p) for p in parts[1:5]]

    # Load C2 terminal nodal displacements and damage
    nodal_disp = {}
    nodal_dam = {}
    with open(PKG89_NODAL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nid = int(row["node_id"])
            nodal_disp[nid] = (float(row["u1"]), float(row["u2"]))
            nodal_dam[nid] = float(row["damage"])

    # Load injected history from candidate_c2_frame88_mapped_state_table.csv
    injected_h = {}
    with open(PKG89_TABLE_CSV, "r", encoding="utf-8") as f:
        for line in f:
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if parts and parts[0] == "ELEM_H" and len(parts) >= 6:
                eid = int(parts[1])
                injected_h[eid] = {
                    1: float(parts[2]),
                    2: float(parts[3]),
                    3: float(parts[4]),
                    4: float(parts[5]),
                }

    # Evaluate exact committed history at 4 Gauss points for each C2 element
    gp_coord = 1.0 / math.sqrt(3.0)
    gauss_pts = [(-gp_coord, -gp_coord), (gp_coord, -gp_coord), (gp_coord, gp_coord), (-gp_coord, gp_coord)]
    gauss_weights = [1.0, 1.0, 1.0, 1.0]

    elem_h_terminal = {}
    total_frac_energy = 0.0

    for eid, conn in elems_u1.items():
        coords = np.array([nodes[n] for n in conn])
        u_elem = np.array([nodal_disp[n] for n in conn])
        d_elem = np.array([nodal_dam[n] for n in conn])

        h_list = []
        for gp_idx, (xi, eta) in enumerate(gauss_pts):
            N, dNdxi, dNdeta = shape_functions(xi, eta)
            J = np.vstack([dNdxi, dNdeta]) @ coords
            detJ = np.linalg.det(J)
            invJ = np.linalg.inv(J)
            dNdx = invJ @ np.vstack([dNdxi, dNdeta])

            dudx = dNdx[0, :] @ u_elem[:, 0]
            dudy = dNdx[1, :] @ u_elem[:, 0]
            dvdx = dNdx[0, :] @ u_elem[:, 1]
            dvdy = dNdx[1, :] @ u_elem[:, 1]

            eps11 = dudx
            eps22 = dvdy
            gam12 = dudy + dvdx

            psi0_pos = spectral_split_psi0(eps11, eps22, gam12)
            h_inj = injected_h.get(eid, {}).get(gp_idx + 1, 0.0)
            h_term = max(h_inj, psi0_pos)
            h_list.append(h_term)

            d_gp = float(np.dot(N, d_elem))
            grad_d = dNdx @ d_elem
            grad_d_sq = float(np.dot(grad_d, grad_d))
            w_f = (d_gp ** 2) / (2.0 * ELL0) + 0.5 * ELL0 * grad_d_sq
            total_frac_energy += GC * w_f * detJ * gauss_weights[gp_idx]

        elem_h_terminal[eid] = h_list

    print(f"Donor C2 loaded: {len(nodes)} nodes, {len(elems_u1)} elements.")
    print(f"Donor C2 terminal AT2 fracture energy: {total_frac_energy * 1e6:.4f} uJ")
    return {
        "nodes": nodes,
        "elems_u1": elems_u1,
        "nodal_disp": nodal_disp,
        "nodal_dam": nodal_dam,
        "elem_h": elem_h_terminal,
        "at2_energy": total_frac_energy
    }

def build_c3_mesh():
    print("Constructing Candidate C3 discretization...")
    # C3 forward-adapted mesh parameters:
    # y-direction: fine band around y = 0.050 (h = 0.0010 mm)
    y_coords = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.012, h_fine=0.0010, growth_ratio=1.15, max_h=0.005)
    # x-direction: fine band forward-adapted to center x = 0.0575, width 0.040 mm (x in [0.0375, 0.0775], h = 0.00125 mm)
    # Key points: original slit tip at 0.040, current crack tip at 0.05125
    x_coords = generate_graded_1d(0.0, 0.100, 0.0575, band_half_width=0.020, h_fine=0.00125, growth_ratio=1.15, max_h=0.005, key_points=[0.040, 0.05125])

    mesh = build_quad_mesh(x_coords, y_coords, slit_y=0.050, slit_a0=0.040)
    print(f"Candidate C3 generated: {mesh['n_elements']} quads, {mesh['n_nodes']} physical nodes.")
    print(f"Min detJ: {mesh['min_det_jac']:.4e}, Max aspect ratio: {mesh['max_aspect_ratio']:.2f}")

    # Determine node flank classifications
    flank = {}
    for nid in sorted(mesh["nodes"].keys()):
        if nid == mesh["rp_nid"]:
            continue
        pt = mesh["nodes"][nid]
        if abs(pt[1] - 0.050) < 1e-6 and pt[0] <= 0.040 + 1e-6:
            # Check element connections
            elems = [eid for eid, conn in mesh["elements"].items() if nid in conn]
            cys = [np.mean([mesh["nodes"][n][1] for n in mesh["elements"][eid]]) for eid in elems]
            if all(cy > 0.050 for cy in cys):
                flank[nid] = "upper"
            elif all(cy < 0.050 for cy in cys):
                flank[nid] = "lower"
            else:
                flank[nid] = "slit_tip"
        else:
            flank[nid] = "intact"
    mesh["flank"] = flank
    return mesh

def transfer_state(donor: Dict[str, Any], receiver: Dict[str, Any]):
    print("Executing rigorous FE state transfer from C2 to C3...")
    # Reconstruct 1D coordinate vectors of donor C2
    c2_x = sorted(list(set(round(p[0], 8) for p in donor["nodes"].values())))
    c2_y = sorted(list(set(round(p[1], 8) for p in donor["nodes"].values())))
    c2_x = np.array(c2_x)
    c2_y = np.array(c2_y)

    nx_c2 = len(c2_x) - 1
    ny_c2 = len(c2_y) - 1

    # Slit indexing on donor C2
    slit_y_idx = int(np.argmin(np.abs(c2_y - 0.050)))
    slit_x_max_idx = int(np.argmin(np.abs(c2_x - 0.040)))

    # Fast spatial locator in C2
    def locate_c2_element(x: float, y: float, flank_type: str) -> Tuple[int, float, float]:
        # Clamp coordinates within domain
        x = max(0.0, min(0.100, x))
        y = max(0.0, min(0.100, y))

        i = int(np.searchsorted(c2_x, x)) - 1
        i = max(0, min(nx_c2 - 1, i))

        # Handle slit boundary row selection
        if abs(y - 0.050) < 1e-8:
            if x <= 0.040 + 1e-8:
                if flank_type == "upper":
                    j = slit_y_idx
                else:
                    j = slit_y_idx - 1
            else:
                j = slit_y_idx if flank_type == "upper" else slit_y_idx - 1
        else:
            j = int(np.searchsorted(c2_y, y)) - 1
            j = max(0, min(ny_c2 - 1, j))

        x0, x1 = c2_x[i], c2_x[i+1]
        y0, y1 = c2_y[j], c2_y[j+1]

        xi = 2.0 * (x - x0) / (x1 - x0) - 1.0
        eta = 2.0 * (y - y0) / (y1 - y0) - 1.0
        xi = max(-1.0, min(1.0, xi))
        eta = max(-1.0, min(1.0, eta))

        # Quad element ID in C2 (1-based, row-major)
        eid = j * nx_c2 + i + 1
        return eid, xi, eta

    # 1. Map nodal displacements and damage to C3 nodes
    c3_nodal_u = {}
    c3_nodal_d = {}

    for nid in sorted(receiver["nodes"].keys()):
        if nid == receiver["rp_nid"]:
            continue
        pt = receiver["nodes"][nid]
        fl = receiver["flank"][nid]
        eid, xi, eta = locate_c2_element(pt[0], pt[1], fl)

        conn = donor["elems_u1"][eid]
        N, _, _ = shape_functions(xi, eta)

        u1 = sum(N[k] * donor["nodal_disp"][conn[k]][0] for k in range(4))
        u2 = sum(N[k] * donor["nodal_disp"][conn[k]][1] for k in range(4))
        d = sum(N[k] * donor["nodal_dam"][conn[k]] for k in range(4))
        d = max(0.0, min(1.0, d))  # Physical bounds

        c3_nodal_u[nid] = (float(u1), float(u2))
        c3_nodal_d[nid] = float(d)

    # 2. Map 4-GP strain history to C3 elements
    gp_coord = 1.0 / math.sqrt(3.0)
    gauss_pts = [(-gp_coord, -gp_coord), (gp_coord, -gp_coord), (gp_coord, gp_coord), (-gp_coord, gp_coord)]
    gauss_weights = [1.0, 1.0, 1.0, 1.0]

    c3_elem_h = {}
    receiver_frac_energy = 0.0

    for eid, conn in sorted(receiver["elements"].items()):
        coords = np.array([receiver["nodes"][n] for n in conn])
        d_elem = np.array([c3_nodal_d[n] for n in conn])
        u_elem = np.array([c3_nodal_u[n] for n in conn])

        elem_h_list = []
        for gp_idx, (xi, eta) in enumerate(gauss_pts):
            N, dNdxi, dNdeta = shape_functions(xi, eta)
            J = np.vstack([dNdxi, dNdeta]) @ coords
            detJ = np.linalg.det(J)
            invJ = np.linalg.inv(J)
            dNdx = invJ @ np.vstack([dNdxi, dNdeta])

            gx = float(np.dot(N, coords[:, 0]))
            gy = float(np.dot(N, coords[:, 1]))
            fl = "upper" if gy > 0.050 else ("lower" if gy < 0.050 else "intact")

            # Locate in donor C2
            donor_eid, d_xi, d_eta = locate_c2_element(gx, gy, fl)

            # Bilinear interpolation of history from donor element's 4 Gauss points
            # Map from element local coordinates (d_xi, d_eta) to Gauss point interpolation
            s3 = math.sqrt(3.0)
            xi_gp = max(-1.0, min(1.0, d_xi * s3))
            eta_gp = max(-1.0, min(1.0, d_eta * s3))
            N_gp, _, _ = shape_functions(xi_gp, eta_gp)

            donor_h_gps = donor["elem_h"][donor_eid]
            h_interp = max(0.0, float(sum(N_gp[k] * donor_h_gps[k] for k in range(4))))

            # Check kinematic strain energy at receiver Gauss point for monotonic history enforcement
            dudx = dNdx[0, :] @ u_elem[:, 0]
            dudy = dNdx[1, :] @ u_elem[:, 0]
            dvdx = dNdx[0, :] @ u_elem[:, 1]
            dvdy = dNdx[1, :] @ u_elem[:, 1]
            psi0_pos = spectral_split_psi0(dudx, dvdy, dudy + dvdx)

            # Monotonic history: H >= max(H_interp, psi0^+)
            h_final = max(h_interp, psi0_pos)
            elem_h_list.append(h_final)

            # Fracture energy contribution
            d_gp = float(np.dot(N, d_elem))
            grad_d = dNdx @ d_elem
            grad_d_sq = float(np.dot(grad_d, grad_d))
            w_f = (d_gp ** 2) / (2.0 * ELL0) + 0.5 * ELL0 * grad_d_sq
            receiver_frac_energy += GC * w_f * detJ * gauss_weights[gp_idx]

        c3_elem_h[eid] = elem_h_list

    donor_at2 = donor["at2_energy"]
    delta_energy_pct = (receiver_frac_energy - donor_at2) / donor_at2 * 100.0
    print(f"C3 mapped AT2 fracture energy: {receiver_frac_energy * 1e6:.4f} uJ (diff vs C2: {delta_energy_pct:+.4f}%)")

    return {
        "nodal_u": c3_nodal_u,
        "nodal_d": c3_nodal_d,
        "elem_h": c3_elem_h,
        "receiver_at2_energy": receiver_frac_energy,
        "delta_energy_pct": delta_energy_pct
    }

def build_package90():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy frozen UEL
    src_uel = REPO_ROOT / "models/pandey_kumar_mode1/89_c2_frame88_early_state_transfer/f42_mixed_uel.for"
    dst_uel = OUT_DIR / "f42_mixed_uel.for"
    import shutil
    shutil.copy2(src_uel, dst_uel)
    assert sha256_file(dst_uel) == FROZEN_UEL_HASH, "Frozen UEL hash mismatch!"

    # 2. Copy job notifications script
    src_notif = REPO_ROOT / "models/pandey_kumar_mode1/89_c2_frame88_early_state_transfer/job_notifications.sh"
    dst_notif = OUT_DIR / "job_notifications.sh"
    shutil.copy2(src_notif, dst_notif)

    # 3. Load donor and construct C3 mesh
    donor = load_donor_c2_state()
    mesh_c3 = build_c3_mesh()

    # 4. Transfer state
    transfer = transfer_state(donor, mesh_c3)

    # 5. Export candidate_c3_frame89_mapped_state_table.csv
    with open(OUT_MAPPED_CSV, "w", encoding="utf-8", newline="\n") as f:
        writer = csv.writer(f)
        writer.writerow(["record_type", "id", "val1", "val2", "val3", "val4", "val5", "val6"])
        for nid in sorted(mesh_c3["nodes"].keys()):
            if nid == mesh_c3["rp_nid"]:
                continue
            u1, u2 = transfer["nodal_u"][nid]
            d = transfer["nodal_d"][nid]
            writer.writerow(["NODE", nid, f"{u1:.10e}", f"{u2:.10e}", f"{d:.10e}", "0.0", "0.0", "0.0"])
        for eid in sorted(mesh_c3["elements"].keys()):
            h = transfer["elem_h"][eid]
            writer.writerow(["ELEM_H", eid, f"{h[0]:.10e}", f"{h[1]:.10e}", f"{h[2]:.10e}", f"{h[3]:.10e}", "0.0", "0.0"])

    print(f"Exported mapped state table: {OUT_MAPPED_CSV}")

    # 6. Build M1_C3_PACKAGE90_TRANSFER.inp
    n_elems = mesh_c3["n_elements"]
    nodes = mesh_c3["nodes"]
    rp_nid = mesh_c3["rp_nid"]
    elements = mesh_c3["elements"]
    top_nodes = mesh_c3["top_nodes"]
    bottom_nodes = mesh_c3["bottom_nodes"]
    pin_nodes = mesh_c3["pin_nodes"]

    lines = [
        "*Heading",
        "** Candidate C3: Second-Cycle Target Crack-Band Resolved (h=0.0010 mm <= ell/7.5)",
        f"** Elements: {n_elems} Quads, Nodes: {len(nodes) - 1} physical + RP {rp_nid}",
        f"** Parameters: E={E_MOD} kN/mm^2, nu={NU}, Gc={GC} kN/mm, l0={ELL0} mm, k={K_RES}",
        "*Preprint, echo=NO, model=NO, history=NO, contact=NO",
        "** ==========================================================",
        f"** USER ELEMENTS (Phase U1: 1..{n_elems}, Mech U2: {n_elems+1}..{2*n_elems})",
        "** ==========================================================",
        "*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM",
        "3",
        "*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM",
        "1, 2",
        "** ==========================================================",
        f"** NODES ({len(nodes) - 1} physical nodes + RP {rp_nid})",
        "** ==========================================================",
        "*Node",
    ]

    for nid in sorted(nodes.keys()):
        x, y = nodes[nid]
        lines.append(f"{nid}, {x:.10f}, {y:.10f}")

    lines.append("** ==========================================================")
    lines.append(f"** LAYER 1: Phase-Field UEL Elements (U1: DOF 3, 1..{n_elems})")
    lines.append("** ==========================================================")
    lines.append("*Element, type=U1, elset=PHASE_QUADS")
    for eid in sorted(elements.keys()):
        conn = elements[eid]
        lines.append(f"{eid}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}")

    lines.append("** ==========================================================")
    lines.append(f"** LAYER 2: Mechanical UEL Elements (U2: DOFs 1,2, {n_elems+1}..{2*n_elems})")
    lines.append("** ==========================================================")
    lines.append("*Element, type=U2, elset=MECH_QUADS")
    for eid in sorted(elements.keys()):
        conn = elements[eid]
        lines.append(f"{eid + n_elems}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}")

    lines.append("** ==========================================================")
    lines.append("** UEL PROPERTIES")
    lines.append("** ==========================================================")
    lines.append("*UEL PROPERTY, ELSET=PHASE_QUADS")
    lines.append(f"{ELL0}, {GC}, {E_MOD}, {NU}, {K_RES}, {n_elems}")
    lines.append("*UEL PROPERTY, ELSET=MECH_QUADS")
    lines.append(f"{ELL0}, {GC}, {E_MOD}, {NU}, {K_RES}, {n_elems}")

    lines.append("** ==========================================================")
    lines.append("** NODE SETS & BOUNDARY CONDITIONS")
    lines.append("** ==========================================================")
    lines.append("*Nset, nset=N_BOTTOM")
    for i in range(0, len(bottom_nodes), 16):
        lines.append(", ".join(str(n) for n in bottom_nodes[i:i + 16]))

    lines.append("*Nset, nset=N_PIN")
    lines.append(", ".join(str(n) for n in pin_nodes))

    lines.append("*Nset, nset=N_TOP")
    for i in range(0, len(top_nodes), 16):
        lines.append(", ".join(str(n) for n in top_nodes[i:i + 16]))

    lines.append("*Nset, nset=N_RP")
    lines.append(f"{rp_nid}")

    # Set of all physical nodes
    phys_nodes = sorted([n for n in nodes.keys() if n != rp_nid])
    lines.append("*Nset, nset=N_PHYSICAL")
    for i in range(0, len(phys_nodes), 16):
        lines.append(", ".join(str(n) for n in phys_nodes[i:i + 16]))

    # Equations coupling top nodes to RP in DOF 2
    lines.append("** ==========================================================")
    lines.append("** EQUATIONS: Tie all top nodes to RP in DOF 2 (u_y)")
    lines.append("** ==========================================================")
    for n in top_nodes:
        lines.append("*EQUATION")
        lines.append("2")
        lines.append(f"{n}, 2, 1.0, {rp_nid}, 2, -1.0")

    # Initial boundary conditions
    lines.append("** ==========================================================")
    lines.append("** INITIAL BOUNDARY CONDITIONS")
    lines.append("** ==========================================================")
    lines.append("*Boundary")
    lines.append("N_BOTTOM, 2, 2, 0.0")
    lines.append("N_PIN, 1, 1, 0.0")
    lines.append("N_RP, 1, 1, 0.0")
    lines.append("N_RP, 2, 2, 0.0")

    # Initial Conditions: 4-Gauss-Point History Field Ingestion
    lines.append("** ==========================================================")
    lines.append("** INITIAL CONDITIONS: 4-Gauss-Point History Field Ingestion")
    lines.append("** Populates SVARS(9..12) via frozen UEL lines 248-262")
    lines.append("** ==========================================================")
    lines.append("*INITIAL CONDITIONS, TYPE=SOLUTION")
    for eid in sorted(elements.keys()):
        h_vals = transfer["elem_h"][eid]
        # Line 1: SVARS(1..8) -> 0.0
        lines.append(f"{eid}, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0")
        # Line 2: SVARS(9..12) = H(1..4), SVARS(13..16) -> 0.0
        lines.append(f"{h_vals[0]:.8e}, {h_vals[1]:.8e}, {h_vals[2]:.8e}, {h_vals[3]:.8e}, 0.0, 0.0, 0.0, 0.0")
        # Line 3: SVARS(17..18) -> 0.0
        lines.append("0.0, 0.0")

    # STEP 1: STATE_INJECTION
    lines.append("** ==========================================================")
    lines.append(f"** STEP 1: STATE_INJECTION (Clamped at u = {CHECKPOINT_U:.8f} mm)")
    lines.append("** Evaluates unrelaxed residual on receiver C3 discretization")
    lines.append("** ==========================================================")
    lines.append("*Step, name=STATE_INJECTION, nlgeom=NO, inc=1")
    lines.append("*Static")
    lines.append("1.0, 1.0, 1e-12, 1.0")
    lines.append("*Boundary")
    lines.append("N_BOTTOM, 2, 2, 0.0")
    lines.append("N_PIN, 1, 1, 0.0")
    lines.append("N_RP, 1, 1, 0.0")
    lines.append(f"N_RP, 2, 2, {CHECKPOINT_U:.10e}")
    for nid in phys_nodes:
        u1, u2 = transfer["nodal_u"][nid]
        d = transfer["nodal_d"][nid]
        pt = nodes[nid]
        # Snap bottom and pin values to exact zeroes to prevent floating epsilon discrepancies
        if abs(pt[1]) < 1e-6:
            u2 = 0.0
        if abs(pt[0]) < 1e-6 and abs(pt[1]) < 1e-6:
            u1 = 0.0
        lines.append(f"{nid}, 1, 1, {u1:.10e}")
        # Top nodes have DOF 2 tied to RP via EQUATION; omit DOF 2 to prevent inactive DOF / conflicting BC
        if abs(pt[1] - 0.100) >= 1e-6:
            lines.append(f"{nid}, 2, 2, {u2:.10e}")
        lines.append(f"{nid}, 3, 3, {d:.10e}")
    lines.append("*Output, field, frequency=1")
    lines.append("*Node Output")
    lines.append("U, RF")
    lines.append("*Output, history, frequency=1")
    lines.append("*Node Output, nset=N_RP")
    lines.append("RF2, U2")
    lines.append("*Energy Output")
    lines.append("ALLSE, ALLWK, ALLFD, ALLIE")
    lines.append("*End Step")

    # STEP 2: MECH_REEQUIL_FROZEN_DAMAGE
    lines.append("** ==========================================================")
    lines.append("** STEP 2: MECH_REEQUIL_FROZEN_DAMAGE (Interior Displacements Released)")
    lines.append("** Relaxes mapped interpolation strains under frozen damage field")
    lines.append("** ==========================================================")
    lines.append("*Step, name=MECH_REEQUIL_FROZEN_DAMAGE, nlgeom=NO, inc=50")
    lines.append("*Static")
    lines.append("0.1, 1.0, 1e-8, 1.0")
    lines.append("*Boundary, OP=NEW")
    lines.append("N_BOTTOM, 2, 2, 0.0")
    lines.append("N_PIN, 1, 1, 0.0")
    lines.append("N_RP, 1, 1, 0.0")
    lines.append(f"N_RP, 2, 2, {CHECKPOINT_U:.10e}")
    for nid in phys_nodes:
        d = transfer["nodal_d"][nid]
        lines.append(f"{nid}, 3, 3, {d:.10e}")
    lines.append("*Output, field, frequency=1")
    lines.append("*Node Output")
    lines.append("U, RF")
    lines.append("*Output, history, frequency=1")
    lines.append("*Node Output, nset=N_RP")
    lines.append("RF2, U2")
    lines.append("*Energy Output")
    lines.append("ALLSE, ALLWK, ALLFD, ALLIE")
    lines.append("*End Step")

    # STEP 3: STAGGERED_PHASE_SUBPROBLEM (Active Set re-equilibration)
    lines.append("** ==========================================================")
    lines.append("** STEP 3: STAGGERED_PHASE_SUBPROBLEM (Active-Set Phase Equilibrium)")
    lines.append("** Solves phase-field Euler-Lagrange equation under relaxed strains")
    lines.append("** ==========================================================")
    lines.append("*Step, name=STAGGERED_PHASE_SUBPROBLEM, nlgeom=NO, inc=100")
    lines.append("*Static")
    lines.append("1.0, 1.0, 1e-12, 1.0")
    lines.append("*Boundary, OP=NEW, FIXED")
    lines.append("N_PHYSICAL, 1, 2")
    lines.append("*Boundary, OP=NEW")
    lines.append("N_BOTTOM, 2, 2, 0.0")
    lines.append("N_PIN, 1, 1, 0.0")
    lines.append("N_RP, 1, 1, 0.0")
    lines.append(f"N_RP, 2, 2, {CHECKPOINT_U:.10e}")

    active_count = 0
    inactive_count = 0
    # Slit tip was at 0.040, crack tip reached 0.05125.
    # Allow nodes near crack path x in [0.038, 0.070], y in [0.045, 0.055] with d >= 0.15 to advance
    for nid in phys_nodes:
        pt = nodes[nid]
        d = transfer["nodal_d"][nid]
        dist_x = abs(pt[0] - 0.05125)
        dist_y = abs(pt[1] - 0.050)
        # Crack band region
        in_band = (0.035 <= pt[0] <= 0.075) and (dist_y <= 0.008)
        if (not in_band) or (d < 0.15):
            lines.append(f"{nid}, 3, 3, {d:.10e}")
            active_count += 1
        else:
            inactive_count += 1
    print(f"Phase active set: {active_count} constrained nodes, {inactive_count} free crack-band nodes.")

    lines.append("*Output, field, frequency=1")
    lines.append("*Node Output")
    lines.append("U, RF")
    lines.append("*Output, history, frequency=1")
    lines.append("*Node Output, nset=N_RP")
    lines.append("RF2, U2")
    lines.append("*Energy Output")
    lines.append("ALLSE, ALLWK, ALLFD, ALLIE")
    lines.append("*End Step")

    # STEP 4: FORWARD_CONTINUATION
    lines.append("** ==========================================================")
    lines.append(f"** STEP 4: FORWARD_CONTINUATION (Loading to u = {CONTINUATION_U:.8f} mm)")
    lines.append("** Tests second-cycle forward propagation on transferred fine discretization")
    lines.append("** ==========================================================")
    lines.append("*Step, name=FORWARD_CONTINUATION, nlgeom=NO, inc=100")
    lines.append("*Static")
    lines.append("0.05, 1.0, 1e-8, 0.2")
    lines.append("*Boundary, OP=NEW")
    lines.append("N_BOTTOM, 2, 2, 0.0")
    lines.append("N_PIN, 1, 1, 0.0")
    lines.append("N_RP, 1, 1, 0.0")
    lines.append(f"N_RP, 2, 2, {CONTINUATION_U:.10e}")
    lines.append("*Output, field, frequency=2")
    lines.append("*Node Output")
    lines.append("U, RF")
    lines.append("*Output, history, frequency=1")
    lines.append("*Node Output, nset=N_RP")
    lines.append("RF2, U2")
    lines.append("*Energy Output")
    lines.append("ALLSE, ALLWK, ALLFD, ALLIE")
    lines.append("*End Step")

    with open(OUT_TRANSFER_INP, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Generated input deck: {OUT_TRANSFER_INP} ({len(lines)} lines)")

    # 7. Write candidate C3 base deck
    from scripts.remeshing.generate_crack_band_mesh import write_abaqus_deck
    write_abaqus_deck(mesh_c3, OUT_C3_INP, ell=ELL0, gc=GC, e_mod=E_MOD, nu=NU, k_res=K_RES,
                      heading="Candidate C3: Second-Cycle Target Crack-Band Resolved (h=0.0010 mm <= ell/7.5)")

    # 8. Write PBS script
    pbs_content = f"""#!/bin/bash
#PBS -N M1_C3_TRANSFER
#PBS -l select=1:ncpus=1:mem=8gb
#PBS -l walltime=04:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_package90_c3_transfer/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_package90_c3_transfer"
cd "${{RUN_DIR}}"

export JOB_NAME="M1_C3_PACKAGE90_TRANSFER"
export NOTIFICATION_CONFIG="${{NOTIFICATION_CONFIG:-${{HOME}}/.config/adaptive-remeshing/notifications.env}}"
source "${{RUN_DIR}}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

JOB_NAME="M1_C3_PACKAGE90_TRANSFER"
INP_NAME="M1_C3_PACKAGE90_TRANSFER.inp"
USER_SUB="f42_mixed_uel.for"

test ! -e "${{JOB_NAME}}.lck"

echo "Starting Abaqus analysis ${{JOB_NAME}} at $(date)"
abaqus job="${{JOB_NAME}}" input="${{INP_NAME}}" user="${{USER_SUB}}" cpus=1 interactive
EXIT_CODE=$?
echo "Abaqus completed with exit code ${{EXIT_CODE}} at $(date)"

exit ${{EXIT_CODE}}
"""
    dst_pbs = OUT_DIR / "submit_M1_C3_PACKAGE90_TRANSFER.pbs"
    dst_pbs.write_bytes(pbs_content.encode("utf-8").replace(b"\r\n", b"\n"))

    # 9. Write Datacheck script
    dc_content = f"""#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_package90_c3_transfer"
cd "${{RUN_DIR}}"

export XDG_RUNTIME_DIR="${{XDG_RUNTIME_DIR:-/tmp/xdg_runtime_${{USER}}}}"
mkdir -p "${{XDG_RUNTIME_DIR}}"
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Running Abaqus Datacheck on M1_C3_PACKAGE90_TRANSFER.inp..."
rm -f M1_C3_PACKAGE90_TRANSFER_DC.lck M1_C3_PACKAGE90_TRANSFER_DC.log M1_C3_PACKAGE90_TRANSFER_DC.dat M1_C3_PACKAGE90_TRANSFER_DC.msg M1_C3_PACKAGE90_TRANSFER_DC.sta M1_C3_PACKAGE90_TRANSFER_DC.prt
abaqus datacheck job=M1_C3_PACKAGE90_TRANSFER_DC input=M1_C3_PACKAGE90_TRANSFER.inp user=f42_mixed_uel.for interactive
DC_EXIT=$?
echo "Datacheck finished with Exit Code: ${{DC_EXIT}}"
exit ${{DC_EXIT}}
"""
    dst_dc = OUT_DIR / "run_pkg90_datacheck.sh"
    dst_dc.write_bytes(dc_content.encode("utf-8").replace(b"\r\n", b"\n"))

    # 10. Audit JSON
    audit_data = {
        "status": "PACKAGE90_PREPARED",
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "package_name": "Package 90: Candidate C2 -> Candidate C3 Second-Cycle Nonmatching State Transfer",
        "donor_state": {
            "source": "Package 89 Terminal State (Job 1416539 Step 4 Inc 8)",
            "u_terminal_mm": CHECKPOINT_U,
            "rf2_terminal_N": 169.5991,
            "d_max_terminal": 0.856958449,
            "donor_at2_fracture_energy_uJ": float(donor["at2_energy"] * 1e6)
        },
        "receiver_discretization": {
            "candidate": "C3",
            "n_quads": n_elems,
            "n_nodes": len(nodes) - 1,
            "min_det_jac": mesh_c3["min_det_jac"],
            "max_aspect_ratio": mesh_c3["max_aspect_ratio"],
            "fine_band_x_mm": [0.0375, 0.0775],
            "fine_band_h_mm": 0.00125,
            "receiver_at2_fracture_energy_uJ": float(transfer["receiver_at2_energy"] * 1e6),
            "delta_fracture_energy_pct": float(transfer["delta_energy_pct"])
        },
        "continuation": {
            "target_displacement_mm": CONTINUATION_U,
            "delta_u_mm": CONTINUATION_U - CHECKPOINT_U,
            "stages": [
                "STATE_INJECTION (Clamped at u = 0.00201511 mm)",
                "MECH_REEQUIL_FROZEN_DAMAGE (Displacements released, damage frozen)",
                "STAGGERED_PHASE_SUBPROBLEM (Active-set phase re-equilibration)",
                "FORWARD_CONTINUATION (Coupled loading to u = 0.00206511 mm)"
            ]
        },
        "files": {
            "M1_C3_PACKAGE90_TRANSFER.inp": sha256_file(OUT_TRANSFER_INP),
            "candidate_c3_frame89_mapped_state_table.csv": sha256_file(OUT_MAPPED_CSV),
            "candidate_crack_band_mesh_c3.inp": sha256_file(OUT_C3_INP),
            "f42_mixed_uel.for": sha256_file(dst_uel),
            "submit_M1_C3_PACKAGE90_TRANSFER.pbs": sha256_file(dst_pbs),
            "run_pkg90_datacheck.sh": sha256_file(dst_dc)
        }
    }

    with open(OUT_AUDIT_JSON, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)
    print(f"Wrote audit artifact: {OUT_AUDIT_JSON}")

if __name__ == "__main__":
    build_package90()
