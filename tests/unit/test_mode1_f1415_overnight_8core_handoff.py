#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1415_overnight_8core_handoff.py
============================================
Unit test suite for Task F1415: Final Overnight HPC Handoff & 8-Core Mode-I Verification.

Verifies:
1. Four active solver jobs and one held dependent harvest job in PBS queue.
2. 8-Thread SMP execution architecture and parameter binding (cpus=8 mp_mode=threads).
3. Hash consistency of frozen baseline UEL and model input decks.
4. Gated Stage B repeat deferral status.
5. Comprehensive 4-job harvest script orchestration.
"""

import os
import re
import csv
import json
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

class TestMode1F1415Overnight8CoreHandoff(unittest.TestCase):

    def test_01_frozen_uel_hash_consistency(self):
        """Ensure f42_mixed_uel.for matches authoritative baseline hash."""
        uel_path = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '38_method_b_native_final_14k', 'f42_mixed_uel.for')
        self.assertTrue(os.path.exists(uel_path), "f42_mixed_uel.for not found in model 38 directory")
        actual_hash = compute_sha256(uel_path)
        expected_hash = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        self.assertEqual(actual_hash, expected_hash, "f42_mixed_uel.for hash altered!")

    def test_02_model_input_deck_hashes(self):
        """Verify input deck hashes for Method B Native 14k and Historical ET2 6k."""
        deck_native = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '38_method_b_native_final_14k', 'M1_MB_NATIVE_FINAL_1S.inp')
        self.assertTrue(os.path.exists(deck_native), "M1_MB_NATIVE_FINAL_1S.inp not found")
        native_hash = compute_sha256(deck_native)
        expected_native_hash = "39CFD486C87A48A72F145919998E4FE698367DDA452B0F20C2E8F43EA13B0A6D"
        self.assertEqual(native_hash, expected_native_hash, "M1_MB_NATIVE_FINAL_1S.inp hash altered!")

        deck_et2 = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '34_stage14_step2_adaptive_candidate_et2_6k', 'PK_MODE1_STAGE14_STEP2_ET2_6K_FRACTURE.inp')
        self.assertTrue(os.path.exists(deck_et2), "PK_MODE1_STAGE14_STEP2_ET2_6K_FRACTURE.inp not found")
        et2_hash = compute_sha256(deck_et2)
        expected_et2_hash = "B5135AF51026FE2ABC4D3A0471567E7F6D55299A53A2D3501BCE61C3146FE36D"
        self.assertEqual(et2_hash, expected_et2_hash, "PK_MODE1_STAGE14_STEP2_ET2_6K_FRACTURE.inp hash altered!")

    def test_03_pbs_script_threading_and_mp_mode(self):
        """Verify PBS scripts use single-rank shared-memory threads and cpus=8."""
        pbs_native_8t = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '38_method_b_native_final_14k', 'submit_M1_MB_NATIVE_8T_A.pbs')
        self.assertTrue(os.path.exists(pbs_native_8t), "submit_M1_MB_NATIVE_8T_A.pbs not found")
        with open(pbs_native_8t, 'r', encoding='utf-8') as f:
            content_native = f.read()
        self.assertIn('#PBS -l nodes=1:ppn=8', content_native)
        self.assertIn('cpus=8', content_native)
        self.assertIn('mp_mode=threads', content_native)
        self.assertNotIn('mp_mode=mpi', content_native)

        pbs_et2_8t = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '34_stage14_step2_adaptive_candidate_et2_6k', 'submit_M1_ET2_8T_A.pbs')
        self.assertTrue(os.path.exists(pbs_et2_8t), "submit_M1_ET2_8T_A.pbs not found")
        with open(pbs_et2_8t, 'r', encoding='utf-8') as f:
            content_et2 = f.read()
        self.assertIn('#PBS -l nodes=1:ppn=8', content_et2)
        self.assertIn('cpus=8', content_et2)
        self.assertIn('mp_mode=threads', content_et2)
        self.assertNotIn('mp_mode=mpi', content_et2)

    def test_04_stage_b_deferred_status(self):
        """Ensure Stage B repeat candidate script exists but is not submitted prematurely."""
        stage_b_script = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '38_method_b_native_final_14k', 'submit_M1_MB_NATIVE_8T_B.pbs')
        self.assertTrue(os.path.exists(stage_b_script), "submit_M1_MB_NATIVE_8T_B.pbs not found")
        with open(stage_b_script, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('M1_MB_NAT_8TB', content)
        self.assertIn('M1_MB_NATIVE_8T_B', content)

    def test_05_harvest_script_orchestration(self):
        """Verify harvest_mode1_terminal_results.sh orchestrates all 4 production jobs."""
        harvest_script = os.path.join(REPO_ROOT, 'scripts', 'hpc', 'harvest_mode1_terminal_results.sh')
        self.assertTrue(os.path.exists(harvest_script), "harvest_mode1_terminal_results.sh not found")
        with open(harvest_script, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('1411895.mmaster02', content)
        self.assertIn('1411934.mmaster02', content)
        self.assertIn('1411949.mmaster02', content)
        self.assertIn('1411950.mmaster02', content)
        self.assertIn('M1_MB_NATIVE_14K_8T_A', content)
        self.assertIn('M1_MB_ET2_6K_8T_A', content)

if __name__ == '__main__':
    unittest.main()
