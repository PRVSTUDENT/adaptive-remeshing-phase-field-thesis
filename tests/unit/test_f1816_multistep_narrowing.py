# -*- coding: utf-8 -*-
"""
tests/unit/test_f1816_multistep_narrowing.py
============================================
Task F1816: Multi-Step Refinement Narrowing Across Four Canonical Benchmarks.
Validates:
  1. Frozen production Fortran UEL bitwise integrity (CE8D5EDC...)
  2. Step 1 Minimum/Maximum sizing investigation findings and rejection verdict
  3. Step 2 Variant 2b (Reduced 2-State Envelope) failure mechanisms (Case 1 and Case 3 gate failures)
  4. Step 2 Variant 2a (Overlapping Native Rules) failure mechanisms (Case 3 gate failure, mesh ballooning)
  5. Case 5 exact regression control preservation across all variants
  6. Step 3 Predeclared Adoption Decision: F1812 baselines confirmed as true Pareto optimum
  7. Verification of all Step 2 donor ODBs, master receipt, and publication figures
  8. Verification of F1814 report artifact table and test suite count clarifications
  9. Governance invariants: 0 new PBS jobs, cumulative 35 preserved, MASTER_GOAL_STATUS = OPEN
"""
import os
import sys
import json
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")

BASE_NARROWING_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing")
STEP1_SUMMARY = os.path.join(BASE_NARROWING_DIR, "step1_minmax", "step1_minmax_summary.json")
STEP2_SUMMARY = os.path.join(BASE_NARROWING_DIR, "step2_envelope", "step2_envelope_summary.json")
RECEIPT_PATH = os.path.join(BASE_NARROWING_DIR, "PK_F1816_MULTISTEP_NARROWING_RECEIPT.json")

FIG_PNG = os.path.join(REPO_ROOT, "results", "figures", "fig_f1816_refinement_width_comparison.png")
FIG_PDF = os.path.join(REPO_ROOT, "results", "figures", "fig_f1816_refinement_width_comparison.pdf")

F1814_REPORT = os.path.join(REPO_ROOT, "docs", "validation", "F1814_SYNTHESIS_LABEL_CORRECTION_REPORT.md")
F1814_TEST = os.path.join(REPO_ROOT, "tests", "unit", "test_f1814_synthesis_label_correction.py")
F1816_REPORT = os.path.join(REPO_ROOT, "docs", "validation", "F1816_MULTISTEP_REFINEMENT_NARROWING_REPORT.md")

DONOR_DIR = os.path.join(BASE_NARROWING_DIR, "step2_envelope", "donors")

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

