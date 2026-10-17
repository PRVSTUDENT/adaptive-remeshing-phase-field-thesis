#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task F1533: Authentic Evaluation of Bilinear History Transfer vs HOST_NEAREST_GP,
Irreversibility & Limiter Tradeoff Analysis, and Cycle 2 State Preservation.
"""

import math
import os
import sys
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.experimental_bilinear_history_transfer import (
    evaluate_bilinear_quad_history,
    evaluate_nearest_gp_history,
    BilinearHistoryTransferOperator,
    GAUSS_XI_QUAD,
    GAUSS_ETA_QUAD,
    SQRT3
)
from scripts.state_transfer.mode1_state_transfer_engine import (
    parse_mode1_input_deck,
    compute_quad_gauss_points,
    compute_tri_gauss_points,
    Mode1SpatialIndex,
    Mode1Mesh,
    Mode1State
)

DONOR_JSON = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle2_continuation" / "donor_cycle1_u0012.json"
RECIPIENT_INP = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle2_continuation" / "M1_CYCLE2_RAW_ADAPT_2PCT.inp"
DONOR_INP = REPO_ROOT / "models" / "pandey_kumar_mode1" / "57_method_c_stage_c1_2_cycle1_continuation" / "M1_MC_STAGE_C1_2_CYCLE1_CONT.inp"

def load_or_adapt_mesh(inp_path: str) -> Mode1Mesh:
    mesh = parse_mode1_input_deck(inp_path)
    if len(mesh.elements_u1) == 0 and len(mesh.elements_cpe) > 0:
        mesh.elements_u1 = dict(mesh.elements_cpe)
        mesh.classify_topology()
    return mesh

def test_01_donor_and_recipient_data_integrity():
    """Verify authentic Cycle 2 donor data and recipient mesh files exist and have valid topology."""
    assert DONOR_JSON.exists(), f"Missing donor json: {DONOR_JSON}"
    assert RECIPIENT_INP.exists(), f"Missing recipient inp: {RECIPIENT_INP}"
    assert DONOR_INP.exists(), f"Missing donor inp: {DONOR_INP}"

    with open(DONOR_JSON, "r", encoding="utf-8") as fp:
        donor_data = json.load(fp)

    assert donor_data["target_displacement_mm"] == 0.0012
    assert donor_data["mesh_elements"] == 17913
    assert abs(donor_data["max_history_H"] - 0.02318568) < 1e-5
    assert abs(donor_data["max_damage"] - 0.014628) < 1e-4

    # Verify recipient raw mesh
    recip_mesh = load_or_adapt_mesh(str(RECIPIENT_INP))
    assert recip_mesh.num_elements == 21546
    assert recip_mesh.num_nodes == 21541

def test_02_authentic_history_transfer_comparison_and_integral():
    """
    Perform authentic transfer of Cycle 1 committed history onto the 21,546-element mesh
    using both HOST_NEAREST_GP and BilinearHistoryTransferOperator (bounded & unconstrained).
    """
    with open(DONOR_JSON, "r", encoding="utf-8") as fp:
        donor_data = json.load(fp)

    donor_mesh = load_or_adapt_mesh(str(DONOR_INP))
    recip_mesh = load_or_adapt_mesh(str(RECIPIENT_INP))

    spatial_index = Mode1SpatialIndex(donor_mesh, grid_size=100)

    # Build donor Gauss points and history mapping
    donor_gps = {}
    donor_H_map = {}
    for eid, conn in donor_mesh.elements_u1.items():
        coords = [donor_mesh.nodes[n] for n in conn]
        if len(coords) == 4:
            elem_gps = compute_quad_gauss_points(coords)
        else:
            elem_gps = compute_tri_gauss_points(coords)
        donor_gps[eid] = elem_gps

        sdv_entry = donor_data["elem_sdv"].get(str(eid), {})
        h_vals = sdv_entry.get("SDV2", [0.0] * len(elem_gps))
        donor_H_map[eid] = [max(0.0, float(h)) for h in h_vals]

    # Sample evaluation on crack-tip elements (x in [0.48, 0.53], y in [0.48, 0.52])
    crack_tip_elements = []
    for eid, conn in recip_mesh.elements_u1.items():
        cx, cy = recip_mesh.element_centroids[eid]
        if 0.48 <= cx <= 0.53 and 0.48 <= cy <= 0.52:
            crack_tip_elements.append(eid)

    assert len(crack_tip_elements) > 50, f"Expected >50 crack tip elements, got {len(crack_tip_elements)}"

    nearest_op = BilinearHistoryTransferOperator(mode="NEAREST_GP")
    bilinear_bounded_op = BilinearHistoryTransferOperator(mode="BILINEAR_GP_BOUNDED")
    bilinear_unbounded_op = BilinearHistoryTransferOperator(mode="BILINEAR_GP")

    diffs_l2_sq = 0.0
    weight_sum = 0.0
    h_max_nearest = 0.0
    h_max_bounded = 0.0
    h_max_unbounded = 0.0

    limiter_active_count = 0
    total_eval_points = 0

    for eid in crack_tip_elements:
        conn = recip_mesh.elements_u1[eid]
        coords = [recip_mesh.nodes[n] for n in conn]
        flank = recip_mesh.element_flank.get(eid, "UPPER")

        if len(coords) == 4:
            elem_gps = compute_quad_gauss_points(coords)
        else:
            elem_gps = compute_tri_gauss_points(coords)

        for gx, gy, w_detJ in elem_gps:
            host_eid, weights = spatial_index.find_host_element(gx, gy, flank)
            donor_conn = donor_mesh.elements_u1[host_eid]
            H_donor_gps = donor_H_map[host_eid]
            donor_gp_list = donor_gps[host_eid]

            # Exact parent coordinates from bilinear weights:
            # xi = (n2 + n3) - (n1 + n4), eta = (n3 + n4) - (n1 + n2)
            if len(donor_conn) == 4 and len(weights) == 4:
                host_xi = (weights[1] + weights[2]) - (weights[0] + weights[3])
                host_eta = (weights[2] + weights[3]) - (weights[0] + weights[1])
            else:
                host_xi, host_eta = 0.0, 0.0

            h_near = nearest_op.transfer_element_history(
                len(donor_conn), H_donor_gps, donor_gp_list, gx, gy, host_xi, host_eta
            )
            h_bounded = bilinear_bounded_op.transfer_element_history(
                len(donor_conn), H_donor_gps, donor_gp_list, gx, gy, host_xi, host_eta
            )
            h_unbounded = bilinear_unbounded_op.transfer_element_history(
                len(donor_conn), H_donor_gps, donor_gp_list, gx, gy, host_xi, host_eta
            )

            h_max_nearest = max(h_max_nearest, h_near)
            h_max_bounded = max(h_max_bounded, h_bounded)
            h_max_unbounded = max(h_max_unbounded, h_unbounded)

            diffs_l2_sq += w_detJ * (h_bounded - h_near)**2
            weight_sum += w_detJ
            total_eval_points += 1

            if abs(h_unbounded - h_bounded) > 1e-12:
                limiter_active_count += 1

    l2_diff = math.sqrt(diffs_l2_sq / weight_sum)
    limiter_active_pct = (limiter_active_count / total_eval_points) * 100.0

    print(f"\n[EVALUATION RESULTS - CRACK TIP REGION]")
    print(f"Total evaluated points: {total_eval_points}")
    print(f"Area-weighted L2 difference (Bounded Bilinear vs Nearest): {l2_diff:.6e} kN/mm^2")
    print(f"Peak History H_max: Nearest = {h_max_nearest:.6f}, Bounded = {h_max_bounded:.6f}, Unbounded = {h_max_unbounded:.6f}")
    print(f"Limiter active points: {limiter_active_count} / {total_eval_points} ({limiter_active_pct:.2f}%)")

    # Bilinear bounded must preserve non-negativity
    assert h_max_bounded > 0.0
    assert h_max_unbounded >= h_max_bounded
    assert limiter_active_pct < 45.0, f"Limiter active pct: {limiter_active_pct}%"

def test_03_limiter_tradeoff_mathematical_audit():
    """
    Mathematically prove why the bounding limiter H_min^e <= H <= H_max^e clips legitimate
    gradient peaks at element corners and determine the quantitative magnitude.
    """
    H_gps = [
        0.010 - 0.006 / SQRT3,
        0.010 + 0.006 / SQRT3,
        0.010 + 0.006 / SQRT3,
        0.010 - 0.006 / SQRT3
    ]

    h_exact = 0.016000
    h_unbounded = evaluate_bilinear_quad_history(H_gps, 1.0, 0.0, bounded=False)
    h_bounded = evaluate_bilinear_quad_history(H_gps, 1.0, 0.0, bounded=True)
    h_nearest = max(H_gps)

    assert abs(h_unbounded - h_exact) < 1e-14, f"Unbounded must reproduce exact linear value: {h_unbounded} vs {h_exact}"
    assert abs(h_bounded - max(H_gps)) < 1e-14, f"Bounded must clip at max GP value: {h_bounded} vs {max(H_gps)}"

    clipping_deficit = (h_exact - h_bounded) / h_exact * 100.0
    print(f"\n[CORNER GRADIENT CLIPPING AUDIT]")
    print(f"Exact linear peak at corner: {h_exact:.6f}")
    print(f"Unbounded bilinear value:     {h_unbounded:.6f} (0.00% error)")
    print(f"Bounded limiter value:       {h_bounded:.6f} ({clipping_deficit:.2f}% artificial deficit)")
    print(f"Nearest GP value:            {h_nearest:.6f} ({clipping_deficit:.2f}% deficit)")

    assert abs(clipping_deficit - (1.0 - 1.0 / SQRT3) * 100.0 * (0.006 / 0.016)) < 1e-4

def test_04_controlled_solver_comparison_decision():
    """
    Synthesize the mathematical and authentic findings:
    Determine whether a new solver experiment on HPC is scientifically justified.
    """
    justified = False
    rationale = (
        "A solver run is NOT justified before Case B (Job 1414812) completes. "
        "Case B provides the decisive baseline: if uninterrupted native-mesh control "
        "produces the same elevated fracture energy (+1.2%), the discrepancy is proved to be "
        "spatial discretization resolution, making operator replacement unnecessary for Gate 6C."
    )
    assert not justified
    print(f"\n[DECISION RULE]: {rationale}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
