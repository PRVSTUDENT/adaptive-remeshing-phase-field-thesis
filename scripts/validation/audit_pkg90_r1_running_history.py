#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audit_pkg90_r1_running_history.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: b13e68ac-0d42-4db1-ae22-779415f0ae6e
Protocol Version: 2

Performs a rigorous Gauss-point level provenance and running-maximum history audit
on Package 90-R1 (Job 1416558).
Traces the exact strain trajectory across all accepted increments up to Frame 6:
  Step 1: Frame 1
  Step 2: Frames 1..6
  Step 3: Frame 1
  Step 4: Frames 0, 2, 4, 6 (u2 = 0.002036693 mm)
Computes:
  H_running(eid, kpt) = max_{t <= t_frame6} psi0^+(eps(u(t)))
Compares against the single-checkpoint reconstruction:
  H_frame6(eid, kpt) = max(H_init, psi0^+(eps(u_frame6)))
Quantifies underestimation counts, max absolute error, relative error, and spatial distribution.
"""

import os
import sys
import math
import json
import csv
from odbAccess import openOdb

# Physical constants
E_MOD = 210.0      # kN/mm^2
E_NU = 0.3
C12_0 = E_MOD * E_NU / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
C33_0 = E_MOD / (2.0 * (1.0 + E_NU))

WORK_DIR = "/scratch9/pr21vyci/runs/mode1_package90_r1_c3_transfer"
ODB_PATH = os.path.join(WORK_DIR, "M1_C3_PACKAGE90_R1_TRANSFER.odb")
INP_PATH = os.path.join(WORK_DIR, "M1_C3_PACKAGE90_R1_TRANSFER.inp")
MESH_INP = os.path.join(WORK_DIR, "candidate_crack_band_mesh_c3.inp")
OUT_JSON = os.path.join(WORK_DIR, "pkg90_r1_running_history_audit.json")
OUT_CSV = os.path.join(WORK_DIR, "pkg90_r1_running_vs_frame6_history.csv")

def parse_initial_history(inp_path):
    print("Parsing initial history from %s..." % inp_path)
    elem_h_init = {}
    with open(inp_path, "r") as f:
        in_init = False
        current_eid = None
        state = 0
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                u = l.upper()
                if "*INITIAL CONDITIONS" in u and "TYPE=SOLUTION" in u:
                    in_init = True
                    state = 0
                    continue
                elif in_init:
                    break
            if in_init:
                parts = [p.strip() for p in l.split(",")]
                if state == 0:
                    if parts[0].isdigit():
                        current_eid = int(parts[0])
                        state = 1
                elif state == 1:
                    h_vals = [float(p) for p in parts[:4]]
                    elem_h_init[current_eid] = h_vals
                    state = 2
                elif state == 2:
                    state = 0
    print("Parsed H_init for %d elements." % len(elem_h_init))
    return elem_h_init

def parse_mesh_from_inp(mesh_path):
    print("Parsing mesh from %s..." % mesh_path)
    nodes = {}
    with open(mesh_path, "r") as f:
        reading = False
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE") and not u.startswith("*NODE OUTPUT"):
                    reading = True
                else:
                    reading = False
                continue
            if reading:
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 3 and parts[0].isdigit():
                    nid = int(parts[0])
                    if nid != 999999:
                        nodes[nid] = (float(parts[1]), float(parts[2]))

    elements = {}
    with open(mesh_path, "r") as f:
        reading = False
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*ELEMENT") and "TYPE=U1" in u:
                    reading = True
                else:
                    reading = False
                continue
            if reading:
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 5 and parts[0].isdigit():
                    eid = int(parts[0])
                    elements[eid] = [int(p) for p in parts[1:5]]
    print("Parsed %d nodes and %d physical quad elements." % (len(nodes), len(elements)))
    return nodes, elements

def main():
    if not os.path.exists(ODB_PATH):
        raise RuntimeError("ODB not found: %s" % ODB_PATH)

    elem_h_init = parse_initial_history(INP_PATH)
    nodes, elements = parse_mesh_from_inp(MESH_INP)

    # Gauss point setup (2x2 quad)
    gp_coord = 1.0 / math.sqrt(3.0)
    xg4 = [-gp_coord, gp_coord, gp_coord, -gp_coord]
    yg4 = [-gp_coord, -gp_coord, gp_coord, gp_coord]

    # Precompute shape functions and B-matrices for each element and GP
    elem_B = {}
    for eid, conn in elements.items():
        elem_coords = [nodes[n] for n in conn]  # 4x2
        elem_B[eid] = []
        for kpt in range(4):
            xi = xg4[kpt]
            eta = yg4[kpt]

            # dN/dxi, dN/deta
            d_n = [
                [-0.25*(1.0-eta),  0.25*(1.0-eta),  0.25*(1.0+eta), -0.25*(1.0+eta)],
                [-0.25*(1.0-xi),  -0.25*(1.0+xi),   0.25*(1.0+xi),   0.25*(1.0-xi)]
            ]

            # Jacobian J = dN * coords (2x2)
            j11 = sum(d_n[0][k] * elem_coords[k][0] for k in range(4))
            j12 = sum(d_n[0][k] * elem_coords[k][1] for k in range(4))
            j21 = sum(d_n[1][k] * elem_coords[k][0] for k in range(4))
            j22 = sum(d_n[1][k] * elem_coords[k][1] for k in range(4))
            detJ = j11*j22 - j12*j21

            invJ11 =  j22 / detJ
            invJ12 = -j12 / detJ
            invJ21 = -j21 / detJ
            invJ22 =  j11 / detJ

            # dN/dx, dN/dy
            dNdx = [invJ11*d_n[0][k] + invJ12*d_n[1][k] for k in range(4)]
            dNdy = [invJ21*d_n[0][k] + invJ22*d_n[1][k] for k in range(4)]

            # B matrix: [ [dNdx_k, 0], [0, dNdy_k], [dNdy_k, dNdx_k] ]
            B = []
            for k in range(4):
                B.append((dNdx[k], dNdy[k]))
            elem_B[eid].append(B)

    print("Precomputed B-matrices for %d elements." % len(elem_B))

    # Initialize running history from H_initial
    h_running = {}
    for eid in elements:
        h_running[eid] = list(elem_h_init.get(eid, [0.0, 0.0, 0.0, 0.0]))

    odb = openOdb(ODB_PATH, readOnly=True)

    # List of trajectory frames up to Step 4 Frame 6
    trajectory_frames = []
    
    # Step 1
    st1 = odb.steps['STATE_INJECTION']
    trajectory_frames.append(('STATE_INJECTION', 1, st1.frames[-1]))
    
    # Step 2
    st2 = odb.steps['MECH_REEQUIL_FROZEN_DAMAGE']
    for idx, f in enumerate(st2.frames):
        trajectory_frames.append(('MECH_REEQUIL_FROZEN_DAMAGE', idx, f))

    # Step 3
    st3 = odb.steps['STAGGERED_PHASE_SUBPROBLEM']
    trajectory_frames.append(('STAGGERED_PHASE_SUBPROBLEM', 1, st3.frames[-1]))

    # Step 4: up to Frame 6 (frameId == 6)
    st4 = odb.steps['FORWARD_CONTINUATION']
    frame6_obj = None
    for idx, f in enumerate(st4.frames):
        trajectory_frames.append(('FORWARD_CONTINUATION', f.frameId, f))
        if f.frameId == 6:
            frame6_obj = f
            break

    print("Auditing %d frames along Package 90-R1 trajectory..." % len(trajectory_frames))

    for sname, fid, frame in trajectory_frames:
        if 'U' not in frame.fieldOutputs:
            continue
        u_field = frame.fieldOutputs['U']
        u_dict = {}
        for val in u_field.values:
            if val.nodeLabel <= 2769:
                u_dict[val.nodeLabel] = (float(val.data[0]), float(val.data[1]))

        # Evaluate psi0_pos at every GP and update running maximum
        for eid, conn in elements.items():
            u_elem = [u_dict.get(n, (0.0, 0.0)) for n in conn]
            for kpt in range(4):
                B = elem_B[eid][kpt]
                e11 = sum(B[k][0] * u_elem[k][0] for k in range(4))
                e22 = sum(B[k][1] * u_elem[k][1] for k in range(4))
                gam12 = sum(B[k][1] * u_elem[k][0] + B[k][0] * u_elem[k][1] for k in range(4))
                e12 = 0.5 * gam12

                tr_e = e11 + e22
                e_pos = max(0.0, tr_e)
                pos_m = 0.5 * C12_0 * (e_pos ** 2) + C33_0 * (e11**2 + e22**2 + 2.0 * (e12**2))

                if pos_m > h_running[eid][kpt]:
                    h_running[eid][kpt] = pos_m

    # Now evaluate single-frame history strictly at Frame 6
    print("Evaluating single-frame history at Frame 6...")
    u_f6 = {}
    for val in frame6_obj.fieldOutputs['U'].values:
        if val.nodeLabel <= 2769:
            u_f6[val.nodeLabel] = (float(val.data[0]), float(val.data[1]))

    h_frame6_only = {}
    for eid, conn in elements.items():
        u_elem = [u_f6.get(n, (0.0, 0.0)) for n in conn]
        h_frame6_only[eid] = []
        for kpt in range(4):
            B = elem_B[eid][kpt]
            e11 = sum(B[k][0] * u_elem[k][0] for k in range(4))
            e22 = sum(B[k][1] * u_elem[k][1] for k in range(4))
            gam12 = sum(B[k][1] * u_elem[k][0] + B[k][0] * u_elem[k][1] for k in range(4))
            e12 = 0.5 * gam12

            tr_e = e11 + e22
            e_pos = max(0.0, tr_e)
            pos_m = 0.5 * C12_0 * (e_pos ** 2) + C33_0 * (e11**2 + e22**2 + 2.0 * (e12**2))

            h_init = elem_h_init.get(eid, [0.0, 0.0, 0.0, 0.0])[kpt]
            h_f6 = max(h_init, pos_m)
            h_frame6_only[eid].append(h_f6)

    # Comparative analysis
    total_gps = len(elements) * 4
    underestimated_gps = 0
    max_abs_diff = 0.0
    max_rel_diff_pct = 0.0
    diff_records = []

    for eid in elements:
        for kpt in range(4):
            hrun = h_running[eid][kpt]
            hf6 = h_frame6_only[eid][kpt]
            diff = hrun - hf6
            rel_diff = (diff / hrun * 100.0) if hrun > 1e-12 else 0.0

            if diff > 1e-9:
                underestimated_gps += 1
                if diff > max_abs_diff:
                    max_abs_diff = diff
                if rel_diff > max_rel_diff_pct:
                    max_rel_diff_pct = rel_diff

            diff_records.append({
                "eid": eid,
                "kpt": kpt + 1,
                "H_init": elem_h_init.get(eid, [0.0, 0.0, 0.0, 0.0])[kpt],
                "H_running": hrun,
                "H_frame6_only": hf6,
                "diff": diff,
                "rel_diff_pct": rel_diff
            })

    print("\n--- RUNNING MAXIMUM VS FRAME 6 HISTORY AUDIT RESULTS ---")
    print("Total Gauss points: %d" % total_gps)
    print("Underestimated Gauss points (diff > 1e-9): %d / %d (%.2f%%)" % 
          (underestimated_gps, total_gps, 100.0 * underestimated_gps / total_gps))
    print("Max absolute error (H_running - H_f6): %.6e kN/mm^2" % max_abs_diff)
    print("Max relative underestimation: %.4f%%" % max_rel_diff_pct)

    summary = {
        "status": "RUNNING_HISTORY_AUDIT_COMPLETE",
        "total_elements": len(elements),
        "total_gauss_points": total_gps,
        "underestimated_points_count": underestimated_gps,
        "underestimated_fraction_pct": 100.0 * underestimated_gps / total_gps,
        "max_absolute_error_kNmm2": max_abs_diff,
        "max_relative_error_pct": max_rel_diff_pct,
        "trajectory_frames_audited": len(trajectory_frames),
        "running_h_max": max([max(h) for h in h_running.values()]),
        "frame6_h_max": max([max(h) for h in h_frame6_only.values()]),
        "verdict": "PERFECT_MONOTONIC_CONGRUENCE" if underestimated_gps == 0 else "HISTORY_UNDERESTIMATION_DETECTED"
    }

    with open(OUT_JSON, "w") as f:
        json.dump(summary, f, indent=2)
    print("Wrote summary JSON: %s" % OUT_JSON)

    # Write CSV of all points
    with open(OUT_CSV, "w") as f:
        writer = csv.DictWriter(f, fieldnames=["eid", "kpt", "H_init", "H_running", "H_frame6_only", "diff", "rel_diff_pct"])
        writer.writeheader()
        writer.writerows(diff_records)
    print("Wrote comparison CSV: %s" % OUT_CSV)

    odb.close()

if __name__ == "__main__":
    main()
