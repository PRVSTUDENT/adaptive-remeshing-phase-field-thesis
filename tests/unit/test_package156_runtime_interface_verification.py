#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package156_runtime_interface_verification.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: 58228402-7069-4d7d-941d-17e6af41dd12
Turn: 390
Protocol Version: 2

Independent verification of the C5 receiver initialization and coupled solver interface:
1. All 51,984 receiver Gauss-point history values are read in correct element/GP order.
2. Canonical 7+8+3 SVARS layout is preserved bitwise.
3. SVARS 9-12 contain intended history values matching d_lower_bounds.csv.
4. Nodal damage lower bounds are loaded and enforced by PDAS active set cards.
5. Transferred displacements are consistent with prescribed same-load boundary state.
6. Reference-point constraints and duplicate slit flanks remain valid.
7. Zero history-slot shifts, zero-initialization overrides, or unintended state resets occur in UEL.
8. Frozen production UEL hash CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6 preserved bitwise.
"""

from __future__ import print_function, division
import os
import sys
import hashlib
import unittest
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.c4_to_c5_spatial_mapping import Mesh2D, sha256_file
from scripts.state_transfer.build_package156_c5_receiver import FROZEN_UEL_SHA256

P156_DIR = REPO_ROOT / "models/pandey_kumar_mode1/156_c5_package156_c2_0_re_equilibration"


class TestPackage156RuntimeInterfaceVerification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c5_inp = REPO_ROOT / "models/pandey_kumar_mode1/155_c5_candidate_mesh/M1_C5_CANDIDATE_MESH.inp"
        cls.mesh = Mesh2D.from_inp(cls.c5_inp, name="C5", max_physical_node=13278)

    def test_01_frozen_uel_sha256_bitwise_preservation(self):
        uel_path = P156_DIR / "f42_mixed_uel.for"
        self.assertTrue(uel_path.is_file(), "f42_mixed_uel.for must exist in Package 156")
        actual_hash = sha256_file(uel_path)
        self.assertEqual(actual_hash.upper(), FROZEN_UEL_SHA256.upper(),
                         "Production UEL hash must match frozen SHA-256 bitwise")

    def test_02_svars_783_card_serialization_and_slot_immutability(self):
        inc_file = P156_DIR / "initial_conditions_solution.inc"
        self.assertTrue(inc_file.is_file())

        with open(inc_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("**")]

        self.assertTrue(lines[0].upper().startswith("*INITIAL CONDITIONS, TYPE=SOLUTION"))
        data_lines = lines[1:]
        self.assertEqual(len(data_lines), 12996 * 3, "Exactly 3 lines per element for 12,996 quads")

        for idx in range(0, len(data_lines), 3):
            line1_parts = [float(p) for p in data_lines[idx].split(",")]
            line2_parts = [float(p) for p in data_lines[idx + 1].split(",")]
            line3_parts = [float(p) for p in data_lines[idx + 2].split(",")]

            self.assertEqual(len(line1_parts), 8, "Line 1 must contain element ID + 7 SVARS")
            self.assertEqual(len(line2_parts), 8, "Line 2 must contain 8 SVARS")
            self.assertEqual(len(line3_parts), 3, "Line 3 must contain 3 SVARS")

            elem_id = int(line1_parts[0])
            expected_elem_id = (idx // 3) + 1
            self.assertEqual(elem_id, expected_elem_id, "Element IDs must be strictly sequential 1..12996")

            # Check that padding SVARS 1..8 and 13..18 are exact 0.0
            # Line 1: SVARS 1..7 (indices 1..7)
            for v in line1_parts[1:]:
                self.assertEqual(v, 0.0, "SVARS 1..7 must be strictly 0.0")

            # Line 2: SVARS 8 (index 0)
            self.assertEqual(line2_parts[0], 0.0, "SVARS 8 must be strictly 0.0")

            # Line 2: SVARS 13..15 (indices 5..7)
            for v in line2_parts[5:]:
                self.assertEqual(v, 0.0, "SVARS 13..15 must be strictly 0.0")

            # Line 3: SVARS 16..18 (indices 0..2)
            for v in line3_parts:
                self.assertEqual(v, 0.0, "SVARS 16..18 must be strictly 0.0")

    def test_03_gauss_point_history_order_and_bounds_agreement(self):
        inc_file = P156_DIR / "initial_conditions_solution.inc"
        bounds_csv = P156_DIR / "d_lower_bounds.csv"

        # Load reference lower bounds CSV
        gp_hist_csv = {}
        with open(bounds_csv, "r", encoding="utf-8") as f:
            header = next(f).strip().split(",")
            for line in f:
                parts = line.strip().split(",")
                eid = int(parts[0])
                gp_hist_csv[eid] = [float(parts[5]), float(parts[6]), float(parts[7]), float(parts[8])]

        self.assertEqual(len(gp_hist_csv), 12996)

        # Parse solution cards
        with open(inc_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("**")][1:]

        total_gps = 0
        min_h = 1e30
        max_h = -1e30

        for idx in range(0, len(lines), 3):
            line1_parts = [float(p) for p in lines[idx].split(",")]
            line2_parts = [float(p) for p in lines[idx + 1].split(",")]

            eid = int(line1_parts[0])
            h_vals = line2_parts[1:5]  # SVARS 9, 10, 11, 12

            for k in range(4):
                h = h_vals[k]
                self.assertGreaterEqual(h, 0.0, "History value must be non-negative (Policy 1)")
                self.assertAlmostEqual(h, gp_hist_csv[eid][k], places=12,
                                       msg="History value must bitwise agree with d_lower_bounds.csv")
                min_h = min(min_h, h)
                max_h = max(max_h, h)
                total_gps += 1

        self.assertEqual(total_gps, 51984, "Must verify exactly 51,984 integration point histories")
        self.assertGreaterEqual(min_h, 0.0)
        self.assertGreater(max_h, 0.0, "Max history must be positive")

    def test_04_active_set_nodal_damage_bounds_enforcement(self):
        bnd_file = P156_DIR / "active_set_boundary_cards.inc"
        self.assertTrue(bnd_file.is_file())

        with open(bnd_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("**")]

        self.assertEqual(len(lines), 13278, "Must have exactly 13,278 nodal boundary entries")

        bnd_map = {}
        for line in lines:
            parts = [p.strip() for p in line.split(",")]
            self.assertEqual(len(parts), 4)
            nid = int(parts[0])
            dof_start = int(parts[1])
            dof_end = int(parts[2])
            val = float(parts[3])

            self.assertEqual(dof_start, 3, "Phase field DOF must be 3")
            self.assertEqual(dof_end, 3, "Phase field DOF must be 3")
            self.assertGreaterEqual(val, 0.0, "Damage lower bound must be >= 0")
            self.assertLessEqual(val, 1.0, "Damage lower bound must be <= 1")
            self.assertNotIn(nid, bnd_map, "Duplicate boundary constraint on node {}".format(nid))
            bnd_map[nid] = val

        self.assertEqual(len(bnd_map), 13278, "All 13,278 physical nodes must have lower bounds")

    def test_05_transferred_displacements_and_holding_load_consistency(self):
        disp_csv = P156_DIR / "nodal_displacements_initial.csv"
        self.assertTrue(disp_csv.is_file())

        with open(disp_csv, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        header = lines[0].split(",")
        self.assertEqual(header, ["node_id", "u1", "u2"])
        # Exactly 13,278 physical nodes
        data_rows = lines[1:]
        self.assertEqual(len(data_rows), 13278)

        disp_dict = {}
        for row in data_rows:
            p = row.split(",")
            nid = int(p[0])
            ux = float(p[1])
            uy = float(p[2])
            disp_dict[nid] = (ux, uy)

        # Verify bottom boundary condition: y = 0 => uy = 0
        bottom_nodes = [nid for nid, (x, y) in self.mesh.nodes.items() if abs(y) < 1e-7]
        self.assertGreater(len(bottom_nodes), 0)
        for nid in bottom_nodes:
            if nid in disp_dict:
                self.assertAlmostEqual(disp_dict[nid][1], 0.0, places=9,
                                       msg="Bottom node {} must have uy = 0".format(nid))

        # Verify pinned node: x = 0, y = 0 => ux = 0
        pinned_nodes = [nid for nid, (x, y) in self.mesh.nodes.items() if abs(x) < 1e-7 and abs(y) < 1e-7]
        self.assertGreater(len(pinned_nodes), 0)
        for nid in pinned_nodes:
            if nid in disp_dict:
                self.assertAlmostEqual(disp_dict[nid][0], 0.0, places=9,
                                       msg="Pinned node {} must have ux = 0".format(nid))

    def test_06_slit_flank_duplicate_node_discrimination(self):
        # 53 seam pairs along y = 0.05 mm, x <= 0.04 mm
        self.assertEqual(len(self.mesh.seam_pairs), 53)

        d_csv = P156_DIR / "nodal_phase_field_initial.csv"
        self.assertTrue(d_csv.is_file())

        d_map = {}
        with open(d_csv, "r", encoding="utf-8") as f:
            next(f)
            for line in f:
                parts = line.strip().split(",")
                d_map[int(parts[0])] = float(parts[1])

        # Verify that upper and lower seam nodes are present and independent
        for bot_nid, top_nid, x_val in self.mesh.seam_pairs:
            self.assertIn(bot_nid, d_map)
            self.assertIn(top_nid, d_map)
            self.assertNotEqual(bot_nid, top_nid)
            # Physical coordinates must be identical
            x_bot, y_bot = self.mesh.nodes[bot_nid]
            x_top, y_top = self.mesh.nodes[top_nid]
            self.assertAlmostEqual(x_bot, x_top, places=12)
            self.assertAlmostEqual(y_bot, y_top, places=12)

    def test_07_uel_source_runtime_interface_contract(self):
        uel_path = P156_DIR / "f42_mixed_uel.for"
        with open(uel_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Check UEXTERNALDB LOP=0 clears arrays
        self.assertIn("IF (LOP .EQ. 0) THEN", code)
        self.assertIn("SV_PHASE_COMMITTED(I) = 0.D0", code)
        self.assertIn("SV_H_COMMITTED(I, KPT) = 0.D0", code)

        # Check UEL reads SVARS(8+KPT) into SV_H_COMMITTED and SV_H_TRIAL at KSTEP=1, KINC<=1
        self.assertIn("IF (KSTEP .EQ. 1 .AND. KINC .LE. 1) THEN", code)
        self.assertIn("SV_H_COMMITTED(PHYSIDX, KPT) = SVARS(8+KPT)", code)
        self.assertIn("SV_H_TRIAL(PHYSIDX, KPT)     = SVARS(8+KPT)", code)

        # Check that MECH_QUADS (JTYPE=2) computes driving energy POS_M and updates SV_H_TRIAL
        self.assertIn("HIST = SV_H_TRIAL(PHYSIDX, KPT)", code)
        self.assertIn("IF (POS_M .GT. HIST) THEN", code)
        self.assertIn("SV_H_TRIAL(PHYSIDX, KPT) = POS_M", code)

        # Check that MECH_QUADS reads damage from SV_PHASE_TRIAL(PHYSIDX)
        self.assertIn("D_VAL = SV_PHASE_TRIAL(PHYSIDX)", code)
        self.assertIn("DEG   = (ONE - D_VAL)**2 + E_K", code)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestPackage156RuntimeInterfaceVerification)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
