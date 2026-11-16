# -*- coding: utf-8 -*-
"""
tests/unit/test_f1821_genuine_minmax.py
=======================================
Unit test suite for Task F1821:
Validates genuine MINIMUM_MAXIMUM execution, Abaqus .rpy execution journals,
F1820 evidentiary correction and withdrawal, and F1821 synthesis artifacts.
"""
import os
import sys
import json
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_265 = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "265_f1821_genuine_minmax")
OUT_264 = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "264_f1820_minmax_sizing")
FRAMEWORK_PATH = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
F1820_REPORT = os.path.join(REPO_ROOT, "docs", "validation", "F1820_MINIMUM_MAXIMUM_SIZING_EVALUATION_REPORT.md")


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def compute_body_sha256(inp_path):
    h = hashlib.sha256()
    with open(inp_path, "r") as f:
        for line in f:
            if line.startswith("**"):
                continue
            h.update(line.strip().encode("utf-8"))
            h.update(b"\n")
    return h.hexdigest().upper()


class TestF1821GenuineMinMaxExecution(unittest.TestCase):

    def test_01_frozen_uel_integrity(self):
        """Verify bitwise invariant production UEL SHA-256."""
        self.assertTrue(os.path.exists(UEL_PATH))
        uel_sha = compute_sha256(UEL_PATH)
        self.assertEqual(uel_sha, "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6")

    def test_02_framework_enhancement_integrity(self):
        """Verify enhanced framework SHA-256 (0578156E...)."""
        self.assertTrue(os.path.exists(FRAMEWORK_PATH))
        fw_sha = compute_sha256(FRAMEWORK_PATH)
        self.assertEqual(fw_sha, "0578156E5551173307892B8881E4BA772F099187BCF332672F39AC825023E80D")

    def test_03_f1821_output_directory_structure(self):
        """Verify fresh 265 directory contains all 4 meshes and receipts."""
        self.assertTrue(os.path.isdir(OUT_265))
        cases = ["case_1", "case_2", "case_3", "case_5"]
        for cid in cases:
            inp = os.path.join(OUT_265, "PK_F1821_MINMAX_%s_ADAPT_PHYS.inp" % cid.upper())
            receipt = os.path.join(OUT_265, "f1821_receipt_%s.json" % cid)
            self.assertTrue(os.path.exists(inp), "Missing mesh for %s" % cid)
            self.assertTrue(os.path.exists(receipt), "Missing receipt for %s" % cid)
            self.assertGreater(os.path.getsize(inp), 1000000)

    def test_04_authentic_rpy_journals_committed(self):
        """Verify all 4 authentic Abaqus .rpy execution journals are present and valid."""
        cases = ["case_1", "case_2", "case_3", "case_5"]
        for cid in cases:
            rpy_path = os.path.join(OUT_265, "%s_abaqus.rpy" % cid)
            self.assertTrue(os.path.exists(rpy_path), "Missing .rpy journal for %s" % cid)
            self.assertGreater(os.path.getsize(rpy_path), 500)
            with open(rpy_path, "r") as f:
                content = f.read()
            self.assertIn("execfile", content)
            self.assertIn("run_f1821_genuine_minmax_single.py", content)
            self.assertIn("MINIMUM_MAXIMUM", content)
            self.assertIn("mesh_bias = 7", content)

    def test_05_summary_and_receipt_data(self):
        """Verify minmax_f1821_summary.json and PK_F1821_GENUINE_MINMAX_RECEIPT.json."""
        summary_path = os.path.join(OUT_265, "minmax_f1821_summary.json")
        receipt_path = os.path.join(OUT_265, "PK_F1821_GENUINE_MINMAX_RECEIPT.json")
        self.assertTrue(os.path.exists(summary_path))
        self.assertTrue(os.path.exists(receipt_path))

        with open(summary_path, "r") as f:
            summary = json.load(f)

        self.assertEqual(summary["task_id"], "F1821-GENUINE-MINIMUM-MAXIMUM-EXECUTION-AND-F1820-CORRECTION")
        self.assertEqual(summary["sizing_method"], "MINIMUM_MAXIMUM")
        self.assertEqual(summary["parameters"]["mesh_bias"], 7)
        self.assertEqual(summary["totals"]["total_elements"], 258894)
        self.assertEqual(summary["totals"]["total_quads"], 252390)
        self.assertEqual(summary["totals"]["total_tris"], 6504)
        self.assertAlmostEqual(summary["totals"]["quad_fraction_pct"], 97.4877745333805, places=3)

    def test_06_f1820_report_corrections(self):
        """Verify F1820 report discloses body SHA matching, withdrawal, and exact script hashes."""
        self.assertTrue(os.path.exists(F1820_REPORT))
        with open(F1820_REPORT, "r") as f:
            content = f.read()

        self.assertIn("F1816 Step 1", content)
        self.assertIn("WITHDRAWN", content)
        self.assertIn("A43051AEE15063E2889389267D07CE3A7A1D5F2024BAF6FBE5983A70D4EF2096", content)
        self.assertIn("38F4B0AB6FFCE0FC788561972F751C006DA9ABC221FD51949E9F918538C191A3", content)
        self.assertIn("EF88AFC8B47171AB6ADBAE3F09D305B3A6684F19D4AE1C5DC87E614C47C056BF", content)

    def test_07_publication_figures_exist(self):
        """Verify F1821 publication figures PNG and PDF exist and are non-empty."""
        png_path = os.path.join(REPO_ROOT, "results", "figures", "fig_f1821_genuine_minmax_comparison.png")
        pdf_path = os.path.join(REPO_ROOT, "results", "figures", "fig_f1821_genuine_minmax_comparison.pdf")
        self.assertTrue(os.path.exists(png_path))
        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(png_path), 50000)
        self.assertGreater(os.path.getsize(pdf_path), 10000)


if __name__ == "__main__":
    unittest.main()
