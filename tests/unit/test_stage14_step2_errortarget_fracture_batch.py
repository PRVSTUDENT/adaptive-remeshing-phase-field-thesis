#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit test suite for Mode-I Stage-14 Step-2 errorTarget fracture batch (ET2, ET3, ET5).
"""

from __future__ import print_function
import os
import sys
import json
import hashlib
import unittest

class TestStage14Step2FractureBatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_dir = r"D:\Master thesis\Adaptive remeshing"
        cls.pkg34_dir = os.path.join(cls.repo_dir, "models", "pandey_kumar_mode1", "34_stage14_step2_adaptive_candidate_et2_6k")
        cls.pkg35_dir = os.path.join(cls.repo_dir, "models", "pandey_kumar_mode1", "35_stage14_step2_adaptive_candidate_et3_5k")
        cls.pkg36_dir = os.path.join(cls.repo_dir, "models", "pandey_kumar_mode1", "36_stage14_step2_adaptive_candidate_et5_4k")
        cls.evaluator_path = os.path.join(cls.repo_dir, "scripts", "evaluation", "evaluate_stage14_step2_errortarget_fracture_batch.py")

    def test_package_directories_and_manifests_exist(self):
        for pkg_dir in [self.pkg34_dir, self.pkg35_dir, self.pkg36_dir]:
            self.assertTrue(os.path.isdir(pkg_dir), "Missing package directory: %s" % pkg_dir)
            manifest_path = os.path.join(pkg_dir, "PACKAGE_MANIFEST.json")
            self.assertTrue(os.path.isfile(manifest_path), "Missing manifest: %s" % manifest_path)
            with open(manifest_path, 'r') as f:
                data = json.load(f)
            self.assertIn("job_name", data)
            self.assertIn("base_elements", data)
            self.assertIn("deck_sha256", data)
            self.assertIn("fortran_sha256", data)

    def test_element_and_node_counts(self):
        expected = {
            'ET2': {'pkg': self.pkg34_dir, 'deck': "PK_MODE1_STAGE14_STEP2_ET2_6K_FRACTURE.inp", 'base_el': 6112, 'total_el': 18336, 'nodes': 6181},
            'ET3': {'pkg': self.pkg35_dir, 'deck': "PK_MODE1_STAGE14_STEP2_ET3_5K_FRACTURE.inp", 'base_el': 5189, 'total_el': 15567, 'nodes': 5262},
            'ET5': {'pkg': self.pkg36_dir, 'deck': "PK_MODE1_STAGE14_STEP2_ET5_4K_FRACTURE.inp", 'base_el': 4692, 'total_el': 14076, 'nodes': 4759}
        }
        for name, spec in expected.items():
            deck_path = os.path.join(spec['pkg'], spec['deck'])
            self.assertTrue(os.path.isfile(deck_path), "Missing deck: %s" % deck_path)
            manifest_path = os.path.join(spec['pkg'], "PACKAGE_MANIFEST.json")
            with open(manifest_path, 'r') as f:
                data = json.load(f)
            self.assertEqual(data['base_elements'], spec['base_el'])
            self.assertEqual(data['total_3layer_elements'], spec['total_el'])
            self.assertEqual(data['nodes'], spec['nodes'])

    def test_property_abi_order(self):
        for pkg_dir, base_el in [(self.pkg34_dir, 6112), (self.pkg35_dir, 5189), (self.pkg36_dir, 4692)]:
            manifest_path = os.path.join(pkg_dir, "PACKAGE_MANIFEST.json")
            with open(manifest_path, 'r') as f:
                data = json.load(f)
            deck_path = os.path.join(pkg_dir, data['deck_file'])
            with open(deck_path, 'r') as f:
                content = f.read()
            expected_uel_prop = "0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.0" % base_el
            expected_umat_prop = "210.0, 0.3, %d." % base_el
            self.assertIn(expected_uel_prop, content, "Missing correct UEL property card in %s" % deck_path)
            self.assertIn(expected_umat_prop, content, "Missing correct UMAT property card in %s" % deck_path)

    def test_pbs_and_scratch_compliance(self):
        for pkg_dir in [self.pkg34_dir, self.pkg35_dir, self.pkg36_dir]:
            pbs_path = os.path.join(pkg_dir, "submit_solver.pbs")
            self.assertTrue(os.path.isfile(pbs_path), "Missing PBS script: %s" % pbs_path)
            with open(pbs_path, 'r') as f:
                pbs_content = f.read()
            self.assertIn("#PBS -l nodes=1:ppn=1", pbs_content)
            self.assertIn("#PBS -l mem=16gb", pbs_content)
            self.assertIn("#PBS -m abe", pbs_content)
            self.assertIn("pr21vyci@mailserver.tu-freiberg.de", pbs_content)
            self.assertIn("job_notifications.sh", pbs_content)
            self.assertIn("notification_install_terminal_trap", pbs_content)
            self.assertIn("notify_start", pbs_content)
            self.assertIn("exit 88", pbs_content)
            self.assertIn("abaqus/2023", pbs_content)

    def test_evaluator_script_exists_and_runs(self):
        self.assertTrue(os.path.isfile(self.evaluator_path), "Missing evaluator script: %s" % self.evaluator_path)
        with open(self.evaluator_path, 'r') as f:
            code = f.read()
        self.assertIn("REFERENCE_VALUES", code)
        self.assertIn("137.945520", code)
        self.assertIn("0.757778", code)
        self.assertIn("compute_canonical_k0", code)
        self.assertIn("compute_trapezoidal_work", code)

if __name__ == '__main__':
    unittest.main()
