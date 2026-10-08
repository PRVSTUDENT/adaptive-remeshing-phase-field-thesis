# -*- coding: utf-8 -*-
"""
Unit tests for Mode-II Step-2 Native Adaptive Mesh Verification & Publication
Mesh: M2_3_ADAPTED_STEP2_RAW_2PCT.inp (22,405 finite elements, 22,512 nodes)
"""
import unittest
import os
import json
import hashlib

class TestMode2Step2AdaptiveMesh(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.mode2_dir = os.path.join(cls.repo_dir, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis")
        cls.fig_dir = os.path.join(cls.repo_dir, "results", "figures", "mode2")
        
        cls.step2_inp = os.path.join(cls.mode2_dir, "M2_3_ADAPTED_STEP2_RAW_2PCT.inp")
        cls.step1_inp = os.path.join(cls.mode2_dir, "M2_3_ADAPTED_RAW_2PCT.inp")
        cls.manifest_json = os.path.join(cls.mode2_dir, "MODE2_M2_3_STEP2_ADAPTED_MESH_MANIFEST.json")
        cls.elems_csv = os.path.join(cls.mode2_dir, "m2_3_mesh_elements_step2_et2pct.csv")
        cls.nodes_csv = os.path.join(cls.mode2_dir, "m2_3_mesh_nodes_step2_et2pct.csv")
        
    def test_step2_input_deck_exists_and_hash(self):
        self.assertTrue(os.path.exists(self.step2_inp), "Step-2 input deck must exist")
        self.assertGreater(os.path.getsize(self.step2_inp), 1000000, "Input deck must be >1 MB")
        
        h = hashlib.sha256()
        with open(self.step2_inp, 'rb') as f:
            h.update(f.read())
        deck_sha = h.hexdigest()
        self.assertEqual(deck_sha, "9c453eb3b004c3a0d9727fc380ff04631108fa091b846a89bc62ca64c800c563")

    def test_step2_manifest_consistency(self):
        self.assertTrue(os.path.exists(self.manifest_json), "Manifest JSON must exist")
        with open(self.manifest_json, 'r') as f:
            data = json.load(f)
            
        self.assertEqual(data["mesh_topology"]["total_finite_elements"], 22405)
        self.assertEqual(data["mesh_topology"]["total_nodes"], 22512)
        self.assertEqual(int(data["mesh_topology"]["quad_elements"]), 21827)
        self.assertEqual(int(data["mesh_topology"]["tri_elements"]), 578)
        self.assertEqual(data["provenance"]["source_step"], "Step-2")
        self.assertAlmostEqual(data["provenance"]["prescribed_shear_disp_ux_mm"], 0.0200, places=4)

    def test_step2_csv_files_exist_and_counts(self):
        self.assertTrue(os.path.exists(self.elems_csv), "Elements CSV must exist")
        self.assertTrue(os.path.exists(self.nodes_csv), "Nodes CSV must exist")
        
        with open(self.elems_csv, 'r') as f:
            elem_lines = [l for l in f if l.strip()]
        self.assertEqual(len(elem_lines), 22406) # header + 22405 elements
        
        with open(self.nodes_csv, 'r') as f:
            node_lines = [l for l in f if l.strip()]
        self.assertEqual(len(node_lines), 22513) # header + 22512 nodes

    def test_comparison_vs_step1_mesh(self):
        self.assertTrue(os.path.exists(self.step1_inp), "Step-1 input deck must exist")
        with open(self.manifest_json, 'r') as f:
            data = json.load(f)
            
        comp = data["comparison_vs_step1_mesh"]
        self.assertEqual(comp["step1_elements"], 22530)
        self.assertEqual(comp["step2_elements"], 22405)
        self.assertEqual(comp["element_difference"], -125)
        self.assertAlmostEqual(comp["element_difference_pct"], -0.5548, places=2)

    def test_publication_figures_exist(self):
        figs = [
            "fig_mode2_m2_3_step2_adaptive_mesh_full.png",
            "fig_mode2_m2_3_step2_adaptive_mesh_full.pdf",
            "fig_mode2_m2_3_step2_adaptive_mesh_crack_tip_zoom.png",
            "fig_mode2_m2_3_step2_adaptive_mesh_crack_tip_zoom.pdf",
            "fig_mode2_m2_3_step2_adaptive_mesh_corridor_zoom.png",
            "fig_mode2_m2_3_step2_adaptive_mesh_corridor_zoom.pdf",
            "fig_mode2_m2_3_step1_vs_step2_mesh_comparison.png",
            "fig_mode2_m2_3_step1_vs_step2_mesh_comparison.pdf"
        ]
        for fig_name in figs:
            fig_path = os.path.join(self.fig_dir, fig_name)
            self.assertTrue(os.path.exists(fig_path), "Figure %s must exist" % fig_name)
            self.assertGreater(os.path.getsize(fig_path), 5000, "Figure %s must be >5KB" % fig_name)

if __name__ == "__main__":
    unittest.main()
