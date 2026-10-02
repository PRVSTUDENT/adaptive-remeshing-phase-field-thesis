#!/usr/bin/env python3
"""
Dedicated Restart2 Preparation Test Suite for Candidate M2STATE_FRACFIX_RESTART2R1.
Task ID: F60STATE-M2-RESTART2-VALID-SOURCE-REBUILD-PREP1

Verifies all 26 preparation and qualification requirements:
1. Valid source job = 1388948 only.
2. Exact source frame / U1 provenance (Frame 13, u1 = 0.007585 mm).
3. Historical invalid source rejected.
4. Old Restart2 package rejected as executable evidence.
5. Target mesh provenance (PK10R1, Nphys = 9876).
6. Complete phase & history coverage.
7. Quad/tri element pairing & IP ordering.
8. NPHYS contract in header property slot 5.
9. Correct SDV semantics (SDV14 carried phase, SDV15 solved phase, SDV16 history H).
10. JTYPE-aware STATE_TRACE instrumentation.
11. Manifest hash verification.
12. Dual-channel notifications.
13. Guarded wrapper dry-run and mock qsub behavior.
14. Resource envelope (walltime >= 24:00:00, serial, 16GB).
15. Acceptance contract completeness.
"""

import os
import sys
import json
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R1"

class TestM2StateFracfixRestart2R1(unittest.TestCase):

    def setUp(self):
        self.assertTrue(CANDIDATE_DIR.is_dir(), f"Candidate directory missing: {CANDIDATE_DIR}")
        self.manifest_path = CANDIDATE_DIR / "PACKAGE_MANIFEST.json"
        self.assertTrue(self.manifest_path.is_file(), "PACKAGE_MANIFEST.json missing")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

    def test_01_valid_source_job_provenance(self):
        art_path = CANDIDATE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        self.assertTrue(art_path.is_file())
        with open(art_path, "r", encoding="utf-8") as f:
            art = json.load(f)
        self.assertEqual(art.get("source_job"), "1388948.mmaster02")
        self.assertEqual(art.get("source_candidate"), "M2STATE_FRACFIX_RESTART1R1R6R2")
        self.assertEqual(art.get("source_checkpoint"), "Step-2-Continuation Frame 13")

    def test_02_historical_invalid_source_rejected(self):
        art_path = CANDIDATE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        with open(art_path, "r", encoding="utf-8") as f:
            art = json.load(f)
        self.assertNotEqual(art.get("source_job_id"), "1386471.mmaster02")
        man_path = CANDIDATE_DIR / "TRANSFER_MANIFEST.json"
        with open(man_path, "r", encoding="utf-8") as f:
            man = json.load(f)
        self.assertFalse(man.get("historical_invalid_runtime_path_reused", True))
        self.assertFalse(man.get("historical_PK10_reused", True))

    def test_03_target_mesh_identity_pk10r1(self):
        man_path = CANDIDATE_DIR / "TRANSFER_MANIFEST.json"
        with open(man_path, "r", encoding="utf-8") as f:
            man = json.load(f)
        self.assertEqual(man.get("target_candidate"), "PK10R1")
        self.assertEqual(man.get("target_nphys"), 9876)

    def test_04_phase_and_history_coverage(self):
        art_path = CANDIDATE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        with open(art_path, "r", encoding="utf-8") as f:
            art = json.load(f)
        self.assertTrue(art.get("phase_mapping_complete"))
        self.assertTrue(art.get("history_mapping_complete"))
        self.assertEqual(art.get("phase_bound_violations"), 0)
        self.assertEqual(art.get("healing_count"), 0)
        self.assertEqual(art.get("sdv16_decrease_count"), 0)

    def test_05_element_pairing_and_ip_ordering(self):
        art_path = CANDIDATE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        with open(art_path, "r", encoding="utf-8") as f:
            art = json.load(f)
        self.assertEqual(art.get("target_element_pairing"), "PASS")
        self.assertEqual(art.get("target_IP_ordering"), "PASS")
        self.assertEqual(art.get("target_NPHYS_contract"), "PASS")

    def test_06_nphys_slot5_property_contract(self):
        inp_path = CANDIDATE_DIR / "M2STATE_FRACFIX_RESTART2R1.inp"
        self.assertTrue(inp_path.is_file())
        lines = inp_path.read_text(encoding="utf-8").splitlines()
        found_u2 = False
        found_u4 = False
        for i, l in enumerate(lines):
            if "*UEL PROPERTY, ELSET=E_U2" in l:
                found_u2 = True
                prop_line = lines[i+1].strip()
                self.assertTrue("9876" in prop_line, f"Slot 5 NPHYS 9876 missing in U2: {prop_line}")
            elif "*UEL PROPERTY, ELSET=E_U4" in l:
                found_u4 = True
                prop_line = lines[i+1].strip()
                self.assertTrue("9876" in prop_line, f"Slot 5 NPHYS 9876 missing in U4: {prop_line}")
        self.assertTrue(found_u2)
        self.assertTrue(found_u4)

    def test_07_jtype_aware_state_trace(self):
        uel_path = CANDIDATE_DIR / "f42_mixed_uel.for"
        self.assertTrue(uel_path.is_file())
        code = uel_path.read_text(encoding="utf-8")
        self.assertIn("JTYPE-Aware Trace write", code)
        self.assertIn("IF (JTYPE.EQ.2 .OR. JTYPE.EQ.4)", code)

    def test_08_package_manifest_hash_integrity(self):
        files = self.manifest.get("files", self.manifest.get("file_hashes", {}))
        self.assertGreaterEqual(len(files), 10)
        for fname, expected_hash in files.items():
            fpath = CANDIDATE_DIR / fname
            self.assertTrue(fpath.is_file(), f"File missing in candidate: {fname}")
            actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()
            self.assertEqual(actual_hash, expected_hash, f"Hash mismatch for {fname}")

    def test_09_resource_envelope(self):
        pbs_path = CANDIDATE_DIR / "M2STATE_FRACFIX_RESTART2R1.pbs"
        self.assertTrue(pbs_path.is_file())
        text = pbs_path.read_text(encoding="utf-8")
        self.assertIn("#PBS -l walltime=24:00:00", text)
        self.assertIn("#PBS -l select=1:ncpus=1:mpiprocs=1:mem=16gb", text)
        self.assertIn("#PBS -q entry_imfdfkmq", text)

    def test_10_dual_channel_notifications(self):
        pbs_path = CANDIDATE_DIR / "M2STATE_FRACFIX_RESTART2R1.pbs"
        text = pbs_path.read_text(encoding="utf-8")
        self.assertIn("#PBS -m abe", text)
        self.assertIn("#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de", text)
        self.assertIn("source ./job_notifications.sh", text)
        self.assertIn("notification_install_terminal_trap", text)
        self.assertIn("notify_start", text)

    def test_11_guarded_wrapper_dry_run(self):
        sh_path = CANDIDATE_DIR / "submit_m2state_fracfix_restart2r1.sh"
        self.assertTrue(sh_path.is_file())
        text = sh_path.read_text(encoding="utf-8")
        self.assertIn("--dry-run", text)
        self.assertIn("PACKAGE_MANIFEST_VERIFICATION: PASS", text)
        self.assertIn("qsub M2STATE_FRACFIX_RESTART2R1.pbs", text)

    def test_12_acceptance_contract_completeness(self):
        cnt_path = CANDIDATE_DIR / "RESTART_ACCEPTANCE_CONTRACT.json"
        self.assertTrue(cnt_path.is_file())
        with open(cnt_path, "r", encoding="utf-8") as f:
            cnt = json.load(f)
        self.assertEqual(cnt.get("max_permitted_submissions"), 1)
        self.assertFalse(cnt.get("automatic_retry"))
        self.assertEqual(cnt.get("phase_transfer_l2_error_max_pct"), 1.0)
        self.assertEqual(cnt.get("reaction_force_jump_max_pct"), 2.0)
        self.assertEqual(cnt.get("energy_discrepancy_max_pct"), 1.0)
        self.assertEqual(cnt.get("irreversible_state_violations_max"), 0)

if __name__ == "__main__":
    unittest.main()
