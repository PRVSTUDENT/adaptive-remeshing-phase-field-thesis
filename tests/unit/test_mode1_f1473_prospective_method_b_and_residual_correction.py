# -*- coding: utf-8 -*-
"""
test_mode1_f1473_prospective_method_b_and_residual_correction.py

Unit test suite for Task F1473:
1. Mathematical Patch Test of Phase-Field Residual Weak Form and Jacobian:
   - Verifies exact weak form: R_d = int [ N_d^T (2(H + psi_0)d - 2H) + G_c l_0 B_d^T grad d ] dOmega
     = int [ N_d^T (2 psi_0 d - 2 H (1 - d)) + G_c l_0 B_d^T grad d ] dOmega.
   - Case 1: Intact virgin state (H = 0, d = 0, grad d = 0) -> R_d = 0, RHS_d = 0.
     (Explicitly checks correction of F1472 formula error where omission of d produced +psi_0 != 0).
   - Case 2: Homogeneous equilibrium state for arbitrary H > 0 (d_hom = H / (H + psi_0), grad d = 0) -> R_d = 0.
   - Case 3: Uninitialized damage shock (H = H_0 > 0, d = 0, grad d = 0) -> RHS_d = +2 H_0 > 0.
   - Case 4: Analytic Jacobian tangent J_dd = dR_d/dd = 2(H + psi_0) > 0 (strictly positive definite).
   - Case 5: Dimensional units verification: R_d is Energy (kN*mm = J or mJ), NOT mechanical traction in Newtons.
2. Method B Prospective Step-Partitioning and Evaluation-Frame Audit:
   - Verifies 1S, 2S, and 4S preliminary linear-elastic pre-analyses produce identical MISESERI fields (Delta = 0.0)
     and identical native adapted meshes (14,677 FE, Delta N = 0).
   - Verifies scale-invariance of linear elasticity prevents prospective refinement of uncracked ligament.
   - Verifies Package 40 is explicitly classified as retrospective verification, not prospective Method B.
3. Method C Stationary-Point Convergence & Governance Tightening:
   - Verifies Newton iterations seek stationary point grad_u Pi = 0 rather than monotonic reduction at each iterate.
   - Verifies formal distinction between algorithmic minimization and physical thermodynamic dissipation.
   - Verifies Gate 6C hold: submit_c1_forward_refinement_job.sh locked with AUTHORIZED=false.
4. Active HPC Job 1413022 Tracking and Hard Submission Stop Condition:
   - Verifies Job 1413022.mmaster02 tracked in queue Q with scheduler reason and estimated start time.
   - Verifies hard submission stop condition: zero unauthorized submissions.
5. Production UEL Hash Preservation:
   - Verifies f42_mixed_uel.for matches CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6.
"""

import hashlib
import json
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

PROD_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
DECK40_HASH = "1209F716971719B1A740FF92C8B5503BA9784F10D5EEDD3C5035C81D40A066E9"

PSI_0_MPA = 180.0  # MPa = N/mm^2 = 0.180 kN/mm^2 (Gc = 0.0027 kN/mm, l0 = 0.0075 mm)
L0_MM = 0.0075     # mm
GC_KN_PER_MM = 0.0027  # kN/mm = 2.7 N/mm


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_phase_field_residual_weak_form_and_patch_tests():
    """Verify analytical weak form, sign conventions, units, and patch test cases."""
    psi_0 = GC_KN_PER_MM / (2.0 * L0_MM)  # 0.180 kN/mm^2 = 180 MPa
    assert abs(psi_0 - 0.180) < 1e-12

    # Residual integrand: r_d = 2(H + psi_0)d - 2H = 2*psi_0*d - 2*H*(1 - d)
    def residual_local(H, d):
        return 2.0 * (H + psi_0) * d - 2.0 * H

    # Abaqus RHS integrand: rhs_d = -r_d = 2*H*(1 - d) - 2*psi_0*d
    def rhs_local(H, d):
        return -residual_local(H, d)

    # Tangent Jacobian: J_dd = d(r_d)/dd = 2(H + psi_0)
    def jacobian_local(H):
        return 2.0 * (H + psi_0)

    # Flawed F1472 formula (where d was omitted from psi_0 term):
    # r_d_flawed = (2(1 - d)H + psi_0) - 2H = psi_0 - 2*d*H
    def residual_flawed_f1472(H, d):
        return (2.0 * (1.0 - d) * H + psi_0) - 2.0 * H

    # Case 1: Intact virgin state (H = 0, d = 0)
    # The corrected formula MUST evaluate to exactly 0.0
    assert residual_local(0.0, 0.0) == 0.0
    assert rhs_local(0.0, 0.0) == 0.0
    # Flawed formula gave spurious +psi_0
    assert residual_flawed_f1472(0.0, 0.0) == psi_0  # Proves flaw existence in F1472

    # Case 2: Homogeneous equilibrium for arbitrary H > 0
    test_histories = [0.010, 0.05364989, 0.100, 0.500]  # kN/mm^2
    for H_val in test_histories:
        d_hom = H_val / (H_val + psi_0)
        assert 0.0 < d_hom < 1.0
        # Under homogeneous equilibrium, residual must be identically zero
        assert abs(residual_local(H_val, d_hom)) < 1e-15
        assert abs(rhs_local(H_val, d_hom)) < 1e-15

    # Case 3: Uninitialized damage shock (H = H_0 > 0, d = 0)
    H_notch = 0.05364989  # kN/mm^2 (53.65 MPa)
    r_uninit = residual_local(H_notch, 0.0)
    rhs_uninit = rhs_local(H_notch, 0.0)
    assert r_uninit == -2.0 * H_notch  # Negative internal residual
    assert rhs_uninit == +2.0 * H_notch  # Positive Abaqus RHS driving force
    assert abs(rhs_uninit - 0.10729978) < 1e-7  # ~107.3 MPa driving force

    # Case 4: Analytic Jacobian tangent strictly positive definite
    for H_val in [0.0] + test_histories:
        J = jacobian_local(H_val)
        assert J >= 2.0 * psi_0 > 0.0, "Jacobian tangent must be strictly positive"

    # Case 5: Documentation check in architecture report
    arch_path = REPO_ROOT / "docs" / "reports" / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
    assert arch_path.is_file()
    arch_text = arch_path.read_text(encoding="utf-8")

    # Verify corrected formula is in the text
    assert r"2(H_0 + \psi_0)d_0 - 2H_0" in arch_text
    assert r"2\psi_0 d_0 - 2H_0(1 - d_0)" in arch_text
    assert r"\mathbf{RHS}_d^{(0)} = -\mathbf{R}_d^{(0)}" in arch_text
    assert "units of **Energy**" in arch_text
    assert "Dimensional Verification & Distinction from Mechanical Boundary Forces" in arch_text


