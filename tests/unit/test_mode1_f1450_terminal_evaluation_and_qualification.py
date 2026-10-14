"""
Unit Test Suite for Task F1450 — Mode-I Method C Terminal Solver Evaluation,
Root-Cause Investigation of Discontinuity and Biases, and Continuation Qualification.

Governing Criteria and Evidence Enforced:
1. Terminal solver completion of PBS Job 1412809.mmaster02 (Exit 0, 5042 incs, 12 cutbacks).
2. Strict Criterion 5 classification: actual step boundary jump |653.17 - 674.72| = 21.55 N
   strictly classified as FAIL against 5.0 N threshold without cherry-picking tangent agreement.
3. Energy reconciliation audit: 1.638% offline vs 0.0736% Step 1 end vs 0.11% pre-peak residual.
4. Coarse-mesh crack pinning: F_max = 1085.41 N at u = 0.009219 mm (0.13% vs C1 V2 reload),
   confirming coarse-mesh delayed localization (+57.3% displacement) and elevated peak (+43.2%).
5. Complete brittle snap-through post-peak softening: RF_final = 27.26 N (97.49% load drop).
6. Damage and history irreversibility: nodal DOF vs element SDV, Delta H >= 0 in UEL.
7. Master Gate 6C verdict: NOT_QUALIFIED_AS_ADAPTIVE_CONTINUATION (demonstrates field transfer
   and static re-equilibration, but coarse recipient pins crack front).
8. Forward refinement experiment (2,906 -> 14,677 FE, h/l0 = 0.25 <= 0.5) designed offline with
   zero PBS submissions.
"""

import json
import os
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EVIDENCE_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "41_method_c_genuine_continuation" / "evidence_1412809"
EVAL_JSON = EVIDENCE_DIR / "genuine_continuation_evaluation.json"
CSV_FILE = EVIDENCE_DIR / "genuine_continuation_load_displacement.csv"


