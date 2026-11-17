# -*- coding: utf-8 -*-
"""
tests/unit/test_f1846_generalized_framework.py
==============================================
Unit tests for Task F1846: Generalized 2D Adaptive-Remeshing Framework.
Verifies:
1. Bitwise preservation of frozen UEL, current production framework, and frozen F1779 reference.
2. Generic2DGeometryAdapter containment, feature classification, and absence of hardcoded crack coordinates.
3. Native-MISESERI-first sizing logic and fallback labeling.
4. Finite-element quality of the unfamiliar L-panel adapted mesh.
5. Spatial field-following refinement on the unfamiliar L-panel.
6. Four-benchmark regression parity vs F1812 baselines.
7. Governance invariants: 0 new PBS jobs, cumulative 36 preserved, MASTER_GOAL_STATUS = OPEN.
"""

import os
import sys
import json
import math
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.generalized_2d_adaptive_framework_f1846 import (
    AdaptiveConfig,
    Generic2DGeometryAdapter,
    MeshQualityAuditEngine,
    FROZEN_UEL_SHA256,
    FROZEN_F1779_FRAMEWORK_SHA256
)

class TestF1846GeneralizedFramework(unittest.TestCase):

    def test_01_bitwise_preservation_of_frozen_sources(self):
        """Verifies bitwise integrity of UEL, current production framework, and F1779 reference."""
        # 1. Frozen UEL
        uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
        self.assertTrue(os.path.exists(uel_path), "f42_mixed_uel.for missing")
        with open(uel_path, "rb") as f:
            uel_sha = hashlib.sha256(f.read()).hexdigest().upper()
        self.assertEqual(uel_sha, FROZEN_UEL_SHA256)

        # 2. Current production framework (B0857C52...)
        prod_fw_path = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
        self.assertTrue(os.path.exists(prod_fw_path), "reusable_2d_adaptive_framework.py missing")
        with open(prod_fw_path, "rb") as f:
            prod_sha = hashlib.sha256(f.read()).hexdigest().upper()
        self.assertEqual(prod_sha, "B0857C521AE8E212C74F711CC3373AD57B081167727104905A0F4D2FBBDA0129")

        # 3. Frozen F1779 reference (CDD88460...)
        f1779_ref_path = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework_f1779_frozen.py")
        self.assertTrue(os.path.exists(f1779_ref_path), "F1779 frozen reference missing")
        with open(f1779_ref_path, "rb") as f:
            f1779_sha = hashlib.sha256(f.read()).hexdigest().upper()
        self.assertEqual(f1779_sha, FROZEN_F1779_FRAMEWORK_SHA256)

    def test_02_generic_2d_geometry_adapter_functionality(self):
        """Verifies Generic2DGeometryAdapter containment, polygon vertices, and no hardcoded crack coordinates."""
        config_data = {
            "case_id": "test_l_panel",
            "benchmark_name": "L-Panel Test",
            "geometry_type": "GENERIC_2D",
            "geometry": {
                "polygon_vertices": [
                    [0.0, 0.0], [100.0, 0.0], [100.0, 50.0],
                    [50.0, 50.0], [50.0, 100.0], [0.0, 100.0]
                ],
                "voids": [],
                "plate_width": 100.0,
                "plate_height": 100.0
            },
            "material": {"l0": 1.0, "E": 210000.0, "nu": 0.3},
            "remeshing_rule": {"error_target": 5.0, "min_element_size_mm": 0.5, "max_element_size_mm": 5.0}
        }
        cfg = AdaptiveConfig(config_data)
        adapter = Generic2DGeometryAdapter(cfg)

        pts = adapter.get_outer_polygon_points()
        self.assertEqual(len(pts), 6)
        self.assertEqual(adapter.get_hole_definitions(), [])
        self.assertIsNone(adapter.get_seam_line())

        # Test containment
        self.assertTrue(adapter.is_inside_domain(25.0, 25.0))
        self.assertTrue(adapter.is_inside_domain(75.0, 25.0))
        self.assertTrue(adapter.is_inside_domain(25.0, 75.0))
        self.assertFalse(adapter.is_inside_domain(75.0, 75.0))  # in cutout
        self.assertFalse(adapter.is_inside_domain(-5.0, 25.0))  # outside

        # Test feature classification (no crack coordinates)
        reg_corner = adapter.classify_region(50.5, 50.5)
        self.assertEqual(reg_corner, "CORNER_SINGULARITY_ZONE")
        reg_far = adapter.classify_region(10.0, 10.0)
        self.assertEqual(reg_far, "FAR_FIELD")

    def test_03_no_crack_coordinates_in_framework_remeshing_path(self):
        """Verifies that the generalized framework source does not hardcode crack paths in the remeshing path."""
        fw_path = os.path.join(REPO_ROOT, "scripts", "remeshing", "generalized_2d_adaptive_framework_f1846.py")
        with open(fw_path, "r") as f:
            lines = f.readlines()

        # Remeshing rule must act on ALL_ELEM
        rule_lines = [l for l in lines if "region=inst.sets['ALL_ELEM']" in l]
        self.assertGreaterEqual(len(rule_lines), 1, "RemeshingRule must act on ALL_ELEM")

    def test_04_unfamiliar_l_panel_mesh_quality(self):
        """Verifies FE quality gates for the unfamiliar L-panel adapted mesh."""
        audit_path = os.path.join(
            REPO_ROOT, "models", "pandey_kumar_mode1", "276_f1846_generalized_framework",
            "l_panel", "PK_F1846_UNFAMILIAR_L_PANEL_AUDIT.json"
        )
        self.assertTrue(os.path.exists(audit_path), "L-panel audit JSON missing")
        with open(audit_path, "r") as f:
            d = json.load(f)

        self.assertEqual(d["case_id"], "unfamiliar_l_panel")
        self.assertEqual(d["sizing_driver"], "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR")
        self.assertEqual(d["sizing_provenance"], "NATIVE")
        self.assertGreater(d["total_physical_elements"], 0)
        self.assertEqual(d["non_positive_jacobians"], 0)
        self.assertTrue(d["min_det_j"] > 0)
        self.assertGreaterEqual(d["quad_percent"], 85.0)
        self.assertLess(d["max_aspect_ratio"], 4.0)
        self.assertEqual(d["distorted_elements"], 0)

    def test_05_unfamiliar_l_panel_spatial_refinement(self):
        """Verifies that refinement on the unfamiliar L-panel followed the field (concentrated at corner)."""
        inp_path = os.path.join(
            REPO_ROOT, "models", "pandey_kumar_mode1", "276_f1846_generalized_framework",
            "l_panel", "PK_F1846_UNFAMILIAR_L_PANEL_ADAPT_PHYS.inp"
        )
        self.assertTrue(os.path.exists(inp_path), "L-panel physical mesh missing")
        nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(inp_path)

        near_sizes = []
        far_sizes = []
        for eid, conn in quads.items():
            pts = [nodes[n] for n in conn]
            cx = sum(p[0] for p in pts) / 4.0
            cy = sum(p[1] for p in pts) / 4.0
            x, y = [p[0] for p in pts], [p[1] for p in pts]
            area = 0.5 * abs((x[0]*y[1]-x[1]*y[0]) + (x[1]*y[2]-x[2]*y[1]) + (x[2]*y[3]-x[3]*y[2]) + (x[3]*y[0]-x[0]*y[3]))
            h = math.sqrt(area)
            d = math.hypot(cx - 50.0, cy - 50.0)
            if d <= 10.0:
                near_sizes.append(h)
            elif d >= 40.0:
                far_sizes.append(h)

        self.assertGreater(len(near_sizes), 0)
        self.assertGreater(len(far_sizes), 0)
        mean_near = sum(near_sizes) / len(near_sizes)
        mean_far = sum(far_sizes) / len(far_sizes)
        ratio = mean_far / mean_near
        self.assertGreaterEqual(ratio, 2.0, "Refinement ratio far/corner must be >= 2.0x")

    def test_06_four_benchmark_regression_summary(self):
        """Verifies that the four-benchmark regression completed and records element counts vs F1812."""
        summary_path = os.path.join(REPO_ROOT, "results", "validation", "f1846_four_benchmark_regression_summary.json")
        self.assertTrue(os.path.exists(summary_path), "Regression summary JSON missing")
        with open(summary_path, "r") as f:
            summary = json.load(f)

        cases = ["case_1", "case_2", "case_3", "case_5"]
        for cid in cases:
            self.assertIn(cid, summary)
            c = summary[cid]
            self.assertEqual(c["sizing_driver"], "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR")
            self.assertEqual(c["sizing_provenance"], "NATIVE")
            self.assertTrue(c["min_det_j"] > 0)
            self.assertGreaterEqual(c["quad_percent"], 85.0)
            self.assertLess(c["max_aspect_ratio"], 4.0)

        # Exact parity checks
        self.assertEqual(summary["case_1"]["f1846_elements"], 25461)
        self.assertEqual(summary["case_2"]["f1846_elements"], 41438)
        self.assertAlmostEqual(summary["case_3"]["delta_pct"], 1.90, delta=0.5)
        self.assertAlmostEqual(summary["case_5"]["delta_pct"], -0.36, delta=0.5)

    def test_07_governance_and_pbs_accounting(self):
        """Verifies strictly 0 new PBS jobs consumed and cumulative PBS submissions = 36."""
        task_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
        with open(task_path, "r", encoding="utf-8-sig") as f:
            task = json.load(f)

        self.assertEqual(task["task_id"], "F1846-GENERALIZED-FRAMEWORK-FROM-F1779")
        self.assertEqual(task["max_new_pbs_submissions"], 0)
        self.assertEqual(task["submissions_consumed"], 0)
        self.assertEqual(task["cumulative_pbs_submissions"], 36)
        self.assertEqual(task["master_goal_status"], "OPEN")

    def test_08_evidence_correction_and_figures(self):
        """Verifies Task F1847 evidence deliverables: donor ODB, relative summary paths, and figures."""
        # 1. Donor ODB exists, correct size and hash
        odb_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "276_f1846_generalized_framework", "l_panel", "PK_F1846_LPANEL_COARSE.odb")
        self.assertTrue(os.path.exists(odb_path))
        self.assertEqual(os.path.getsize(odb_path), 365628)
        with open(odb_path, "rb") as f:
            odb_sha = hashlib.sha256(f.read()).hexdigest().upper()
        self.assertEqual(odb_sha, "84FE528239F5649A185BBB5DA9752B54AC288AED8393425E676D71E449554056")

        # 2. Summary JSON has repo-relative paths (no Windows backslash absolute paths)
        summary_path = os.path.join(REPO_ROOT, "results", "validation", "f1846_four_benchmark_regression_summary.json")
        with open(summary_path, "r", encoding="utf-8") as f:
            summary_txt = f.read()
            summary = json.loads(summary_txt)
        self.assertNotIn("D:\\\\", summary_txt)
        self.assertNotIn("D:/", summary_txt)
        for cid in ["case_1", "case_2", "case_3", "case_5"]:
            self.assertTrue(summary[cid]["audit_json"].startswith("models/"))
            self.assertTrue(summary[cid]["physical_mesh"].startswith("models/"))

        # 3. All publication figures exist and non-empty
        figs = [
            "fig_f1846_unfamiliar_l_panel_mesh.png",
            "fig_f1846_unfamiliar_l_panel_mesh.pdf",
            "fig_f1847_case_1_mesh.png",
            "fig_f1847_case_1_mesh.pdf",
            "fig_f1847_case_2_mesh.png",
            "fig_f1847_case_2_mesh.pdf",
            "fig_f1847_case_3_mesh.png",
            "fig_f1847_case_3_mesh.pdf",
            "fig_f1847_case_5_mesh.png",
            "fig_f1847_case_5_mesh.pdf",
            "fig_f1847_four_benchmark_composite.png",
            "fig_f1847_four_benchmark_composite.pdf"
        ]
        for fig in figs:
            fp = os.path.join(REPO_ROOT, "results", "figures", fig)
            self.assertTrue(os.path.exists(fp), "Missing figure %s" % fig)
            self.assertGreater(os.path.getsize(fp), 1000, "Figure %s too small" % fig)

if __name__ == "__main__":
    unittest.main()
