"""
Unit test suite for Task F1721 Post-Peak Convergence Diagnosis (Revision R1).
Verifies primary solver telemetry, MSG divergence signatures, node localization,
tangent softening, coupled FE block-operator mathematics, subroutine defect detection,
proposed staggered patch integrity, and completeness of revised hypothesis F1721-H1-R1.
"""

import os
import re
import csv
import pytest

BASE_DIR = "models/pandey_kumar_mode1/214_f1720_adapted_mesh"
MSG_PATH = os.path.join(BASE_DIR, "PK_F1720_ADAPTED_PFM.msg")
STA_PATH = os.path.join(BASE_DIR, "PK_F1720_ADAPTED_PFM.sta")
DAT_PATH = os.path.join(BASE_DIR, "PK_F1720_ADAPTED_PFM.dat")
INP_PATH = os.path.join(BASE_DIR, "PK_F1720_ADAPTED_PFM.inp")
FOR_F1720_PATH = os.path.join(BASE_DIR, "f1720_direct_coupling_uel.for")
FOR_F1721_PATH = os.path.join(BASE_DIR, "f1721_proposed_staggered_coupling_uel.for")
PATCH_PATH = "docs/validation/f1721_staggered_coupling_proposed.patch"
CURVES_PATH = "results/validation/f1720_adapted_pfm_curves.csv"
REPORT_PATH = "docs/validation/F1721_POSTPEAK_CONVERGENCE_DIAGNOSTIC_REPORT.md"


def test_01_primary_solver_receipts_integrity():
    """Verify existence, non-emptiness, and basic properties of solver receipts."""
    for path in [MSG_PATH, STA_PATH, DAT_PATH, INP_PATH, FOR_F1720_PATH, FOR_F1721_PATH, PATCH_PATH, CURVES_PATH, REPORT_PATH]:
        assert os.path.isfile(path), f"File missing: {path}"
        assert os.path.getsize(path) > 0, f"File empty: {path}"

    with open(STA_PATH, "r", encoding="utf-8", errors="ignore") as f:
        sta_lines = [l.strip() for l in f if l.strip()]
    assert len(sta_lines) >= 170, f"Insufficient STA records: {len(sta_lines)}"

    with open(MSG_PATH, "r", encoding="utf-8", errors="ignore") as f:
        msg_text = f.read()
    assert "***ERROR: TIME INCREMENT REQUIRED IS LESS THAN THE MINIMUM SPECIFIED" in msg_text
    assert "THE SOLUTION APPEARS TO BE DIVERGING" in msg_text


def test_02_terminal_increment_127_divergence_signature():
    """Verify exact residual and correction DOFs in terminal increment 127."""
    with open(MSG_PATH, "r", encoding="utf-8", errors="ignore") as f:
        msg_text = f.read()

    # Search for Increment 127 Attempt 3 convergence checks
    inc127_match = re.search(r'INCREMENT\s+127\s+STARTS.*?ATTEMPT NUMBER\s+3.*?(?=ANALYSIS SUMMARY|\Z)', msg_text, re.DOTALL)
    assert inc127_match is not None, "Increment 127 Attempt 3 not found in MSG"
    att3_text = inc127_match.group(0)

    # Check largest residual force: must be at node 3292 DOF 2
    res_matches = re.findall(r'LARGEST SCALED RESIDUAL FORCE\s+([\d\.E\+\-]+)\s+AT NODE\s+(\d+)\s+DOF\s+(\d+)', att3_text)
    assert len(res_matches) >= 4, f"Fewer than 4 iterations in Attempt 3: {len(res_matches)}"
    for res_val, node, dof in res_matches:
        assert int(node) == 3292, f"Unexpected residual node: {node}"
        assert int(dof) == 2, f"Residual DOF is not 2 (mechanical uy): {dof}"

    # Check largest correction to disp: must be DOF 3 (phase field d)
    corr_matches = re.findall(r'LARGEST CORRECTION TO DISP\.\s+([\d\.E\+\-]+)\s+AT NODE\s+(\d+)\s+DOF\s+(\d+)', att3_text)
    assert len(corr_matches) >= 4, f"Fewer than 4 correction records: {len(corr_matches)}"
    for corr_val, node, dof in corr_matches:
        assert int(dof) == 3, f"Correction DOF is not 3 (phase field d): {dof}"
        assert int(node) in [3286, 3909, 4508, 5648], f"Correction node outside critical cluster: {node}"


