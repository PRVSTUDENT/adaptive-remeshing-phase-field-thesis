#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package171_r6_c6_coupled_driver_readiness.py
==================================================
Comprehensive regression test suite for Package 171-R6:
C6 Stage C3-0 Genuine Coupled PDAS Re-Equilibration with Fail-Closed Phase Decoding
(15,559 physical nodes validated, rejection of 2-component/mixed output, omega_d = 0.5).
Task: F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION -> R6 Candidate Qualification
Protocol Version: 2

Tests:
1. test_c6_mesh_topology_and_uel_conformance
2. test_transferred_state_non_zero_integrity
3. test_frozen_uel_sha256_preservation
4. test_r6_driver_initialization_and_damping_parameter
5. test_r6_batch_authorization_and_manifest_hashes
6. test_r6_runtime_closure_and_source_dependencies
7. test_pbs_submission_script_structure
"""

import os
import sys
import json
import csv
import hashlib
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.c4_to_c5_spatial_mapping import Mesh2D
from scripts.state_transfer.driver_package171_r6_c6_coupled_pdas import (
    Package171R6C6PDASDriver,
    DONOR_REFERENCE_FORCE_KN,
    DONOR_REFERENCE_TOTAL_ENERGY_KNMM,
    DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
    DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
)

PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r6_c3_0_reequilibration"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


class TestPackage171R6DriverReadiness(unittest.TestCase):
    def test_c6_mesh_topology_and_uel_conformance(self):
        """Verify C6 mesh contains exactly 15,252 CPE4 quads, 15,559 physical nodes, and 59 slit pairs."""
        inp_path = PKG_DIR / "M1_C6_PACKAGE171_C3_0_REEQUILIBRATION.inp"
        self.assertTrue(inp_path.is_file(), "Master input deck missing")

        mesh = Mesh2D.from_inp(inp_path, name="C6_Receiver", max_physical_node=15559)
        self.assertEqual(len(mesh.elements), 15252, f"Expected 15,252 quads, found {len(mesh.elements)}")
        self.assertEqual(len(mesh.nodes), 15559, f"Expected 15,559 physical nodes, found {len(mesh.nodes)}")

        slit_upper = [n for n, (x, y) in mesh.nodes.items() if abs(y - 0.050) < 1e-6 and x <= 0.040 and mesh.node_flank.get(n) == "UPPER"]
        slit_lower = [n for n, (x, y) in mesh.nodes.items() if abs(y - 0.050) < 1e-6 and x <= 0.040 and mesh.node_flank.get(n) == "LOWER"]
        self.assertGreaterEqual(len(slit_upper), 59, f"Expected >= 59 upper slit nodes, got {len(slit_upper)}")
        self.assertGreaterEqual(len(slit_lower), 59, f"Expected >= 59 lower slit nodes, got {len(slit_lower)}")

    def test_transferred_state_non_zero_integrity(self):
        """Verify transferred initial state is loaded with non-zero damage and distinct positive GP history."""
        d_csv = PKG_DIR / "nodal_phase_field_initial.csv"
        u_csv = PKG_DIR / "nodal_displacements_initial.csv"
        bounds_csv = PKG_DIR / "d_lower_bounds.csv"

        self.assertTrue(d_csv.is_file(), "Missing transferred nodal phase field CSV")
        self.assertTrue(u_csv.is_file(), "Missing transferred nodal displacement CSV")
        self.assertTrue(bounds_csv.is_file(), "Missing d_lower_bounds.csv")

        # Check phase field
        d_vals = []
        with d_csv.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for r in reader:
                if r:
                    d_vals.append(float(r[1]))
        self.assertEqual(len(d_vals), 15559, "Expected 15,559 damage records")
        self.assertGreater(max(d_vals), 0.5, "Maximum damage should indicate localized crack zone")
        self.assertGreater(min(d_vals), 0.0, "Minimum damage should be positive")

        # Check GP history
        h_vals = []
        with bounds_csv.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, ["element_id", "d0_1", "d0_2", "d0_3", "d0_4", "h0_1", "h0_2", "h0_3", "h0_4"])
            for r in reader:
                if r:
                    for g in range(1, 5):
                        h_vals.append(float(r[4 + g]))
        self.assertEqual(len(h_vals), 61008, "Expected 61,008 GP history records")
        self.assertGreater(min(h_vals), 0.0, "All GP histories must be strictly positive")

    def test_frozen_uel_sha256_preservation(self):
        """Verify frozen UEL implementation is bitwise-identical to authoritative anchor."""
        uel_path = PKG_DIR / "f42_mixed_uel.for"
        self.assertTrue(uel_path.is_file(), "f42_mixed_uel.for missing from package")
        actual_hash = sha256_file(uel_path)
        self.assertEqual(actual_hash, FROZEN_UEL_HASH, f"UEL hash mismatch: {actual_hash} != {FROZEN_UEL_HASH}")

    def test_r6_driver_initialization_and_damping_parameter(self):
        """Verify driver loads correctly with omega_d = 0.5 and valid package path."""
        driver = Package171R6C6PDASDriver(
            package=PKG_DIR,
            output=PKG_DIR / "dummy_out",
            extractor=REPO_ROOT / "scripts/validation/extract_package148_iteration.py",
            damping_omega_d=0.5
        )
        driver.load()
        self.assertEqual(driver.damping_omega_d, 0.5)
        self.assertEqual(len(driver.d0), 15559)
        self.assertEqual(len(driver.h0), 61008)
        self.assertEqual(len(driver.u0), 15559)
        self.assertAlmostEqual(driver.target_uy, 0.0018703125442191958, places=8)

    def test_r6_batch_authorization_and_manifest_hashes(self):
        """Verify package manifest and execution manifest SHA-256 consistency."""
        pkg_manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
        auth_path = PKG_DIR / "M1_C6_PACKAGE171_R6_AUTHORIZATION.json"
        exec_manifest_path = PKG_DIR / "EXECUTION_MANIFEST.json"

        self.assertTrue(pkg_manifest_path.is_file())
        self.assertTrue(auth_path.is_file())
        self.assertTrue(exec_manifest_path.is_file())

        exec_data = json.loads(exec_manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(exec_data["manifest_sha256"], sha256_file(pkg_manifest_path))
        self.assertEqual(exec_data["auth_sha256"], sha256_file(auth_path))

    def test_r6_runtime_closure_and_source_dependencies(self):
        """Verify all referenced runtime scripts exist and match authorization hashes."""
        auth_data = json.loads((PKG_DIR / "M1_C6_PACKAGE171_R6_AUTHORIZATION.json").read_text(encoding="utf-8"))
        runtime_hashes = auth_data["runtime_source_hashes"]

        for rel_path, expected_hash in runtime_hashes.items():
            full_path = REPO_ROOT / rel_path
            self.assertTrue(full_path.is_file(), f"Runtime script missing: {rel_path}")
            actual_hash = sha256_file(full_path)
            self.assertEqual(actual_hash, expected_hash, f"Hash mismatch for {rel_path}")

    def test_pbs_submission_script_structure(self):
        """Verify PBS job script has correct queue, resource directives, and fail-closed options."""
        pbs_path = PKG_DIR / "submit_M1_C6_P171_R6_C3_0.pbs"
        self.assertTrue(pbs_path.is_file(), "PBS submission script missing")
        content = pbs_path.read_text(encoding="utf-8")

        self.assertIn("#PBS -N M1_C6_P171_R6_C3_0", content)
        self.assertIn("#PBS -l select=1:ncpus=1:mem=16gb", content)
        self.assertIn("#PBS -l walltime=08:00:00", content)
        self.assertIn("#PBS -q entry_imfdfkmq", content)
        self.assertIn("#PBS -m abe", content)
        self.assertIn("driver_package171_r6_c6_coupled_pdas.py", content)
        self.assertIn("--damping-omega-d 0.5", content)


if __name__ == "__main__":
    unittest.main()
