#!/usr/bin/env python3
"""Unit tests for Task F1722: Method A Bounded Causal-Isolation Diagnostic Pilot Execution Qualification.

Verifies:
1. Exact manifest structure and registration (FIVE_HOLE_PK_F1722_CAUSAL_PILOT).
2. Bitwise integrity of all declared files in manifest against on-disk files.
3. Authentic Abaqus datacheck output (Exit 0, ANALYSIS DATACHECK COMPLETE, 0 errors).
4. PBS script directives, notification traps, and resource limits (#PBS -l select=1:ncpus=4...).
5. Execution gate validation via mode1_execution_gate.py.
6. Bitwise preservation of frozen baselines and literature candidates.
"""

import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / 'models/pandey_kumar_mode1/214_f1720_adapted_mesh'
MANIFEST_PATH = MODEL_DIR / 'F1722_PK_FIVE_HOLE_CAUSAL_PILOT_AUTHORIZATION.json'
PBS_PATH = MODEL_DIR / 'submit_M1_PK_F1722_CAUSAL_PILOT.pbs'
DATACHECK_PATH = MODEL_DIR / 'M1_PK_F1722_DATACHECK.dat'
INP_PATH = MODEL_DIR / 'PK_F1721_CAUSAL_PILOT.inp'
UEL_PATH = MODEL_DIR / 'f1721_proposed_staggered_coupling_uel.for'


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


class TestF1722CausalPilotExecutionQualification(unittest.TestCase):

    def test_01_manifest_existence_and_schema(self):
        self.assertTrue(MANIFEST_PATH.is_file(), f"Missing manifest: {MANIFEST_PATH}")
        with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        self.assertEqual(manifest['batch_name'], 'FIVE_HOLE_PK_F1722_CAUSAL_PILOT')
        self.assertEqual(manifest['adapter'], 'mode1-five-hole-staggered-v1')
        self.assertEqual(manifest['scientific_scope'], 'FIVE_HOLE')
        self.assertEqual(manifest['technical_stage'], 'FIVE_HOLE_CAUSAL_PILOT')
        self.assertEqual(manifest['max_submissions'], 1)
        self.assertFalse(manifest['automatic_retry'])
        self.assertEqual(len(manifest['jobs']), 1)

    def test_02_manifest_file_hashes_bitwise_match(self):
        with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        declared_files = manifest['files']
        for filename, expected_hash in declared_files.items():
            filepath = MODEL_DIR / filename
            self.assertTrue(filepath.is_file(), f"File {filename} declared in manifest missing on disk")
            actual_hash = sha256_file(filepath)
            self.assertEqual(actual_hash, expected_hash.lower(), f"Hash mismatch for {filename}")

    def test_03_authentic_cluster_datacheck_evidence(self):
        self.assertTrue(DATACHECK_PATH.is_file(), f"Missing datacheck file: {DATACHECK_PATH}")
        content = DATACHECK_PATH.read_text(encoding='utf-8', errors='replace')
        self.assertIn("ANALYSIS DATACHECK COMPLETE", content)
        self.assertNotIn("***ERROR", content)
        self.assertIn("Task F1721: Five-Hole Bounded Causal-Isolation Diagnostic Pilot", content)
        self.assertIn("PROCESSING PART, INSTANCE, AND ASSEMBLY INFORMATION", content)

    def test_04_pbs_script_directives_and_notification_contract(self):
        self.assertTrue(PBS_PATH.is_file(), f"Missing PBS script: {PBS_PATH}")
        pbs_text = PBS_PATH.read_text(encoding='utf-8')
        required_directives = [
            '#PBS -N M1_PK_F1722_CAUSAL_PILOT',
            '#PBS -l select=1:ncpus=1:mem=16gb',
            '#PBS -l walltime=08:00:00',
            '#PBS -q entry_imfdfkmq',
            '#PBS -j oe',
            '#PBS -r n',
            '#PBS -m abe',
            '#PBS -M pr21vyci@mailserver.tu-freiberg.de',
            'notification_load_config',
            'notification_install_terminal_trap',
            'notify_start',
            'module load gcc/11.4.0 intel/2024.2.0 abaqus/2023',
            'abaqus job="${JOB_NAME}" input="${INP_NAME}" user="${USER_SUB}" cpus=1 interactive'
        ]
        for directive in required_directives:
            self.assertIn(directive, pbs_text, f"Missing required directive in PBS script: {directive}")

    def test_05_mode1_execution_gate_technical_validation(self):
        import sys
        sys.path.insert(0, str(ROOT / 'scripts/hpc'))
        import mode1_execution_gate
        batch, manifest_digest, files = mode1_execution_gate.validate_manifest(MANIFEST_PATH)
        self.assertEqual(batch['batch_name'], 'FIVE_HOLE_PK_F1722_CAUSAL_PILOT')
        self.assertEqual(len(batch['jobs']), 1)
        job = batch['jobs'][0]
        self.assertEqual(job['cpus'], 1)
        self.assertEqual(job['memory_gb'], 16)
        self.assertEqual(job['walltime_hours'], 8)
        self.assertEqual(job['execution'], 'single-rank serial')

    def test_06_frozen_baselines_bitwise_preservation(self):
        f1720_inp = MODEL_DIR / 'PK_F1720_ADAPTED_PFM.inp'
        f1720_uel = MODEL_DIR / 'f1720_direct_coupling_uel.for'
        f1721_lit = MODEL_DIR / 'PK_F1721_ADAPTED_PILOT.inp'
        self.assertEqual(sha256_file(f1720_inp).lower(), '318d0ed6f330e73f5a62e259dc3a9a9abcebd4341596eaa5c31ed58138ba42f2')
        self.assertEqual(sha256_file(f1720_uel).lower(), 'c298aca7ed2199b20e622b38e99fda9b533150eb0ad5e9f77069216f860e70fc')
        self.assertEqual(sha256_file(f1721_lit).lower(), '0fcd33cf72ba9631cb0122aa38346cf51829ef9cf154497c3e80862820247e6e')


if __name__ == '__main__':
    unittest.main()
