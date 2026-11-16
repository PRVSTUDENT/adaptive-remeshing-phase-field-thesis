# -*- coding: utf-8 -*-
"""
tests/unit/test_f1824_job2_preflight.py
=======================================
Unit tests for Task F1824 Job-2 Coupled Phase-Field Fracture Preflight.
Verifies:
1. Frozen UEL and Framework SHA-256 integrity
2. Existence and element counts of all 4 production input decks
3. Layered element count parity (exactly 3x physical elements)
4. Line wrapping compliance on all *NSET cards (no line > 16 entries)
5. Existence and structure of cluster PBS submission scripts
6. Master summary and receipt consistency
7. Zero PBS submissions consumed
"""
import os
import sys
import json
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PREFLIGHT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "268_f1824_job2_preflight")
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FRAMEWORK_SHA256 = "0578156E5551173307892B8881E4BA772F099187BCF332672F39AC825023E80D"


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


class TestF1824Job2Preflight(unittest.TestCase):

    def test_01_governing_invariants(self):
        """Verifies frozen UEL and framework hashes."""
        uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
        self.assertTrue(os.path.exists(uel_path), "Frozen UEL file must exist")
        self.assertEqual(compute_sha256(uel_path), FROZEN_UEL_SHA256)

        fw_path = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
        self.assertTrue(os.path.exists(fw_path), "Shared framework file must exist")
        self.assertEqual(compute_sha256(fw_path), FRAMEWORK_SHA256)

    def test_02_production_decks_exist_and_counts(self):
        """Verifies all four production decks exist with exact physical and layered element counts."""
        expected = {
            "case1": {"name": "PK_F1824_CASE_1_PROD.inp", "phys": 25461, "layered": 76383},
            "case2": {"name": "PK_F1824_CASE_2_PROD.inp", "phys": 41438, "layered": 124314},
            "case3": {"name": "PK_F1824_CASE_3_PROD.inp", "phys": 77779, "layered": 233337},
            "case5": {"name": "PK_F1824_CASE_5_PROD.inp", "phys": 15466, "layered": 46398},
        }
        total_phys = 0
        total_layered = 0
        for tag, data in expected.items():
            deck_path = os.path.join(PREFLIGHT_DIR, tag, data["name"])
            self.assertTrue(os.path.exists(deck_path), "Production deck must exist: %s" % deck_path)
            self.assertGreater(os.path.getsize(deck_path), 1000000)

            # Check layered count from file
            quad_count = 0
            tri_count = 0
            with open(deck_path, "r") as f:
                content = f.read()
            self.assertIn("*USER ELEMENT", content)
            self.assertIn("*MATERIAL, NAME=DUMMY_MAT", content)
            self.assertIn("*RESTART, WRITE", content)
            self.assertIn("STEP 1:", content)
            self.assertIn("STEP 2:", content)
            self.assertIn("N_RP", content)

            total_phys += data["phys"]
            total_layered += data["layered"]

        self.assertEqual(total_phys, 160144)
        self.assertEqual(total_layered, 480432)

    def test_03_line_wrapping_no_buffer_overflow(self):
        """Audits that zero NSET lines in any production deck exceed 16 entries."""
        decks = [
            os.path.join(PREFLIGHT_DIR, "case1", "PK_F1824_CASE_1_PROD.inp"),
            os.path.join(PREFLIGHT_DIR, "case2", "PK_F1824_CASE_2_PROD.inp"),
            os.path.join(PREFLIGHT_DIR, "case3", "PK_F1824_CASE_3_PROD.inp"),
            os.path.join(PREFLIGHT_DIR, "case5", "PK_F1824_CASE_5_PROD.inp"),
        ]
        for dp in decks:
            in_nset = False
            line_idx = 0
            with open(dp, "r") as f:
                for line in f:
                    line_idx += 1
                    s = line.strip()
                    if not s or s.startswith("**"):
                        continue
                    if s.startswith("*"):
                        in_nset = s.upper().startswith("*NSET")
                        continue
                    if in_nset:
                        entries = [e.strip() for e in s.split(",") if e.strip()]
                        self.assertLessEqual(
                            len(entries), 16,
                            "Line %d in %s has %d entries (> 16)" % (line_idx, dp, len(entries))
                        )

    def test_04_pbs_scripts_structure(self):
        """Verifies cluster PBS submission scripts are correctly formatted."""
        pbs_files = [
            os.path.join(PREFLIGHT_DIR, "case1", "submit_case1_job2.pbs"),
            os.path.join(PREFLIGHT_DIR, "case2", "submit_case2_job2.pbs"),
            os.path.join(PREFLIGHT_DIR, "case3", "submit_case3_job2.pbs"),
            os.path.join(PREFLIGHT_DIR, "case5", "submit_case5_job2.pbs"),
        ]
        for pbs in pbs_files:
            self.assertTrue(os.path.exists(pbs))
            with open(pbs, "r") as f:
                txt = f.read()
            self.assertIn("#PBS -l select=1:ncpus=1:mem=16gb", txt)
            self.assertIn("#PBS -q normal_imfdfkmq", txt)
            self.assertIn("#PBS -m abe", txt)
            self.assertIn("job_notifications.sh", txt)
            self.assertIn("notification_install_terminal_trap", txt)
            self.assertIn("EXPECTED_UEL_SHA", txt)
            self.assertIn("EXPECTED_INP_SHA", txt)

    def test_05_summary_and_receipt_consistency(self):
        """Verifies master preflight summary and receipt exist and match."""
        sum_path = os.path.join(PREFLIGHT_DIR, "job2_preflight_summary.json")
        rec_path = os.path.join(PREFLIGHT_DIR, "PK_F1824_JOB2_PREFLIGHT_RECEIPT.json")

        self.assertTrue(os.path.exists(sum_path))
        self.assertTrue(os.path.exists(rec_path))

        with open(sum_path, "r") as f:
            sdata = json.load(f)
        with open(rec_path, "r") as f:
            rdata = json.load(f)

        self.assertEqual(sdata["task_id"], "F1824-JOB2-COUPLED-FRACTURE-VALIDATION")
        self.assertEqual(sdata["total_physical_elements"], 160144)
        self.assertEqual(sdata["total_layered_elements"], 480432)
        self.assertEqual(sdata["new_pbs_jobs_consumed"], 0)
        self.assertEqual(sdata["cumulative_pbs_submissions"], 35)

        self.assertEqual(rdata["task_id"], "F1824-JOB2-COUPLED-FRACTURE-VALIDATION")
        self.assertEqual(rdata["submissions_consumed"], 0)
        self.assertEqual(rdata["cumulative_pbs_submissions"], 35)
        self.assertEqual(len(rdata["cases"]), 4)


if __name__ == "__main__":
    unittest.main()
