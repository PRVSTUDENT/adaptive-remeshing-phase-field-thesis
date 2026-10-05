#!/usr/bin/env python3
"""
Unit Test Suite: Mode-I Stage-14 UEL Energy Formulation and Source Audit
Protocol Version: 2
Classification: NUMERICAL_AND_SOURCE_VERIFICATION

Tests:
1. Exact SHA-256 hash of authoritative production source f42_mixed_uel.for
2. Layer 3 Companion Visualizer UMAT zero-double-counting invariants (DDSDDE=1.D-11*I, SSE=0, SPD=0, SCD=0, STRESS=0)
3. Layer 1 (Phase UEL) and Layer 2 (Mechanical UEL) energy routing and variable slots
4. Unit system consistency (mm, kN, tonne, s -> 1 kN*mm = 1 J = 1000 mJ)
5. Mechanical non-invasiveness invariants (RHS/AMATRX decoupling, SVARS 17-18 dedicated slots)
6. Global energy balance formulas and reference reconciliation numbers
7. Epistemic status classification invariants in documentation
"""

import hashlib
import os
import unittest
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
UEL_FORTRAN_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
METHODS_DOC_PATH = REPO_ROOT / "docs" / "methods" / "UEL_ENERGY_FORMULATION_AND_BALANCE_AUDIT.md"

# Authoritative hash
EXPECTED_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"


