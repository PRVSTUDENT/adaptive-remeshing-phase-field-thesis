#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit test suite verifying the integrity and static contract of the Mode-I
adapted production decks (1.0%, 2.0%, 3.0%, 5.0%) produced from the corrected
Job-1_UEL pre-analysis.
"""

import os
import unittest
import hashlib

class TestMode1AdaptedDecksContract(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "models", "pandey_kumar_mode1", "88_mode1_preanalysis_uel_corrected")
        )
        self.cases = {
            "1PCT": {
                "deck": "PK_M1_JOB2_ADAPTED_1PCT.inp",
                "sha256": "028A604FFECAF37454309D4A4C6A966A79BEED72B3BC76AC59413B4E467B74C6",
                "expected_nodes": 42162,
                "expected_elems": 42318,
                "expected_quads": 41224,
                "expected_tris": 1094
            },
            "2PCT": {
                "deck": "PK_M1_JOB2_ADAPTED_2PCT.inp",
                "sha256": "B3D3B99F43BD1E0CC9C40B8FF1179AC950B37DEDF963DD9092113753274BA685",
                "expected_nodes": 10321,
                "expected_elems": 10253,
                "expected_quads": 9952,
                "expected_tris": 301
            },
            "3PCT": {
                "deck": "PK_M1_JOB2_ADAPTED_3PCT.inp",
                "sha256": "AA8A3B4189E9789F097BAD674BF8E3D174E546F4A8D0A01BA22882BA4BE901E2",
                "expected_nodes": 4721,
                "expected_elems": 4604,
                "expected_quads": 4484,
                "expected_tris": 120
            },
            "5PCT": {
                "deck": "PK_M1_JOB2_ADAPTED_5PCT.inp",
                "sha256": "7091DCC89D0068DBD956DA06AA4537CB1125E55CB5B895C48532E514456D485F",
                "expected_nodes": 3647,
                "expected_elems": 3536,
                "expected_quads": 3452,
                "expected_tris": 84
            }
        }

    def test_deck_files_exist(self):
        for name, info in self.cases.items():
            path = os.path.join(self.base_dir, info["deck"])
            self.assertTrue(os.path.exists(path), "Deck %s not found at %s" % (name, path))

    def test_deck_sha256_hashes(self):
        for name, info in self.cases.items():
            path = os.path.join(self.base_dir, info["deck"])
            with open(path, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest().upper()
            self.assertEqual(h, info["sha256"], "SHA-256 mismatch for %s" % name)

    def test_wrapped_nset_format(self):
        for name, info in self.cases.items():
            path = os.path.join(self.base_dir, info["deck"])
            with open(path, "r") as f:
                lines = f.readlines()
            
            in_nset = False
            for line in lines:
                l = line.strip()
                if l.startswith("*NSET"):
                    in_nset = True
                    continue
                elif l.startswith("*"):
                    in_nset = False
                
                if in_nset and l:
                    entries = [e.strip() for e in l.split(",") if e.strip()]
                    self.assertLessEqual(len(entries), 16, "NSET line has >16 entries in %s: %s" % (name, l))

    def test_three_layer_architecture(self):
        for name, info in self.cases.items():
            path = os.path.join(self.base_dir, info["deck"])
            with open(path, "r") as f:
                content = f.read()
            
            self.assertIn("*USER ELEMENT, TYPE=U1", content)
            self.assertIn("*USER ELEMENT, TYPE=U2", content)
            self.assertIn("ELSET=PHASE_QUAD", content)
            self.assertIn("ELSET=DISP_QUAD", content)
            self.assertIn("ELSET=UMAT_QUADS", content)
            self.assertIn("*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT", content)
            self.assertIn("N_BOTTOM, 2, 2, 0.0", content)
            self.assertIn("N_RP, 2, 2, 0.0050", content)
            self.assertIn("N_RP, 2, 2, 0.0100", content)

if __name__ == "__main__":
    unittest.main()
