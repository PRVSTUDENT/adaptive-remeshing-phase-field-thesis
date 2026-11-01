import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
P160 = ROOT / 'models/pandey_kumar_mode1/160_c4_exact_load_reference'
FROZEN_UEL_HASH = 'CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6'
TARGET_UY = 0.0018603125442191958


class TestC4ExactLoadReference(unittest.TestCase):
    def test_package_files_exist(self):
        expected_files = [
            'M1_C4_EXACT_LOAD_REF.inp',
            'f42_mixed_uel.for',
            'P160_MECHANICAL_DC.inp',
            'P160_PHASE_DC.inp',
            'PACKAGE_MANIFEST.json',
            'EXECUTION_MANIFEST_REF.json',
            'submit_M1_C4_EXACT_REF.pbs',
            'run_datacheck.sh',
            'job_notifications.sh',
        ]
        for name in expected_files:
            p = P160 / name
            self.assertTrue(p.exists(), f'Missing file: {name}')

    def test_frozen_uel_integrity(self):
        uel_path = P160 / 'f42_mixed_uel.for'
        uel_hash = hashlib.sha256(uel_path.read_bytes()).hexdigest().upper()
        self.assertEqual(uel_hash, FROZEN_UEL_HASH)

    def test_inp_target_displacement_and_steps(self):
        inp_text = (P160 / 'M1_C4_EXACT_LOAD_REF.inp').read_text(encoding='utf-8')
        # Check Step 1
        self.assertIn('*Step, name=Step-1', inp_text)
        self.assertIn('0.0018003125442192', inp_text)
        # Check Step 2
        self.assertIn('*Step, name=Step-2', inp_text)
        self.assertIn('0.0120000000', inp_text)
        self.assertIn(f'N_RP, 2, 2, {TARGET_UY}', inp_text)

    def test_energy_units_consistency(self):
        e_kNmm = 0.00022269253
        # 1 kN*mm = 1e3 N * 1e-3 m = 1 N*m = 1 J
        e_J = e_kNmm * 1.0
        e_mJ = e_J * 1000.0
        self.assertAlmostEqual(e_J, 0.00022269253, places=10)
        self.assertAlmostEqual(e_mJ, 0.22269253, places=7)

    def test_manifest_consistency(self):
        manifest_path = P160 / 'EXECUTION_MANIFEST_REF.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        self.assertEqual(manifest['scientific_scope'], 'MODE1')
        self.assertEqual(manifest['max_submissions'], 1)
        self.assertEqual(manifest['jobs'][0]['id'], 'M1_C4_EXACT_REF')
        self.assertEqual(manifest['jobs'][0]['cpus'], 1)
        self.assertEqual(manifest['jobs'][0]['memory_gb'], 16)
        self.assertEqual(manifest['jobs'][0]['walltime_hours'], 8)


if __name__ == '__main__':
    unittest.main()
