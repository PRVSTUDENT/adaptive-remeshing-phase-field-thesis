#!/usr/bin/env python3
"""
test_package157_r6_candidate.py

Unit tests verifying the isolated Package 157 R6 candidate restart continuation.
Validates:
1. Exact restart identity against authentic Checkpoint 01 (7265 nodes, 28224 GPs, uy=0.00186031 mm)
2. Target load (+5 nm to uy=0.00186531 mm) and iteration budget (max_outer=130)
3. Analytical contraction projection (N_add ~ 7.30 iters, projected total ~108)
4. Frozen production UEL integrity (CE8D5EDC...)
5. Driver startup validation without solver execution
6. Execution cost and scheduler limits compliance (<=8.0 h walltime, <=16 GB RAM, 1 CPU)
7. Operation definition prepared for independent registration review
"""

import os
import sys
import json
import math
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.state_transfer.driver_package157_r6 import AdaptiveContinuationR6, START, TARGETS

FROZEN_UEL_SHA256 = 'ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6'


class TestPackage157R6Candidate(unittest.TestCase):
    def setUp(self):
        self.pkg_dir = ROOT / 'models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r6'
        self.r5_dir = ROOT / 'models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r5'
        self.chkpt_path = self.r5_dir / 'converged_checkpoint_01.json'
        self.op_def_path = ROOT / 'project_coordination/operation_definitions/execute_mode1_package157_c1_2_r6_adaptive_continuation.json'

    def test_checkpoint01_restart_identity(self):
        self.assertTrue(self.chkpt_path.exists(), "Authentic Checkpoint 01 must exist")
        chkpt = json.loads(self.chkpt_path.read_text())
        self.assertEqual(chkpt['target_uy_mm'], START)
        self.assertTrue(chkpt['coupled_convergence'])
        self.assertEqual(len(chkpt['displacement']), 7265)
        self.assertEqual(len(chkpt['damage']), 7265)
        self.assertEqual(len(chkpt['history']), 28224)

        # Check copied checkpoint in R6 package
        r6_chkpt = self.pkg_dir / 'initial_checkpoint_01.json'
        self.assertTrue(r6_chkpt.exists())
        self.assertEqual(
            hashlib.sha256(r6_chkpt.read_bytes()).hexdigest(),
            hashlib.sha256(self.chkpt_path.read_bytes()).hexdigest()
        )

    def test_r6_target_and_budget(self):
        self.assertEqual(START, 0.0018603125442191958)
        self.assertEqual(TARGETS, [0.0018653125442191958])
        delta_uy = TARGETS[0] - START
        self.assertAlmostEqual(delta_uy, 5.0e-6, places=12)

        pkg_manifest = json.loads((self.pkg_dir / 'PACKAGE_MANIFEST.json').read_text())
        self.assertEqual(pkg_manifest['max_outer'], 130)
        self.assertEqual(pkg_manifest['baseline_uy_mm'], START)
        self.assertEqual(pkg_manifest['targets_mm'], TARGETS)

    def test_analytical_contraction_projection(self):
        delta_h_100 = 2.0427325377880834e-06
        tol_h = 1.0e-06
        rho_h = 0.9066707073342885

        n_add = math.log(tol_h / delta_h_100) / math.log(rho_h)
        self.assertAlmostEqual(n_add, 7.2904, places=3)
        projected_outer = 100 + math.ceil(n_add)
        self.assertEqual(projected_outer, 108)

        # Proposed budget is 130, providing a 22-iteration margin
        margin = 130 - projected_outer
        self.assertEqual(margin, 22)
        self.assertGreaterEqual(margin, 20)

    def test_frozen_uel_integrity(self):
        uel_path = self.pkg_dir / 'f42_mixed_uel.for'
        self.assertTrue(uel_path.exists())
        uel_sha = hashlib.sha256(uel_path.read_bytes()).hexdigest()
        self.assertEqual(uel_sha.lower(), FROZEN_UEL_SHA256.lower())

    def test_driver_startup_load(self):
        extractor = ROOT / 'scripts/validation/extract_package148_iteration.py'
        controller = AdaptiveContinuationR6(self.pkg_dir, self.pkg_dir / 'unused', extractor, max_outer=130)
        controller.load()
        self.assertEqual(len(controller.d0), 7265)
        self.assertEqual(len(controller.h0), 28224)
        self.assertEqual(controller.max_outer, 130)

    def test_execution_cost_feasibility(self):
        per_iter_sec = 82.0
        budget_iters = 130
        walltime_hours = (budget_iters * per_iter_sec) / 3600.0
        self.assertLess(walltime_hours, 8.0)
        self.assertAlmostEqual(walltime_hours, 2.961, places=2)

        exec_manifest = json.loads((self.pkg_dir / 'EXECUTION_MANIFEST.json').read_text())
        job = exec_manifest['jobs'][0]
        self.assertEqual(job['cpus'], 1)
        self.assertLessEqual(job['memory_gb'], 16)
        self.assertLessEqual(job['walltime_hours'], 8)
        self.assertEqual(job['execution'], 'single-rank serial')

    def test_operation_definition_prepared(self):
        self.assertTrue(self.op_def_path.exists())
        op_def = json.loads(self.op_def_path.read_text())
        self.assertEqual(op_def['operation_id'], 'execute_mode1_package157_c1_2_r6_adaptive_continuation')
        self.assertEqual(op_def['registration_status'], 'PREPARED_FOR_INDEPENDENT_REGISTRATION_REVIEW')
        self.assertEqual(op_def['physical_acceptance'], 'UNVERIFIED')


if __name__ == '__main__':
    unittest.main()
