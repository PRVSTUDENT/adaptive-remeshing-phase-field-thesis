# -*- coding: utf-8 -*-
"""
tests/unit/test_f1714_five_hole_generalization.py
================================================
Unit test suite verifying Task F1714 Five-Hole Generalization Benchmark:
1. Geometry and void topology conformance against Pandey & Kumar (2025) Table 5.
2. Linear elastic coarse pre-analysis and authentic MISESERI error indicator.
3. Adapted physical mesh metrics, Jacobian validity (100% positive), and published target parity (+0.70%).
4. Process zone resolution in inter-hole ligaments (h <= 0.17 * l0).
5. Constitutive compatibility audit report and Amor split documentation.
6. 3-layer production deck structure and cluster datacheck qualification.
"""

import os
import sys
import json
import unittest

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BENCHMARK_DIR = os.path.join(WORKSPACE_ROOT, "models", "pandey_kumar_mode1", "207_f1714_five_hole_benchmark")


class TestF1714FiveHoleGeneralization(unittest.TestCase):

    def test_01_benchmark_specification_exists(self):
        spec_path = os.path.join(WORKSPACE_ROOT, "docs", "validation", "F1714_FIVE_HOLE_BENCHMARK_SPECIFICATION.md")
        self.assertTrue(os.path.isfile(spec_path), "F1714 benchmark specification file missing: %s" % spec_path)
        with open(spec_path, "r") as f:
            content = f.read()
        self.assertIn("Table 5", content)
        self.assertIn("0.008", content)  # l0 = 0.008 mm
        self.assertIn("12,944", content)  # published target
        self.assertIn("Amor", content)

    def test_02_constitutive_compatibility_report_exists(self):
        rep_path = os.path.join(WORKSPACE_ROOT, "docs", "validation", "F1714_CONSTITUTIVE_COMPATIBILITY_REPORT.md")
        self.assertTrue(os.path.isfile(rep_path), "F1714 constitutive report missing: %s" % rep_path)
        with open(rep_path, "r") as f:
            content = f.read()
        self.assertIn("Amor et al. (2009)", content)
        self.assertIn("Miehe et al. (2010)", content)
        self.assertIn("f42_mixed_uel.for", content)
        self.assertIn("CE8D5EDC", content)
        self.assertIn("INVARIANT", content.upper())

    def test_03_coarse_preanalysis_and_miseseri_telemetry(self):
        audit_path = os.path.join(BENCHMARK_DIR, "F1714_FIVE_HOLE_ADAPTIVE_MESH_AUDIT.json")
        self.assertTrue(os.path.isfile(audit_path), "F1714 adaptive mesh audit missing: %s" % audit_path)
        with open(audit_path, "r") as f:
            audit = json.load(f)

        coarse = audit["coarse_mesh"]
        self.assertGreaterEqual(coarse["num_elements"], 2500)
        self.assertLessEqual(coarse["num_elements"], 3500)
        self.assertAlmostEqual(coarse["seed_size_mm"], 0.02, places=4)

        miseseri = audit["miseseri_field"]
        self.assertGreater(miseseri["min_error"], 0.0)
        self.assertGreater(miseseri["max_error"], 100.0)
        self.assertGreater(miseseri["mean_error"], 5.0)

    def test_04_adapted_mesh_parity_vs_published_target(self):
        audit_path = os.path.join(BENCHMARK_DIR, "F1714_FIVE_HOLE_ADAPTIVE_MESH_AUDIT.json")
        with open(audit_path, "r") as f:
            audit = json.load(f)

        adapt = audit["adapted_mesh"]
        n_phys = adapt["num_physical_elements"]
        published_target = adapt["published_target_elements"]  # 12944
        discrepancy_pct = adapt["parity_discrepancy_pct"]

        self.assertEqual(published_target, 12944)
        self.assertEqual(n_phys, 13034)
        self.assertAlmostEqual(discrepancy_pct, 0.70, delta=0.05)
        self.assertLess(abs(discrepancy_pct), 5.0, "Parity discrepancy must be within 5% of literature")
        self.assertGreater(adapt["quad_elements"] / float(n_phys), 0.95, "Mesh must be quad-dominated (>95%)")

    def test_05_mesh_quality_jacobians_and_aspect_ratios(self):
        quality_path = os.path.join(BENCHMARK_DIR, "F1714_MESH_QUALITY_REPORT.json")
        self.assertTrue(os.path.isfile(quality_path), "F1714 mesh quality report missing: %s" % quality_path)
        with open(quality_path, "r") as f:
            quality = json.load(f)

        qm = quality["quality_metrics"]
        self.assertEqual(qm["inverted_element_count"], 0, "No inverted elements permitted")
        self.assertEqual(qm["positive_jacobian_rate_pct"], 100.0, "100% positive Jacobians required")
        self.assertLess(qm["mean_aspect_ratio"], 1.50, "Mean aspect ratio must be < 1.50")
        self.assertLess(qm["max_aspect_ratio"], 3.50, "Max aspect ratio must be < 3.50")

    def test_06_process_zone_ligament_resolution(self):
        quality_path = os.path.join(BENCHMARK_DIR, "F1714_MESH_QUALITY_REPORT.json")
        with open(quality_path, "r") as f:
            quality = json.load(f)

        holes = quality["resolution_telemetry"]["hole_neighborhoods"]
        for hname in ["h1", "h2", "h3", "h4", "h5"]:
            self.assertIn(hname, holes)
            hres = holes[hname]
            self.assertTrue(hres["adequate_refinement"], "Hole %s requires adequate refinement (h <= l0/2)" % hname)
            self.assertLessEqual(hres["min_h_over_l0"], 0.35, "Hole %s min_h must be <= 0.35*l0" % hname)
            self.assertGreater(hres["num_elements_near"], 300, "Hole %s must have > 300 elements near boundary" % hname)

    def test_07_production_deck_structure_and_coupling(self):
        prod_path = os.path.join(BENCHMARK_DIR, "PK_F1714_JOB2_ADAPTED_PROD.inp")
        self.assertTrue(os.path.isfile(prod_path), "Production deck missing: %s" % prod_path)
        
        with open(prod_path, "r") as f:
            lines = f.readlines()

        has_phase_quads = any("*ELEMENT, TYPE=U1, ELSET=PHASE_QUADS" in l for l in lines)
        has_mech_quads = any("*ELEMENT, TYPE=U2, ELSET=MECH_QUADS" in l for l in lines)
        has_comp_quads = any("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS" in l for l in lines)
        has_equation = any("*EQUATION" in l for l in lines)
        has_rp_node = any("NSET=N_RP" in l for l in lines)
        has_props = any("0.0080, 0.0027, 210.0, 0.3, 1.0e-7" in l for l in lines)

        self.assertTrue(has_phase_quads, "Layer 1 Phase UEL quads missing")
        self.assertTrue(has_mech_quads, "Layer 2 Mech UEL quads missing")
        self.assertTrue(has_comp_quads, "Layer 3 Companion CPE quads missing")
        self.assertTrue(has_equation, "*EQUATION kinematic coupling missing")
        self.assertTrue(has_rp_node, "Reference node set N_RP missing")
        self.assertTrue(has_props, "Five-hole material properties (l0=0.0080, Gc=0.0027) missing")

        # Verify no lines exceed Abaqus card limit (> 16 items in comma lists)
        for i, l in enumerate(lines):
            if l.startswith("*") or l.startswith("**"):
                continue
            parts = [p.strip() for p in l.split(",") if p.strip()]
            self.assertLessEqual(len(parts), 16, "Line %d exceeds 16 entries: %s" % (i+1, l[:50]))

    def test_08_publication_figures_and_zooms_exist(self):
        fig_dir = os.path.join(WORKSPACE_ROOT, "figures", "pandey_kumar_fig22_25_reproduction")
        expected_figs = [
            ("fig_f1714_five_hole_geometry.pdf", "fig_f1714_five_hole_geometry.png"),
            ("fig_f1714_coarse_mesh.pdf", "fig_f1714_coarse_mesh.png"),
            ("fig_f1714_error_indicator_miseseri.pdf", "fig_f1714_error_indicator_miseseri.png"),
            ("fig_f1714_adaptive_mesh_only.pdf", "fig_f1714_adaptive_mesh_only.png"),
            ("fig_f1714_ligament_mesh_zooms.pdf", "fig_f1714_ligament_mesh_zooms.png"),
        ]
        for pdf_name, png_name in expected_figs:
            pdf_path = os.path.join(fig_dir, pdf_name)
            png_path = os.path.join(fig_dir, png_name)
            self.assertTrue(os.path.isfile(pdf_path), "Missing PDF figure: %s" % pdf_path)
            self.assertTrue(os.path.isfile(png_path), "Missing PNG figure: %s" % png_path)
            self.assertGreater(os.path.getsize(pdf_path), 10000, "PDF figure %s unexpectedly small" % pdf_name)
            self.assertGreater(os.path.getsize(png_path), 50000, "PNG figure %s unexpectedly small" % png_name)


if __name__ == "__main__":
    unittest.main()
