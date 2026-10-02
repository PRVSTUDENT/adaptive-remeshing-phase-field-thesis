#!/usr/bin/env python3
"""
Unit test for static validation of corrected Pandey & Kumar Mode-I Pre-Analysis UEL Deck.
"""

import os
import sys
import unittest

class TestMode1PreUelCorrectedStatic(unittest.TestCase):
    def setUp(self):
        self.target_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "models", "pandey_kumar_mode1", "88_mode1_preanalysis_uel_corrected", "PK_M1_PRE_UEL_CORRECTED.inp")
        )
        self.deck_path = self.target_path

    def test_deck_exists(self):
        self.assertTrue(os.path.exists(self.deck_path), f"Deck not found at {self.deck_path}")

    def test_layered_structure_and_element_counts(self):
        with open(self.deck_path, 'r') as f:
            content = f.read()

        # Check User Element interfaces
        self.assertIn("*User Element, nodes=4, type=U1", content)
        self.assertIn("*User Element, nodes=4, type=U2", content)

        # Check 3 layers present
        self.assertIn("*Element, type=U1, elset=PF_QUADS", content)
        self.assertIn("*Element, type=U2, elset=MECH_QUADS", content)
        self.assertIn("*Element, type=CPE4, elset=UMAT_QUADS", content)

        # Check elsets
        self.assertIn("*Elset, elset=umatelem", content)
        self.assertIn("*Elset, elset=All_elem", content)

    def test_card_wrapping_limit(self):
        # Verify no NSET line exceeds 16 entries
        with open(self.deck_path, 'r') as f:
            lines = f.readlines()

        in_nset = False
        for line in lines:
            l = line.strip()
            if l.startswith('*'):
                in_nset = l.upper().startswith('*NSET')
                continue
            if in_nset:
                entries = [e.strip() for e in l.split(',') if e.strip()]
                self.assertLessEqual(len(entries), 16, f"NSET line exceeds 16 entries: {l}")

    def test_properties_and_fracture_parameters(self):
        with open(self.deck_path, 'r') as f:
            content = f.read()

        # Check UEL property values: l0=0.0075, Gc=0.0027, E=210.0, nu=0.3, k=1.0e-7
        self.assertIn("*UEL Property, elset=PF_QUADS\n0.0075, 0.0027, 210.0, 0.3, 1.0E-7, 2700.0", content)
        self.assertIn("*UEL Property, elset=MECH_QUADS\n0.0075, 0.0027, 210.0, 0.3, 1.0E-7, 2700.0", content)
        self.assertIn("*Solid Section, elset=umatelem, material=MAT_UMAT", content)
        self.assertIn("*Material, name=MAT_UMAT\n*User Material, constants=3\n1.0E-11, 0.3, 2700.0", content)
        self.assertIn("*Depvar\n20,", content)

    def test_two_step_schedule_and_outputs(self):
        with open(self.deck_path, 'r') as f:
            content = f.read()

        self.assertIn("*Step, name=Step-1", content)
        self.assertIn("N_RP, 2, 2, 0.0050", content)
        self.assertIn("*Step, name=Step-2", content)
        self.assertIn("N_RP, 2, 2, 0.0100", content)
        self.assertIn("MISESERI, MISESAVG, S, EVOL", content)
        self.assertIn("SDV", content)

if __name__ == '__main__':
    unittest.main()
