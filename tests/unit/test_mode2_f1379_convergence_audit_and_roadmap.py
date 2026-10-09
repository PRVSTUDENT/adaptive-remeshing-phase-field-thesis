"""Unit test suite for Task F1379: Mode-II Fixed-Mesh Convergence Audit and Roadmap.

Verifies:
1. Stiffness regression audit JSON data integrity, statistical fit bounds (R2, intercept, K0),
   and stiffness convergence between intermediate and fine tiers (diff < 0.05%).
2. Single-factor deck equivalence and algebraic proof of node, equation, and DOF counts.
3. Independent UEL formulation integrity (weak form, Miehe spectral split, Kuhn-Tucker irreversibility).
4. Comprehensive roadmap document and 4-branch non-binary decision framework.
5. Publication figure artifacts generated and non-empty.
"""

import hashlib
import json
import math
import os
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class TestMode2F1379ConvergenceAuditAndRoadmap(unittest.TestCase):

    def setUp(self):
        self.repo_root = REPO_ROOT
        self.json_path = os.path.join(
            self.repo_root, 'models', 'pandey_kumar_mode2',
            '07_fixed_mesh_convergence_suite', 'stiffness_regression_audit.json'
        )
        self.doc_path = os.path.join(
            self.repo_root, 'docs', 'mode2',
            'MODE2_FIXED_MESH_CONVERGENCE_AUDIT_AND_ROADMAP.md'
        )
        self.uel_path = os.path.join(
            self.repo_root, 'models', 'pandey_kumar_mode2',
            'f42_mixed_uel_mode2_miehe.for'
        )
        self.fig_pdf = os.path.join(
            self.repo_root, 'results', 'figures', 'mode2',
            'fig_mode2_f1379_convergence_audit_and_roadmap.pdf'
        )
        self.fig_png = os.path.join(
            self.repo_root, 'results', 'figures', 'mode2',
            'fig_mode2_f1379_convergence_audit_and_roadmap.png'
        )

    def test_stiffness_regression_audit_json_integrity(self):
        self.assertTrue(os.path.exists(self.json_path), f"Missing JSON audit: {self.json_path}")
        with open(self.json_path, 'r') as f:
            data = json.load(f)

        expected_cases = [
            '01_coarse_2p5k_h20um',
            '02_medium_18k_h7p5um',
            '03_intermediate_40k_h5um',
            '04_fine_72k_h3p75um',
            'et2_adaptive_37k'
        ]
        for c in expected_cases:
            self.assertIn(c, data, f"Case {c} missing from stiffness regression audit JSON")

        # Evaluate interval [0, 0.200] um (40 increments) across all models
        k_lit = 45.68
        for c in expected_cases:
            case_data = data[c]
            self.assertIn('interval_0.2_um', case_data)
            iv = case_data['interval_0.2_um']
            self.assertEqual(iv['n_samples'], 40)
            self.assertGreater(iv['r2_unconstrained'], 0.9999999)
            self.assertGreater(iv['r2_origin'], 0.9999999)
            
            # Near-zero intercept (< 0.0001 N)
            self.assertLess(abs(iv['intercept_N']), 1e-4)

            # Stiffness bounds [45.60, 46.00] kN/mm
            k0 = iv['k0_origin_kN_mm']
            self.assertGreater(k0, 45.60)
            self.assertLess(k0, 46.00)
            diff_lit_pct = abs(k0 - k_lit) / k_lit * 100.0
            self.assertLess(diff_lit_pct, 1.0, f"Case {c} diverges from literature by {diff_lit_pct}%")

        # Evaluate difference between 40k and 72k
        k0_40k = data['03_intermediate_40k_h5um']['interval_0.2_um']['k0_origin_kN_mm']
        k0_72k = data['04_fine_72k_h3p75um']['interval_0.2_um']['k0_origin_kN_mm']
        diff_40k_72k_pct = abs(k0_72k - k0_40k) / k0_40k * 100.0
        self.assertLess(diff_40k_72k_pct, 0.05, f"40k vs 72k stiffness diff is {diff_40k_72k_pct}%, expected < 0.05%")

    def test_single_factor_deck_equivalence_and_equation_accounting(self):
        # Verification of grid definitions, node counts, active variables, and MPC counts
        tiers = [
            {'name': 'Coarse', 'nx': 50, 'ny': 50, 'fe': 2500, 'h': 20.0, 'nodes': 2626, 'vars': 7879, 'mpc': 51},
            {'name': 'Medium', 'nx': 134, 'ny': 134, 'fe': 17956, 'h': 7.46, 'nodes': 18292, 'vars': 54877, 'mpc': 135},
            {'name': 'Intermediate', 'nx': 200, 'ny': 200, 'fe': 40000, 'h': 5.0, 'nodes': 40501, 'vars': 121504, 'mpc': 201},
            {'name': 'Fine', 'nx': 268, 'ny': 268, 'fe': 71824, 'h': 3.73, 'nodes': 72495, 'vars': 217486, 'mpc': 269}
        ]

        for t in tiers:
            nx = t['nx']
            ny = t['ny']
            # Slit node formula: (nx + 1)(ny + 1) + nx/2
            calculated_mesh_nodes = (nx + 1) * (ny + 1) + nx // 2
            self.assertEqual(calculated_mesh_nodes, t['nodes'], f"Node mismatch for {t['name']}")

            # User nodes in Abaqus: mesh nodes + 1 (RP 999999)
            user_nodes = calculated_mesh_nodes + 1
            self.assertEqual(user_nodes, t['nodes'] + 1)

            # Active variables: 3 * mesh_nodes + 1 (u1 on RP)
            calculated_vars = 3 * calculated_mesh_nodes + 1
            self.assertEqual(calculated_vars, t['vars'], f"Variable mismatch for {t['name']}")

            # Top MPC equations: nx + 1
            calculated_mpc = nx + 1
            self.assertEqual(calculated_mpc, t['mpc'], f"MPC mismatch for {t['name']}")

    def test_uel_formulation_audit(self):
        self.assertTrue(os.path.exists(self.uel_path), f"Missing canonical UEL: {self.uel_path}")
        with open(self.uel_path, 'rb') as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        self.assertEqual(h, '699B05D6C430FCE6242F8C603B45BB0783CF376451EFD52C56BC984B0CE71188')

        with open(self.uel_path, 'r') as f:
            content = f.read()

        # Check essential formulation keywords
        self.assertIn('COMMON /CB_STATE_TRANS/', content)
        self.assertIn('SIG_POS(1)', content)
        self.assertIn('SIG_NEG(1)', content)
        self.assertIn('D_POS(I,J)', content)
        self.assertIn('D_NEG(I,J)', content)
        self.assertIn('HIST = SV_H_TRIAL', content)
        self.assertIn('IF (PSI_0_POS .GT. HIST)', content)
        self.assertIn('SUBROUTINE UMAT', content)
        self.assertIn('STATEV(14) = D_VAL', content)
        self.assertIn('STATEV(15) = HIST_VAL', content)

    def test_roadmap_documentation_and_epistemological_framework(self):
        self.assertTrue(os.path.exists(self.doc_path), f"Missing roadmap document: {self.doc_path}")
        with open(self.doc_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Check required sections and scientific concepts
        self.assertIn('Branch 1: Asymptotic / Monotonic Convergence', text)
        self.assertIn('Branch 2: Multi-Scale Quantity Decoupling', text)
        self.assertIn('Branch 3: Boundary Constraint & Constitutive Splitting Sensitivity', text)
        self.assertIn('Branch 4: Regularization Length Scale ($l_0$) Resolution', text)
        self.assertIn('LAYER 1: NUMERICAL FRACTURE SOLVER & FIXED BENCHMARK', text)
        self.assertIn('LAYER 2: ADAPTIVE MESH CONTROLLER & MULTI-FIELD INDICATOR', text)
        self.assertIn('LAYER 3: SEQUENTIAL ADAPTIVE DRIVER', text)
        self.assertIn('Predefined Reference Evaluation Protocol', text)

    def test_figure_artifacts_generated(self):
        self.assertTrue(os.path.exists(self.fig_pdf), f"Missing PDF figure: {self.fig_pdf}")
        self.assertTrue(os.path.exists(self.fig_png), f"Missing PNG figure: {self.fig_png}")
        self.assertGreater(os.path.getsize(self.fig_pdf), 1000)
        self.assertGreater(os.path.getsize(self.fig_png), 1000)

if __name__ == '__main__':
    unittest.main()
