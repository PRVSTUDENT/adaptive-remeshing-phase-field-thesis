#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_c5_input_assembly.py
Mode-I Method C Cycle 2: Unit Regression Test Suite for C5 Input Assembly Verification.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Tests technical verification of the C5 candidate receiver input deck assembly:
1. Disposable fixture generation without modifying production Package 156.
2. U1/U2 element correspondence across all 12,996 quads (1..12996 vs 12997..25992).
3. DOF ordering and boundary card prescriptions (strictly DOF 3,3 for active set; DOFs 1,2 for mechanical).
4. Initial solution-variable serialization (13,278 nodes, 51,984 GPs, 7+8+3 SVARS, H >= 0).
5. Boundary coupling (115 top-edge MPC equations to RP 999999).
6. Slit-face isolation (53 duplicate slit pairs, 0 cross-slit elements, distinct crack tips).
7. Same-load holding conditions (target_uy = 0.0018503125442191958 mm, zero advance).
8. Jacobian positivity (all 51,984 Gauss points det(J) > 0, domain area = 0.01 mm^2).
9. Frozen production UEL SHA-256 bitwise match.
"""

from __future__ import print_function, division
import os
import sys
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.audit_c5_input_assembly import (
    run_c5_input_assembly_audit, compute_c5_jacobian_bounds,
    parse_inp_elements, parse_solution_inc,
    C4_STEP1_ENDPOINT, C4_STEP1_FULL_HISTORY, FROZEN_UEL_SHA256, sha256_file
)
from scripts.state_transfer.c4_to_c5_spatial_mapping import Mesh2D

FIXTURE_DIR = REPO_ROOT / "scratch/c5_fixture_deck"
AUDIT_OUTPUT = REPO_ROOT / "results/validation/c5_input_assembly_audit.json"
P156_PROD_DIR = REPO_ROOT / "models/pandey_kumar_mode1/156_c5_package156_c2_0_re_equilibration"


class TestMode1C5InputAssembly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Record mtime of production Package 156 files before audit to prove no modification
        cls.p156_mtimes = {}
        if P156_PROD_DIR.is_dir():
            for f in P156_PROD_DIR.iterdir():
                if f.is_file():
                    cls.p156_mtimes[f.name] = f.stat().st_mtime_ns

        # Run audit on disposable fixture directory
        cls.summary = run_c5_input_assembly_audit(
            fixture_dir=FIXTURE_DIR,
            output_path=AUDIT_OUTPUT
        )

    def test_01_disposable_fixture_preserves_production_package156(self):
        """Verifies that production Package 156 files were completely untouched."""
        self.assertEqual(self.summary["status"], "C5_INPUT_ASSEMBLY_TECHNICALLY_VERIFIED")
        self.assertTrue(AUDIT_OUTPUT.is_file())
        for fname, mtime in self.p156_mtimes.items():
            curr_file = P156_PROD_DIR / fname
            self.assertTrue(curr_file.is_file(), f"Missing production file: {fname}")
            self.assertEqual(curr_file.stat().st_mtime_ns, mtime, f"Production file was modified: {fname}")

    def test_02_u1_u2_element_correspondence(self):
        """Verifies exact 1:1 connectivity correspondence between U1 (phase) and U2 (mechanical) quads."""
        u1_u2 = self.summary["assembly_verification"]["u1_u2_element_correspondence"]
        self.assertTrue(u1_u2["verified"])
        self.assertEqual(u1_u2["mismatch_count"], 0)
        self.assertEqual(self.summary["receiver_discretization"]["u1_phase_elements"], 12996)
        self.assertEqual(self.summary["receiver_discretization"]["u2_mechanical_elements"], 12996)
        self.assertEqual(self.summary["receiver_discretization"]["element_offset"], 12996)

    def test_03_dof_ordering_and_active_set(self):
        """Verifies DOF ordering: U1=DOF 3, U2=DOFs 1,2, and active set prescribes DOF 3,3."""
        dof_info = self.summary["assembly_verification"]["dof_ordering"]
        self.assertEqual(dof_info["u1_phase_dof"], 3)
        self.assertEqual(dof_info["u2_mechanical_dofs"], [1, 2])
        self.assertEqual(dof_info["active_set_dof_range"], "3,3")
        self.assertEqual(dof_info["dof_violations"], 0)
        self.assertEqual(dof_info["damage_bounds_violations"], 0)
        self.assertEqual(dof_info["active_set_card_count"], 13278)

    def test_04_solution_variable_serialization(self):
        """Verifies 7+8+3 serialization for 12,996 quads and 51,984 GPs with non-negative H."""
        sol = self.summary["assembly_verification"]["solution_variable_serialization"]
        self.assertEqual(sol["element_blocks"], 12996)
        self.assertEqual(sol["svars_per_element"], 18)
        self.assertEqual(sol["total_svars"], 233928)
        self.assertEqual(sol["gauss_points"], 51984)
        self.assertEqual(sol["negative_h_count"], 0)
        self.assertEqual(sol["nan_inf_count"], 0)
        self.assertGreaterEqual(sol["h_min_mpa"], 0.0)
        self.assertLess(sol["h_max_mpa"], 10.0)
        self.assertEqual(sol["nodal_displacements_count"], 13278)
        self.assertEqual(sol["nodal_phase_field_count"], 13278)
        self.assertEqual(sol["d_lower_bounds_count"], 12996)

    def test_05_boundary_coupling_and_mpc(self):
        """Verifies 115 MPC equations coupling all top nodes to RP 999999."""
        bc = self.summary["assembly_verification"]["boundary_coupling"]
        self.assertEqual(bc["top_edge_mpc_equations"], 115)
        self.assertEqual(bc["coupled_top_nodes"], 115)
        self.assertEqual(bc["reference_point_node"], 999999)
        self.assertEqual(bc["mpc_violations"], 0)

    def test_06_slit_face_isolation(self):
        """Verifies 53 duplicate slit pairs, 0 cross-slit elements, and distinct crack tips."""
        slit = self.summary["assembly_verification"]["slit_face_isolation"]
        self.assertEqual(slit["duplicate_slit_pairs"], 53)
        self.assertEqual(slit["cross_slit_elements"], 0)
        self.assertEqual(slit["upper_crack_tip_node"], 6608)
        self.assertEqual(slit["lower_crack_tip_node"], 13278)
        self.assertTrue(slit["independent_crack_tips_verified"])

    def test_07_same_load_holding_conditions(self):
        """Verifies target_uy = 0.0018503125442191958 mm with zero displacement advance."""
        holding = self.summary["assembly_verification"]["same_load_holding_conditions"]
        self.assertTrue(holding["verified"])
        self.assertAlmostEqual(holding["prescribed_uy_mm"], 0.0018503125442191958, places=15)
        self.assertEqual(holding["displacement_advance_increment"], 0.0)
        self.assertEqual(holding["step_name"], "C2_0_REEQUILIBRATION")

    def test_08_jacobian_positivity_and_area(self):
        """Verifies det(J) > 0 for all 51,984 Gauss points and total area = 0.01 mm^2."""
        jac = self.summary["assembly_verification"]["jacobian_positivity"]
        self.assertTrue(jac["all_positive"])
        self.assertGreater(jac["min_det_j"], 0.0)
        self.assertAlmostEqual(jac["total_area_mm2"], 0.010, places=5)

    def test_09_frozen_uel_preservation(self):
        """Verifies frozen production UEL SHA-256 bitwise preservation."""
        uel_info = self.summary["assembly_verification"]["frozen_uel_preservation"]
        self.assertTrue(uel_info["verified"])
        self.assertEqual(uel_info["actual_sha256"], FROZEN_UEL_SHA256)


if __name__ == "__main__":
    unittest.main()
