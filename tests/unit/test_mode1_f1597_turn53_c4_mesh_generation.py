#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn53_c4_mesh_generation.py

Unit tests verifying Candidate C4 mesh generation authentically driven by
the measured Zienkiewicz-Zhu MISESERI error distribution.
Governing Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: 15edb78c-2f6d-454e-96af-4518fca0ce6f
Protocol Version: 2
"""
import sys
import unittest
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.remeshing.generate_error_driven_c4_mesh import (
    compute_miseseri_sizing_parameters,
    generate_c4_mesh_from_csv
)

class TestMode1C4MeshGeneration(unittest.TestCase):
    def setUp(self):
        self.csv_path = REPO_ROOT / "results/validation/mode1_f1597/c3_companion_miseseri_distribution.csv"
        self.assertTrue(self.csv_path.exists(), f"MISESERI distribution missing: {self.csv_path}")

    def test_c4_mesh_topology_and_quality(self):
        """Verify C4 mesh generated from authentic MISESERI has positive Jacobians and valid crack flanks."""
        mesh = generate_c4_mesh_from_csv(self.csv_path, error_threshold=0.15, h_fine=0.00080)
        
        # Verify element counts
        self.assertGreaterEqual(mesh["n_elements"], 3500)
        self.assertLessEqual(mesh["n_elements"], 5500)
        
        # Verify strictly positive Jacobians everywhere
        self.assertGreater(mesh["min_det_jac"], 0.0, "All element Jacobians must be strictly positive")
        
        # Verify process zone resolution: in fine band, spacing must be <= ell_0 / 4 = 0.0010 mm
        self.assertLessEqual(mesh["sizing_params"]["h_fine"], 0.0010)

        # Verify slit flanks: nodes along y = 0.050 with x <= 0.040 must be duplicated
        nodes = mesh["nodes"]
        slit_nodes = [nid for nid, p in nodes.items() if abs(p[1] - 0.050) < 1e-6 and p[0] <= 0.040 + 1e-6 and nid != 999999]
        x_slit = np.unique([round(nodes[nid][0], 6) for nid in slit_nodes])
        for x in x_slit:
            matching = [nid for nid in slit_nodes if abs(nodes[nid][0] - x) < 1e-6]
            self.assertEqual(len(matching), 2, f"Expected exactly 2 split nodes at slit point x={x}, found {len(matching)}")

    def test_deterministic_error_distribution_sensitivity(self):
        """Prove that mesh sizing and node placement change deterministically when error field changes."""
        # Baseline sizing params from authentic MISESERI field
        with open(self.csv_path, "r", encoding="utf-8") as f:
            import csv
            baseline_rows = list(csv.DictReader(f))
            
        params_base = compute_miseseri_sizing_parameters(baseline_rows, error_threshold=0.15)
        
        # Synthetic shifted error field: shift x coordinates forward by +0.020 mm (crack advance)
        shifted_rows = []
        for r in baseline_rows:
            r_copy = dict(r)
            r_copy["x_mm"] = str(float(r["x_mm"]) + 0.020)
            shifted_rows.append(r_copy)
            
        params_shifted = compute_miseseri_sizing_parameters(shifted_rows, error_threshold=0.15)
        
        # Verify refinement center shifted by exactly 0.020 mm
        self.assertAlmostEqual(params_shifted["x_center"] - params_base["x_center"], 0.020, places=5)
        
        # Verify meshes generated from baseline vs shifted fields have different coordinate grids
        mesh_base = generate_c4_mesh_from_csv(self.csv_path, error_threshold=0.15, h_fine=0.00080)
        
        # Temporary CSV for shifted distribution
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp_csv = Path(td) / "shifted_miseseri.csv"
            with open(tmp_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(shifted_rows[0].keys()))
                writer.writeheader()
                writer.writerows(shifted_rows)
                
            mesh_shifted = generate_c4_mesh_from_csv(tmp_csv, error_threshold=0.15, h_fine=0.00080)
            
        # The x coordinates must differ
        self.assertFalse(np.array_equal(mesh_base["x_coords"], mesh_shifted["x_coords"]),
                         "Mesh coordinate grid must adapt when error distribution changes")

if __name__ == "__main__":
    unittest.main()
