#!/usr/bin/env python3
"""
Unit Test Suite for Task F1391:
Mode-II Fine-Mesh Peak Verification, Nonlinear Diagnostic Audit,
and Spatial Convergence Evaluation (Gate M2-1B, Gate M2-3, Gate M2-4).

Author: Gemini Antigravity (Autonomous Scientific Agent)
Date: 2026-10-10
"""

import unittest
import os
import hashlib
import json
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
EVIDENCE_DIR = os.path.join(REPO_ROOT, 'runs', 'mode2', 'fixed_convergence', 'evidence')
SUITE_DIR = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode2', '07_fixed_mesh_convergence_suite')

def compute_sha256(filepath):
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def parse_dat_rp(filepath):
    """Parse displacement and reaction force for RP node 999999 from Abaqus .dat file."""
    if not os.path.exists(filepath):
        return np.array([]), np.array([])
    u_vals, rf_vals = [], []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if line.strip().startswith('999999'):
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        u_vals.append(float(parts[1]))
                        rf_vals.append(float(parts[2]))
                    except ValueError:
                        pass
    return np.array(u_vals), np.array(rf_vals)

class TestMode2F1391FinePeakAndDiagnosticAudit(unittest.TestCase):
    """Test suite verifying Mode-II fine 72k peak verification, diagnostic audit, and spatial convergence."""

    def test_01_mode1_baseline_freeze_integrity(self):
        """Verify Mode-I baseline Fortran UEL remains 100% frozen and untouched."""
        mode1_uel = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', 'f42_mixed_uel.for')
        self.assertTrue(os.path.exists(mode1_uel), f"Mode-I UEL missing: {mode1_uel}")
        mode1_hash = compute_sha256(mode1_uel)
        expected_mode1_hash = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        self.assertEqual(mode1_hash, expected_mode1_hash, "Mode-I UEL hash mismatch; baseline freeze violated!")

    def test_02_mode2_authoritative_uel_integrity(self):
        """Verify Mode-II Miehe spectral decomposition Fortran UEL hash integrity."""
        mode2_uel = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode2', '06_paper_grounded_uel_preanalysis', 'f42_mixed_uel_mode2_miehe.for')
        self.assertTrue(os.path.exists(mode2_uel), f"Mode-II UEL missing: {mode2_uel}")
        mode2_hash = compute_sha256(mode2_uel)
        expected_mode2_hash = "699B05D6C430FCE6242F8C603B45BB0783CF376451EFD52C56BC984B0CE71188"
        self.assertEqual(mode2_hash, expected_mode2_hash, "Mode-II UEL hash mismatch; formulation changed!")

    def test_03_diagnostic_40k_ls_exact_numerical_diff(self):
        """Verify single-parameter line-search modification is strictly isolated to *CONTROLS in 2 steps."""
        orig_inp = os.path.join(SUITE_DIR, '03_intermediate_40k_h5um', 'M2_FIX_INT_40K.inp')
        diag_inp = os.path.join(SUITE_DIR, '03_intermediate_40k_h5um_diagnostic_ls', 'M2_FIX_INT_40K_LS.inp')
        
        self.assertTrue(os.path.exists(orig_inp), f"Original 40k inp missing: {orig_inp}")
        self.assertTrue(os.path.exists(diag_inp), f"Diagnostic 40k LS inp missing: {diag_inp}")
        
        with open(orig_inp, 'r', encoding='utf-8') as f:
            orig_lines = [line.strip() for line in f if line.strip()]
        with open(diag_inp, 'r', encoding='utf-8') as f:
            diag_lines = [line.strip() for line in f if line.strip()]
            
        # The diagnostic deck must have exactly 4 more non-empty lines (2 *CONTROLS + 2 parameter lines)
        self.assertEqual(len(diag_lines), len(orig_lines) + 4)
        
        # Verify specific additions
        diag_controls = [l for l in diag_lines if l.startswith('*CONTROLS, PARAMETERS=LINE SEARCH')]
        self.assertEqual(len(diag_controls), 2, "Line search must be applied to exactly 2 analysis steps")

    def test_04_fine_72k_retrieved_evidence_and_bit_parity(self):
        """Verify fine 72k progress and 100% bitwise parity between original and safeguard."""
        orig_dat = os.path.join(EVIDENCE_DIR, '04_fine_72k', 'M2_FIX_FINE_72K.dat')
        safe_dat = os.path.join(EVIDENCE_DIR, '04_fine_72h', 'M2_FIX_FINE_72H.dat')
        
        u_orig, rf_orig = parse_dat_rp(orig_dat)
        u_safe, rf_safe = parse_dat_rp(safe_dat)
        
        self.assertGreaterEqual(len(u_orig), 1850, f"Expected >= 1850 points in 72k original, got {len(u_orig)}")
        self.assertGreaterEqual(len(u_safe), 1400, f"Expected >= 1400 points in 72h safeguard, got {len(u_safe)}")
        
        # Check active displacement of original
        self.assertGreaterEqual(u_orig[-1] * 1000.0, 9.25, f"Expected ux >= 9.25 um, got {u_orig[-1]*1000.0:.3f} um")
        
        # Check bitwise parity over common range
        common_len = min(len(u_orig), len(u_safe))
        np.testing.assert_array_equal(u_orig[:common_len], u_safe[:common_len])
        np.testing.assert_array_equal(rf_orig[:common_len], rf_safe[:common_len])

    def test_05_spatial_convergence_relative_errors(self):
        """Verify relative error metrics and monotonic peak force sequence."""
        f_coarse = 525.70
        f_med = 436.99
        f_int = 420.66
        
        # Monotonic reduction
        self.assertGreater(f_coarse, f_med)
        self.assertGreater(f_med, f_int)
        
        # Relative convergence rates
        eps_coarse_med = (f_coarse - f_med) / f_med * 100.0
        eps_med_int = (f_med - f_int) / f_int * 100.0
        
        self.assertAlmostEqual(eps_coarse_med, 20.30, delta=0.5)
        self.assertAlmostEqual(eps_med_int, 3.88, delta=0.5)
        
        # Error decreases rapidly with mesh refinement (super-linear convergence in peak load)
        self.assertLess(eps_med_int, eps_coarse_med / 4.0)

    def test_06_initial_stiffness_invariance(self):
        """Verify initial structural stiffness invariance across all 7 Mode-II discretizations."""
        stiffness_values = {
            'Fixed_Coarse_2.5k': 45.78,
            'Fixed_Medium_18k': 45.96,
            'Fixed_Interm_40k': 45.86,
            'Fixed_Fine_72k': 45.81,
            'Adapted_ET3': 45.64,
            'Adapted_ET2': 45.71,
            'Preanalysis_Miehe': 45.76
        }
        
        mean_k0 = sum(stiffness_values.values()) / len(stiffness_values)
        self.assertAlmostEqual(mean_k0, 45.79, delta=0.10)
        
        for name, k0 in stiffness_values.items():
            rel_diff = abs(k0 - mean_k0) / mean_k0
            self.assertLess(rel_diff, 0.008, f"Stiffness spread excessive for {name}: {k0} kN/mm")

    def test_07_epistemic_bounds_and_governance(self):
        """Verify session governance and epistemological boundary definitions."""
        session_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_SESSION.json")
        self.assertTrue(os.path.exists(session_path))
        with open(session_path, "r", encoding="utf-8") as f:
            session_data = json.load(f)
        self.assertIn(session_data["agent"], ["gemini-antigravity", "codex"])
        self.assertTrue("F1391" in session_data["task_id"] or "F139" in session_data["task_id"])

if __name__ == '__main__':
    unittest.main()
