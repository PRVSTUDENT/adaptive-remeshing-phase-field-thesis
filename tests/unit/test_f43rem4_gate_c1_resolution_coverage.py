#!/usr/bin/env python3
"""
Unit tests for F43REM4 Task R4 crack-corridor audit and resolution coverage analysis.
"""

import json
import os
import unittest
from pathlib import Path

from scripts.validation.analyze_f43rem4_gate_c1_resolution_coverage import (
    compute_sha256,
    parse_inp_mesh,
    polygon_signed_area,
    compute_element_geometry,
    extract_connected_corridor_from_notch,
    evaluate_connected_fine_path,
    analyze_crack_corridor_coverage
)


class TestF43REM4CrackCorridorAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parent.parent.parent
        cls.bridge_dir = cls.repo_root / "models" / "generated" / "mode_ii" / "f43_stage_c_bridge"
        cls.batch_dir = cls.bridge_dir / "remesh_sensitivity_batch"
        cls.audit_json = cls.batch_dir / "F43REM4_CRACK_CORRIDOR_AUDIT.json"
        cls.master_report = cls.batch_dir / "F43REM4_GATEC1_COMPARISON_REPORT.json"

    def test_audit_json_structure_and_governance(self):
        self.assertTrue(self.audit_json.exists(), "F43REM4_CRACK_CORRIDOR_AUDIT.json must exist")
        with open(self.audit_json, "r", encoding="utf-8") as f:
            d = json.load(f)

        self.assertEqual(d["task_id"], "F43REM4-GATEC1-R4")
        self.assertEqual(d["scientific_classification"]["Gate_C1_localization"], "PASS")
        self.assertEqual(d["scientific_classification"]["best_adaptive_candidate"], "F43REM4_MM")
        self.assertEqual(d["scientific_classification"]["Gate_C1_phase_field_resolution"], "HOLD")
        self.assertFalse(d["scientific_classification"]["final_production_mesh_selected"])
        self.assertEqual(d["scientific_classification"]["final_selected_candidate"], "none")

        gov = d["authority_and_governance"]
        self.assertFalse(gov["execution_authorized"])
        self.assertFalse(gov["submission_approved"])
        self.assertEqual(gov["maximum_jobs_now"], 0)

    def test_extracted_summary_metrics_values(self):
        with open(self.audit_json, "r", encoding="utf-8") as f:
            d = json.load(f)

        m = d["extracted_summary_metrics"]
        self.assertAlmostEqual(m["MM_top1_fraction_h_le_l0_over_2"], 0.0462, delta=0.01)
        self.assertAlmostEqual(m["MM_top5_fraction_h_le_l0_over_2"], 0.0301, delta=0.01)
        self.assertAlmostEqual(m["MM_top10_fraction_h_le_l0_over_2"], 0.0211, delta=0.01)

        self.assertAlmostEqual(m["PK5_top1_fraction_h_le_l0_over_2"], 0.1263, delta=0.01)
        self.assertAlmostEqual(m["PK5_top5_fraction_h_le_l0_over_2"], 0.1064, delta=0.01)
        self.assertAlmostEqual(m["PK5_top10_fraction_h_le_l0_over_2"], 0.0846, delta=0.01)

        self.assertAlmostEqual(m["PK1_top1_fraction_h_le_l0_over_2"], 0.8247, delta=0.01)
        self.assertAlmostEqual(m["PK1_top5_fraction_h_le_l0_over_2"], 0.8493, delta=0.01)
        self.assertAlmostEqual(m["PK1_top10_fraction_h_le_l0_over_2"], 0.8692, delta=0.01)

        self.assertFalse(m["MM_connected_fine_corridor"])
        self.assertFalse(m["PK5_connected_fine_corridor"])
        self.assertTrue(m["PK1_connected_fine_corridor"])

        self.assertEqual(m["best_adaptive_candidate"], "MM")
        self.assertEqual(m["final_selected_candidate"], "none")
        self.assertEqual(m["Gate_C1"], "HOLD")

    def test_svg_figures_generated(self):
        figures_dir = self.batch_dir / "figures"
        self.assertTrue(figures_dir.exists())
        for cname in ["f43rem4_pk1", "f43rem4_pk5", "f43rem4_mm"]:
            svg_file = figures_dir / f"{cname}_crack_corridor_audit.svg"
            self.assertTrue(svg_file.exists(), f"SVG figure {svg_file.name} must exist")
            self.assertGreater(svg_file.stat().st_size, 1000)

    def test_master_report_updated_classification(self):
        with open(self.master_report, "r", encoding="utf-8") as f:
            mreport = json.load(f)

        dec = mreport["gate_c1_decision"]
        self.assertEqual(dec["gate_c1"], "HOLD")
        self.assertEqual(dec["Gate_C1_localization"], "PASS")
        self.assertEqual(dec["best_adaptive_candidate"], "F43REM4_MM")
        self.assertEqual(dec["Gate_C1_phase_field_resolution"], "HOLD")
        self.assertFalse(dec["final_production_mesh_selected"])
        self.assertEqual(dec["selected_candidate"], "none")


if __name__ == "__main__":
    unittest.main()
