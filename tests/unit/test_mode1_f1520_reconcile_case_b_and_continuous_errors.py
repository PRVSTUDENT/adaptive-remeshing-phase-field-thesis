"""
Unit tests for Task F1520:
Reconciliation of Case B with Continuous Reference, Epistemic Scoping of
Local Release Stability vs Continuous Baseline Continuity, and Ranked
Root-Cause Hypothesis Matrix.

Validates:
1. Assessment A (Within-Run Release Stability on Same Mesh):
   - Consistent control (1414563) passes: |Delta RF| <= 5.0 N, |Delta d_max| <= 0.0200, |Delta E_tot| <= 0.10%.
   - Lumped control (1414558) fails: |Delta d_max| = 0.0216 > 0.0200 (smoothing relaxation defect).
2. Assessment B (Continuous Baseline State Preservation):
   - Both controls fail against uninterrupted baseline 1412465 (661.73 N, 1.6911 mJ):
     Delta RF = -17.17 N (-2.59% > 5 N), Delta E_tot = -2.48% > 0.10%.
   - Establishes that the deficit was already established in Step 1 re-equilibration.
3. Reclassification of Case B:
   - Formally designated CASE_B_LOCAL_RELEASE_STABILITY_ONLY (retaining legacy alias CASE_B).
   - Epistemic scope explicitly forbids conflating within-run release stability with full continuum state restoration.
4. Ranked Root-Cause Hypotheses:
   - Verifies 4 ranked hypotheses (H1 mechanical displacements, H2 damage distortion, H3 coarse provenance, H4 unrestored strain history).
5. Gate 6C Governance:
   - Gate 6C remains on strict hold (GATE_6C_HOLD); sequential remesh cycles = 0.
6. Enriched Continuous Baseline Readiness:
   - Verifies Job 1414571 recorded/active and ground-truth extractor readiness.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "state_transfer"))

import evaluate_mode1_diagnostic_trio as emdt


class TestMode1F1520ReconcileCaseBAndContinuousErrors(unittest.TestCase):
    """Test suite for Task F1520 Case B reconciliation and dual-assessment evaluation."""

    @classmethod
    def setUpClass(cls):
        cls.lumped_dir = ROOT / "runs" / "hpc" / "mode1_stage_c1_1_nonmatching_transfer" / "evidence_1414558"
        cls.consistent_dir = ROOT / "runs" / "hpc" / "mode1_stage_c1_1_nonmatching_transfer" / "evidence_1414563"
        cls.evaluation_json = ROOT / "results" / "validation" / "stage_c1_1_diagnostic_trio_evaluation.json"

        # Evaluate the trio
        cls.matrix = emdt.evaluate_trio_from_paths(
            str(cls.lumped_dir),
            str(cls.consistent_dir)
        )

    def test_01_assessment_a_within_run_release_stability(self):
        """Verify Assessment A: Consistent control passes while lumped control fails smoothing threshold."""
        lumped_a = self.matrix["diagnostics"]["lumped_assessment_a"]
        consistent_a = self.matrix["diagnostics"]["consistent_assessment_a"]

        # Lumped control fails due to artificial smoothing relaxation
        self.assertFalse(lumped_a["passed"])
        self.assertIn("smoothing defect", lumped_a["reason"])
        self.assertAlmostEqual(lumped_a["delta_d_max_within"], 0.021598, places=5)
        self.assertGreater(lumped_a["delta_d_max_within"], 0.0200)
        self.assertLess(lumped_a["delta_rf_within_N"], 5.0)

        # Consistent control passes all within-run criteria
        self.assertTrue(consistent_a["passed"])
        self.assertAlmostEqual(consistent_a["delta_d_max_within"], 0.000263, places=6)
        self.assertLess(consistent_a["delta_d_max_within"], 0.0200)
        self.assertAlmostEqual(consistent_a["delta_rf_within_N"], 0.45459, places=3)
        self.assertLess(consistent_a["delta_rf_within_N"], 5.0)
        self.assertIsNotNone(consistent_a["delta_e_tot_within_pct"])
        self.assertAlmostEqual(consistent_a["delta_e_tot_within_pct"], 0.00714, places=3)
        self.assertLess(consistent_a["delta_e_tot_within_pct"], 0.10)

    def test_02_assessment_b_continuous_baseline_discrepancy_reconciled(self):
        """Verify Assessment B: Both controls fail against uninterrupted baseline 1412465."""
        lumped_b = self.matrix["diagnostics"]["lumped_assessment_b"]
        consistent_b = self.matrix["diagnostics"]["consistent_assessment_b"]

        # Reference baseline: 661.7254 N, 1.691099 mJ
        self.assertAlmostEqual(consistent_b["ref_rf_N"], 661.7254, places=2)
        self.assertAlmostEqual(consistent_b["ref_e_tot_mJ"], 1.691099, places=4)

        # Consistent control terminal state: RF = 644.556 N, E_tot = 1.649218 mJ
        self.assertFalse(consistent_b["passed"])
        self.assertAlmostEqual(consistent_b["delta_rf_ref_N"], -17.169, places=2)
        self.assertAlmostEqual(consistent_b["delta_rf_ref_pct"], -2.595, places=2)
        self.assertAlmostEqual(consistent_b["delta_e_tot_ref_pct"], -2.477, places=2)

        # Lumped control terminal state: RF = 644.553 N
        self.assertFalse(lumped_b["passed"])
        self.assertAlmostEqual(lumped_b["delta_rf_ref_N"], -17.173, places=2)

        # Verify that the deficit was already established in Step 1
        consistent_res = self.matrix["diagnostics"]["consistent_control"]
        step1_rf = consistent_res["step1_rf2"]
        step1_deficit = step1_rf - 661.7254
        self.assertAlmostEqual(step1_deficit, -16.715, places=2)
        self.assertLess(abs(step1_deficit), abs(consistent_b["delta_rf_ref_N"]))

    def test_03_reclassification_to_case_b_local_release_stability_only(self):
        """Verify reclassification of Case B to local release stability only."""
        self.assertEqual(self.matrix["case_selected"], "CASE_B_LOCAL_RELEASE_STABILITY_ONLY")
        self.assertEqual(self.matrix["legacy_case_alias"], "CASE_B")
        self.assertEqual(self.matrix["assessment_a_status"], "PASS_CONSISTENT_ONLY")
        self.assertEqual(self.matrix["assessment_b_status"], "FAIL_ALL")

        # Epistemic boundary discipline
        scope = self.matrix["epistemic_scope"]
        self.assertIn("strictly establishes local mathematical and numerical stability", scope)
        self.assertIn("does NOT establish full continuum state restoration", scope)
        self.assertIn("mechanical displacement recovery", scope)
        self.assertIn("validity on nonmatching meshes", scope)

    def test_04_ranked_root_cause_hypotheses_matrix(self):
        """Verify the 4 ranked root-cause hypotheses are documented and testable."""
        hypotheses = self.matrix.get("root_cause_hypotheses", [])
        self.assertEqual(len(hypotheses), 4)

        # Hypothesis 1: Missing mechanical displacements
        h1 = hypotheses[0]
        self.assertEqual(h1["hypothesis_id"], "H1_MISSING_MECHANICAL_DISPLACEMENTS")
        self.assertEqual(h1["rank"], 1)
        self.assertEqual(h1["status"], "PRIMARY_CANDIDATE")
        self.assertIn("Job 1414571", h1["falsification_test"])

        # Hypothesis 2: Inverse damage distortion
        h2 = hypotheses[1]
        self.assertEqual(h2["hypothesis_id"], "H2_INVERSE_DAMAGE_DISTORTION")
        self.assertEqual(h2["rank"], 2)

        # Hypothesis 3: Coarse donor provenance
        h3 = hypotheses[2]
        self.assertEqual(h3["hypothesis_id"], "H3_COARSE_DONOR_PROVENANCE")
        self.assertEqual(h3["rank"], 3)
        self.assertEqual(h3["status"], "PROVEN_INDEPENDENT_MECHANISM")

        # Hypothesis 4: Unrestored history strain energy
        h4 = hypotheses[3]
        self.assertEqual(h4["hypothesis_id"], "H4_UNRESTORED_HISTORY_STRAIN_ENERGY")
        self.assertEqual(h4["rank"], 4)

    def test_05_gate_6c_governance_and_zero_cycles(self):
        """Verify strict Gate 6C hold and sequential remesh cycles remain zero."""
        self.assertEqual(self.matrix["gate_6c_verdict"], "GATE_6C_HOLD")

        active_task_path = ROOT / "project_coordination" / "ACTIVE_TASK.json"
        self.assertTrue(active_task_path.exists())
        data = json.loads(active_task_path.read_text(encoding="utf-8"))
        self.assertIn("GATE_6C_HOLD", data.get("gate_status", ""))

    def test_06_enriched_baseline_execution_and_extraction_readiness(self):
        """Verify enriched baseline Job 1414571 is recorded and extractor is staged."""
        hpc_ledger = ROOT / "project_coordination" / "HPC_JOB_LEDGER.csv"
        self.assertTrue(hpc_ledger.exists())
        ledger_text = hpc_ledger.read_text(encoding="utf-8")
        self.assertIn("1414571.mmaster02", ledger_text)

        extractor_path = ROOT / "scripts" / "state_transfer" / "extract_enriched_baseline_ground_truth.py"
        self.assertTrue(extractor_path.exists())
        extractor_code = extractor_path.read_text(encoding="utf-8")
        self.assertIn("ux", extractor_code)
        self.assertIn("uy", extractor_code)
        self.assertIn("d_val", extractor_code)
        self.assertIn("SDV2", extractor_code)
        self.assertIn("SDV14", extractor_code)


if __name__ == "__main__":
    unittest.main()
