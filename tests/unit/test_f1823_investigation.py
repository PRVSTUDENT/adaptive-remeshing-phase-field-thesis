# -*- coding: utf-8 -*-
"""
tests/unit/test_f1823_investigation.py
======================================
Comprehensive automated verification suite for Task F1823:
  1. Governing research invariants (Frozen UEL, Shared Framework, 0 new PBS jobs)
  2. Step 1: Framework kwargs comparison & bitwise mesh parity, Case 3 width bugfix, eta_R provenance
  3. Step 2: Bounded coarsening sweep (Cases 2 & 3 vs Controls, Gate 06 plateau)
  4. Step 3: Targeted donor investigation (Case 2 and Case 3 state ablation & causal responsibility)
  5. Multi-panel publication figure existence and non-emptiness.
"""
import os
import sys
import json
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

FROZEN_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

FRAMEWORK_PATH = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
EXPECTED_FRAMEWORK_SHA = "0578156E5551173307892B8881E4BA772F099187BCF332672F39AC825023E80D"

STEP1_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "267_f1823_investigation", "step1_comparison", "step1_framework_comparison_results.json")
STEP2_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "267_f1823_investigation", "step2_coarsening", "step2_coarsening_sweep_summary.json")
STEP3_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "267_f1823_investigation", "step3_donors", "step3_targeted_donors_summary.json")

FIG_PNG = os.path.join(REPO_ROOT, "results", "figures", "fig_f1823_coarsening_and_donor_investigation.png")
FIG_PDF = os.path.join(REPO_ROOT, "results", "figures", "fig_f1823_coarsening_and_donor_investigation.pdf")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

