#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_mode1_f1419_method_b_completion_and_supervisor_briefing.py
Unit tests verifying the formal scientific completion of Method B,
the supervisor briefing package, reproduction commands, mirror synchronization,
and Method C readiness under Task F1419.
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
COMMANDS_TXT = os.path.join(NATIVE_DIR, "commands.txt")
MANIFEST_JSON = os.path.join(NATIVE_DIR, "PACKAGE_MANIFEST.json")
DECK_INP = os.path.join(NATIVE_DIR, "M1_MB_NATIVE_FINAL_1S.inp")
UEL_FILE = os.path.join(NATIVE_DIR, "f42_mixed_uel.for")

BRIEFING_MD = os.path.join(REPO_ROOT, "docs", "supervisor_reports", "22-10-2026", "MODE1_METHOD_B_FINAL_SUPERVISOR_BRIEFING_AND_GATE6B_EVALUATION.md")
DECISION_MD = os.path.join(REPO_ROOT, "docs", "decisions", "SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md")

THESIS_CH4 = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "chapter04_current_status.tex")
MIRROR_CH4 = os.path.join(REPO_ROOT, "docs", "MA_AdaptiveRemeshing_Report_2026_main", "chapter04_current_status.tex")
HPC_LEDGER = os.path.join(REPO_ROOT, "project_coordination", "HPC_JOB_LEDGER.csv")

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FROZEN_DECK_HASH = "39CFD486C87A48A72F145919998E4FE698367DDA452B0F20C2E8F43EA13B0A6D"


class TestMode1F1419MethodBCompletionAndSupervisorBriefing(unittest.TestCase):

    def test_01_frozen_hashes_preserved(self):
        """Verify UEL user subroutine and Method B input deck hashes are strictly preserved."""
        self.assertTrue(os.path.exists(UEL_FILE), "f42_mixed_uel.for must exist")
        with open(UEL_FILE, "rb") as f:
            h_uel = hashlib.sha256(f.read()).hexdigest().upper()
        self.assertEqual(h_uel, FROZEN_UEL_HASH, "Frozen UEL Fortran source hash must match exactly")

        self.assertTrue(os.path.exists(DECK_INP), "M1_MB_NATIVE_FINAL_1S.inp must exist")
        with open(DECK_INP, "rb") as f:
            h_deck = hashlib.sha256(f.read()).hexdigest().upper()
        self.assertEqual(h_deck, FROZEN_DECK_HASH, "Frozen deck hash must match exactly")

    def test_02_reproduction_package_complete(self):
        """Verify reproduction package files exist and have valid structure."""
        for p in [COMMANDS_TXT, MANIFEST_JSON, EVAL_JSON, MATCHED_CSV, FU_CSV, LIGAMENT_CSV]:
            self.assertTrue(os.path.exists(p), "Reproduction package file must exist: %s" % p)
            self.assertGreater(os.path.getsize(p), 100, "File must not be empty: %s" % p)

        # Check commands.txt contains step-by-step instructions
        with open(COMMANDS_TXT, "r") as f:
            content = f.read()
        self.assertIn("M1_MB_NATIVE_FINAL_1S", content)
        self.assertIn("f42_mixed_uel.for", content)
        self.assertIn("14,677", content)
        self.assertIn("cpus=8", content)
        self.assertIn("mp_mode=threads", content)
        self.assertIn("extract_native_14k_spatial_damage.py", content)

    def test_03_supervisor_briefing_deliverable(self):
        """Verify supervisor briefing document for 22-Oct-2026 exists and contains core sections."""
        self.assertTrue(os.path.exists(BRIEFING_MD), "Supervisor briefing must exist: %s" % BRIEFING_MD)
        with open(BRIEFING_MD, "r") as f:
            text = f.read()
        self.assertIn("METHOD_B_COMPLETE_SCIENTIFICALLY_EVALUATED", text)
        self.assertIn("137.891881", text)
        self.assertIn("0.743021", text)
        self.assertIn("0.757778", text)
        self.assertIn("1.91", text)
        self.assertIn("19.66", text)
        self.assertIn("2.140", text)
        self.assertIn("792BE67D", text)

    def test_04_thesis_mirror_synchronization(self):
        """Verify bitwise source synchronization between authoritative thesis and docs mirror."""
        self.assertTrue(os.path.exists(THESIS_CH4), "Authoritative chapter04 must exist")
        self.assertTrue(os.path.exists(MIRROR_CH4), "Mirror chapter04 must exist")
        with open(THESIS_CH4, "rb") as f1, open(MIRROR_CH4, "rb") as f2:
            h1 = hashlib.sha256(f1.read()).hexdigest()
            h2 = hashlib.sha256(f2.read()).hexdigest()
        self.assertEqual(h1, h2, "Chapter04 must be 100% bitwise identical across both mirrors")

    def test_05_hpc_job_ledger_terminal_states(self):
        """Verify all 5 Method B PBS jobs are registered as terminal in HPC_JOB_LEDGER.csv."""
        self.assertTrue(os.path.exists(HPC_LEDGER), "HPC_JOB_LEDGER.csv must exist")
        expected_jobs = {
            "1411895.mmaster02": ("F", 0),
            "1411934.mmaster02": ("F", 0),
            "1411949.mmaster02": ("F", 0),
            "1411950.mmaster02": ("F", 0),
            "1411947.mmaster02": ("F", -29)
        }
        found_jobs = {}
        with open(HPC_LEDGER, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 8:
                    job_id = row[0].strip()
                    if job_id in expected_jobs:
                        state = row[6].strip()
                        exit_code = int(row[7].strip())
                        found_jobs[job_id] = (state, exit_code)

        self.assertEqual(len(found_jobs), len(expected_jobs), "All 5 Method B jobs must be in HPC ledger")
        for jid, (exp_state, exp_exit) in expected_jobs.items():
            self.assertEqual(found_jobs[jid], (exp_state, exp_exit), "Job %s state/exit must match" % jid)

    def test_06_method_c_architecture_readiness(self):
        """Verify authoritative Fortran UEL source exposes required state-transfer infrastructure."""
        with open(UEL_FILE, "r") as f:
            src = f.read()
        self.assertIn("COMMON /CB_STATE_TRANS/", src, "Shared COMMON state block must be present")
        self.assertIn("UEXTERNALDB", src, "UEXTERNALDB entrypoint must be present")
        self.assertIn("STATEV(1)", src, "STATEV history variable access must be present")


if __name__ == "__main__":
    unittest.main()
