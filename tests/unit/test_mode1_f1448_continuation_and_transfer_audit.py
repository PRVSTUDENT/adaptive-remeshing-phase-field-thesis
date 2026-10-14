"""
Unit Test Suite for Task F1449 — Method C Continuation, Force Discontinuity, and Transfer Validity Audit
Enforces strict scientific classification across:
1. Criterion 3 strict threshold check (5.0465% vs 5.0% threshold) as FAIL under strict threshold rules.
2. Exact 1D analytical formula xi*coth(xi) - 1 = +53.25% vs 2D domain-integrated (+5.05%).
3. Criterion 5 step-boundary force discontinuity (Delta RF = 21.55 N) classified as FAIL_AGAINST_STRICT_5N_THRESHOLD.
4. Step 1 re-equilibration (674.72 N, 0.07% energy diff) vs Step 2 Inc 1 entry (653.17 N vs donor 653.09 N).
5. Coarse-mesh crack pinning characterization (h/l0 = 2.67 > 1, elevated peak force > 1.0 kN).
6. Forward refinement design (2,906 FE -> 14,677 FE, offline only, zero PBS submissions).
7. Preservation of authoritative UEL hash CE8D5EDC...
"""

import json
import hashlib
import os
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.postprocessing.evaluate_mode1_f1448_continuation_and_transfer_audit import (
    compute_analytical_coth_formula,
    compute_analytical_chordal_bias,
    audit_gate6c_transfer_criteria,
    audit_mesh_adaptivity_lineage,
    audit_job_1412809_initial_state,
    audit_coarse_mesh_crack_pinning,
    design_forward_refinement_experiment
)

class TestMode1F1449ContinuationAndTransferAudit:

    def test_01_frozen_uel_subroutine_hash_preserved(self):
        uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "41_method_c_genuine_continuation" / "f42_mixed_uel.for"
        assert os.path.exists(uel_path), f"Missing UEL file: {uel_path}"
        with open(uel_path, "rb") as f:
            actual_sha = hashlib.sha256(f.read()).hexdigest().upper()
        expected_sha = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        assert actual_sha == expected_sha, f"UEL hash mismatch: {actual_sha} != {expected_sha}"

    def test_02_criterion_3_strict_threshold_classification(self):
        criteria = audit_gate6c_transfer_criteria()
        crit3 = criteria["criterion_3_integrated_damage"]
        assert crit3["threshold"] == 5.0, "Predeclared threshold must remain 5.0%"
        assert abs(crit3["evaluated_value"] - 5.046520) < 1e-4, "Evaluated value must match 5.0465%"
        assert not crit3["passed_strict"], "Criterion 3 strictly exceeds 5.0% limit"
        assert crit3["strict_verdict"] == "FAIL_AGAINST_STRICT_5PCT_THRESHOLD"
        assert "FAIL under strict threshold governance" in crit3["qualification"]

    def test_03_analytical_coth_formula_and_chordal_identity(self):
        coarse_coth = compute_analytical_coth_formula(h=0.020, l0=0.0075)
        fine_coth = compute_analytical_coth_formula(h=0.001875, l0=0.0075)
        
        # User formula: xi * coth(xi) - 1
        assert abs(coarse_coth["xi"] - 4.0 / 3.0) < 1e-6
        assert abs(coarse_coth["bias_pct"] - 53.25) < 0.1, "Coarse mesh 1D analytical error must be +53.25%"
        assert abs(fine_coth["bias_pct"] - 0.52) < 0.05, "Fine mesh 1D analytical error must be +0.52%"
        
        # Algebraic identity with chordal integration
        coarse_chordal = compute_analytical_chordal_bias(h=0.020, l0=0.0075)
        assert abs(coarse_chordal["bias_pct"] - coarse_coth["bias_pct"]) < 1e-6

    def test_04_criterion_5_strict_step_boundary_classification(self):
        criteria = audit_gate6c_transfer_criteria()
        crit5 = criteria["criterion_5_boundary_force_continuity"]
        assert crit5["threshold"] == 5.0, "Predeclared threshold must remain 5.0 N"
        assert abs(crit5["evaluated_value"] - 21.5473) < 0.01, "Must evaluate actual step boundary jump (21.55 N)"
        assert not crit5["passed_strict"], "Step boundary jump of 21.55 N exceeds 5.0 N threshold"
        assert crit5["strict_verdict"] == "FAIL_AGAINST_STRICT_5N_THRESHOLD"
        assert "cherry-picking" in crit5["qualification"]

    def test_05_job_1412809_step_boundary_discontinuity_and_tangent_drop(self):
        job_audit = audit_job_1412809_initial_state()
        assert job_audit["job_id"] == "1412809.mmaster02"
        
        # Step 1 re-equilibration
        step1 = job_audit["step_1_re_equilibration"]
        assert step1["converged_increments"] == 1
        assert step1["newton_iterations"] == 2
        assert abs(step1["rf_evaluated_N"] - 674.72) < 0.1
        assert abs(step1["energy_discrepancy_pct"] - 0.0736) < 0.01, "Step 1 internal energy discrepancy must be ~0.07%"
        assert abs(step1["delta_rf_vs_donor_N"] - 21.63) < 0.1, "Step 1 transient force jump vs donor is +21.63 N"

        # Step 2 continuation entry
        step2 = job_audit["step_2_continuation_entry"]
        assert abs(step2["inc_1_rf_N"] - 653.1694) < 1e-3
        assert abs(step2["step_boundary_jump_N"] - 21.55) < 0.02, "Step boundary jump |653.17 - 674.72| must be 21.55 N"
        assert step2["step_boundary_verdict"] == "FAIL_AGAINST_STRICT_5N_THRESHOLD"
        assert abs(step2["delta_rf_vs_donor_N"] - 0.0794) < 1e-3, "Tangent agreement with donor is 0.0794 N"

    def test_06_coarse_mesh_crack_pinning_characterization(self):
        pinning = audit_coarse_mesh_crack_pinning()
        assert pinning["mesh_resolution_ratio_h_over_l0"] > 1.0, "h/l0 must exceed 1.0 (actual 2.67)"
        assert abs(pinning["mesh_resolution_ratio_h_over_l0"] - 2.6667) < 0.01
        assert "crack pinning" in pinning["pinning_mechanism"]
        assert "NOT" in pinning["scientific_conclusion"]

    def test_07_forward_refinement_experiment_design(self):
        forward = design_forward_refinement_experiment()
        assert forward["status"] == "OFFLINE_DESIGN_ONLY_ZERO_PBS_SUBMISSIONS_AUTHORIZED"
        assert forward["donor"]["elements"] == 2906
        assert forward["recipient"]["elements"] == 14677
        assert forward["recipient"]["meets_resolution_criterion"] is True
        assert forward["recipient"]["h_over_l0"] == 0.25

    def test_08_audit_json_artifact_integrity(self):
        json_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "41_method_c_genuine_continuation" / "method_c_genuine_continuation_audit.json"
        assert os.path.exists(json_path), f"Missing audit JSON: {json_path}"
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["task_id"] == "F1449"
        assert "analytical_coarsening_formula" in data
        assert "gate_6c_criteria_audit" in data
        assert "mesh_adaptivity_lineage" in data
        assert "job_1412809_initial_state_audit" in data
        assert "coarse_mesh_crack_pinning_audit" in data
        assert "forward_refinement_design" in data
