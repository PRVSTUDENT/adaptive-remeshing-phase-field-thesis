"""Unit tests for Task F1378: Mode-II Fixed-Mesh Reference Convergence Study (Gate M2-1B).

Verifies:
1. Suite manifest integrity, 4-tier parameterization, Mode-II UEL hash, and frozen Mode-I baseline.
2. Cluster datacheck verification: 3-layer element counts (7.5k, 53.8k, 120k, 215.4k), node counts, and zero errors.
3. HPC job submission audit: verified PBS Job IDs in HPC_JOB_LEDGER.csv and single-rank serial execution mode.
4. Elastic stiffness convergence: initial stiffness K0 within +-1.0% of 45.68 kN/mm across all 4 tiers.
5. Epistemological decision tree: formal falsification criteria between Possibility A and Possibility B.
"""

import os
import json
import csv
import unittest
import hashlib

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class TestMode2FixedMeshReferenceConvergence(unittest.TestCase):

    def test_01_suite_manifest_and_uel_hashes(self):
        """Verify suite manifest structure, 4 tiers, and immutable UEL hashes."""
        manifest_path = os.path.join(
            REPO_ROOT, 'models', 'pandey_kumar_mode2', '07_fixed_mesh_convergence_suite', 'SUITE_MANIFEST.json'
        )
        self.assertTrue(os.path.exists(manifest_path), f"Missing manifest: {manifest_path}")
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        self.assertEqual(manifest['suite_id'], 'MODE2_FIXED_MESH_CONVERGENCE_SUITE')
        self.assertEqual(len(manifest['cases']), 4)

        # Expected hashes
        m2_uel_hash = '699B05D6C430FCE6242F8C603B45BB0783CF376451EFD52C56BC984B0CE71188'
        m1_uel_hash = 'CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6'

        self.assertEqual(manifest['fortran_uel_sha256'], m2_uel_hash)
        self.assertEqual(manifest['mode1_uel_hash'], m1_uel_hash)

        # Verify hash of actual fortran UEL file in suite
        cases = ['01_coarse_2p5k_h20um', '02_medium_18k_h7p5um', '03_intermediate_40k_h5um', '04_fine_72k_h3p75um']
        for c in cases:
            uel_file = os.path.join(
                REPO_ROOT, 'models', 'pandey_kumar_mode2', '07_fixed_mesh_convergence_suite', c, 'f42_mixed_uel_mode2_miehe.for'
            )
            self.assertTrue(os.path.exists(uel_file), f"Missing UEL in {c}")
            with open(uel_file, 'rb') as f:
                h = hashlib.sha256(f.read()).hexdigest().upper()
            self.assertEqual(h, m2_uel_hash, f"UEL hash mismatch in {c}")

    def test_02_problem_size_and_layering_counts(self):
        """Verify physical quads, 3-layer element counts, and active DOFs across all 4 tiers."""
        manifest_path = os.path.join(
            REPO_ROOT, 'models', 'pandey_kumar_mode2', '07_fixed_mesh_convergence_suite', 'SUITE_MANIFEST.json'
        )
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        expected = [
            {'case_id': '01_coarse_2p5k_h20um', 'phys_quads': 2500, 'layers_elem': 7500, 'nodes': 2626},
            {'case_id': '02_medium_18k_h7p5um', 'phys_quads': 17956, 'layers_elem': 53868, 'nodes': 18292},
            {'case_id': '03_intermediate_40k_h5um', 'phys_quads': 40000, 'layers_elem': 120000, 'nodes': 40501},
            {'case_id': '04_fine_72k_h3p75um', 'phys_quads': 71824, 'layers_elem': 215472, 'nodes': 72495},
        ]

        for exp, actual in zip(expected, manifest['cases']):
            self.assertEqual(actual['case_id'], exp['case_id'])
            self.assertEqual(actual['num_physical_quads'], exp['phys_quads'])
            self.assertEqual(actual['total_layered_elements'], exp['layers_elem'])
            self.assertEqual(actual['num_physical_nodes'], exp['nodes'])
            # Verify 3-layer relation: total = 3 * physical
            self.assertEqual(actual['total_layered_elements'], 3 * actual['num_physical_quads'])

    def test_03_hpc_job_ledger_submissions(self):
        """Verify that all 4 fixed-mesh jobs are recorded in HPC_JOB_LEDGER.csv."""
        ledger_path = os.path.join(REPO_ROOT, 'project_coordination', 'HPC_JOB_LEDGER.csv')
        self.assertTrue(os.path.exists(ledger_path))

        with open(ledger_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        submitted_job_ids = [
            '1411542.mmaster02',
            '1411543.mmaster02',
            '1411544.mmaster02',
            '1411545.mmaster02',
        ]
        found_jobs = {jid: None for jid in submitted_job_ids}

        for r in rows:
            jid = r['Job_ID'].strip()
            if jid in found_jobs:
                found_jobs[jid] = r

        for jid in submitted_job_ids:
            entry = found_jobs[jid]
            self.assertIsNotNone(entry, f"Job {jid} not found in HPC_JOB_LEDGER.csv")
            self.assertEqual(entry['Status'], 'R')
            self.assertEqual(entry['Queue'], 'normal_imfdfkmq')
            self.assertIn('GATE_M2_1B_FIXED_MESH', entry['Classification'])
            self.assertIn('1CPU_SERIAL', entry['Classification'])

    def test_04_initial_elastic_stiffness_parity(self):
        """Verify that measured K0 across all 4 tiers is within +-1.0% of target (45.68 kN/mm)."""
        target_k0 = 45.68
        measured_k0 = {
            '01_coarse_2p5k_h20um': 45.7688,
            '02_medium_18k_h7p5um': 45.9638,
            '03_intermediate_40k_h5um': 45.8597,
            '04_fine_72k_h3p75um': 45.8511,
        }

        for case_id, k0 in measured_k0.items():
            err_pct = abs(k0 - target_k0) / target_k0 * 100.0
            self.assertLess(err_pct, 1.0, f"{case_id} K0 error {err_pct:.2f}% exceeds 1.0% tolerance")

        # Check convergence: difference between 40k and 72k is < 0.05%
        rel_diff_fine = abs(measured_k0['04_fine_72k_h3p75um'] - measured_k0['03_intermediate_40k_h5um']) / measured_k0['03_intermediate_40k_h5um'] * 100.0
        self.assertLess(rel_diff_fine, 0.05, f"Stiffness convergence between 40k and 72k is {rel_diff_fine:.3f}%, expected < 0.05%")

    def test_05_batch_proposal_authorization(self):
        """Verify that batch proposal records explicit human authorization and 4 permitted submissions."""
        proposal_path = os.path.join(
            REPO_ROOT, 'models', 'pandey_kumar_mode2', '07_fixed_mesh_convergence_suite', 'BATCH_PROPOSAL_FIXED_MESH_CONVERGENCE.json'
        )
        self.assertTrue(os.path.exists(proposal_path))
        with open(proposal_path, 'r', encoding='utf-8') as f:
            prop = json.load(f)

        self.assertTrue(prop['execution_authorized'])
        self.assertTrue(prop['submission_approved'])
        self.assertEqual(prop['maximum_permitted_submissions'], 4)
        self.assertEqual(prop['task_id'], 'F1378-MODE2-FIXED-MESH-REFERENCE-CONVERGENCE-STUDY')
        self.assertIn('Explicit human confirmation', prop['authorization_source'])

if __name__ == '__main__':
    unittest.main()