class TestF1823Investigation(unittest.TestCase):

    def test_01_governing_invariants(self):
        """Verify bitwise preservation of UEL and shared framework."""
        self.assertTrue(os.path.exists(FROZEN_UEL_PATH), "Frozen UEL file missing")
        uel_sha = compute_sha256(FROZEN_UEL_PATH)
        self.assertEqual(uel_sha, EXPECTED_UEL_SHA, "Frozen UEL hash altered!")

        self.assertTrue(os.path.exists(FRAMEWORK_PATH), "Shared framework file missing")
        fw_sha = compute_sha256(FRAMEWORK_PATH)
        self.assertEqual(fw_sha, EXPECTED_FRAMEWORK_SHA, "Shared framework hash altered!")

    def test_02_step1_framework_comparison_and_kwargs(self):
        """Verify Step 1: Old vs Enhanced framework produces bitwise-identical meshes."""
        self.assertTrue(os.path.exists(STEP1_JSON), "Step 1 comparison JSON missing")
        with open(STEP1_JSON, "r") as f:
            data = json.load(f)

        # 3.0% error target comparison
        old_3 = data["old_fw_ue_3pct"]
        enh_3 = data["enhanced_fw_ue_3pct"]
        self.assertEqual(old_3["total_elements"], 62611)
        self.assertEqual(enh_3["total_elements"], 62611)
        self.assertEqual(old_3["body_sha256"], enh_3["body_sha256"])
        self.assertEqual(old_3["body_sha256"], "D36603D89FF9D953395A176D8C327F097FE69E92469FA73F6CC3193426B6E768")

        # 4.5% error target comparison
        old_45 = data["old_fw_ue_45pct"]
        enh_45 = data["enhanced_fw_ue_45pct"]
        self.assertEqual(old_45["total_elements"], 25461)
        self.assertEqual(enh_45["total_elements"], 25461)
        self.assertEqual(old_45["body_sha256"], enh_45["body_sha256"])
        self.assertEqual(old_45["body_sha256"], "50CB4E3C826D66C7BDAB7FEBEADF5254CDEE33B709B214E9714CD776B3CE379E")

    def test_03_step1_case3_width_bug_fix(self):
        """Verify that run_f1816_step2_master.py line 76 bounds the second segment to plate width (65mm)."""
        f1816_master = os.path.join(REPO_ROOT, "scripts", "remeshing", "run_f1816_step2_master.py")
        self.assertTrue(os.path.exists(f1816_master))
        with open(f1816_master, "r") as f:
            content = f.read()
        self.assertIn("((50.0, 60.0), (65.0, 60.0))", content, "Case 3 width bug not fixed in run_f1816_step2_master.py!")
        self.assertNotIn("((70.0, 60.0), (120.0, 60.0))", content, "Old out-of-bounds segment still present!")

    def test_04_step2_coarsening_sweep_controls(self):
        """Verify Step 2 regression controls for Case 1 and Case 5."""
        self.assertTrue(os.path.exists(STEP2_JSON), "Step 2 summary JSON missing")
        with open(STEP2_JSON, "r") as f:
            data = json.load(f)

        c1_ctrl = data["c1_ctrl_eta45_h020"]
        self.assertEqual(c1_ctrl["total_elements"], 25461)
        self.assertTrue(c1_ctrl["gate_06_pass"])
        self.assertTrue(c1_ctrl["scientific_gate_pass"])
        self.assertEqual(c1_ctrl["body_sha256"], "50CB4E3C826D66C7BDAB7FEBEADF5254CDEE33B709B214E9714CD776B3CE379E")

        c5_ctrl = data["c5_ctrl_eta568_h030"]
        self.assertEqual(c5_ctrl["total_elements"], 15466)
        self.assertTrue(c5_ctrl["gate_06_pass"])
        self.assertTrue(c5_ctrl["scientific_gate_pass"])
        self.assertEqual(c5_ctrl["body_sha256"], "78009AAEE4FE732C0FA56F2DE5487C1717E82E245B4CAF32C3B9CE19AB2B4065")

    def test_05_step2_coarsening_sweep_plateau(self):
        """Verify that Gate 06 coarsening ratio fails to reach 2.0x on Case 2 and Case 3 sweeps."""
        with open(STEP2_JSON, "r") as f:
            data = json.load(f)

        # Case 2 coarsening ratio plateaus at ~1.56x (< 2.0x)
        for var in ["c2_base_eta40_h020", "c2_var1_eta40_h030", "c2_var2_eta40_h040", "c2_var3_eta50_h030"]:
            self.assertFalse(data[var]["gate_06_pass"], "Gate 06 should fail for %s" % var)
            self.assertLess(data[var]["coarsening_ratio"], 2.0)

        # Case 3 coarsening ratio reaches at most 1.85x (< 2.0x)
        for var in ["c3_base_eta30_h200", "c3_var1_eta30_h300", "c3_var2_eta30_h400", "c3_var3_eta35_h300"]:
            self.assertFalse(data[var]["gate_06_pass"], "Gate 06 should fail for %s" % var)
            self.assertLess(data[var]["coarsening_ratio"], 2.0)

    def test_06_step3_case2_targeted_donor_ablation(self):
        """Verify Step 3 Case 2 targeted donor ablation findings."""
        self.assertTrue(os.path.exists(STEP3_JSON), "Step 3 summary JSON missing")
        with open(STEP3_JSON, "r") as f:
            data = json.load(f)["investigations"]

        c2_base = data["c2_base_4states"]
        c2_omit_s1 = data["c2_omit_state1"]
        c2_omit_s3 = data["c2_omit_state3"]
        c2_omit_s4 = data["c2_omit_state4"]

        # Base passes outer distal (100.0%) and notch (92.11%)
        self.assertEqual(c2_base["scientific_gate"]["val"], 100.0)
        self.assertGreater(c2_base["scientific_gate"]["extra_val"], 90.0)

        # Omit State 1 causes primary notch corridor to collapse (26.18% vs 92.11%)
        self.assertEqual(c2_omit_s1["scientific_gate"]["val"], 100.0)
        self.assertLess(c2_omit_s1["scientific_gate"]["extra_val"], 30.0, "Notch corridor should collapse when State 1 is omitted!")

        # Omit State 3 preserves outer distal (100.0%) and notch (93.36%)
        self.assertEqual(c2_omit_s3["scientific_gate"]["val"], 100.0)
        self.assertGreater(c2_omit_s3["scientific_gate"]["extra_val"], 90.0)

        # Omit State 4 causes outer distal to collapse below threshold (83.97% < 100.0%)
        self.assertFalse(c2_omit_s4["scientific_gate"]["pass"])
        self.assertLess(c2_omit_s4["scientific_gate"]["val"], 90.0, "Outer distal should collapse when State 4 is omitted!")

    def test_07_step3_case3_targeted_donor_ablation(self):
        """Verify Step 3 Case 3 targeted donor ablation findings."""
        with open(STEP3_JSON, "r") as f:
            data = json.load(f)["investigations"]

        c3_base = data["c3_base_3states"]
        c3_omit_s1 = data["c3_omit_state1"]
        c3_omit_s2 = data["c3_omit_state2"]
        c3_omit_s3 = data["c3_omit_state3"]

        # Omit State 1 causes primary notch corridor to collapse to ~3.57%
        self.assertLess(c3_omit_s1["scientific_gate"]["extra_val"], 10.0, "Primary corridor must collapse when State 1 is omitted!")

        # Omit State 2 preserves primary corridor (85.70%) and saves only 4.6% of elements (72,853 vs 76,371)
        self.assertGreater(c3_omit_s2["scientific_gate"]["extra_val"], 80.0)
        self.assertGreater(c3_omit_s2["elements"], 70000)

        # Omit State 3 causes secondary corridor within-3*l0 elements to drop to 0 (0.00%)
        self.assertEqual(c3_omit_s3["width_metrics"]["n_3l0"], 0, "Secondary corridor must have 0 elements within 3*l0 when State 3 is omitted!")
        self.assertEqual(c3_omit_s3["width_metrics"]["f_3l0"], 0.0)
        self.assertLess(c3_omit_s3["scientific_gate"]["val"], 60.0)

    def test_08_visual_artifacts_exist(self):
        """Verify multi-panel publication figures exist and are non-empty."""
        self.assertTrue(os.path.exists(FIG_PNG), "PNG figure missing")
        self.assertGreater(os.path.getsize(FIG_PNG), 50000, "PNG figure unexpectedly small")
        self.assertTrue(os.path.exists(FIG_PDF), "PDF figure missing")
        self.assertGreater(os.path.getsize(FIG_PDF), 10000, "PDF figure unexpectedly small")

if __name__ == "__main__":
    unittest.main()
