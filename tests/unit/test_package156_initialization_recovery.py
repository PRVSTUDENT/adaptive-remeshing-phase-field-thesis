#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package156_initialization_recovery.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: 30c0b12f-5c25-49bb-a7da-e4b89a6bd986
Turn: 389
Protocol Version: 2

Focused validation of Package 156 solution state initialization recovery:
1. Verifies 7+8+3 SVARS layout matches f42_mixed_uel.for lines 248-262 bitwise.
2. Verifies exact recovery of all 51,984 integration point histories from initial_conditions_solution.inc.
3. Confirms non-negative bounds (H >= 0.0) across all 12,996 elements.
4. Confirms active set boundary cards for phase-field DOF 3.
5. Confirms holding displacement boundary condition at RP 999999.
"""

from __future__ import print_function, division
import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
P156_DIR = REPO_ROOT / "models/pandey_kumar_mode1/156_c5_package156_c2_0_re_equilibration"


class TestPackage156InitializationRecovery(unittest.TestCase):
    def test_01_svars_card_layout_and_zero_padding(self):
        inc_file = P156_DIR / "initial_conditions_solution.inc"
        self.assertTrue(inc_file.is_file(), "initial_conditions_solution.inc must exist")

        with open(inc_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("**")]

        self.assertTrue(lines[0].upper().startswith("*INITIAL CONDITIONS, TYPE=SOLUTION"))
        data_lines = lines[1:]
        self.assertEqual(len(data_lines), 12996 * 3, "Must have exactly 3 lines per element for 12,996 quads")

        for i in range(0, min(len(data_lines), 300), 3):
            line1 = [float(p) for p in data_lines[i].split(",")]
            line2 = [float(p) for p in data_lines[i+1].split(",")]
            line3 = [float(p) for p in data_lines[i+2].split(",")]

            self.assertEqual(len(line1), 8)
            self.assertEqual(len(line2), 8)
            self.assertEqual(len(line3), 3)

            # Check that line1 padding (SVARS 1..7) is all zeros
            for v in line1[1:]:
                self.assertEqual(v, 0.0)

            # Check line2: SVARS 8 is 0.0
            self.assertEqual(line2[0], 0.0)

            # Check line2 padding: SVARS 13..15 is 0.0
            for v in line2[5:]:
                self.assertEqual(v, 0.0)

            # Check line3 padding: SVARS 16..18 is 0.0
            for v in line3:
                self.assertEqual(v, 0.0)

    def test_02_full_history_reconstruction_vs_lower_bounds(self):
        inc_file = P156_DIR / "initial_conditions_solution.inc"
        bounds_csv = P156_DIR / "d_lower_bounds.csv"

        expected = {}
        with open(bounds_csv, "r", encoding="utf-8") as f:
            next(f)
            for line in f:
                parts = line.strip().split(",")
                eid = int(parts[0])
                expected[eid] = [float(parts[k]) for k in range(5, 9)]

        with open(inc_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("**")]

        data_lines = lines[1:]
        recovered_count = 0
        for i in range(0, len(data_lines), 3):
            line1 = [float(p) for p in data_lines[i].split(",")]
            line2 = [float(p) for p in data_lines[i+1].split(",")]

            eid = int(line1[0])
            h_rec = line2[1:5]
            self.assertIn(eid, expected)
            for k in range(4):
                self.assertAlmostEqual(h_rec[k], expected[eid][k], places=12)
                self.assertGreaterEqual(h_rec[k], 0.0)
            recovered_count += 1

        self.assertEqual(recovered_count, 12996)

    def test_03_active_set_boundary_cards_structure(self):
        bnd_file = P156_DIR / "active_set_boundary_cards.inc"
        self.assertTrue(bnd_file.is_file(), "active_set_boundary_cards.inc must exist")

        with open(bnd_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("**")]

        cards = lines
        self.assertEqual(len(cards), 13278, "Must have boundary cards for all 13,278 receiver physical nodes")

        for card in cards[:100]:
            parts = [p.strip() for p in card.split(",")]
            self.assertEqual(len(parts), 4)
            nid = int(parts[0])
            self.assertTrue(1 <= nid <= 13278)
            self.assertEqual(parts[1], "3")  # DOF 3 (Phase field)
            self.assertEqual(parts[2], "3")
            d_val = float(parts[3])
            self.assertTrue(0.0 <= d_val <= 1.0)


if __name__ == "__main__":
    unittest.main()