class TestF1816MultistepNarrowing(unittest.TestCase):

    def test_01_frozen_uel_integrity(self):
        self.assertTrue(os.path.exists(UEL_PATH), "UEL file must exist")
        self.assertEqual(sha256_file(UEL_PATH), FROZEN_UEL_SHA, "Production UEL must be bitwise frozen")

    def test_02_step1_minmax_sizing_rejection(self):
        self.assertTrue(os.path.exists(STEP1_SUMMARY), "Step 1 summary must exist")
        with open(STEP1_SUMMARY, "r") as f:
            d1 = json.load(f)
        self.assertEqual(d1["sizing_method"], "MINIMUM_MAXIMUM")
        total_el = sum(c["total_elements"] for c in d1["cases"].values())
        self.assertEqual(total_el, 258894, "Min/Max sizing must produce exactly 258,894 elements (+61.7%)")
        
        # Verify budget and coarsening failures
        self.assertGreater(d1["cases"]["case_1"]["total_elements"], 30000, "Case 1 must fail Gate 07 budget (>30k)")
        self.assertGreater(d1["cases"]["case_3"]["total_elements"], 80000, "Case 3 must fail Gate 07 budget (>80k)")
        self.assertGreater(d1["cases"]["case_5"]["total_elements"], 30000, "Case 5 must fail Gate 07 budget (>30k)")
        for cid, c in d1["cases"].items():
            self.assertLess(c["coarsening_ratio"], 2.0, "%s must fail Gate 06 coarsening (<2.0x)" % cid)

    def test_03_step2_variant_2b_failure_modes(self):
        self.assertTrue(os.path.exists(STEP2_SUMMARY), "Step 2 summary must exist")
        with open(STEP2_SUMMARY, "r") as f:
            d2 = json.load(f)
        s2b = d2["variant_2b_reduced"]
        
        # Case 1 full ligament resolution fails (< 95.0%)
        self.assertLess(s2b["case_1"]["scientific_gate"]["val"], 95.0, "Case 1 under Var 2b must fail < 95.0%")
        self.assertFalse(s2b["case_1"]["scientific_gate"]["pass"])
        
        # Case 2 mesh ballooning
        self.assertGreater(s2b["case_2"]["elements"], 80000, "Case 2 under Var 2b must double to >80,000 el")
        self.assertLess(s2b["case_2"]["coarsening_ratio"], 2.0, "Case 2 under Var 2b must fail coarsening (<2.0x)")
        
        # Case 3 secondary corridor resolution fails (< 90.0%)
        self.assertLess(s2b["case_3"]["scientific_gate"]["val"], 90.0, "Case 3 under Var 2b must fail < 90.0%")
        self.assertFalse(s2b["case_3"]["scientific_gate"]["pass"])

    def test_04_step2_variant_2a_failure_modes(self):
        with open(STEP2_SUMMARY, "r") as f:
            d2 = json.load(f)
        s2a = d2["variant_2a_overlapping"]
        
        # Case 3 secondary corridor resolution fails (< 90.0%)
        self.assertLess(s2a["case_3"]["scientific_gate"]["val"], 90.0, "Case 3 under Var 2a must fail < 90.0%")
        self.assertFalse(s2a["case_3"]["scientific_gate"]["pass"])
        
        # Mesh ballooning on Cases 1 and 2
        self.assertGreater(s2a["case_1"]["elements"], 35000, "Case 1 under Var 2a must balloon to >35,000 el")
        self.assertGreater(s2a["case_2"]["elements"], 80000, "Case 2 under Var 2a must balloon to >80,000 el")
        self.assertLess(s2a["case_2"]["coarsening_ratio"], 2.0, "Case 2 under Var 2a must fail coarsening")

    def test_05_case5_regression_control(self):
        with open(STEP2_SUMMARY, "r") as f:
            d2 = json.load(f)
        for var in ["variant_2b_reduced", "variant_2a_overlapping"]:
            c5 = d2[var]["case_5"]
            self.assertEqual(c5["elements"], 15466, "Case 5 control must preserve exactly 15,466 elements")
            self.assertGreaterEqual(c5["scientific_gate"]["val"], 90.0, "Case 5 must PASS inter-hole gate")
            self.assertTrue(c5["scientific_gate"]["pass"])
            self.assertGreaterEqual(c5["coarsening_ratio"], 2.0, "Case 5 must PASS Gate 06 coarsening")

    def test_06_step3_pareto_optimum_decision(self):
        self.assertTrue(os.path.exists(RECEIPT_PATH), "Master narrowing receipt must exist")
        with open(RECEIPT_PATH, "r") as f:
            rcpt = json.load(f)
        self.assertEqual(rcpt["step3_combine_and_validate_decision"]["adopted_framework_configuration"],
                         "F1812_BASELINES_ADOPTED_AS_PARETO_OPTIMUM")
        self.assertEqual(rcpt["step3_combine_and_validate_decision"]["total_canonical_elements"], 160144)

    def test_07_donor_odbs_existence(self):
        expected_donors = [
            "PK_CASE1_2STATE_ENVELOPE.odb",
            "PK_CASE2_2STATE_ENVELOPE.odb",
            "PK_CASE3_2STATE_ENVELOPE.odb",
            "PK_CASE1_MULTISTEP_RULES.odb",
            "PK_CASE2_MULTISTEP_RULES.odb",
            "PK_CASE3_MULTISTEP_RULES.odb"
        ]
        for dname in expected_donors:
            dp = os.path.join(DONOR_DIR, dname)
            self.assertTrue(os.path.exists(dp), "Donor ODB must exist: %s" % dname)
            self.assertGreater(os.path.getsize(dp), 1000000, "Donor ODB must be non-trivial")

    def test_08_publication_figures_existence(self):
        self.assertTrue(os.path.exists(FIG_PNG), "Figure PNG must exist")
        self.assertGreater(os.path.getsize(FIG_PNG), 500000, "Figure PNG must be high resolution")
        self.assertTrue(os.path.exists(FIG_PDF), "Figure PDF must exist")
        self.assertGreater(os.path.getsize(FIG_PDF), 30000, "Figure PDF must be valid vector graphics")

    def test_09_f1814_report_correction_verification(self):
        self.assertTrue(os.path.exists(F1814_REPORT), "F1814 report must exist")
        self.assertTrue(os.path.exists(F1814_TEST), "F1814 test file must exist")
        actual_test_sha = sha256_file(F1814_TEST)
        with open(F1814_REPORT, "r") as f:
            content = f.read()
        self.assertIn(actual_test_sha, content, "F1814 report must contain the exact actual test file hash")
        self.assertIn("11 test functions", content, "F1814 report must clarify the 11 test function count")
        self.assertIn("34/34", content, "F1814 report must document combined 34-test regression count")

    def test_10_governance_invariants(self):
        with open(RECEIPT_PATH, "r") as f:
            rcpt = json.load(f)
        self.assertEqual(rcpt["governing_objectives"]["cumulative_pbs_submissions"], 35)
        self.assertEqual(rcpt["governing_objectives"]["new_pbs_submissions"], 0)
        self.assertEqual(rcpt["governing_objectives"]["master_goal_status"], "OPEN")
        self.assertTrue(os.path.exists(F1816_REPORT), "F1816 report must exist")

if __name__ == "__main__":
    unittest.main()
