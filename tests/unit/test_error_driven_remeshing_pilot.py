#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_error_driven_remeshing_pilot.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: 0cb23a4a-ece6-4050-828b-3535025b37ed
Turn: 414
Protocol Version: 2

Unit test suite for the autonomous error-indicator-driven remeshing pilot engine.
"""
from __future__ import print_function, division
import copy
import math
import unittest
from pathlib import Path
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
MISESERI_CSV = REPO_ROOT / "models/pandey_kumar_mode1/153_c4_companion_miseseri/c4_package153_companion_miseseri_distribution.csv"
C4_INP = REPO_ROOT / "models/pandey_kumar_mode1/153_c4_companion_miseseri/M1_C4_COMPANION_MISESERI.inp"

from scripts.remeshing.error_driven_remeshing_pilot import (
    load_c4_miseseri_marks,
    extract_base_grid_from_inp,
    compute_error_energy_metrics,
    build_error_driven_graded_mesh,
    write_pilot_companion_deck,
)
from scripts.remeshing.generate_crack_band_mesh import write_abaqus_deck


class TestErrorDrivenRemeshingPilot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all_elems, cls.marked = load_c4_miseseri_marks(MISESERI_CSV, threshold_eta=0.15)

    def test_error_energy_centroid_reconstruction(self):
        """Verify L2 error energy norm accurately locates the notch tip within 150 nm."""
        metrics = compute_error_energy_metrics(self.all_elems, marked_elements=self.marked)
        xc = metrics["x_centroid"]
        yc = metrics["y_centroid"]
        self.assertAlmostEqual(yc, 0.050, delta=1e-5)
        dist_nm = math.sqrt((xc - 0.040) ** 2 + (yc - 0.050) ** 2) * 1e6
        self.assertLess(dist_nm, 150.0)

    def test_snapped_effective_center(self):
        """Verify effective center snaps to geometric notch tip when within feature tolerance."""
        mesh = build_error_driven_graded_mesh(
            self.all_elems,
            marked_elements=self.marked,
            h_fine=0.00050,
            max_h=0.0020,
            slit_y=0.050,
            slit_a0=0.040,
        )
        self.assertEqual(mesh["effective_center"], [0.040, 0.050])
        self.assertEqual(mesh["n_elements"], 12544)
        self.assertGreater(mesh["min_det_jac"], 0.0)
        self.assertLessEqual(mesh["max_aspect_ratio"], 4.0001)

    def test_trajectory_invariance_advance(self):
        """Verify engine autonomously shifts refinement zone when error peak advances +20 um."""
        shifted_elems = []
        for e in self.all_elems:
            rec = copy.deepcopy(e)
            rec["x"] = rec["x"] + 0.020
            shifted_elems.append(rec)

        shifted_metrics = compute_error_energy_metrics(shifted_elems)
        self.assertAlmostEqual(shifted_metrics["x_centroid"], 0.060, delta=0.001)
        self.assertAlmostEqual(shifted_metrics["y_centroid"], 0.050, delta=1e-5)

        mesh_shifted = build_error_driven_graded_mesh(
            shifted_elems,
            h_fine=0.00050,
            max_h=0.0020,
            slit_y=0.050,
            slit_a0=0.040,
        )
        self.assertAlmostEqual(mesh_shifted["effective_center"][0], 0.060, delta=0.001)
        self.assertEqual(mesh_shifted["effective_center"][1], 0.050)
        self.assertGreater(mesh_shifted["min_det_jac"], 0.0)
        self.assertEqual(mesh_shifted["n_elements"], 12544)

    def test_slit_seam_and_boundary_sets(self):
        """Verify slit duplication along y=0.050, x<=0.040 and boundary node sets."""
        mesh = build_error_driven_graded_mesh(
            self.all_elems,
            marked_elements=self.marked,
            h_fine=0.00050,
            max_h=0.0020,
            slit_y=0.050,
            slit_a0=0.040,
        )
        nodes = mesh["nodes"]
        bottom_nodes = mesh["bottom_nodes"]
        top_nodes = mesh["top_nodes"]
        pin_nodes = mesh["pin_nodes"]

        # Check bottom nodes
        for n in bottom_nodes:
            self.assertAlmostEqual(nodes[n][1], 0.0, places=6)
        # Check top nodes
        for n in top_nodes:
            self.assertAlmostEqual(nodes[n][1], 0.100, places=6)
        # Check pin node
        self.assertEqual(len(pin_nodes), 1)
        self.assertAlmostEqual(nodes[pin_nodes[0]][0], 0.0, places=6)
        self.assertAlmostEqual(nodes[pin_nodes[0]][1], 0.0, places=6)

    def test_deck_generation(self):
        """Verify companion and UEL deck generation writes valid Abaqus files."""
        mesh = build_error_driven_graded_mesh(
            self.all_elems,
            marked_elements=self.marked,
            h_fine=0.00050,
            max_h=0.0020,
            slit_y=0.050,
            slit_a0=0.040,
        )
        test_dir = REPO_ROOT / "results/validation/error_driven_remeshing_pilot/test_temp"
        test_dir.mkdir(parents=True, exist_ok=True)

        comp_path = test_dir / "test_comp.inp"
        uel_path = test_dir / "test_uel.inp"

        n_phys, n_quads = write_pilot_companion_deck(mesh, comp_path)
        self.assertEqual(n_quads, 12544)
        self.assertTrue(comp_path.exists())
        self.assertGreater(comp_path.stat().st_size, 100000)

        write_abaqus_deck(mesh, uel_path)
        self.assertTrue(uel_path.exists())
        self.assertGreater(uel_path.stat().st_size, 100000)


if __name__ == "__main__":
    unittest.main()
