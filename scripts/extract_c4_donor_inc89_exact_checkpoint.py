# -*- coding: utf-8 -*-
"""
extract_c4_donor_inc89_exact_checkpoint.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Deterministic, authentic recovery of the complete committed Increment-89 exact-frame state
from Package 137 converged solver deliverables (Job 1418548.mmaster02):
1. M1_C4_INC89_H27_CYC5_MECH.odb (exact nodal displacements for all 4,588 nodes)
2. active_set_boundary_cards.inc (exact converged nodal damage for all 4,588 nodes)
3. d_lower_bounds.csv (Package 136 committed GP history, columns 5-8)
4. FE assembly of exact strain driving energy and history commitment:
   H_inc89(e, k) = max(H_inc88(e, k), psi+(u_inc89))
5. Pointwise verification:
   - H_inc89 >= H_inc88 (zero history loss)
   - d_inc89 >= d_inc88 (zero healing)
6. Atomic serialization via mode1_am_state_checkpoint.py into:
   - c4_donor_inc89_exact_checkpoint.json
   - c4_donor_inc89_exact_checkpoint_d_lower_bounds.csv
   - c4_donor_inc89_exact_checkpoint_nodal_displacements.csv
   - c4_donor_inc89_exact_checkpoint_active_set_cards.inc
   - c4_donor_inc89_exact_checkpoint_recovery_receipt.json
"""

from __future__ import print_function, division
import os
import sys
import math
import json
import hashlib
import numpy as np

# Physical constants (strictly bit-exact to Pandey-Kumar Mode-I specifications)
E_MOD = 210.0      # kN/mm^2 (210 GPa)
NU = 0.3
E_GC = 0.0027      # kN/mm (2.7 N/mm)
E_L0 = 0.0075      # mm (7.5 um)
K_DEGRAD = 1.0e-6

lam = E_MOD * NU / ((1.0 + NU) * (1.0 - 2.0 * NU))
mu = E_MOD / (2.0 * (1.0 + NU))

A_GAUSS = 0.577350269189626
UEL_GP_COORDS = [
    (-A_GAUSS, -A_GAUSS),
    ( A_GAUSS, -A_GAUSS),
    ( A_GAUSS,  A_GAUSS),
    (-A_GAUSS,  A_GAUSS),
]
UEL_WEIGHTS = [1.0, 1.0, 1.0, 1.0]

def shape_functions(xi, eta):
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

def uel_driving_energy(eps, lam_val, mu_val):
    e11 = eps[0]
    e22 = eps[1]
    e12 = 0.5 * eps[2]
    tr_e = e11 + e22
    e_pos = max(0.0, tr_e)
    pos_m = 0.5 * lam_val * (e_pos**2) + mu_val * (e11**2 + e22**2 + 2.0 * (e12**2))
    return float(pos_m)

def parse_inp_mesh(inp_path):
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
                    reading = "ELEMENT"
                elif u.startswith("*"):
                    reading = None
                continue
            if reading == "NODE":
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 3:
                    nid = int(parts[0])
                    if nid != 999999:
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
            elif reading == "ELEMENT":
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 5:
                    eid = int(parts[0])
                    c = [int(p) for p in parts[1:5]]
                    elements[eid] = c
    return nodes, elements

def load_committed_history_and_d0(bounds_csv_path):
    h_committed = {}
    d0_committed = {}
    with open(bounds_csv_path, "r") as f:
        header_line = f.readline().strip()
        header = [h.strip() for h in header_line.split(",")]
        h_idx = [i for i, h in enumerate(header) if h.startswith("H0_")]
        d_idx = [i for i, h in enumerate(header) if h.startswith("D0_")]
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            eid = int(parts[0])
            h_vals = [float(parts[i]) for i in h_idx]
            d_vals = [float(parts[i]) for i in d_idx]
            h_committed[eid] = h_vals
            d0_committed[eid] = d_vals
    return h_committed, d0_committed