def test_03_geometric_corridor_ligament3_localization():
    """Verify that all diverging nodes lie strictly within Ligament 3 (h3 <-> h4)."""
    node_coords = {}
    with open(INP_PATH, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("*ELEMENT"):
                break
            if not line.startswith("*"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        node_coords[nid] = (float(parts[1]), float(parts[2]))
                    except ValueError:
                        pass

    critical_nodes = [3286, 3292, 3909, 4508]
    for nid in critical_nodes:
        assert nid in node_coords, f"Node {nid} missing from INP"
        x, y = node_coords[nid]
        # Ligament 3 spans x in [0.647, 0.679], y in [0.520, 0.550]
        assert 0.645 <= x <= 0.665, f"Node {nid} x-coord outside Ligament 3 corridor: x={x}"
        assert 0.530 <= y <= 0.550, f"Node {nid} y-coord outside Ligament 3 corridor: y={y}"


def test_04_load_displacement_tangent_collapse():
    """Verify the structural softening drop across terminal increments."""
    with open(CURVES_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    u_vals = [float(r["displacement_mm"]) for r in reader]
    f_vals = [float(r["force_kN"]) for r in reader]
    d_vals = [float(r["max_damage"]) for r in reader]

    peak_f = max(f_vals)
    peak_idx = f_vals.index(peak_f)
    assert peak_f == pytest.approx(0.921726, abs=1e-5), f"Peak force mismatch: {peak_f}"
    assert u_vals[peak_idx] == pytest.approx(0.0056638, abs=1e-6), f"Peak displacement mismatch: {u_vals[peak_idx]}"

    # Terminal point
    u_term = u_vals[-1]
    f_term = f_vals[-1]
    d_term = d_vals[-1]
    assert u_term == pytest.approx(0.0056645, abs=1e-6)
    assert f_term == pytest.approx(0.912794, abs=1e-4)
    assert d_term == pytest.approx(0.7167, abs=1e-3)

    delta_u = u_term - u_vals[peak_idx]
    assert delta_u < 1.0e-5, f"Displacement advance too large: {delta_u} mm"
    assert delta_u > 0.0, "Displacement must advance strictly monotonically"


def test_05_coupled_fe_residual_block_iteration_formulation():
    """Verify coupled FE residual formulation and conditional limits of local 1D model."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    # Must contain exact block-iteration error matrix formulation
    assert r"\mathbf{J}_{\text{mono}}" in text or r"J_{\text{mono}}" in text
    assert r"\mathbf{J}_{\text{diag}}" in text or r"J_{\text{diag}}" in text
    assert r"\mathbf{K}_{ud}" in text or r"K_{ud}" in text
    # Must acknowledge conditionality (not universal theorem)
    assert "simplified 1D unconstrained scalar" in text or "local 1D" in text
    assert "neither pure stress-controlled nor pure strain-controlled" in text


def test_06_subroutine_coupling_defect_detection():
    """Verify exact line locations of trial-state reads in f1720_direct_coupling_uel.for."""
    with open(FOR_F1720_PATH, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # Line 397 (0-indexed 396)
    assert "HIST = SV_H_TRIAL(PHYSIDX, KPT)" in lines[396], f"Line 397 mismatch: {lines[396]}"
    # Line 452 (0-indexed 451)
    assert "D_VAL = SV_PHASE_TRIAL(PHYSIDX)" in lines[451], f"Line 452 mismatch: {lines[451]}"
    # Line 661 (0-indexed 660)
    assert "HIST = SV_H_TRIAL(PHYSIDX, 1)" in lines[660], f"Line 661 mismatch: {lines[660]}"
    # Line 709 (0-indexed 708)
    assert "D_VAL = SV_PHASE_TRIAL(PHYSIDX)" in lines[708], f"Line 709 mismatch: {lines[708]}"


def test_07_proposed_staggered_patch_verification():
    """Verify existence, non-emptiness, and exact diff structure of proposed patch."""
    assert os.path.isfile(PATCH_PATH), f"Patch missing: {PATCH_PATH}"
    with open(PATCH_PATH, "r", encoding="utf-8") as f:
        patch_text = f.read()

    assert "-          HIST = SV_H_TRIAL(PHYSIDX, KPT)" in patch_text
    assert "+          HIST = SV_H_COMMITTED(PHYSIDX, KPT)" in patch_text
    assert "-        D_VAL = SV_PHASE_TRIAL(PHYSIDX)" in patch_text
    assert "+        D_VAL = SV_PHASE_COMMITTED(PHYSIDX)" in patch_text
    assert "-        HIST = SV_H_TRIAL(PHYSIDX, 1)" in patch_text
    assert "+        HIST = SV_H_COMMITTED(PHYSIDX, 1)" in patch_text


def test_08_falsifiable_hypothesis_specification_completeness():
    """Verify that the revised report defines all mandatory specification items."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        report_text = f.read()

    required_sections = [
        "Falsifiable Corrective Hypothesis (F1721-H1-R1)",
        "Suspected Mechanism:",
        "Exact Source Location:",
        "Mathematical Defect:",
        "Supporting Evidence:",
        "Evaluated Competing Co-Factors",
        "Scientifically Valid Future Diagnostic Pilot Specification",
        "Objective Success Criteria:"
    ]
    for sec in required_sections:
        assert sec in report_text, f"Mandatory hypothesis section missing: {sec}"