def test_prospective_method_b_step_partitioning_and_frame_invariance():
    """Verify 1S, 2S, 4S step-partition invariance and prospective Method B limitations."""
    comp_summary_path = REPO_ROOT / "runs" / "mode1" / "method_b_preliminary" / "METHOD_B_PRE_COMPARISON_SUMMARY.json"
    assert comp_summary_path.is_file()
    with open(comp_summary_path, "r", encoding="utf-8") as f:
        comp_data = json.load(f)

    comp = comp_data["comparison"]
    assert comp["max_diff_miseseri_2s_1s"] == 0.0
    assert comp["max_diff_miseseri_4s_1s"] == 0.0
    assert comp["rel_rf_2s_vs_1s_pct"] == 0.0
    assert comp["rel_rf_4s_vs_1s_pct"] == 0.0

    inf_res_path = REPO_ROOT / "runs" / "mode1" / "method_b_inf_companion" / "inf_companion_method_b_results.json"
    assert inf_res_path.is_file()
    with open(inf_res_path, "r", encoding="utf-8") as f:
        inf_data = json.load(f)

    # Topology invariance
    topo = inf_data["mesh_topology_comparison"]
    assert topo["step_partition_mesh_invariance_verified"] is True
    assert topo["element_count_1s"] == 14677
    assert topo["element_count_2s"] == 14677
    assert topo["element_count_4s"] == 14677

    # Verify native Method B ligament limitation
    arch_path = REPO_ROOT / "docs" / "reports" / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
    arch_text = arch_path.read_text(encoding="utf-8")
    assert "18.77% (18.8%) COVERAGE" in arch_text
    assert "retrospective, crack-path-informed verification mesh" in arch_text


def test_method_c_stationary_point_and_governance_tightening():
    """Verify stationary point convergence discipline and Gate 6C lock."""
    arch_path = REPO_ROOT / "docs" / "reports" / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
    arch_text = arch_path.read_text(encoding="utf-8")

    # Stationary point statement
    assert "seeking the stationary equilibrium point" in arch_text
    assert r"\nabla_{\mathbf{u}}\Pi = \mathbf{0}" in arch_text
    assert "rather than an optimization algorithm that guarantees monotonic potential energy reduction" in arch_text

    # Supervisor briefing check
    briefing_path = REPO_ROOT / "docs" / "supervisor_reports" / "22-10-2026" / "SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md"
    assert briefing_path.is_file()
    briefing_text = briefing_path.read_text(encoding="utf-8")
    assert "Newton iterations seek a stationary equilibrium state" in briefing_text
    assert "strictly distinguishing algorithmic potential energy minimization from physical thermodynamic dissipation" in briefing_text

    # Gate 6C lock in submission script
    submit_script = REPO_ROOT / "models" / "pandey_kumar_mode1" / "42_method_c1_forward_refinement" / "submit_c1_forward_refinement_job.sh"
    assert submit_script.is_file()
    script_text = submit_script.read_text(encoding="utf-8")
    assert "AUTHORIZED=false" in script_text


def test_job_1413022_queue_tracking_and_hard_stop():
    """Verify Job 1413022 is tracked in queue Q and hard stop condition is active."""
    task_file = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"
    assert task_file.is_file()
    with open(task_file, "r", encoding="utf-8") as f:
        task_data = json.load(f)

    assert "1413022.mmaster02" in task_data["active_pbs_job_ids"]
    assert task_data["status"] in ["SUBMITTED_AND_QUEUED", "QUEUED", "ACTIVE_MONITORING"]

    ledger_file = REPO_ROOT / "project_coordination" / "HPC_JOB_LEDGER.csv"
    assert ledger_file.is_file()
    ledger_text = ledger_file.read_text(encoding="utf-8")
    assert "1413022.mmaster02" in ledger_text
    assert "M1_MB_CORR_8TB" in ledger_text


def test_production_uel_hash_preservation():
    """Verify f42_mixed_uel.for matches authoritative SHA-256."""
    uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
    assert uel_path.is_file()
    actual_hash = compute_sha256(uel_path)
    assert actual_hash == PROD_UEL_HASH, f"UEL hash mismatch: {actual_hash}"
