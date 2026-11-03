#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package171_r3_c6_coupled_driver_readiness.py
==================================================
Comprehensive regression test suite for Package 171-R3:
C6 Stage C3-0 Genuine Coupled PDAS Re-Equilibration with Post-Update KKT, Coupled-Field Consistency,
and Gated Checkpointing (omega_d = 0.5).
Task: F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION -> Successor Execution Qualification
Protocol Version: 2

Tests:
1. test_c6_mesh_topology_and_uel_conformance
2. test_transferred_state_non_zero_integrity
3. test_frozen_uel_sha256_preservation
4. test_r3_driver_initialization_and_damping_parameter
5. test_r3_batch_authorization_and_manifest_hashes
6. test_r3_runtime_closure_and_source_dependencies
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
from scripts.state_transfer.driver_package171_r3_c6_coupled_pdas import (
    Package171R3C6PDASDriver,
    DONOR_REFERENCE_FORCE_KN,
    DONOR_REFERENCE_TOTAL_ENERGY_KNMM,
    DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
    DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
)

PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r3_c3_0_reequilibration"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


class TestPackage171R3DriverReadiness(unittest.TestCase):
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
        """Verify transferred damage and history fields are authentically non-zero and bounded."""
        d_csv = PKG_DIR / "nodal_phase_field_initial.csv"
        self.assertTrue(d_csv.is_file(), "nodal_phase_field_initial.csv missing")
        with open(d_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            d_vals = {int(r[0]): float(r[1]) for r in reader}

        self.assertEqual(len(d_vals), 15559, f"Expected 15,559 damage entries, got {len(d_vals)}")
        min_d = min(d_vals.values())
        max_d = max(d_vals.values())
        self.assertGreater(min_d, 0.0, f"Damage must be strictly positive: {min_d}")
        self.assertGreater(max_d, 0.5, f"Damage peak must exceed 0.5 (got {max_d})")
        self.assertLessEqual(max_d, 1.0, f"Damage peak must not exceed 1.0: {max_d}")

        bounds_csv = PKG_DIR / "d_lower_bounds.csv"
        self.assertTrue(bounds_csv.is_file(), "d_lower_bounds.csv missing")
        with open(bounds_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            h_vals = []
            for r in reader:
                for g in range(1, 5):
                    h_vals.append(float(r[4 + g]))

        self.assertEqual(len(h_vals), 15252 * 4, f"Expected 61,008 GP history entries, got {len(h_vals)}")
        min_h = min(h_vals)
        self.assertGreater(min_h, 0.0, f"History must be strictly positive: {min_h}")

    def test_frozen_uel_sha256_preservation(self):
        """Verify frozen production UEL is byte-for-byte identical to authoritative hash."""
        uel_path = PKG_DIR / "f42_mixed_uel.for"
        self.assertTrue(uel_path.is_file(), "f42_mixed_uel.for missing from package")
        uel_hash = sha256_file(uel_path)
        self.assertEqual(uel_hash, FROZEN_UEL_HASH, f"UEL hash mismatch! Expected {FROZEN_UEL_HASH}, got {uel_hash}")

    def test_r3_driver_initialization_and_damping_parameter(self):
        """Verify Package171R3C6PDASDriver loads and verifies transferred state with omega_d = 0.5."""
        driver = Package171R3C6PDASDriver(
            package=PKG_DIR,
            output=PKG_DIR / "temp_test_output",
            extractor=REPO_ROOT / "scripts/validation/extract_package148_iteration.py",
            memory_gb=16,
            timeout=100,
            max_outer=100,
            damping_omega_d=0.5
        )
        driver.load()
        self.assertEqual(len(driver.d0), 15559)
        self.assertEqual(len(driver.h0), 15252 * 4)
        self.assertEqual(len(driver.u0), 15559)
        self.assertAlmostEqual(driver.damping_omega_d, 0.5)
        self.assertAlmostEqual(driver.target_uy, 0.0018703125442191958, places=12)

    def test_r3_batch_authorization_and_manifest_hashes(self):
        """Verify PACKAGE_MANIFEST.json and M1_C6_PACKAGE171_R3_AUTHORIZATION.json hashes match files on disk."""
        manifest_p = PKG_DIR / "PACKAGE_MANIFEST.json"
        with open(manifest_p, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        for fname, expected_hash in manifest["files"].items():
            actual_hash = sha256_file(PKG_DIR / fname).lower()
            self.assertEqual(actual_hash, expected_hash.lower(), f"Manifest hash mismatch for {fname}")

        auth_p = PKG_DIR / "M1_C6_PACKAGE171_R3_AUTHORIZATION.json"
        with open(auth_p, "r", encoding="utf-8") as f:
            auth = json.load(f)

        for fname, expected_hash in auth["files"].items():
            actual_hash = sha256_file(PKG_DIR / fname).lower()
            self.assertEqual(actual_hash, expected_hash.lower(), f"Auth hash mismatch for {fname}")

    def test_r3_runtime_closure_and_source_dependencies(self):
        """Verify M1_C6_PACKAGE171_R3_AUTHORIZATION.json includes driver_package171_r3_c6_coupled_pdas.py and transitive dependencies."""
        auth_p = PKG_DIR / "M1_C6_PACKAGE171_R3_AUTHORIZATION.json"
        with open(auth_p, "r", encoding="utf-8") as f:
            auth = json.load(f)

        rsh = auth.get("runtime_source_hashes", {})
        self.assertIn("scripts/state_transfer/driver_package171_r3_c6_coupled_pdas.py", rsh)
        r3_driver_hash = rsh["scripts/state_transfer/driver_package171_r3_c6_coupled_pdas.py"]
        self.assertEqual(r3_driver_hash, sha256_file(REPO_ROOT / "scripts/state_transfer/driver_package171_r3_c6_coupled_pdas.py"))

    def test_pbs_submission_script_structure(self):
        """Verify PBS script specifies 1 CPU, 16 GB, 8h, entry_imfdfkmq, and invokes driver with omega_d = 0.5."""
        pbs_path = PKG_DIR / "submit_M1_C6_P171_R3_C3_0.pbs"
        self.assertTrue(pbs_path.is_file())
        text = pbs_path.read_text(encoding="utf-8")

        self.assertIn("#PBS -N M1_C6_P171_R3_C3_0", text)
        self.assertIn("#PBS -l select=1:ncpus=1:mem=16gb", text)
        self.assertIn("#PBS -l walltime=08:00:00", text)
        self.assertIn("#PBS -q entry_imfdfkmq", text)
        self.assertIn("driver_package171_r3_c6_coupled_pdas.py", text)
        self.assertIn("--damping-omega-d 0.5", text)
        self.assertIn("--max-outer 100", text)


if __name__ == "__main__":
    unittest.main()
