#!/usr/bin/env python3
"""
Unit Test Suite for Mode-II Uniform Phase-Field Reference Contract
Task: F43MODEREF-PREP1
"""

import os
import sys
import json
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_BATCH_MANIFEST.json"
EXPECTED_UEL_SHA256 = "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class TestModeIIReferenceContract(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not MANIFEST_PATH.is_file():
            raise FileNotFoundError(f"Manifest not found: {MANIFEST_PATH}")
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
        cls.candidates = cls.manifest.get("candidates", {})

    def test_manifest_structure(self):
        self.assertEqual(self.manifest.get("protocol_version"), 1)
        self.assertEqual(self.manifest.get("task_id"), "F43MODEREF-PREP1")
        self.assertIn("material_constants", self.manifest)
        self.assertIn("loading_endpoint", self.manifest)

        mat = self.manifest["material_constants"]
        self.assertAlmostEqual(mat["l0_mm"], 0.015, places=6)
        self.assertAlmostEqual(mat["Gc_kN_per_mm"], 0.0027, places=6)
        self.assertAlmostEqual(mat["E_kN_per_mm2"], 210.0, places=4)
        self.assertAlmostEqual(mat["nu"], 0.3, places=4)
        self.assertAlmostEqual(mat["k_residual"], 1.0e-7, places=9)
        self.assertAlmostEqual(mat["thickness_mm"], 1.0, places=4)

        load = self.manifest["loading_endpoint"]
        self.assertAlmostEqual(load.get("target_final_u1_mm", load.get("final_u_target_mm")), 0.0100, places=6)
        self.assertEqual(load["step1_increments"], 500)
        self.assertEqual(load["step2_increments"], 2000)

    def test_expected_candidates_present(self):
        expected = ["M2REF_H0", "M2REF_H1", "M2REF_H2"]
        for c in expected:
            self.assertIn(c, self.candidates, f"Missing candidate {c}")

    def test_file_presence_and_hashes(self):
        for cname, cinfo in self.candidates.items():
            deck = ROOT / Path(cinfo["deck_path"].replace("\\", "/"))
            uel = ROOT / Path(cinfo["uel_path"].replace("\\", "/"))
            pbs = ROOT / Path(cinfo["pbs_path"].replace("\\", "/"))
            submit = ROOT / Path(cinfo["submit_wrapper"].replace("\\", "/"))

            self.assertTrue(deck.is_file(), f"Deck missing for {cname}")
            self.assertTrue(uel.is_file(), f"UEL missing for {cname}")
            self.assertTrue(pbs.is_file(), f"PBS script missing for {cname}")
            self.assertTrue(submit.is_file(), f"Submit wrapper missing for {cname}")

            self.assertEqual(sha256_file(deck), cinfo["deck_sha256"], f"Deck SHA mismatch for {cname}")
            self.assertEqual(sha256_file(uel), EXPECTED_UEL_SHA256, f"UEL SHA mismatch for {cname}")

    def test_element_and_layer_counts(self):
        expected_counts = {
            "M2REF_H0": (3930, 11790),
            "M2REF_H1": (12064, 36192),
            "M2REF_H2": (33852, 101556)
        }
        for cname, (n_phys, n_layer) in expected_counts.items():
            cinfo = self.candidates[cname]
            self.assertEqual(cinfo["physical_elements"], n_phys)
            self.assertEqual(cinfo["layered_elements"], n_layer)

    def test_monotonic_mesh_hierarchy(self):
        h0 = self.candidates["M2REF_H0"]
        h1 = self.candidates["M2REF_H1"]
        h2 = self.candidates["M2REF_H2"]

        # Element counts strictly increase
        self.assertLess(h0["physical_elements"], h1["physical_elements"])
        self.assertLess(h1["physical_elements"], h2["physical_elements"])

        # Minimum element sizes strictly decrease
        self.assertGreater(h0["h_area_min_mm"], h1["h_area_min_mm"])
        self.assertGreater(h1["h_area_min_mm"], h2["h_area_min_mm"])

        # Target h / l0 strictly decreases
        self.assertGreater(h0["h_over_l0_min"], h1["h_over_l0_min"])
        self.assertGreater(h1["h_over_l0_min"], h2["h_over_l0_min"])

    def test_deck_content_and_equations(self):
        for cname, cinfo in self.candidates.items():
            deck_path = ROOT / cinfo["deck_path"]
            text = deck_path.read_text(encoding="utf-8")

            # Check key keywords
            self.assertIn("*User Element, type=U1", text)
            self.assertIn("*User Element, type=U2", text)
            self.assertIn("*Element, type=CPE4", text)
            self.assertIn("*Equation", text)
            self.assertIn("*Amplitude, name=Amp-1", text)
            self.assertIn("*Amplitude, name=Amp-2", text)
            self.assertIn("*Step, name=Step-1", text)
            self.assertIn("*Step, name=Step-2", text)
            self.assertIn("RP, 1, 1, 1.0", text)
            self.assertIn("bottom_nodes, 1, 2", text)

    def test_cross_model_fairness_with_adaptive_candidates(self):
        # Verify material properties match Stage C adaptive rebuilt decks exactly
        mm_rebuilt = ROOT / "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/F43UEL_MM_REBUILT.inp"
        if mm_rebuilt.is_file():
            mm_text = mm_rebuilt.read_text(encoding="utf-8")
            # Same material and UEL constants
            self.assertIn("1.500000e-02", mm_text)
            self.assertIn("2.700000e-03", mm_text)
            self.assertIn("2.100000e+02", mm_text)
            self.assertIn("3.000000e-01", mm_text)
            self.assertIn("1.000000e-07", mm_text)
            self.assertIn("1.000000e-11", mm_text)



if __name__ == "__main__":
    unittest.main()
