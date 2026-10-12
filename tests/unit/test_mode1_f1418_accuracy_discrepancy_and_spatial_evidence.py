#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_mode1_f1418_accuracy_discrepancy_and_spatial_evidence.py
Unit tests verifying the scientific resolution of the Method B accuracy discrepancy,
the spatial damage localization evidence, and the tri-model synthesis under Task F1418.
"""

import os
import json
import csv
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

NATIVE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "38_method_b_native_final_14k")
EVAL_JSON = os.path.join(NATIVE_DIR, "M1_MB_NATIVE_14K_TERMINAL_EVALUATION.json")
MATCHED_CSV = os.path.join(NATIVE_DIR, "M1_MB_NATIVE_14K_matched_states_summary.csv")
FU_CSV = os.path.join(NATIVE_DIR, "M1_MB_NATIVE_14K_fu.csv")
LIGAMENT_CSV = os.path.join(NATIVE_DIR, "M1_MB_NATIVE_14K_ligament_profiles.csv")
UEL_FILE = os.path.join(NATIVE_DIR, "f42_mixed_uel.for")

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


class TestMode1F1418AccuracyDiscrepancyAndSpatialEvidence(unittest.TestCase):

    def test_01_uel_fortran_hash_preserved(self):
        """Verify UEL user subroutine source hash is strictly preserved."""
        self.assertTrue(os.path.exists(UEL_FILE), "f42_mixed_uel.for must exist")
        with open(UEL_FILE, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        self.assertEqual(h, FROZEN_UEL_HASH, "Frozen UEL Fortran source hash must match exactly")

    def test_02_evidence_files_exist_and_non_empty(self):
        """Verify all harvested spatial and terminal evidence files exist and are populated."""
        for p in [EVAL_JSON, MATCHED_CSV, FU_CSV, LIGAMENT_CSV]:
            self.assertTrue(os.path.exists(p), "Evidence file must exist: %s" % p)
            self.assertGreater(os.path.getsize(p), 1000, "Evidence file must not be empty: %s" % p)

    def test_03_terminal_metrics_and_accuracy(self):
        """Verify terminal evaluation metrics for Method B Native."""
        with open(EVAL_JSON, "r") as f:
            data = json.load(f)
        
        tm = data["terminal_metrics"]
        self.assertAlmostEqual(tm["F_max_kN"], 0.743021, places=5)
        self.assertAlmostEqual(tm["u_peak_mm"], 0.005727, places=5)
        self.assertAlmostEqual(tm["delta_F_max_pct"], -1.9474, places=2)
        
        # Initial stiffness
        self.assertAlmostEqual(tm["K0_measured_kN_per_mm"], 137.8919, places=2)
        self.assertLess(abs(tm["delta_K0_pct"]), 0.05, "Initial stiffness error must be < 0.05%")
        self.assertGreater(tm["K0_R2"], 0.99999, "Stiffness linear fit R2 must be > 0.99999")
        
        # Energies
        self.assertAlmostEqual(tm["w_ext_final_mJ"], 3.331934, places=4)
        self.assertAlmostEqual(tm["e_frac_final_mJ"], 3.031673, places=4)
        self.assertAlmostEqual(tm["e_elas_final_mJ"], 0.041312, places=4)
        
        # Dissipation ratio
        e_tot = tm["e_model_final_mJ"]
        w_ext = tm["w_ext_final_mJ"]
        ratio = (e_tot / w_ext) * 100.0
        self.assertGreater(ratio, 92.0, "Total recovered energy must be > 92% of external work")

    def test_04_scientific_discrepancy_root_cause_audit(self):
        """Verify documented root causes for the peak force and work discrepancies."""
        with open(EVAL_JSON, "r") as f:
            data = json.load(f)
        
        ntd = data["near_tip_discretization"]
        # Tip element size is ~1.91 um (h/l0 ~ 0.25)
        self.assertAlmostEqual(ntd["mean_tip_element_size_um"], 1.91, places=2)
        self.assertAlmostEqual(ntd["tip_h_over_l0"], 0.255, places=2)
        
        # Far ligament element size is ~19.66 um (h/l0 ~ 2.62)
        self.assertAlmostEqual(ntd["far_ligament_max_element_size_um"], 19.66, places=2)
        self.assertAlmostEqual(ntd["far_ligament_h_over_l0"], 2.62, places=2)
        
        # Scientific resolution text must be present
        res = data["scientific_discrepancy_resolution"]
        self.assertIn("root_cause_1_crack_tip_resolution", res)
        self.assertIn("root_cause_2_pre_analysis_state_window", res)
        self.assertIn("root_cause_3_energy_and_work_accumulation", res)

    def test_05_spatial_damage_progression(self):
        """Verify spatial damage localization and crack progression across matched states."""
        with open(EVAL_JSON, "r") as f:
            data = json.load(f)
        bundle = data["matched_displacement_bundle"]
        
        # Pre-peak state u = 0.0050 mm
        b_005 = bundle["0.005"]
        self.assertAlmostEqual(b_005["crack_length_a_mm"], 0.0, places=4)
        self.assertLess(b_005["d_max"], 0.35, "Pre-peak damage must be < 0.35")
        
        # Peak load state u = 0.005727 mm
        b_peak = bundle["0.005727"]
        self.assertAlmostEqual(b_peak["crack_length_a_mm"], 0.0, places=4)
        self.assertGreater(b_peak["d_max"], 0.60, "Peak damage must be > 0.60")
        self.assertLess(b_peak["d_max"], 0.90, "Peak damage must be < 0.90")
        
        # Post-peak crack propagation
        b_006 = bundle["0.006"]
        self.assertGreater(b_006["crack_length_a_mm"], 0.10, "Crack must initiate post-peak")
        self.assertGreater(b_006["d_max"], 1.0, "Crack must reach d ~ 1.0")
        
        b_007 = bundle["0.007"]
        self.assertGreater(b_007["crack_length_a_mm"], b_006["crack_length_a_mm"], "Crack must advance monotonically")
        
        # Terminal state u = 0.0100 mm
        b_term = bundle["0.01"]
        self.assertGreater(b_term["crack_length_a_mm"], 0.48, "Terminal crack length must traverse ligament (~0.49 mm)")
        
        # Damage bandwidth regularization
        self.assertAlmostEqual(b_term["damage_bandwidth_w05_over_l0"], 1.97, places=1)


if __name__ == "__main__":
    unittest.main()
