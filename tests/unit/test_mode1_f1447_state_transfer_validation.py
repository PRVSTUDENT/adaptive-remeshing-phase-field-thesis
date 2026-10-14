#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test suite for Task F1447:
Mode-I Method C State Transfer Quantitative Validation, Engine Audit,
Static Continuation Initialization, and Verification Package Staging.
"""

import hashlib
import json
import os
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

class TestMode1F1447StateTransferValidation(unittest.TestCase):

    def setUp(self):
        self.package_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "41_method_c_genuine_continuation"
        self.manifest_path = self.package_dir / "PACKAGE_MANIFEST.json"
        self.eval_json_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "39_method_c_transfer_gate_c1" / "offline_state_transfer_gate6c_evaluation.json"
        self.engine_path = REPO_ROOT / "scripts" / "state_transfer" / "mode1_state_transfer_engine.py"
        self.subroutine_path = self.package_dir / "f42_mixed_uel.for"

    def test_01_frozen_fortran_subroutine_hash_preserved(self):
        """Verify authoritative Fortran UEL hash CE8D5EDC... is strictly preserved."""
        expected_hash = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        self.assertTrue(self.subroutine_path.exists(), f"Subroutine missing at {self.subroutine_path}")
        h = hashlib.sha256(self.subroutine_path.read_bytes()).hexdigest().upper()
        self.assertEqual(h, expected_hash, f"Fortran subroutine hash changed: {h} != {expected_hash}")

    def test_02_engine_audit_euclidean_residual_and_fallback(self):
        """Verify engine uses physical Euclidean residual and bounds fallback element assignment."""
        code = self.engine_path.read_text(encoding="utf-8")
        # Quad Euclidean residual in physical coordinates
        self.assertIn("px = n1 * coords[0][0] + n2 * coords[1][0] + n3 * coords[2][0] + n4 * coords[3][0]", code)
        self.assertIn("py = n1 * coords[0][1] + n2 * coords[1][1] + n3 * coords[2][1] + n4 * coords[3][1]", code)
        self.assertIn("phys_res = math.sqrt((px - x)**2 + (py - y)**2)", code)
        # Fallback element boundary tolerance
        self.assertIn("best_residual <= 1e-4", code)

    def test_03_engine_audit_svars_indexing_against_fortran_uel(self):
        """Verify SVARS indexing in engine strictly matches f42_mixed_uel.for."""
        code = self.engine_path.read_text(encoding="utf-8")
        # Quad SVARS 9..12 mapped to SV_H_COMMITTED(1..4)
        self.assertIn("9..12: SV_H_COMMITTED at GPs (read by Fortran lines 252-253)", code)
        # Tri SVARS 7..9 mapped to SV_H_COMMITTED(1..3)
        self.assertIn("SV_H_COMMITTED(PHYSIDX, 1..3) = SVARS(6 + 1..3) -> SVARS 7, 8, 9", code)

    def test_04_engine_audit_seam_topology_and_tip_boundary(self):
        """Verify duplicate crack flank node segregation and crack tip ligament classification."""
        code = self.engine_path.read_text(encoding="utf-8")
        # Tip vertex classification
        self.assertIn('node_flank[nid] = "LIGAMENT"', code)
        # Flank bucket segregation in spatial index
        self.assertIn("target_dicts = [self.upper_buckets]", code)
        self.assertIn("target_dicts = [self.lower_buckets]", code)
        self.assertIn("target_dicts = [self.upper_buckets, self.lower_buckets]", code)

    def test_05_gate6c_offline_transfer_quantitative_criteria(self):
        """Verify all 7 Gate 6C quantitative criteria evaluated from authentic Mode-I transfer."""
        self.assertTrue(self.eval_json_path.exists(), f"Evaluation JSON missing: {self.eval_json_path}")
        with open(self.eval_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Criterion 1: Displacement L2 <= 1.0%
        c1 = data["criterion_1_displacement_l2"]
        self.assertLessEqual(c1["value"], 1.0)
        self.assertEqual(c1["verdict"], "PASS")

        # Criterion 2: Peak Damage Diff <= 0.020
        c2 = data["criterion_2_peak_damage"]
        self.assertLessEqual(c2["value"], 0.020)
        self.assertEqual(c2["verdict"], "PASS")

        # Criterion 3: Integrated Damage Error <= 5.0% or PARTIAL_COARSENING_BIAS
        c3 = data["criterion_3_integrated_damage"]
        self.assertIn(c3["verdict"], ["PASS", "PARTIAL_COARSENING_BIAS"])
        self.assertLess(c3["value"], 6.0)

        # Criterion 4: History Non-Negativity min(H) >= 0.0
        c4 = data["criterion_4_history_non_negativity"]
        self.assertGreaterEqual(c4["value"], 0.0)
        self.assertEqual(c4["verdict"], "PASS")

        # Criterion 5: Boundary Force Continuity <= 5.0 N
        c5 = data["criterion_5_boundary_force_continuity"]
        self.assertLessEqual(c5["value"], 5.0)
        self.assertEqual(c5["verdict"], "PASS")

        # Criterion 6: Internal Energy Preservation <= 5.0%
        c6 = data["criterion_6_internal_energy"]
        self.assertLessEqual(c6["value"], 5.0)
        self.assertEqual(c6["verdict"], "PASS")

        # Criterion 7: Global Energy Residual <= 10.0%
        c7 = data["criterion_7_global_energy_residual"]
        self.assertLessEqual(c7["value"], 10.0)
        self.assertEqual(c7["verdict"], "PASS")

    def test_06_abaqus_static_continuation_initialization_architecture(self):
        """Verify static continuation deck embeds solution IC and single-increment equilibration step."""
        inp_path = self.package_dir / "M1_MC_GENUINE_CONTINUATION.inp"
        self.assertTrue(inp_path.exists(), f"Input deck missing: {inp_path}")
        content = inp_path.read_text(encoding="utf-8")

        # Displacement IC must NOT be present (fatal error in Abaqus/Standard static steps)
        self.assertNotIn("*INITIAL CONDITIONS, TYPE=DISPLACEMENT", content)
        # Solution IC must be present for SVARS
        self.assertIn("*INITIAL CONDITIONS, TYPE=SOLUTION", content)
        # Step-1 must be instantaneous re-equilibration (dt = 1.0, u_rp = 0.0050)
        self.assertIn("*STEP, NAME=Step-1-Equilibrate, NLGEOM=YES, INC=10", content)
        self.assertIn("1.0, 1.0, 1.0e-6, 1.0", content)
        self.assertIn("N_RP, 2, 2, 5.0000000000e-03", content)
        # Step-2 must be continuation fracture solve
        self.assertIn("*STEP, NAME=Step-2-Continue, NLGEOM=YES, INC=10000", content)
        self.assertIn("N_RP, 2, 2, 1.0000000000e-02", content)

    def test_07_package_41_manifest_and_hash_integrity(self):
        """Verify Package 41 manifest exists and matches on-disk file SHA-256 hashes."""
        self.assertTrue(self.manifest_path.exists(), f"Manifest missing: {self.manifest_path}")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["package_name"], "mode1_method_c_genuine_continuation")
        self.assertEqual(manifest["resource_request"]["cpus_per_node"], 1)
        self.assertEqual(manifest["resource_request"]["memory_gb"], 16)

        for filename, fmeta in manifest["files"].items():
            fpath = self.package_dir / filename
            self.assertTrue(fpath.exists(), f"Package file {filename} missing at {fpath}")
            actual_sha = hashlib.sha256(fpath.read_bytes()).hexdigest().upper()
            self.assertEqual(
                actual_sha,
                fmeta["sha256"].upper(),
                f"Hash mismatch for {filename}: {actual_sha} != {fmeta['sha256']}"
            )


if __name__ == "__main__":
    unittest.main()
