"""
Unit Test Suite for Task F1448 — Method C Continuation and State Transfer Audit
Enforces strict scientific classification across:
1. Criterion 3 threshold check (5.0465% vs 5.0% threshold) as FAIL under strict threshold rules.
2. Mesh adaptivity lineage: 14.7k donor -> 2.9k recipient as coarsening feasibility experiment.
3. Job 1412809 initial-state preservation: Step 1 re-equilibration (674.72 N, 0.07% energy diff)
   vs Step 2 Inc 1 force continuity (653.1694 N vs donor 653.09 N, jump 0.0794 N).
4. Preservation of authoritative UEL hash.
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
    compute_analytical_chordal_bias,
    audit_gate6c_transfer_criteria,
    audit_mesh_adaptivity_lineage,
    audit_job_1412809_initial_state
)

class TestMode1F1448ContinuationAndTransferAudit:

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
        assert "analytical convex chordal" in crit3["qualification"]

    def test_03_analytical_chordal_bias_mechanism(self):
        coarse = compute_analytical_chordal_bias(h=0.020, l0=0.0075)
        fine = compute_analytical_chordal_bias(h=0.001875, l0=0.0075)
        assert coarse["bias_pct"] > 0, "Coarse linear interpolant must overestimate convex exponential integral"
        assert fine["bias_pct"] < coarse["bias_pct"], "Fine mesh bias must be substantially lower than coarse mesh"
        assert coarse["h_over_l0"] > 1.0, "Coarse mesh element size must exceed length scale l0"

    def test_04_mesh_adaptivity_classification(self):
        mesh_audit = audit_mesh_adaptivity_lineage()
        assert mesh_audit["donor_mesh"]["element_count"] == 14677
        assert mesh_audit["recipient_mesh"]["element_count"] == 2906
        assert mesh_audit["transfer_direction"] == "COARSENING (14,677 FE -> 2,906 FE, ratio 5.05 : 1)"
        assert mesh_audit["scientific_classification"] == "COARSENING_FEASIBILITY_EXPERIMENT_AND_STATIC_CONTINUATION_QUALIFICATION"
        assert "NOT" in mesh_audit["distinction_note"]

    def test_05_job_1412809_initial_state_and_force_continuity(self):
        job_audit = audit_job_1412809_initial_state()
        assert job_audit["job_id"] == "1412809.mmaster02"
        
        # Step 1 re-equilibration
        step1 = job_audit["step_1_re_equilibration"]
        assert step1["converged_increments"] == 1
        assert step1["newton_iterations"] == 2
        assert abs(step1["rf_evaluated_N"] - 674.72) < 0.1
        assert abs(step1["energy_discrepancy_pct"] - 0.0736) < 0.01, "Step 1 internal energy discrepancy must be ~0.07%"
        assert abs(step1["delta_rf_vs_donor_N"] - 21.63) < 0.1, "Step 1 transient force jump is +21.63 N"

        # Step 2 Inc 1 continuation entry
        step2 = job_audit["step_2_continuation_entry"]
        assert abs(step2["inc_1_rf_N"] - 653.1694) < 1e-3
        assert abs(step2["delta_rf_vs_donor_N"] - 0.0794) < 1e-3, "Step 2 Inc 1 force jump vs donor must be 0.0794 N"
        assert step2["force_continuity_verdict"] == "PASS", "Step 2 Inc 1 force jump (0.08 N) is well within 5.0 N threshold"

    def test_06_audit_json_artifact_integrity(self):
        json_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "41_method_c_genuine_continuation" / "method_c_genuine_continuation_audit.json"
        assert os.path.exists(json_path), f"Missing audit JSON: {json_path}"
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["task_id"] == "F1448"
        assert "gate_6c_criteria_audit" in data
        assert "mesh_adaptivity_lineage" in data
        assert "job_1412809_initial_state_audit" in data
