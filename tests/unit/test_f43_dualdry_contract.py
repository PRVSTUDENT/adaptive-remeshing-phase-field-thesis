#!/usr/bin/env python3
"""
Unit and Contract Tests for Task F43DUALDRY-PREP1:
Dual-Candidate Mixed-UEL Dry-Test Preparation & Contract Qualification
"""

import os
import sys
import json
import unittest
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.validation.validate_f43_dualdry_contract import (
    audit_dualdry_preparation,
    FROZEN_MM_REBUILT_SHA,
    FROZEN_PK5_REBUILT_SHA,
    FROZEN_UEL_SOURCE_SHA,
    MM_DECK_PATH,
    PK5_DECK_PATH,
    UEL_SOURCE_PATH,
    DRY_MM_DIR,
    DRY_PK5_DIR,
    REPORT_PATH
)


class TestF43DualDryContract(unittest.TestCase):
    """Deterministic offline qualification tests for F43 dual dry-test packages."""

    def test_01_frozen_hashes(self):
        """Verify rebuilt decks and UEL subroutine hashes match frozen baseline."""
        self.assertEqual(hashlib.sha256(MM_DECK_PATH.read_bytes()).hexdigest(), FROZEN_MM_REBUILT_SHA)
        self.assertEqual(hashlib.sha256(PK5_DECK_PATH.read_bytes()).hexdigest(), FROZEN_PK5_REBUILT_SHA)
        self.assertEqual(hashlib.sha256(UEL_SOURCE_PATH.read_bytes()).hexdigest(), FROZEN_UEL_SOURCE_SHA)

    def test_02_all_four_uel_branches_present_mm(self):
        """Verify MM deck exercises U1, U2, U3, U4 and CPE4, CPE3."""
        text = MM_DECK_PATH.read_text(encoding="utf-8")
        self.assertIn("*Element, type=U1", text)
        self.assertIn("*Element, type=U2", text)
        self.assertIn("*Element, type=U3", text)
        self.assertIn("*Element, type=U4", text)
        self.assertIn("*Element, type=CPE4", text)
        self.assertIn("*Element, type=CPE3", text)

        # Count occurrences
        u1_count = len(re.findall(r"^\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+", text[text.find("*Element, type=U1"):text.find("*Element, type=U3")], re.M))
        u3_count = len(re.findall(r"^\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+", text[text.find("*Element, type=U3"):text.find("*Element, type=U2")], re.M))
        self.assertEqual(u1_count, 2137)
        self.assertEqual(u3_count, 69)

    def test_03_all_four_uel_branches_present_pk5(self):
        """Verify PK5 deck exercises U1, U2, U3, U4 and CPE4, CPE3."""
        text = PK5_DECK_PATH.read_text(encoding="utf-8")
        self.assertIn("*Element, type=U1", text)
        self.assertIn("*Element, type=U2", text)
        self.assertIn("*Element, type=U3", text)
        self.assertIn("*Element, type=U4", text)
        self.assertIn("*Element, type=CPE4", text)
        self.assertIn("*Element, type=CPE3", text)

        u1_count = len(re.findall(r"^\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+", text[text.find("*Element, type=U1"):text.find("*Element, type=U3")], re.M))
        u3_count = len(re.findall(r"^\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+", text[text.find("*Element, type=U3"):text.find("*Element, type=U2")], re.M))
        self.assertEqual(u1_count, 4766)
        self.assertEqual(u3_count, 128)

    def test_04_isolated_package_directories(self):
        """Verify candidate dry-test packages are isolated and complete."""
        self.assertTrue((DRY_MM_DIR / "F43UEL_MM_REBUILT.inp").is_file())
        self.assertTrue((DRY_MM_DIR / "f43_mixed_uel.for").is_file())
        self.assertTrue((DRY_MM_DIR / "F43DRY_MM.pbs").is_file())
        self.assertTrue((DRY_MM_DIR / "submit_f43dry_mm.sh").is_file())
        self.assertTrue((DRY_MM_DIR / "MANIFEST.json").is_file())

        self.assertTrue((DRY_PK5_DIR / "F43UEL_PK5_REBUILT.inp").is_file())
        self.assertTrue((DRY_PK5_DIR / "f43_mixed_uel.for").is_file())
        self.assertTrue((DRY_PK5_DIR / "F43DRY_PK5.pbs").is_file())
        self.assertTrue((DRY_PK5_DIR / "submit_f43dry_pk5.sh").is_file())
        self.assertTrue((DRY_PK5_DIR / "MANIFEST.json").is_file())

    def test_05_pbs_resource_contract(self):
        """Verify PBS resources: entry_imfdfkmq, 1 CPU, 8 GB, 00:30:00."""
        for pbs_file in [DRY_MM_DIR / "F43DRY_MM.pbs", DRY_PK5_DIR / "F43DRY_PK5.pbs"]:
            content = pbs_file.read_text(encoding="utf-8")
            self.assertIn("#PBS -q entry_imfdfkmq", content)
            self.assertIn("#PBS -l select=1:ncpus=1:mpiprocs=1:mem=8gb", content)
            self.assertIn("#PBS -l walltime=00:30:00", content)
            self.assertIn("module load gcc/11.4.0 intel/2024.2.0 abaqus/2023", content)

    def test_06_guarded_submission_contract(self):
        """Verify submitters check authorization flags and enforce guarded execution."""
        sub_mm = (DRY_MM_DIR / "submit_f43dry_mm.sh").read_text(encoding="utf-8")
        sub_pk5 = (DRY_PK5_DIR / "submit_f43dry_pk5.sh").read_text(encoding="utf-8")

        self.assertIn("F43DRY_MM_AUTHORIZED", sub_mm)
        self.assertIn("qsub -v F43DRY_MM_WRAPPER_AUTHORIZED=1 F43DRY_MM.pbs", sub_mm)

        self.assertIn("F43DRY_PK5_AUTHORIZED", sub_pk5)
        self.assertIn("qsub -v F43DRY_PK5_WRAPPER_AUTHORIZED=1 F43DRY_PK5.pbs", sub_pk5)

    def test_07_full_dualdry_contract_audit_pass(self):
        """Verify audit_dualdry_preparation passes all checks."""
        rep = audit_dualdry_preparation()
        self.assertTrue(rep["all_passed"], f"Audit failed: {rep['checks']}")
        self.assertFalse(rep["authority_boundary"]["execution_authorized"])
        self.assertEqual(rep["authority_boundary"]["maximum_jobs_now"], 0)


if __name__ == "__main__":
    unittest.main()