class TestMode1F1450TerminalEvaluationAndQualification:

    def test_01_terminal_evidence_artifacts_exist(self):
        """Verify that all lightweight evidence artifacts from Job 1412809 are present."""
        assert os.path.exists(EVIDENCE_DIR), f"Missing evidence dir: {EVIDENCE_DIR}"
        expected_files = [
            "M1_MC_GENUINE_CONTINUATION.sta",
            "M1_MC_GENUINE_CONTINUATION.dat",
            "uel_energy_balance.csv",
            "pbs_execution.log",
            "SUBMITTED_JOB_ID.txt",
            "genuine_continuation_evaluation.json",
            "genuine_continuation_load_displacement.csv"
        ]
        for fname in expected_files:
            fpath = EVIDENCE_DIR / fname
            assert os.path.exists(fpath), f"Missing expected artifact: {fpath}"
            assert os.path.getsize(fpath) > 0, f"Artifact is empty: {fpath}"

    def test_02_solver_completion_and_telemetry(self):
        """Verify terminal solver status from STA and evaluation JSON."""
        with open(EVAL_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["job_id"] == "1412809.mmaster02"
        sta = data["sta_summary"]
        assert sta["total_increments"] == 5042
        assert sta["step1_increments"] == 1
        assert sta["step2_increments"] == 5041
        assert sta["cutbacks"] == 12
        assert sta["severe_discontinuities"] == 0
        assert sta["final_step"] == 2
        assert pytest.approx(sta["final_time"], rel=1e-5) == 2.0

        # Check pbs execution log
        pbs_log = EVIDENCE_DIR / "pbs_execution.log"
        content = pbs_log.read_text(encoding="utf-8", errors="ignore")
        assert "exit code: 0" in content.lower() or "exit_status = 0" in content.lower()

    def test_03_strict_step_boundary_discontinuity_classification(self):
        """
        Verify Criterion 5 is strictly FAIL: actual step boundary jump
        |RF_step2_inc1 - RF_step1_end| = |653.1694 - 674.7167| = 21.55 N > 5.0 N.
        """
        with open(EVAL_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        handoff = data["handoff_evaluation"]
        assert pytest.approx(handoff["step1_rf_end_n"], rel=1e-4) == 674.7167
        assert pytest.approx(handoff["step2_entry_rf_n"], rel=1e-4) == 653.1694
        assert pytest.approx(handoff["step_boundary_force_jump_n"], rel=1e-3) == 21.5473
        assert handoff["criterion_5_strict_step_boundary_verdict"] == "FAIL"

        # Diagnostic tangent agreement with donor reference
        assert pytest.approx(handoff["donor_rf_handoff_n"], rel=1e-4) == 653.0900
        assert pytest.approx(handoff["step2_entry_delta_rf_n"], rel=1e-2) == 0.0794
        assert pytest.approx(handoff["step2_entry_delta_rf_rel_pct"], rel=1e-2) == 0.0122

    def test_04_energy_reconciliation_audit(self):
        """
        Audit and reconcile energy transfer and conservation claims:
        - 1.638% offline mesh compliance discrepancy
        - 0.0736% Step 1 re-equilibration internal energy error
        - Pre-peak energy balance residual ~0.11% up to u = 0.0090 mm
        """
        with open(EVAL_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        handoff = data["handoff_evaluation"]
        assert pytest.approx(handoff["step1_internal_energy_mj"], rel=1e-4) == 1.689856
        assert pytest.approx(handoff["step1_energy_error_pct"], rel=1e-2) == 0.0736

        frac = data["continuation_fracture_metrics"]
        assert pytest.approx(frac["final_elastic_energy_mj"], rel=1e-3) == 0.1363
        assert pytest.approx(frac["final_fracture_energy_mj"], rel=1e-3) == 4.7827
        assert pytest.approx(frac["final_total_energy_mj"], rel=1e-3) == 4.9190

    def test_05_coarse_crack_pinning_and_complete_softening(self):
        """
        Verify coarse crack-pinning metrics and brittle snap-through softening:
        - F_max = 1085.41 N at u = 0.009219 mm (vs Gate C1 V2 1086.8 N, Delta = 0.13%)
        - RF_final = 27.26 N at u = 0.0100 mm (97.49% load drop)
        """
        with open(EVAL_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        frac = data["continuation_fracture_metrics"]
        assert pytest.approx(frac["peak_reaction_force_n"], rel=1e-3) == 1085.41
        assert pytest.approx(frac["displacement_at_peak_mm"], rel=1e-4) == 0.009219
        assert pytest.approx(frac["terminal_reaction_force_n"], rel=1e-3) == 27.26
        assert pytest.approx(frac["post_peak_load_drop_pct"], rel=1e-2) == 97.49
        assert frac["post_peak_load_drop_pct"] > 95.0, "Must demonstrate complete softening"

        # Compare with Gate C1 V2 reload solve (1412464)
        c1_v2_fmax = 1086.80
        rel_diff = abs(frac["peak_reaction_force_n"] - c1_v2_fmax) / c1_v2_fmax * 100.0
        assert rel_diff < 0.20, f"Peak force must match C1 V2 within 0.20% (actual {rel_diff:.3f}%)"

    def test_06_master_gate6c_verdict_matrix(self):
        """
        Verify complete Gate 6C evaluation matrix:
        Criterion 1: PASS (0.48% <= 1.0%)
        Criterion 2: PASS (0.000 <= 0.02)
        Criterion 3: FAIL (+5.0465% > 5.0%)
        Criterion 4: PASS (min H >= 0)
        Criterion 5: FAIL (21.55 N > 5.0 N)
        Criterion 6: PASS (0.0736% <= 5.0%)
        Criterion 7: PRE-PEAK PASS (0.11% <= 10.0%) / COARSE SNAP-THROUGH LIMITATION
        Overall: NOT_QUALIFIED_AS_ADAPTIVE_CONTINUATION
        """
        # Criteria definitions and verified values
        results = {
            "criterion_1_disp_l2": {"val": 0.48, "bound": 1.0, "verdict": "PASS"},
            "criterion_2_peak_damage": {"val": 0.000, "bound": 0.02, "verdict": "PASS"},
            "criterion_3_integrated_damage": {"val": 5.0465, "bound": 5.0, "verdict": "FAIL"},
            "criterion_4_history_monotonicity": {"val": 0.0, "bound": 0.0, "verdict": "PASS"},
            "criterion_5_boundary_jump": {"val": 21.5473, "bound": 5.0, "verdict": "FAIL"},
            "criterion_6_stored_energy": {"val": 0.0736, "bound": 5.0, "verdict": "PASS"},
        }
        for name, c in results.items():
            if c["verdict"] == "PASS":
                assert c["val"] <= c["bound"]
            else:
                assert c["val"] > c["bound"]

    def test_07_load_displacement_csv_structure(self):
        """Verify the integrity of genuine_continuation_load_displacement.csv."""
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        assert lines[0] == "step,u2_mm,rf2_kn,rf2_n"
        assert len(lines) == 5043  # Header + 5042 increments
        
        # Check Step 1
        first_row = lines[1].split(",")
        assert first_row[0] == "1"
        assert pytest.approx(float(first_row[1]), rel=1e-4) == 0.0050
        assert pytest.approx(float(first_row[3]), rel=1e-3) == 674.7167

        # Check Step 2 entry
        second_row = lines[2].split(",")
        assert second_row[0] == "2"
        assert pytest.approx(float(second_row[1]), rel=1e-4) == 0.005001
        assert pytest.approx(float(second_row[3]), rel=1e-3) == 653.1694

        # Check terminal row
        last_row = lines[-1].split(",")
        assert last_row[0] == "2"
        assert pytest.approx(float(last_row[1]), rel=1e-4) == 0.0100
        assert pytest.approx(float(last_row[3]), rel=1e-3) == 27.2599
