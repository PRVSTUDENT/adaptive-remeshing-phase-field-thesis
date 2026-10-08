#!/usr/bin/env python3
"""
Unit Tests for Mode-II Gate M2-3 Step-2 errorTarget=1.0% Native Adaptive Mesh Verification
Task F1341: Verify generated mesh deck, CSVs, manifest, topology, and comparison figures.
"""
import os
import json
import unittest
import pandas as pd

class TestMode2Step21PctAdaptiveMesh(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base_dir = r"D:\Master thesis\Adaptive remeshing"
        cls.model_dir = os.path.join(cls.base_dir, r"models\pandey_kumar_mode2\06_paper_grounded_uel_preanalysis")
        cls.fig_dir = os.path.join(cls.base_dir, r"results\figures\mode2")

        cls.inp_path = os.path.join(cls.model_dir, "M2_3_ADAPTED_STEP2_RAW_1PCT.inp")
        cls.elems_csv = os.path.join(cls.model_dir, "m2_3_mesh_elements_step2_et1pct.csv")
        cls.nodes_csv = os.path.join(cls.model_dir, "m2_3_mesh_nodes_step2_et1pct.csv")
        cls.manifest_path = os.path.join(cls.model_dir, "MODE2_M2_3_STEP2_1PCT_ADAPTED_MESH_MANIFEST.json")

    def test_01_mesh_files_exist_and_non_empty(self):
        """Verify all generated Step-2 1% mesh files exist with expected file sizes."""
        self.assertTrue(os.path.exists(self.inp_path), f"Input deck missing: {self.inp_path}")
        self.assertTrue(os.path.exists(self.elems_csv), f"Elements CSV missing: {self.elems_csv}")
        self.assertTrue(os.path.exists(self.nodes_csv), f"Nodes CSV missing: {self.nodes_csv}")
        self.assertTrue(os.path.exists(self.manifest_path), f"Manifest missing: {self.manifest_path}")

        self.assertGreater(os.path.getsize(self.inp_path), 5_000_000, "Input deck size unexpectedly small")
        self.assertGreater(os.path.getsize(self.elems_csv), 5_000_000, "Elements CSV size unexpectedly small")
        self.assertGreater(os.path.getsize(self.nodes_csv), 2_000_000, "Nodes CSV size unexpectedly small")

    def test_02_manifest_topology_and_provenance(self):
        """Verify manifest contains exact expected topology metrics and provenance metadata."""
        with open(self.manifest_path, 'r') as f:
            data = json.load(f)

        prov = data.get("provenance", {})
        self.assertEqual(prov.get("source_step"), "Step-2")
        self.assertEqual(prov.get("source_frame_id"), 2000)
        self.assertAlmostEqual(prov.get("prescribed_shear_disp_ux_mm", 0.0), 0.02, places=4)
        self.assertEqual(prov.get("remeshing_rule", {}).get("error_target_pct"), 1.0)

        topo = data.get("mesh_topology", {})
        self.assertEqual(topo.get("total_finite_elements"), 80474)
        self.assertEqual(int(topo.get("quad_elements", 0)), 78363)
        self.assertEqual(int(topo.get("tri_elements", 0)), 2111)
        self.assertEqual(topo.get("total_nodes"), 80136)

    def test_03_element_csv_consistency_and_sizes(self):
        """Verify element geometry CSV table contains 80,474 rows with valid coordinates and size metrics."""
        df_elems = pd.read_csv(self.elems_csv)
        self.assertEqual(len(df_elems), 80474)
        self.assertIn("h_eq", df_elems.columns)
        self.assertIn("area", df_elems.columns)
        self.assertIn("xc", df_elems.columns)
        self.assertIn("yc", df_elems.columns)

        h_min = df_elems["h_eq"].min()
        h_max = df_elems["h_eq"].max()
        h_mean = df_elems["h_eq"].mean()

        self.assertAlmostEqual(h_min * 1000.0, 0.60, places=1) # ~0.60 um
        self.assertLess(h_max, 0.020)                          # < 20 um
        self.assertAlmostEqual(h_mean * 1000.0, 3.23, places=1)# ~3.23 um

    def test_04_node_csv_consistency(self):
        """Verify nodes CSV table contains 80,136 nodes within [0.0, 1.0] domain."""
        df_nodes = pd.read_csv(self.nodes_csv)
        self.assertEqual(len(df_nodes), 80136)
        self.assertGreaterEqual(df_nodes["x"].min(), -1e-6)
        self.assertLessEqual(df_nodes["x"].max(), 1.0 + 1e-6)
        self.assertGreaterEqual(df_nodes["y"].min(), -1e-6)
        self.assertLessEqual(df_nodes["y"].max(), 1.0 + 1e-6)

    def test_05_three_way_comparison_figures_exist(self):
        """Verify all publication figures generated for Step-2 1% and 3-way comparison exist."""
        figs = [
            "fig_mode2_m2_3_three_way_mesh_comparison.png",
            "fig_mode2_m2_3_three_way_mesh_comparison.pdf",
            "fig_mode2_m2_3_step2_1pct_mesh_full.png",
            "fig_mode2_m2_3_step2_1pct_mesh_full.pdf",
            "fig_mode2_m2_3_step2_1pct_mesh_crack_tip_zoom.png",
            "fig_mode2_m2_3_step2_1pct_mesh_crack_tip_zoom.pdf",
            "fig_mode2_m2_3_step2_1pct_mesh_corridor_zoom.png",
            "fig_mode2_m2_3_step2_1pct_mesh_corridor_zoom.pdf"
        ]
        for fig_name in figs:
            fig_path = os.path.join(self.fig_dir, fig_name)
            self.assertTrue(os.path.exists(fig_path), f"Figure missing: {fig_path}")
            self.assertGreater(os.path.getsize(fig_path), 10_000, f"Figure unexpectedly small: {fig_path}")

if __name__ == "__main__":
    unittest.main()
