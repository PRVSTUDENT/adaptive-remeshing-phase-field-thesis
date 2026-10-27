#!/usr/bin/env python3
"""
Unit test for independent comparative convergence and crack-localization audit
between Package 125 (canonical unaccelerated AM) and Package 126 Revision 4
(safeguarded Anderson-accelerated AM) at authentic Increment 87.

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Gate: STAGE_C1_2_STEP2_ENERGY_GATE_FAILED
"""

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AUDIT_JSON = REPO_ROOT / "results" / "validation" / "package125_vs_package126_r4_convergence_audit.json"


class TestPackage125VsPackage126R4ConvergenceAudit(unittest.TestCase):
    """Test suite verifying the Package 125 vs Package 126 R4 convergence audit artifact."""

    @classmethod
    def setUpClass(cls):
        if not AUDIT_JSON.exists():
            raise FileNotFoundError(f"Missing audit JSON: {AUDIT_JSON}")
        with open(AUDIT_JSON, "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_01_schema_and_task(self):
        """Verify schema version, task ID, and investigation type."""
        self.assertEqual(self.data.get("schema"), 1)
        self.assertEqual(self.data.get("task_id"), "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(
            self.data.get("investigation"),
            "INDEPENDENT_COMPARATIVE_CONVERGENCE_AND_CRACK_LOCALIZATION_AUDIT",
        )
        self.assertEqual(self.data.get("governing_gate"), "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED")

    def test_02_classification_and_candidates(self):
        """Verify classification is ACCELERATION_CAUSES_OSCILLATORY_ITERATION among 5 candidates."""
        expected_candidates = [
            "ACCELERATION_DEGRADES_FIXED_POINT_CONVERGENCE",
            "ACCELERATION_CAUSES_OSCILLATORY_ITERATION",
            "ACCELERATION_NEUTRAL_WITHIN_TESTED_BUDGET",
            "COMPARISON_NUMERICALLY_INVALID",
            "MECHANISM_NOT_RESOLVED",
        ]
        self.assertEqual(self.data.get("classification_candidates"), expected_candidates)
        self.assertEqual(self.data.get("classification"), "ACCELERATION_CAUSES_OSCILLATORY_ITERATION")
        self.assertGreaterEqual(len(self.data.get("finding", "")), 20)

    def test_03_provenance(self):
        """Verify solver jobs provenance and exit status."""
        prov = self.data.get("summary_provenance", {})
        self.assertEqual(prov.get("p125_job_id"), "1417969.mmaster02")
        self.assertEqual(prov.get("p125_exit_status"), 0)
        self.assertEqual(prov.get("r4_job_id"), "1418006.mmaster02")
        self.assertEqual(prov.get("r4_exit_status"), 0)
        self.assertGreater(prov.get("p125_walltime_s", 0), 0)
        self.assertGreater(prov.get("r4_walltime_s", 0), 0)

    def test_04_amplification_metrics(self):
        """Verify damage and force update amplification factors."""
        metrics = self.data.get("amplification_metrics", {})
        alpha_d = metrics.get("terminal_delta_d_amplification_alpha")
        alpha_rf2 = metrics.get("terminal_delta_rf2_amplification_alpha")

        # Anderson R4 terminal updates are amplified compared to P125
        self.assertGreater(alpha_d, 2.0)
        self.assertAlmostEqual(alpha_d, 2.3042, places=2)
        self.assertGreater(alpha_rf2, 30.0)
        self.assertAlmostEqual(alpha_rf2, 32.62, places=1)

        # Absolute terminal values
        p125_d = metrics.get("p125_terminal_delta_d")
        r4_d = metrics.get("r4_terminal_delta_d")
        self.assertLess(p125_d, 0.0012)
        self.assertGreater(r4_d, 0.0025)

        p125_rf2 = metrics.get("p125_terminal_delta_rf2_N")
        r4_rf2 = metrics.get("r4_terminal_delta_rf2_N")
        self.assertLess(p125_rf2, 0.1)
        self.assertGreater(r4_rf2, 2.0)

    def test_05_anderson_safeguard_statistics(self):
        """Verify Anderson depth, proposal acceptance, and fallback counts."""
        stats = self.data.get("anderson_safeguard_statistics", {})
        self.assertEqual(stats.get("depth_m"), 3)
        self.assertEqual(stats.get("start_cycle"), 6)
        self.assertEqual(stats.get("total_intervention_cycles"), 35)
        self.assertEqual(stats.get("accepted_proposals"), 21)
        self.assertEqual(stats.get("safeguard_fallback_proposals"), 13)
        self.assertAlmostEqual(stats.get("acceptance_ratio"), 0.6, places=2)

    def test_06_block_statistics_parity_and_divergence(self):
        """Verify baseline parity in Cycles 1-5 and oscillatory divergence in Cycles 26-40."""
        blocks = self.data.get("block_statistics", {})
        p125_c1_5 = blocks.get("package_125", {}).get("cycles_1_5", {})
        r4_c1_5 = blocks.get("package_126_r4", {}).get("cycles_1_5", {})

        # Machine precision parity in unaccelerated window
        self.assertAlmostEqual(p125_c1_5.get("terminal_rf2_N"), r4_c1_5.get("terminal_rf2_N"), places=7)
        self.assertAlmostEqual(p125_c1_5.get("terminal_delta_d"), r4_c1_5.get("terminal_delta_d"), places=12)

        # Terminal block (Cycles 26-40) contrast
        p125_c26_40 = blocks.get("package_125", {}).get("cycles_26_40", {})
        r4_c26_40 = blocks.get("package_126_r4", {}).get("cycles_26_40", {})

        self.assertLess(p125_c26_40.get("mean_rho_d"), 1.0)
        self.assertGreater(r4_c26_40.get("mean_rho_d"), 1.0)
        self.assertGreater(r4_c26_40.get("rho_d_gt_1_count"), p125_c26_40.get("rho_d_gt_1_count"))

    def test_07_spatial_audit_crack_path_localization(self):
        """Verify spatial damage overlap and crack tip positioning."""
        spatial = self.data.get("spatial_audit", {})
        self.assertTrue(spatial.get("spatial_data_verified"))
        self.assertEqual(spatial.get("total_physical_nodes"), 4588)

        overlap = spatial.get("crack_tip_and_overlap_by_threshold", {})
        # Broad damaged zone (d >= 0.1) has near-perfect Dice overlap
        self.assertGreater(overlap.get("threshold_0.1", {}).get("dice_overlap_coefficient"), 0.99)
        # Moderate damage (d >= 0.3) has >95% Dice overlap
        self.assertGreater(overlap.get("threshold_0.3", {}).get("dice_overlap_coefficient"), 0.97)
        # Core softening band (d >= 0.5) has >85% Dice overlap
        self.assertGreater(overlap.get("threshold_0.5", {}).get("dice_overlap_coefficient"), 0.85)

        # Crack tip difference at d >= 0.5 is less than element width (~0.014 mm)
        diff_tip = overlap.get("threshold_0.5", {}).get("diff_max_x_mm")
        self.assertLess(diff_tip, 0.002)

    def test_08_controlled_future_hypothesis_assessment(self):
        """Verify controlled future hypothesis recommendation is False with technical rationale."""
        hyp = self.data.get("controlled_future_hypothesis_assessment", {})
        self.assertFalse(hyp.get("hypothesis_recommended"))
        self.assertIn("Anderson acceleration", hyp.get("rationale", ""))
        self.assertIn("softening", hyp.get("rationale", ""))


if __name__ == "__main__":
    unittest.main()
