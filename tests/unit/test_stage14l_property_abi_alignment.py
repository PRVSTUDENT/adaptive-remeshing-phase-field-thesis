"""Unit test for Stage 14L: UEL Property ABI Card Alignment and Regression Guard."""

import os
import re
import unittest


class TestStage14LPropertyABIAlignment(unittest.TestCase):
    """Regression guard proving f42 Fortran subroutine ABI and input *UEL PROPERTY cards are aligned."""

    def setUp(self):
        self.subroutine_path = os.path.join(
            "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "f42_mixed_uel.for"
        )
        self.inp_path = os.path.join(
            "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp"
        )
        self.ref_inp_path = os.path.join(
            "models", "pandey_kumar_mode1", "16_energy_qualification_reference_15k", "PK_MODE1_REF15K_ENERGY.inp"
        )

    def test_fortran_subroutine_abi_order(self):
        """Verify the Fortran subroutine source strictly parses PROPS in canonical order."""
        self.assertTrue(os.path.exists(self.subroutine_path), "f42_mixed_uel.for must exist")
        with open(self.subroutine_path, "r", encoding="utf-8", errors="replace") as f:
            src = f.read()

        # Check UEL assignment lines
        self.assertRegex(src, r"E_L0\s*=\s*PROPS\(1\)", "PROPS(1) must map to E_L0")
        self.assertRegex(src, r"E_GC\s*=\s*PROPS\(2\)", "PROPS(2) must map to E_GC")
        self.assertRegex(src, r"E_MOD\s*=\s*PROPS\(3\)", "PROPS(3) must map to E_MOD")
        self.assertRegex(src, r"E_NU\s*=\s*PROPS\(4\)", "PROPS(4) must map to E_NU")
        self.assertRegex(src, r"E_K\s*=\s*PROPS\(5\)", "PROPS(5) must map to E_K")
        self.assertRegex(src, r"N_PHYS\s*=\s*INT\(PROPS\(6\)\)", "PROPS(6) must map to N_PHYS")

    def test_input_deck_uel_property_cards(self):
        """Verify every *UEL PROPERTY card in the corrected Stage-14 deck matches the f42 ABI."""
        self.assertTrue(os.path.exists(self.inp_path), "Stage-14 .inp deck must exist")
        with open(self.inp_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        uel_cards = []
        for i, line in enumerate(lines):
            if line.strip().upper().startswith("*UEL PROPERTY"):
                data_line = lines[i + 1].strip()
                uel_cards.append((line.strip(), data_line))

        self.assertGreaterEqual(len(uel_cards), 2, "Must have at least 2 *UEL PROPERTY cards (PHASE_ELEM, MECH_ELEM)")

        expected_values = [0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 14483.0]

        for header, data_line in uel_cards:
            tokens = [float(t.strip()) for t in data_line.split(",") if t.strip()]
            self.assertEqual(len(tokens), 6, f"Card '{header}' must have exactly 6 constants")
            
            l0_val, gc_val, e_val, nu_val, k_val, n_phys_val = tokens
            self.assertAlmostEqual(l0_val, 0.0075, places=6, msg="PROPS(1) l0 must be 0.0075 mm")
            self.assertAlmostEqual(gc_val, 0.0027, places=6, msg="PROPS(2) Gc must be 0.0027 kN/mm")
            self.assertAlmostEqual(e_val, 210.0, places=4, msg="PROPS(3) E must be 210.0 kN/mm^2")
            self.assertAlmostEqual(nu_val, 0.30, places=4, msg="PROPS(4) nu must be 0.30")
            self.assertAlmostEqual(k_val, 1.0e-7, places=10, msg="PROPS(5) k must be 1.0e-7")
            self.assertEqual(int(n_phys_val), 14483, msg="PROPS(6) N_PHYS must be exactly 14,483")

    def test_companion_umat_material_card(self):
        """Verify Layer 3 companion visualization UMAT card is properly configured."""
        with open(self.inp_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

        self.assertIn("*MATERIAL, NAME=UMAT_MAT", text)
        self.assertIn("*USER MATERIAL, CONSTANTS=3", text)
        self.assertIn("210.0, 0.3, 14483.", text)

    def test_no_molnar_order_inversion_present(self):
        """Prove that the inverted Molnar order (210.0, 0.3, 0.0075, ...) does not exist in the deck."""
        with open(self.inp_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

        self.assertNotIn("210.0, 0.3, 0.0075", text, "Inverted Molnar property string must not be present in deck")


if __name__ == "__main__":
    unittest.main()
