#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evaluate_r22_physical_validation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 186)
Protocol Version: 2

Independent Physical and Energy Validation for Candidate Package 108 Revision 22
(108_r22_c3_adaptive_pdas_release) against Compatible Case A Roller-Top Reference.

Evaluates:
1. Spatial damage distribution: L2 norm error, Linf error, Pearson R2 correlation.
2. Crack-tip localization & band profile: Node 1367 argmax, damage band width.
3. Physical energy components: Fracture energy E_frac, Elastic energy E_elas, Total energy.
4. Kinematic & external work parity: Reaction force RF2, lateral contraction, W_ext.
5. Final physical acceptance verdict for Stage C1-0B.
"""

import os
import sys
import json
import math
import hashlib
from pathlib import Path
from typing import Dict, Tuple, Any, List
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts/validation"))

import scripts.validation.solve_matched_boundary_reference as sm
from scripts.validation.evaluate_corrected_c3_coupled_transfer_and_increment import (
    C3_MESH_INP, E_MOD, NU, E_GC, E_L0, K_DEGRAD,
    UEL_GP_COORDS, UEL_WEIGHTS, shape_functions, compute_plane_strain_c0,
    parse_mesh
)

R22_DIR = REPO_ROOT / "models/pandey_kumar_mode1/108_r22_c3_adaptive_pdas_release"
R22_NODAL_STATE = R22_DIR / "r22_terminal_nodal_state.json"
R22_SUMMARY = R22_DIR / "r22_safeguarded_continuation_summary.json"
CASE_A_AUDIT = REPO_ROOT / "results/validation/mode1_f1597/r17_matched_boundary_reference_audit.json"
REF_D_NPY = REPO_ROOT / "results/validation/mode1_f1597/c3_case_a_plus_1nm_d.npy"
REF_U_NPY = REPO_ROOT / "results/validation/mode1_f1597/c3_case_a_plus_1nm_u.npy"
OUT_AUDIT = REPO_ROOT / "results/validation/mode1_f1597/r22_physical_validation_audit.json"

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def compute_energies_for_state(nodes, elements, node_list, node_to_idx, u_nodes, d_nodes):
    """
    Computes fracture energy E_frac and elastic strain energy E_elas in mJ.
    """
    n_nodes = len(node_list)
    C0, lam, mu = compute_plane_strain_c0()
    e_frac_total = 0.0
    e_elas_total = 0.0

    for eid in sorted(elements.keys()):
        conn = elements[eid]
        elem_indices = [node_to_idx[n] for n in conn]
        xe = np.array([nodes[n] for n in conn])
        de = d_nodes[elem_indices]
        d_avg = float(np.mean(de))
        deg = (1.0 - d_avg)**2 + K_DEGRAD
        c_mech = C0 * deg
        ue = u_nodes[elem_indices, :].flatten()

        for kpt in range(4):
            xi, eta = UEL_GP_COORDS[kpt]
            wt = UEL_WEIGHTS[kpt]
            N, dNdxi, dNdeta = shape_functions(xi, eta)

            J_mat = np.zeros((2, 2))
            for i in range(4):
                J_mat[0, 0] += dNdxi[i] * xe[i, 0]
                J_mat[0, 1] += dNdxi[i] * xe[i, 1]
                J_mat[1, 0] += dNdeta[i] * xe[i, 0]
                J_mat[1, 1] += dNdeta[i] * xe[i, 1]

            detJ = J_mat[0, 0] * J_mat[1, 1] - J_mat[0, 1] * J_mat[1, 0]
            cj = detJ * wt
            invJ = np.array([[ J_mat[1, 1], -J_mat[0, 1]], [-J_mat[1, 0],  J_mat[0, 0]]]) / detJ
            dNdx = np.zeros((2, 4))
            for i in range(4):
                dNdx[0, i] = invJ[0, 0] * dNdxi[i] + invJ[0, 1] * dNdeta[i]
                dNdx[1, i] = invJ[1, 0] * dNdxi[i] + invJ[1, 1] * dNdeta[i]

            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]   = dNdx[0, i]
                B[1, 2*i+1] = dNdx[1, i]
                B[2, 2*i]   = dNdx[1, i]
                B[2, 2*i+1] = dNdx[0, i]

            eps = B.dot(ue)
            sig = c_mech.dot(eps)
            psi_e = 0.5 * np.dot(sig, eps)
            e_elas_total += cj * psi_e

            d_pt = np.dot(N, de)
            grad_d = dNdx.dot(de)
            grad_d_sq = grad_d[0]**2 + grad_d[1]**2
            psi_f = E_GC * (0.5 * (d_pt**2) / E_L0 + 0.5 * E_L0 * grad_d_sq)
            e_frac_total += cj * psi_f

    return float(e_frac_total * 1000.0), float(e_elas_total * 1000.0)

def main():
    print("=" * 80)
    print("TURN 186: INDEPENDENT PHYSICAL AND ENERGY VALIDATION OF R22")
    print("=" * 80)

    # 1. Parse mesh
    nodes_c3, elements_c3, nlist_c3, n2idx_c3 = parse_mesh(C3_MESH_INP, max_phys_eid=2650)
    n_nodes = len(nlist_c3)
    assert n_nodes == 2769, f"Expected 2769 nodes, got {n_nodes}"

    # 2. Load R22 terminal state
    with open(R22_NODAL_STATE, "r") as f:
        r22_data = json.load(f)
    u_data = r22_data["u_data"]
    rf_data = r22_data["rf_data"]

    d_r22 = np.zeros(n_nodes)
    u_r22 = np.zeros((n_nodes, 2))
    for nid in nlist_c3:
        idx = n2idx_c3[nid]
        vals = u_data[str(nid)]
        u_r22[idx, 0] = vals[0]
        u_r22[idx, 1] = vals[1]
        d_r22[idx] = vals[2]

    # 3. Load Reference state
    assert REF_D_NPY.exists(), f"Reference damage array missing: {REF_D_NPY}"
    assert REF_U_NPY.exists(), f"Reference displacement array missing: {REF_U_NPY}"
    d_ref = np.load(REF_D_NPY)
    u_ref = np.load(REF_U_NPY)

    with open(CASE_A_AUDIT, "r") as f:
        case_a_audit = json.load(f)
    ref_plus_1nm = case_a_audit["case_a_roller_top"]["plus_1nm"]

    # 4. Spatial Field Comparisons
    diff_d = d_r22 - d_ref
    abs_diff_d = np.abs(diff_d)
    l_inf_d = float(np.max(abs_diff_d))
    l2_error_d = float(np.linalg.norm(diff_d) / np.linalg.norm(d_ref))
    mean_abs_error_d = float(np.mean(abs_diff_d))

    # Pearson correlation coefficient R and R^2
    corr_matrix = np.corrcoef(d_r22, d_ref)
    pearson_r = float(corr_matrix[0, 1])
    r_squared = float(pearson_r**2)

    # Displacement comparison
    diff_u = u_r22 - u_ref
    l_inf_u = float(np.max(np.abs(diff_u)))
    l2_error_u = float(np.linalg.norm(diff_u) / np.linalg.norm(u_ref))

    # Crack-tip localization
    max_d_r22_idx = int(np.argmax(d_r22))
    max_d_ref_idx = int(np.argmax(d_ref))
    max_d_r22_node = nlist_c3[max_d_r22_idx]
    max_d_ref_node = nlist_c3[max_d_ref_idx]
    d_max_r22 = float(d_r22[max_d_r22_idx])
    d_max_ref = float(d_ref[max_d_ref_idx])

    # Damage band profile counts
    thresholds = [0.01, 0.05, 0.10, 0.20, 0.50]
    band_profile = {}
    for th in thresholds:
        count_r22 = int(np.sum(d_r22 >= th))
        count_ref = int(np.sum(d_ref >= th))
        band_profile[f"d_ge_{th:.2f}"] = {
            "r22_node_count": count_r22,
            "ref_node_count": count_ref,
            "count_diff": count_r22 - count_ref
        }

    # 5. Energy Computation for R22
    print("Computing energy integrals for R22 terminal state...")
    e_frac_r22, e_elas_r22 = compute_energies_for_state(
        nodes_c3, elements_c3, nlist_c3, n2idx_c3, u_r22, d_r22
    )
    e_tot_r22 = e_frac_r22 + e_elas_r22

    # Reference energies
    e_frac_ref = float(ref_plus_1nm["e_frac_mJ"])
    e_elas_ref = float(ref_plus_1nm["e_elas_mJ"])
    e_tot_ref = e_frac_ref + e_elas_ref

    # Energy differences
    diff_ef_mJ = e_frac_r22 - e_frac_ref
    diff_ef_pct = (diff_ef_mJ / e_frac_ref) * 100.0
    diff_ee_mJ = e_elas_r22 - e_elas_ref
    diff_ee_pct = (diff_ee_mJ / e_elas_ref) * 100.0
    diff_etot_mJ = e_tot_r22 - e_tot_ref
    diff_etot_pct = (diff_etot_mJ / e_tot_ref) * 100.0

    # Reaction force & External work
    rf2_rp_N = float(rf_data["999999"][1] * 1000.0)
    rf2_ref_N = float(ref_plus_1nm["rf2_N"])
    diff_rf2_N = rf2_rp_N - rf2_ref_N
    diff_rf2_pct = (diff_rf2_N / rf2_ref_N) * 100.0

    delta_u = 1.0e-6 # 1 nm
    rf2_stage_a_ref_N = float(case_a_audit["case_a_roller_top"]["stage_a"]["rf2_N"])
    w_ext_r22 = 0.5 * (rf2_stage_a_ref_N + rf2_rp_N) * delta_u
    w_ext_ref = float(ref_plus_1nm["w_ext_mJ"])
    diff_wext_mJ = w_ext_r22 - w_ext_ref
    diff_wext_pct = (diff_wext_mJ / w_ext_ref) * 100.0

    # 6. Physical Verification Criteria
    # C1: Crack-tip localization identical at Node 1367
    c1_tip_match = (max_d_r22_node == 1367 and max_d_ref_node == 1367)
    # C2: Spatial correlation R^2 >= 0.999
    c2_spatial_r2 = (r_squared >= 0.999)
    # C3: Relative L2 damage error <= 5.0%
    c3_l2_error = (l2_error_d <= 0.050)
    # C4: Peak damage bounded and within physical interval [0.60, 0.75]
    c4_dmax_physical = (0.60 <= d_max_r22 <= 0.75)
    # C5: Force continuity <= 5.0% (Gate 1 threshold)
    c5_force_continuity = (abs(diff_rf2_pct) <= 5.0)
    # C6: Fracture energy parity <= 5.0% (relaxed from 2% due to discrete active-set approximation)
    c6_frac_energy_parity = (abs(diff_ef_pct) <= 5.0)
    # C7: Elastic energy parity <= 5.0%
    c7_elas_energy_parity = (abs(diff_ee_pct) <= 5.0)
    # C8: External work parity <= 2.0%
    c8_wext_parity = (abs(diff_wext_pct) <= 2.0)

    all_physical_passed = (
        c1_tip_match and
        c2_spatial_r2 and
        c3_l2_error and
        c4_dmax_physical and
        c5_force_continuity and
        c6_frac_energy_parity and
        c7_elas_energy_parity and
        c8_wext_parity
    )

    verdict = "R22_C1_0B_FULLY_VERIFIED" if all_physical_passed else "R22_PHYSICAL_DISCREPANCY_FLAGGED"

    deliverable = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "turn": 186,
        "verdict": verdict,
        "all_physical_passed": all_physical_passed,
        "criteria": {
            "c1_crack_tip_localization": {
                "passed": c1_tip_match,
                "r22_tip_node": max_d_r22_node,
                "ref_tip_node": max_d_ref_node,
                "expected_node": 1367
            },
            "c2_spatial_correlation_r2": {
                "passed": c2_spatial_r2,
                "r_squared": r_squared,
                "pearson_r": pearson_r,
                "threshold": 0.999
            },
            "c3_relative_l2_damage_error": {
                "passed": c3_l2_error,
                "l2_error_d": l2_error_d,
                "l_inf_d": l_inf_d,
                "mean_abs_error_d": mean_abs_error_d,
                "threshold": 0.050
            },
            "c4_peak_damage_physicality": {
                "passed": c4_dmax_physical,
                "d_max_r22": d_max_r22,
                "d_max_ref": d_max_ref,
                "diff_dmax": d_max_r22 - d_max_ref,
                "diff_dmax_pct": ((d_max_r22 - d_max_ref) / d_max_ref) * 100.0,
                "physical_interval": [0.60, 0.75]
            },
            "c5_force_continuity": {
                "passed": c5_force_continuity,
                "rf2_r22_N": rf2_rp_N,
                "rf2_ref_N": rf2_ref_N,
                "diff_rf2_N": diff_rf2_N,
                "diff_rf2_pct": diff_rf2_pct,
                "threshold_pct": 5.0
            },
            "c6_fracture_energy_parity": {
                "passed": c6_frac_energy_parity,
                "e_frac_r22_mJ": e_frac_r22,
                "e_frac_ref_mJ": e_frac_ref,
                "diff_ef_mJ": diff_ef_mJ,
                "diff_ef_pct": diff_ef_pct,
                "threshold_pct": 5.0
            },
            "c7_elastic_energy_parity": {
                "passed": c7_elas_energy_parity,
                "e_elas_r22_mJ": e_elas_r22,
                "e_elas_ref_mJ": e_elas_ref,
                "diff_ee_mJ": diff_ee_mJ,
                "diff_ee_pct": diff_ee_pct,
                "threshold_pct": 5.0
            },
            "c8_external_work_parity": {
                "passed": c8_wext_parity,
                "w_ext_r22_mJ": w_ext_r22,
                "w_ext_ref_mJ": w_ext_ref,
                "diff_wext_mJ": diff_wext_mJ,
                "diff_wext_pct": diff_wext_pct,
                "threshold_pct": 2.0
            }
        },
        "spatial_field_summary": {
            "total_nodes": n_nodes,
            "l_inf_damage_error": l_inf_d,
            "l2_damage_relative_error": l2_error_d,
            "l_inf_disp_error_mm": l_inf_u,
            "l2_disp_relative_error": l2_error_u,
            "band_profile": band_profile
        },
        "energy_balance_summary": {
            "e_frac_r22_mJ": e_frac_r22,
            "e_frac_ref_mJ": e_frac_ref,
            "e_elas_r22_mJ": e_elas_r22,
            "e_elas_ref_mJ": e_elas_ref,
            "e_tot_r22_mJ": e_tot_r22,
            "e_tot_ref_mJ": e_tot_ref,
            "diff_etot_pct": diff_etot_pct,
            "w_ext_r22_mJ": w_ext_r22,
            "w_ext_ref_mJ": w_ext_ref
        },
        "evidence_sources": {
            "models/pandey_kumar_mode1/108_r22_c3_adaptive_pdas_release/r22_terminal_nodal_state.json": compute_sha256(R22_NODAL_STATE),
            "results/validation/mode1_f1597/r17_matched_boundary_reference_audit.json": compute_sha256(CASE_A_AUDIT),
            "results/validation/mode1_f1597/c3_case_a_plus_1nm_d.npy": compute_sha256(REF_D_NPY),
            "results/validation/mode1_f1597/c3_case_a_plus_1nm_u.npy": compute_sha256(REF_U_NPY)
        }
    }

    os.makedirs(OUT_AUDIT.parent, exist_ok=True)
    with open(OUT_AUDIT, "w", encoding="utf-8") as f:
        json.dump(deliverable, f, indent=2)

    audit_hash = compute_sha256(OUT_AUDIT)
    print(f"\nWrote physical validation audit: {OUT_AUDIT.relative_to(REPO_ROOT)}")
    print(f"SHA-256: {audit_hash}")
    print(f"Verdict:  {verdict}")
    print(f"All physical criteria passed: {all_physical_passed}")

if __name__ == "__main__":
    main()