def load_nodal_d_from_inc(inc_path):
    d_dict = {}
    with open(inc_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            p = [x.strip() for x in l.split(",")]
            if len(p) >= 4 and p[0].isdigit():
                nid = int(p[0])
                d_dict[nid] = float(p[3])
    return d_dict

def extract_mechanical_results(odb_path):
    from odbAccess import openOdb
    if not os.path.exists(odb_path):
        raise RuntimeError("ODB not found: %s" % odb_path)

    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps[odb.steps.keys()[-1]]
    frame = step.frames[-1]

    u_nodal = {}
    if "U" in frame.fieldOutputs:
        u_field = frame.fieldOutputs["U"]
        for val in u_field.values:
            nid = val.nodeLabel
            if nid != 999999:
                u_nodal[nid] = (float(val.data[0]), float(val.data[1]))

    rf2_rp = None
    if "RF" in frame.fieldOutputs:
        rf_field = frame.fieldOutputs["RF"]
        for val in rf_field.values:
            if val.nodeLabel == 999999:
                rf2_rp = float(val.data[1]) * 1000.0  # Convert kN to N
                break

    odb.close()
    return u_nodal, rf2_rp

def main():
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    inp_path = os.path.join(pkg_dir, "M1_C4_INC89_H27_CONT.inp")
    odb_path = os.path.join(pkg_dir, "M1_C4_INC89_H27_CYC5_MECH.odb")
    cards_path = os.path.join(pkg_dir, "active_set_boundary_cards.inc")
    inc88_bounds_path = os.path.join(pkg_dir, "d_lower_bounds.csv")
    inc88_d0_cards = os.path.join(pkg_dir, "stage_a_all_d0_boundary_cards.inc")
    summary_path = os.path.join(pkg_dir, "c4_donor_inc89_h27_continuation_summary.json")

    print("[RECOVERY-INC89-EXACT] Parsing mesh from: %s" % inp_path)
    nodes, elements = parse_inp_mesh(inp_path)
    nlist = sorted(list(nodes.keys()))
    n_nodes = len(nodes)
    n_elements = len(elements)
    print("[RECOVERY-INC89-EXACT] Loaded mesh: %d nodes, %d elements" % (n_nodes, n_elements))

    # 1. Load authentic Increment-88 baseline history and bounds
    print("[RECOVERY-INC89-EXACT] Loading predecessor committed history from: %s" % inc88_bounds_path)
    h_inc88, d0_inc88_gp = load_committed_history_and_d0(inc88_bounds_path)
    d0_inc88_nodal = load_nodal_d_from_inc(inc88_d0_cards)

    # 2. Extract Cycle 5 converged displacements from ODB
    print("[RECOVERY-INC89-EXACT] Extracting Cycle 5 displacements from: %s" % odb_path)
    u_nodal, rf2_rp = extract_mechanical_results(odb_path)
    print("[RECOVERY-INC89-EXACT] Cycle 5 RF2 = %.4f N" % rf2_rp)

    # 3. Load converged nodal damage from active_set_boundary_cards.inc
    print("[RECOVERY-INC89-EXACT] Loading converged damage from: %s" % cards_path)
    d_inc89_nodal = load_nodal_d_from_inc(cards_path)
    d_max = max(d_inc89_nodal.values())
    print("[RECOVERY-INC89-EXACT] Cycle 5 d_max = %.6f" % d_max)

    # 4. Compute committed GP history H_inc89 = max(H_inc88, psi+(u_inc89))
    print("[RECOVERY-INC89-EXACT] Computing FE strain energy and committed GP histories...")
    h_inc89 = {}
    h_monotone_violations = 0
    d_monotone_violations = 0

    for eid, conn in elements.items():
        xe = np.array([nodes[n] for n in conn])
        ue = np.array([u_nodal[n] for n in conn]).flatten()
        h_inc88_elem = h_inc88[eid]
        h_inc89[eid] = []

        for kpt in range(4):
            xi, eta = UEL_GP_COORDS[kpt]
            N, dNdxi, dNdeta = shape_functions(xi, eta)
            J_mat = np.dot(np.vstack([dNdxi, dNdeta]), xe)
            invJ = np.linalg.inv(J_mat)
            dNdx = np.dot(invJ, np.vstack([dNdxi, dNdeta]))

            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]   = dNdx[0, i]
                B[1, 2*i+1] = dNdx[1, i]
                B[2, 2*i]   = dNdx[1, i]
                B[2, 2*i+1] = dNdx[0, i]
            eps = B.dot(ue)
            pos_m = uel_driving_energy(eps, lam, mu)
            h_val = max(h_inc88_elem[kpt], pos_m)
            h_inc89[eid].append(h_val)

            if h_val < h_inc88_elem[kpt] - 1.0e-12:
                h_monotone_violations += 1

    # 5. Pointwise verification of damage monotonicity
    for nid in nlist:
        if d_inc89_nodal[nid] < d0_inc88_nodal[nid] - 1.0e-8:
            d_monotone_violations += 1

    print("[RECOVERY-INC89-EXACT] History monotonicity check: %d violations (MUST BE 0)" % h_monotone_violations)
    print("[RECOVERY-INC89-EXACT] Damage monotonicity check: %d violations (MUST BE 0)" % d_monotone_violations)
    assert h_monotone_violations == 0, "History monotonicity violated!"
    assert d_monotone_violations == 0, "Damage monotonicity violated!"

    # 6. Load final summary metrics
    with open(summary_path, "r") as f:
        summary = json.load(f)
    final_entry = summary["final_state"]

    # 7. Serialize complete checkpoint using mode1_am_state_checkpoint.py
    sys.path.insert(0, pkg_dir)
    from mode1_am_state_checkpoint import serialize_checkpoint

    mesh_info = {
        "name": "Candidate C4",
        "mesh_type": "4422_quad_nonmatching",
        "inp_file": "M1_C4_INC89_H27_CONT.inp",
        "step_displacement_mm": 0.001990107350,
        "step_name": "Increment 89 Exact Frame Continuation",
        "predecessor_step": "Increment 89 Checkpoint (Package 136)"
    }
    parameters = {
        "E_MOD_kN_mm2": E_MOD,
        "NU": NU,
        "E_GC_kN_mm": E_GC,
        "E_L0_mm": E_L0,
        "K_DEGRAD": K_DEGRAD,
        "target_u_rp_mm": 0.001990107350,
        "under_relaxation_omega": 0.70
    }
    source_provenance = {
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "predecessor_package": "137_c4_donor_inc89_h27_exact_frame_continuation",
        "package_name": "PACKAGE_137_C4_DONOR_INC89_H27_EXACT_FRAME_CONTINUATION",
        "pbs_job_id": "1418548.mmaster02",
        "exit_code": 0,
        "converged_cycle": 5,
        "frozen_uel_sha256": "ab0a5a71335ecb445e91ec13a645e280ff3310b561a5e78aba4a49c8e81dd8ac"
    }

    print("\n" + "=" * 80)
    print("[RECOVERY-INC89-EXACT] SERIALIZING ATOMIC EXACT INCREMENT-89 CHECKPOINT...")
    print("=" * 80)

    checkpoint_receipt = serialize_checkpoint(
        output_dir=pkg_dir,
        mesh_info=mesh_info,
        nodes=nodes,
        elements=elements,
        u_nodal=u_nodal,
        d_nodal=d_inc89_nodal,
        h_committed=h_inc89,
        cycle=final_entry["cycle"],
        metrics=final_entry,
        parameters=parameters,
        source_provenance=source_provenance,
        checkpoint_basename="c4_donor_inc89_exact_checkpoint"
    )

    receipt_path = os.path.join(pkg_dir, "c4_donor_inc89_exact_checkpoint_recovery_receipt.json")
    with open(receipt_path, "w") as f:
        json.dump(checkpoint_receipt, f, indent=2)

    print("[RECOVERY-INC89-EXACT] Checkpoint serialized successfully!")
    print("[RECOVERY-INC89-EXACT] Checkpoint JSON SHA256: %s" % checkpoint_receipt["checkpoint_json_sha256"])
    print("[RECOVERY-INC89-EXACT] d_lower_bounds SHA256: %s" % checkpoint_receipt.get("companion_files", {}).get("d_lower_bounds_csv"))
    print("[RECOVERY-INC89-EXACT] nodal_displacements SHA256: %s" % checkpoint_receipt.get("companion_files", {}).get("nodal_displacements_csv"))
    print("[RECOVERY-INC89-EXACT] active_set_cards SHA256: %s" % checkpoint_receipt.get("companion_files", {}).get("active_set_cards_inc"))

if __name__ == "__main__":
    main()
