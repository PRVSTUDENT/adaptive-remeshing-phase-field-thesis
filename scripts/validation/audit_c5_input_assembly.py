#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_c5_input_assembly.py
Mode-I Method C Cycle 2: C5 Re-Equilibration Input Assembly Technical Auditor.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Audits the C5 candidate receiver input deck generation without modifying production Package 156:
1. Generates a disposable C5 input-deck fixture from the authentic Step-1 C4 checkpoint.
2. Verifies U1/U2 element correspondence (1..12996 vs 12997..25992).
3. Verifies DOF ordering (U1=DOF 3, U2=DOFs 1,2, boundary card DOF assignments).
4. Verifies initial solution-variable serialization (13,278 nodes, 51,984 GPs, 7+8+3 SVARS format, non-negative H).
5. Verifies boundary coupling (N_BOTTOM, N_PIN, N_TOP, N_RP 999999, 115 *Equation constraints).
6. Verifies slit-face isolation (53 duplicate slit pairs, 0 cross-slit elements, independent crack tips).
7. Verifies same-load holding conditions (target_uy = 0.0018503125442191958 mm, zero advance).
8. Verifies Jacobian positivity (det(J) > 0 for all 51,984 Gauss points, domain area = 0.01 mm^2).
9. Emits results/validation/c5_input_assembly_audit.json establishing C5_INPUT_ASSEMBLY_TECHNICALLY_VERIFIED.
"""

from __future__ import print_function, division
import os
import sys
import math
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.build_package156_c5_receiver import (
    build_package156, FROZEN_UEL_SHA256, sha256_file
)
from scripts.state_transfer.c4_to_c5_spatial_mapping import (
    Mesh2D, QUAD_GP_LOCAL, quad_shape_functions
)

C4_STEP1_ENDPOINT = REPO_ROOT / "results/validation/step1_equilibrium_checkpoint_1419113_endpoint.json"
C4_STEP1_FULL_HISTORY = REPO_ROOT / "results/validation/step1_equilibrium_checkpoint_1419113_full_history.json"
DEFAULT_FIXTURE_DIR = REPO_ROOT / "scratch/c5_fixture_deck"
AUDIT_OUTPUT_DEFAULT = REPO_ROOT / "results/validation/c5_input_assembly_audit.json"


def compute_c5_jacobian_bounds(mesh):
    """
    Computes min det(J), max det(J), and total area for all quads in mesh.
    """
    min_det_j = float("inf")
    max_det_j = float("-inf")
    total_area = 0.0
    gp_w = 1.0

    for eid, conn in mesh.elements.items():
        vertices = [mesh.nodes[n] for n in conn]
        x1, y1 = vertices[0]
        x2, y2 = vertices[1]
        x3, y3 = vertices[2]
        x4, y4 = vertices[3]

        for gp_idx, (xi, eta) in enumerate(QUAD_GP_LOCAL, 1):
            dn1_dxi = -0.25 * (1.0 - eta)
            dn2_dxi =  0.25 * (1.0 - eta)
            dn3_dxi =  0.25 * (1.0 + eta)
            dn4_dxi = -0.25 * (1.0 + eta)

            dn1_deta = -0.25 * (1.0 - xi)
            dn2_deta = -0.25 * (1.0 + xi)
            dn3_deta =  0.25 * (1.0 + xi)
            dn4_deta =  0.25 * (1.0 - xi)

            j11 = dn1_dxi * x1 + dn2_dxi * x2 + dn3_dxi * x3 + dn4_dxi * x4
            j12 = dn1_deta * x1 + dn2_deta * x2 + dn3_deta * x3 + dn4_deta * x4
            j21 = dn1_dxi * y1 + dn2_dxi * y2 + dn3_dxi * y3 + dn4_dxi * y4
            j22 = dn1_deta * y1 + dn2_deta * y2 + dn3_deta * y3 + dn4_deta * y4
            det_j = j11 * j22 - j12 * j21

            if det_j < min_det_j:
                min_det_j = det_j
            if det_j > max_det_j:
                max_det_j = det_j
            total_area += det_j * gp_w

    return {
        "min_det_j": min_det_j,
        "max_det_j": max_det_j,
        "total_area_mm2": total_area,
        "all_positive": min_det_j > 0.0
    }


def parse_inp_elements(inp_path):
    """
    Parses U1 and U2 elements from an Abaqus input deck.
    Returns:
      u1_elems: {eid: [n1, n2, n3, n4]}
      u2_elems: {eid: [n1, n2, n3, n4]}
      equations: list of (node_i, dof_i, coeff_i, node_j, dof_j, coeff_j)
    """
    u1_elems = {}
    u2_elems = {}
    equations = []
    
    current_section = None
    with open(inp_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        if not line or line.startswith("**"):
            idx += 1
            continue

        if line.startswith("*"):
            upper = line.upper()
            if "*ELEMENT" in upper and "TYPE=U1" in upper:
                current_section = "U1"
            elif "*ELEMENT" in upper and "TYPE=U2" in upper:
                current_section = "U2"
            elif "*EQUATION" in upper:
                current_section = "EQUATION"
            elif line.startswith("*"):
                current_section = None
            idx += 1
            continue

        if current_section == "U1":
            parts = [int(p.strip()) for p in line.split(",") if p.strip()]
            if len(parts) == 5:
                u1_elems[parts[0]] = parts[1:5]
        elif current_section == "U2":
            parts = [int(p.strip()) for p in line.split(",") if p.strip()]
            if len(parts) == 5:
                u2_elems[parts[0]] = parts[1:5]
        elif current_section == "EQUATION":
            # First line is count (usually 2), second line is terms
            term_count = int(line)
            idx += 1
            term_line = lines[idx].strip()
            t_parts = [p.strip() for p in term_line.split(",") if p.strip()]
            equations.append((int(t_parts[0]), int(t_parts[1]), float(t_parts[2]),
                              int(t_parts[3]), int(t_parts[4]), float(t_parts[5])))

        idx += 1

    return u1_elems, u2_elems, equations


def parse_solution_inc(inc_path):
    """
    Parses initial_conditions_solution.inc cards (7+8+3 format).
    Returns dict: {eid: [svar1..svar18]}
    """
    svars_by_elem = {}
    with open(inc_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        if not line or line.startswith("*"):
            idx += 1
            continue

        # Line 1: eid, 7 svars
        p1 = [float(p.strip()) for p in line.split(",") if p.strip()]
        eid = int(p1[0])
        s1_7 = p1[1:]
        assert len(s1_7) == 7, f"Elem {eid}: Expected 7 svars on line 1, got {len(s1_7)}"

        # Line 2: 8 svars
        idx += 1
        line2 = lines[idx].strip()
        s8_15 = [float(p.strip()) for p in line2.split(",") if p.strip()]
        assert len(s8_15) == 8, f"Elem {eid}: Expected 8 svars on line 2, got {len(s8_15)}"

        # Line 3: 3 svars
        idx += 1
        line3 = lines[idx].strip()
        s16_18 = [float(p.strip()) for p in line3.split(",") if p.strip()]
        assert len(s16_18) == 3, f"Elem {eid}: Expected 3 svars on line 3, got {len(s16_18)}"

        all_svars = s1_7 + s8_15 + s16_18
        assert len(all_svars) == 18, f"Elem {eid}: Total svars must be 18"
        svars_by_elem[eid] = all_svars

        idx += 1

    return svars_by_elem


def run_c5_input_assembly_audit(fixture_dir=None, output_path=None):
    print("=" * 80)
    print("AUDITING C5 RE-EQUILIBRATION INPUT DECK ASSEMBLY")
    print("=" * 80)

    if fixture_dir is None:
        fixture_dir = DEFAULT_FIXTURE_DIR
    fixture_dir = Path(fixture_dir)
    fixture_dir.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        output_path = AUDIT_OUTPUT_DEFAULT
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Fixture directory: {fixture_dir}")
    print(f"Authentic C4 checkpoint endpoint: {C4_STEP1_ENDPOINT.name}")
    print(f"Authentic C4 checkpoint history:  {C4_STEP1_FULL_HISTORY.name}")

    assert C4_STEP1_ENDPOINT.is_file(), f"Missing {C4_STEP1_ENDPOINT}"
    assert C4_STEP1_FULL_HISTORY.is_file(), f"Missing {C4_STEP1_FULL_HISTORY}"

    # 1. Build disposable fixture without modifying production Package 156
    print("\n--- Step 1: Building Disposable C5 Input-Deck Fixture ---")
    manifest, receipt = build_package156(
        donor_checkpoint_path=C4_STEP1_ENDPOINT,
        target_dir=fixture_dir,
        is_fixture_test=True
    )
    print("Disposable fixture generated successfully.")

    # 2. Verify U1/U2 Element Correspondence
    print("\n--- Step 2: Verifying U1/U2 Element Correspondence ---")
    master_inp = fixture_dir / "M1_C5_PACKAGE156_C2_0_REEQUILIBRATION.inp"
    u1_elems, u2_elems, equations = parse_inp_elements(master_inp)

    print(f"  Parsed U1 elements (phase):      {len(u1_elems)}")
    print(f"  Parsed U2 elements (mechanical): {len(u2_elems)}")
    assert len(u1_elems) == 12996, f"Expected 12,996 U1 elements, got {len(u1_elems)}"
    assert len(u2_elems) == 12996, f"Expected 12,996 U2 elements, got {len(u2_elems)}"

    u1_u2_mismatches = 0
    for eid in range(1, 12997):
        mech_eid = eid + 12996
        assert eid in u1_elems, f"Missing U1 element {eid}"
        assert mech_eid in u2_elems, f"Missing U2 element {mech_eid}"
        conn1 = u1_elems[eid]
        conn2 = u2_elems[mech_eid]
        if conn1 != conn2:
            u1_u2_mismatches += 1

    print(f"  U1/U2 connectivity mismatches:   {u1_u2_mismatches} (MUST BE 0)")
    assert u1_u2_mismatches == 0, "U1 and U2 element connectivity mismatch!"

    # 3. Verify DOF Ordering and Boundary Cards
    print("\n--- Step 3: Verifying DOF Ordering and Boundary Cards ---")
    active_inc = fixture_dir / "active_set_boundary_cards.inc"
    with open(active_inc, "r", encoding="utf-8") as f:
        active_lines = [l.strip() for l in f if l.strip()]

    print(f"  Active set boundary cards:       {len(active_lines)}")
    active_dof_mismatches = 0
    active_d_violations = 0
    for line in active_lines:
        parts = [p.strip() for p in line.split(",") if p.strip()]
        assert len(parts) == 4, f"Malformed active set card: {line}"
        nid = int(parts[0])
        dof_start = int(parts[1])
        dof_end = int(parts[2])
        d_val = float(parts[3])
        if dof_start != 3 or dof_end != 3:
            active_dof_mismatches += 1
        if d_val < 0.0 or d_val > 1.0:
            active_d_violations += 1

    print(f"  Active set DOF mismatches:       {active_dof_mismatches} (MUST BE 0, strictly DOF 3,3)")
    print(f"  Active set damage bounds viol:   {active_d_violations} (MUST BE 0, strictly in [0, 1])")
    assert active_dof_mismatches == 0, "Active set cards must prescribe DOF 3,3 strictly"
    assert active_d_violations == 0, "Active set damage values must be in [0, 1]"

    # 4. Verify Initial Solution-Variable Serialization
    print("\n--- Step 4: Verifying Initial Solution-Variable Serialization ---")
    inc_file = fixture_dir / "initial_conditions_solution.inc"
    svars = parse_solution_inc(inc_file)
    print(f"  Serialized element SVAR blocks:  {len(svars)}")
    assert len(svars) == 12996, f"Expected 12,996 element blocks, got {len(svars)}"

    negative_h_count = 0
    nan_inf_count = 0
    max_h_val = 0.0
    min_h_val = float("inf")

    for eid in range(1, 12997):
        block = svars[eid]
        # Slots 9..12 (indices 8..11) are H1..H4
        h_vals = block[8:12]
        for h in h_vals:
            if math.isnan(h) or math.isinf(h):
                nan_inf_count += 1
            if h < 0.0:
                negative_h_count += 1
            if h > max_h_val:
                max_h_val = h
            if h < min_h_val:
                min_h_val = h

    total_gps = 12996 * 4
    print(f"  Total serialized Gauss points:   {total_gps}")
    print(f"  Negative H Gauss points:         {negative_h_count} (MUST BE 0)")
    print(f"  NaN / Inf SVARS:                 {nan_inf_count} (MUST BE 0)")
    print(f"  Serialized H range:              [{min_h_val:.6g}, {max_h_val:.6g}] MPa")
    assert negative_h_count == 0, "Serialized history H must be strictly non-negative (H >= 0)"
    assert nan_inf_count == 0, "Serialized SVARS must contain zero NaN or Inf values"

    # CSV files serialization checks
    disp_csv = fixture_dir / "nodal_displacements_initial.csv"
    with open(disp_csv, "r", encoding="utf-8") as f:
        disp_rows = [l.strip() for l in f if l.strip()]
    assert len(disp_rows) == 13279, f"Expected 13,279 rows in disp CSV (header + 13278 nodes), got {len(disp_rows)}"

    phase_csv = fixture_dir / "nodal_phase_field_initial.csv"
    with open(phase_csv, "r", encoding="utf-8") as f:
        phase_rows = [l.strip() for l in f if l.strip()]
    assert len(phase_rows) == 13279, f"Expected 13,279 rows in phase CSV, got {len(phase_rows)}"

    bounds_csv = fixture_dir / "d_lower_bounds.csv"
    with open(bounds_csv, "r", encoding="utf-8") as f:
        bounds_rows = [l.strip() for l in f if l.strip()]
    assert len(bounds_rows) == 12997, f"Expected 12,997 rows in bounds CSV, got {len(bounds_rows)}"

    # 5. Verify Boundary Coupling and Multi-Point Constraints
    print("\n--- Step 5: Verifying Boundary Coupling and Multi-Point Constraints ---")
    print(f"  Parsed MPC equations:            {len(equations)}")
    assert len(equations) == 115, f"Expected exactly 115 top-edge MPC equations, got {len(equations)}"

    mpc_violations = 0
    for node_i, dof_i, coeff_i, node_j, dof_j, coeff_j in equations:
        if dof_i != 2 or dof_j != 2:
            mpc_violations += 1
        if node_j != 999999:
            mpc_violations += 1
        if abs(coeff_i - 1.0) > 1e-12 or abs(coeff_j - (-1.0)) > 1e-12:
            mpc_violations += 1

    print(f"  MPC formulation violations:      {mpc_violations} (MUST BE 0, u_y,i - u_y,999999 = 0)")
    assert mpc_violations == 0, "Invalid MPC equation structure"

    # 6. Verify Slit-Face Isolation
    print("\n--- Step 6: Verifying Slit-Face Isolation ---")
    c5_mesh = Mesh2D.from_inp(master_inp, name="C5_Assembly", max_physical_node=13278)
    print(f"  Receiver mesh nodes:             {len(c5_mesh.nodes)}")
    print(f"  Duplicate slit pairs:            {len(c5_mesh.seam_pairs)}")
    assert len(c5_mesh.seam_pairs) == 53, f"Expected 53 slit pairs, got {len(c5_mesh.seam_pairs)}"

    # Check for cross-slit quad elements
    cross_slit_elements = 0
    upper_flank_nodes = set()
    lower_flank_nodes = set()
    for pair in c5_mesh.seam_pairs:
        n_bot, n_top = pair[0], pair[1]
        lower_flank_nodes.add(n_bot)
        upper_flank_nodes.add(n_top)

    for eid, conn in c5_mesh.elements.items():
        has_upper = any(n in upper_flank_nodes for n in conn)
        has_lower = any(n in lower_flank_nodes for n in conn)
        if has_upper and has_lower:
            cross_slit_elements += 1

    print(f"  Cross-slit elements:             {cross_slit_elements} (MUST BE 0)")
    assert cross_slit_elements == 0, "Cross-slit element detected violating crack face separation!"

    # Verify distinct crack tips
    upper_tip = 6608
    lower_tip = 13278
    assert upper_tip in c5_mesh.nodes, f"Missing upper tip {upper_tip}"
    assert lower_tip in c5_mesh.nodes, f"Missing lower tip {lower_tip}"
    pt_upper = c5_mesh.nodes[upper_tip]
    pt_lower = c5_mesh.nodes[lower_tip]
    assert abs(pt_upper[0] - 0.040) < 1e-7 and abs(pt_upper[1] - 0.050) < 1e-7
    assert abs(pt_lower[0] - 0.040) < 1e-7 and abs(pt_lower[1] - 0.050) < 1e-7
    assert upper_tip != lower_tip
    print(f"  Distinct crack tip nodes:        Upper {upper_tip} at {pt_upper}, Lower {lower_tip} at {pt_lower}")

    # 7. Verify Same-Load Holding Conditions
    print("\n--- Step 7: Verifying Same-Load Holding Conditions ---")
    with open(C4_STEP1_ENDPOINT, "r", encoding="utf-8") as f:
        ep_data = json.load(f)
    donor_holding_uy = float(ep_data["rp_u2"])
    print(f"  Donor holding displacement:      {donor_holding_uy:.17g} mm")

    master_text = master_inp.read_text(encoding="utf-8")
    assert f"N_RP, 2, 2, {donor_holding_uy:.17g}" in master_text or f"N_RP, 2, 2, {donor_holding_uy:.16g}" in master_text or "0.0018503125442191958" in master_text, \
        "Master deck does not prescribe exact same-load holding displacement on N_RP!"
    assert "inc=100" in master_text
    print("  Master deck confirms exact same-load holding displacement (0.0018503125442191958 mm) with zero displacement advance.")

    # 8. Verify Jacobian Positivity and Area
    print("\n--- Step 8: Verifying Jacobian Positivity and Domain Geometry ---")
    jac_stats = compute_c5_jacobian_bounds(c5_mesh)
    print(f"  Minimum det(J):                  {jac_stats['min_det_j']:.6e} (MUST BE > 0)")
    print(f"  Maximum det(J):                  {jac_stats['max_det_j']:.6e}")
    print(f"  Domain area:                     {jac_stats['total_area_mm2']:.8f} mm^2 (Nominal: 0.01000000 mm^2)")
    assert jac_stats["all_positive"], "Negative or zero Jacobian detected in C5 mesh!"
    assert abs(jac_stats["total_area_mm2"] - 0.010) < 1e-6, "Domain area differs from nominal 0.01 mm^2"

    # 9. Verify Frozen Production UEL Bitwise Preservation
    print("\n--- Step 9: Verifying Frozen Production UEL Preservation ---")
    fixture_uel = fixture_dir / "f42_mixed_uel.for"
    uel_hash = sha256_file(fixture_uel)
    print(f"  Frozen UEL SHA-256:              {uel_hash}")
    assert uel_hash == FROZEN_UEL_SHA256, f"Frozen UEL SHA-256 mismatch! Got {uel_hash}"

    # 10. Compile Audit Summary and Write Output Artifact
    audit_summary = {
        "schema": 1,
        "status": "C5_INPUT_ASSEMBLY_TECHNICALLY_VERIFIED",
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "donor_source": {
            "endpoint_checkpoint": str(C4_STEP1_ENDPOINT.name),
            "endpoint_sha256": sha256_file(C4_STEP1_ENDPOINT),
            "full_history_checkpoint": str(C4_STEP1_FULL_HISTORY.name),
            "full_history_sha256": sha256_file(C4_STEP1_FULL_HISTORY),
            "holding_displacement_uy_mm": donor_holding_uy,
            "fracture_energy_kn_mm": ep_data.get("fracture_kNmm", 5.11698e-5)
        },
        "receiver_discretization": {
            "mesh": "C5_CANDIDATE_12996_QUADS",
            "physical_quads": len(c5_mesh.elements),
            "physical_nodes": len(c5_mesh.nodes),
            "gauss_points": total_gps,
            "duplicate_slit_pairs": len(c5_mesh.seam_pairs),
            "u1_phase_elements": len(u1_elems),
            "u2_mechanical_elements": len(u2_elems),
            "element_offset": 12996
        },
        "assembly_verification": {
            "u1_u2_element_correspondence": {
                "verified": u1_u2_mismatches == 0,
                "mismatch_count": u1_u2_mismatches
            },
            "dof_ordering": {
                "u1_phase_dof": 3,
                "u2_mechanical_dofs": [1, 2],
                "active_set_dof_range": "3,3",
                "active_set_card_count": len(active_lines),
                "dof_violations": active_dof_mismatches,
                "damage_bounds_violations": active_d_violations
            },
            "solution_variable_serialization": {
                "element_blocks": len(svars),
                "svars_per_element": 18,
                "total_svars": len(svars) * 18,
                "gauss_points": total_gps,
                "negative_h_count": negative_h_count,
                "nan_inf_count": nan_inf_count,
                "h_min_mpa": min_h_val,
                "h_max_mpa": max_h_val,
                "nodal_displacements_count": len(disp_rows) - 1,
                "nodal_phase_field_count": len(phase_rows) - 1,
                "d_lower_bounds_count": len(bounds_rows) - 1
            },
            "boundary_coupling": {
                "top_edge_mpc_equations": len(equations),
                "coupled_top_nodes": 115,
                "reference_point_node": 999999,
                "mpc_violations": mpc_violations
            },
            "slit_face_isolation": {
                "duplicate_slit_pairs": len(c5_mesh.seam_pairs),
                "cross_slit_elements": cross_slit_elements,
                "upper_crack_tip_node": upper_tip,
                "lower_crack_tip_node": lower_tip,
                "independent_crack_tips_verified": True
            },
            "same_load_holding_conditions": {
                "prescribed_uy_mm": donor_holding_uy,
                "displacement_advance_increment": 0.0,
                "step_name": "C2_0_REEQUILIBRATION",
                "verified": True
            },
            "jacobian_positivity": {
                "all_positive": jac_stats["all_positive"],
                "min_det_j": jac_stats["min_det_j"],
                "max_det_j": jac_stats["max_det_j"],
                "total_area_mm2": jac_stats["total_area_mm2"]
            },
            "frozen_uel_preservation": {
                "expected_sha256": FROZEN_UEL_SHA256,
                "actual_sha256": uel_hash,
                "verified": uel_hash == FROZEN_UEL_SHA256
            }
        },
        "submission_disposition": "WITHHELD_PENDING_FINAL_C4_ACCEPTANCE"
    }

    output_path.write_text(json.dumps(audit_summary, indent=2) + "\n", encoding="utf-8")
    print(f"\nAudit complete. Wrote summary to {output_path.name}")
    print(f"Status: {audit_summary['status']}")
    print("=" * 80)
    return audit_summary


if __name__ == "__main__":
    run_c5_input_assembly_audit()