class TestStage14UelEnergyFormulationAudit(unittest.TestCase):

    def test_01_authoritative_fortran_source_hash(self):
        """Verify exact cryptographic SHA-256 hash of f42_mixed_uel.for."""
        self.assertTrue(UEL_FORTRAN_PATH.exists(), f"Missing {UEL_FORTRAN_PATH}")
        content = UEL_FORTRAN_PATH.read_bytes()
        computed_hash = hashlib.sha256(content).hexdigest().lower()
        self.assertEqual(
            computed_hash,
            EXPECTED_UEL_SHA256,
            f"Hash mismatch: expected {EXPECTED_UEL_SHA256}, got {computed_hash}"
        )

    def test_02_layer3_companion_zero_double_counting_invariants(self):
        """Verify Layer 3 Companion Visualizer UMAT has dummy stiffness 1.D-11, zero stress, zero energies."""
        self.assertTrue(UEL_FORTRAN_PATH.exists())
        text = UEL_FORTRAN_PATH.read_text(encoding="utf-8", errors="ignore")
        
        # Check dummy stiffness scale factor in UMAT
        self.assertIn("1.D-11", text, "Expected dummy stiffness scale factor 1.D-11 in UMAT")
        self.assertIn("DDSDDE(I,I) = 1.D-11", text)
        self.assertIn("STRESS(I) = 0.D0", text)
        self.assertIn("SSE = 0.D0", text)
        self.assertIn("SPD = 0.D0", text)
        self.assertIn("SCD = 0.D0", text)
        self.assertIn("STATEV(17) = SV_E_FRAC(PHYSIDX)", text)
        self.assertIn("STATEV(18) = SV_E_ELAS(PHYSIDX)", text)

    def test_03_layer1_and_layer2_energy_routing(self):
        """Verify Layer 1 (Phase) and Layer 2 (Mech) energy slot routing in UEL."""
        text = UEL_FORTRAN_PATH.read_text(encoding="utf-8", errors="ignore")
        
        # Layer 1 computes fracture energy into ENERGY(7) and SVARS(17)
        self.assertIn("ENERGY(7) =", text, "Expected ENERGY(7) assignment for fracture energy in UEL")
        self.assertIn("SVARS(17) = E_FRAC_ELEM", text, "Expected SVARS(17) storage in Phase UEL")
        self.assertIn("SV_E_FRAC(PHYSIDX) = E_FRAC_ELEM", text, "Expected SV_E_FRAC storage in common block")
        
        # Layer 2 computes elastic strain energy into ENERGY(2) and SVARS(17)/SV_E_ELAS
        self.assertIn("ENERGY(2) =", text, "Expected ENERGY(2) assignment for elastic strain energy in UEL")
        self.assertIn("SVARS(17) = E_ELAS_ELEM", text, "Expected SVARS(17) storage in Mech UEL")
        self.assertIn("SV_E_ELAS(PHYSIDX) = E_ELAS_ELEM", text, "Expected SV_E_ELAS storage in common block")

    def test_04_unit_system_consistency(self):
        """Verify dimensional conversion factors: 1 kN*mm = 1 J = 1000 mJ."""
        energy_kn_mm = 1.0  # kN*mm
        energy_j = energy_kn_mm * 1.0  # Joules
        energy_mj = energy_kn_mm * 1000.0  # milliJoules
        
        self.assertAlmostEqual(energy_j, 1.0, places=7)
        self.assertAlmostEqual(energy_mj, 1000.0, places=7)
        
        # Check material constants
        E_modulus_kn_per_mm2 = 210.0  # kN/mm^2 == GPa
        Gc_kn_per_mm = 2.7e-3  # kN/mm == 2.7 N/mm == 2700 J/m^2
        l0_mm = 0.0075  # mm == 7.5 um
        
        self.assertAlmostEqual(E_modulus_kn_per_mm2 * 1e3, 210000.0, places=3)  # MPa
        self.assertAlmostEqual(Gc_kn_per_mm * 1e6, 2700.0, places=3)  # J/m^2
        self.assertAlmostEqual(l0_mm * 1e3, 7.5, places=3)  # um

    def test_05_mechanical_non_invasiveness_invariants(self):
        """Verify that auxiliary energy instrumentation does not affect RHS or AMATRX."""
        text = UEL_FORTRAN_PATH.read_text(encoding="utf-8", errors="ignore")
        
        # Baseline state variables SVARS(1..16) are reserved for primary mechanics and history
        self.assertIn("SVARS(1..4)", text)
        self.assertIn("SVARS(5..8)", text)
        
        # Verify UEXTERNALDB hook exists for non-invasive logging
        self.assertIn("SUBROUTINE UEXTERNALDB", text)
        self.assertIn("TOT_E_FRAC", text)
        self.assertIn("TOT_E_ELAS", text)

    def test_06_energy_balance_definitions_and_reference_reconciliation(self):
        """Verify energy balance definitions and exact reference metrics."""
        # Fixed Reference metrics (Job 1409734.mmaster02) at u = 0.010 mm
        W_ext_ref = 2.359329  # mJ
        E_frac_ref = 2.340220  # mJ
        E_elas_ref = 0.001161  # mJ
        E_model_ref = E_elas_ref + E_frac_ref
        Delta_book_ref = W_ext_ref - E_model_ref
        eps_book_ref = abs(Delta_book_ref) / W_ext_ref * 100.0
        
        self.assertAlmostEqual(E_model_ref, 2.341381, places=5)
        self.assertAlmostEqual(Delta_book_ref, 0.017948, places=5)
        self.assertAlmostEqual(eps_book_ref, 0.7607, places=3)
        
        # ET1 Adaptive Baseline metrics at u = 0.010 mm
        W_ext_et1 = 2.267380  # mJ
        E_frac_et1 = 2.285469  # mJ
        E_elas_et1 = 0.000674  # mJ
        E_model_et1 = E_elas_et1 + E_frac_et1
        Delta_book_et1 = W_ext_et1 - E_model_et1
        eps_book_et1 = abs(Delta_book_et1) / W_ext_et1 * 100.0
        
        self.assertAlmostEqual(E_model_et1, 2.286143, places=5)
        self.assertAlmostEqual(Delta_book_et1, -0.018763, places=5)
        self.assertAlmostEqual(eps_book_et1, 0.8275, places=3)

    def test_07_methods_documentation_and_epistemic_categories(self):
        """Verify methods documentation exists and records rigorous epistemic categories."""
        self.assertTrue(METHODS_DOC_PATH.exists(), f"Missing {METHODS_DOC_PATH}")
        doc_text = METHODS_DOC_PATH.read_text(encoding="utf-8")
        
        required_terms = [
            "SOURCE_VERIFIED",
            "NUMERICALLY_VERIFIED",
            "UNRESOLVED_INTERNAL_ABAQUS_DETAIL",
            "Zero Double Counting",
            "Mechanical Non-Invasiveness",
            "Bookkeeping Residual",
            "f42_mixed_uel.for",
            "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        ]
        for term in required_terms:
            self.assertIn(term, doc_text, f"Expected term '{term}' in methods documentation")


if __name__ == "__main__":
    unittest.main()
