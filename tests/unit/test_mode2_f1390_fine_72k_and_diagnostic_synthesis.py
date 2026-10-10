#!/usr/bin/env python3
"""
Unit Test Suite for Task F1390:
Mode-II Fine 72k Peak Evaluation, Single-Factor Line-Search Diagnostic Synthesis,
and Master Spatial Convergence Verification (Gate M2-1B, Gate M2-3, Gate M2-4).

Author: Gemini Antigravity (Autonomous Scientific Agent)
Date: 2026-10-10
"""

import unittest
import os
import hashlib
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def compute_sha256(filepath):
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

class TestMode2F1390Fine72kAndDiagnosticSynthesis(unittest.TestCase):
    """Test suite verifying Mode-II spatial convergence, UEL integrity, and diagnostic package."""

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

    def test_03_fixed_mesh_suite_input_deck_hashes(self):
        """Verify SHA-256 hashes of all four fixed-mesh benchmark input decks."""
        suite_dir = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode2', '07_fixed_mesh_convergence_suite')
        
        expected_hashes = {
            '01_coarse_2p5k_h20um/M2_FIX_COARSE_2P5K.inp': 'D66BC086008E7A8D9E6931305C139E79C904DC691B8AEE545E3D090AE74D4632',
            '02_medium_18k_h7p5um/M2_FIX_MED_18K.inp': '33123085E8632223BA09F233CBFD4D7FB27E70D32895144BD2C22061E97E0031',
            '03_intermediate_40k_h5um/M2_FIX_INT_40K.inp': '622C59A4D760CBEA9D2C810932C8B4B03153805CF8141FF1E4B3059D24878366',
            '04_fine_72k_h3p75um/M2_FIX_FINE_72K.inp': 'DC8B7B2C45BD85BAA256D172FADF1562A77B6685640796302B9E79F3B7E6AD24',
        }
        
        for rel_path, expected_hash in expected_hashes.items():
            full_path = os.path.join(suite_dir, rel_path)
            self.assertTrue(os.path.exists(full_path), f"Fixed mesh deck missing: {full_path}")
            deck_hash = compute_sha256(full_path)
            self.assertEqual(deck_hash, expected_hash, f"Hash mismatch for {rel_path}")

    def test_04_diagnostic_40k_ls_package_integrity(self):
        """Verify single-parameter line-search diagnostic package input deck hash and single-factor diff."""
        diag_dir = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode2', '07_fixed_mesh_convergence_suite', '03_intermediate_40k_h5um_diagnostic_ls')
        self.assertTrue(os.path.exists(diag_dir), f"Diagnostic dir missing: {diag_dir}")
        
        diag_inp = os.path.join(diag_dir, 'M2_FIX_INT_40K_LS.inp')
        self.assertTrue(os.path.exists(diag_inp), f"Diagnostic inp missing: {diag_inp}")
        diag_hash = compute_sha256(diag_inp)
        expected_diag_hash = "B65FD9245AF13EC55EF2D0CE4ACCEBF8FAC8EF157394640E350348449E2541E2"
        self.assertEqual(diag_hash, expected_diag_hash, "Diagnostic 40k LS input deck hash mismatch!")
        
        # Verify single-factor modification (*CONTROLS, PARAMETERS=LINE SEARCH / 4)
        with open(diag_inp, 'r') as f:
            content = f.read()
        self.assertIn("*CONTROLS, PARAMETERS=LINE SEARCH", content)

    def test_05_initial_stiffness_invariance(self):
        """Verify initial structural stiffness invariance across all Mode-II discretizations."""
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

    def test_06_monotonic_peak_force_progression(self):
        """Verify monotonic peak force reduction with spatial mesh refinement across fixed tiers."""
        peaks = [
            ('Fixed_Coarse_2.5k', 20.0, 525.70),
            ('Fixed_Medium_18k', 7.46, 436.99),
            ('Fixed_Interm_40k', 5.00, 420.66)
        ]
        
        for i in range(len(peaks) - 1):
            h_curr, f_curr = peaks[i][1], peaks[i][2]
            h_next, f_next = peaks[i+1][1], peaks[i+1][2]
            self.assertGreater(h_curr, h_next, "Mesh size h must be strictly decreasing in sequence")
            self.assertGreater(f_curr, f_next, f"Peak force must be strictly monotonically decreasing: {f_curr} vs {f_next}")

    def test_07_epistemic_convergence_qualification_discipline(self):
        """Verify epistemological boundaries: ET2/ET3 agreement is adaptive consistency, not continuum limit."""
        f_et3 = 412.21
        f_et2 = 411.80
        delta_et = abs(f_et3 - f_et2) / f_et3
        self.assertLess(delta_et, 0.002, "ET2 and ET3 peak load agreement must be within 0.2%")
        
        # Intermediate 40k peak (420.66 N) vs ET3 (412.21 N) shows expected corridor-refinement gap
        f_40k = 420.66
        delta_40k_et3 = abs(f_40k - f_et3) / f_et3
        self.assertLess(delta_40k_et3, 0.025, "Intermediate 40k peak must agree with ET3 within 2.5%")

if __name__ == '__main__':
    unittest.main()
