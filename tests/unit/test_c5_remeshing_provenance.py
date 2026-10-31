"""Unit tests for C5 adaptive remeshing provenance and spatial qualification.

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Tests source companion job reconciliation, MISESERI stress recovery formulation,
spatial refinement metrics, 0 coarsened elements, and classification as
SCRIPTED_REFINEMENT_WITH_LIMITATIONS.
"""
from __future__ import print_function, division
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
AUDIT_REPORT = ROOT / "results/validation/c5_remeshing_provenance_audit.json"


class TestC5RemeshingProvenance(unittest.TestCase):
    def setUp(self):
        self.assertTrue(AUDIT_REPORT.is_file(), "Audit report must exist: %s" % AUDIT_REPORT)
        self.report = json.loads(AUDIT_REPORT.read_text(encoding="utf-8"))

    def test_companion_source_job_reconciliation(self):
        """Verify authentic source job 1419101.mmaster02, 7056 C4 quads, and 266 marked elements."""
        src = self.report["source_error_estimation_job"]
        self.assertEqual(src["pbs_job_id"], "1419101.mmaster02")
        self.assertEqual(src["job_name"], "M1_C4_COMPANION_MISESERI")
        self.assertEqual(src["analysis_type"], "Linear elastic companion continuum")
        self.assertEqual(src["step_name"], "STATIC_ELASTIC")
        self.assertEqual(src["c4_elements_total"], 7056)
        self.assertEqual(src["elements_marked_eta_015"], 266)
        self.assertAlmostEqual(src["marked_fraction_pct"], 3.7698, places=3)
        self.assertAlmostEqual(src["peak_miseseri_kNmm2"], 5.96102, places=3)

    def test_miseseri_formulation_and_units(self):
        """Verify MISESERI is treated as continuum recovered stress error, not phase field."""
        self.assertIn("SCRIPTED_REFINEMENT_WITH_LIMITATIONS", self.report["remeshing_provenance_classification"])
        justification = self.report["classification_justification"]
        self.assertIn("companion MISESERI stress recovery", justification)
        self.assertIn("1.77x area refinement", justification)

    def test_spatial_quantification_and_refinement_ratio(self):
        """Verify 7056 -> 12996 quads, 7265 -> 13278 nodes, and 0 coarsened elements."""
        spatial = self.report["spatial_quantification"]
        self.assertEqual(spatial["c4_quads"], 7056)
        self.assertEqual(spatial["c4_nodes"], 7265)
        self.assertEqual(spatial["c5_quads"], 12996)
        self.assertEqual(spatial["c5_nodes"], 13278)
        self.assertAlmostEqual(spatial["c5_fine_element_size_mm"], 0.0005, places=6)
        self.assertEqual(spatial["coarsened_elements_count"], 0)
        self.assertEqual(spatial["refinement_policy"], "REFINEMENT_ONLY")
        self.assertAlmostEqual(spatial["area_refinement_ratio_marked_mean"], 0.5653, places=3)
        self.assertEqual(spatial["spatial_coverage_of_high_error_zone_pct"], 100.0)

    def test_remeshing_classification_and_limits(self):
        """Verify classification is SCRIPTED_REFINEMENT_WITH_LIMITATIONS and documented boundary."""
        self.assertEqual(self.report["remeshing_provenance_classification"], "SCRIPTED_REFINEMENT_WITH_LIMITATIONS")
        meth = self.report["methodology_evaluation"]
        self.assertFalse(meth["is_native_abaqus_remeshing"])
        self.assertTrue(meth["is_scripted_generator"])
        self.assertFalse(meth["trajectory_prescribed"])
        self.assertIn("Strictly valid for straight Mode-I crack propagation", meth["applicability_boundary"])
        self.assertTrue(len(meth["minimal_adaptation_change_for_sequential_cycles"]) > 20)

    def test_evidence_sources_integrity(self):
        """Verify all evidence sources exist and have non-empty hashes."""
        sources = self.report["evidence_sources"]
        self.assertTrue(len(sources) >= 8)
        for rel_path, digest in sources.items():
            full = ROOT / rel_path
            self.assertTrue(full.is_file(), "Missing evidence file: %s" % full)
            self.assertEqual(len(digest), 64)


if __name__ == "__main__":
    unittest.main()
