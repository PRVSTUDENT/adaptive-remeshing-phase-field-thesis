#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package171_r4_c6_coupled_driver_readiness.py
==================================================
Comprehensive regression test suite for Package 171-R4:
C6 Stage C3-0 Genuine Coupled PDAS Re-Equilibration with Post-Update KKT, Joint Displacement/History
Consistency Gates, and Gated Checkpointing (omega_d = 0.5).
Task: F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION -> R4 Candidate Qualification
Protocol Version: 2

Tests:
1. test_c6_mesh_topology_and_uel_conformance
2. test_transferred_state_non_zero_integrity
3. test_frozen_uel_sha256_preservation
4. test_r4_driver_initialization_and_damping_parameter
5. test_r4_batch_authorization_and_manifest_hashes
6. test_r4_runtime_closure_and_source_dependencies
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
from scripts.state_transfer.driver_package171_r4_c6_coupled_pdas import (
    Package171R4C6PDASDriver,
    DONOR_REFERENCE_FORCE_KN,
    DONOR_REFERENCE_TOTAL_ENERGY_KNMM,
    DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
    DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
)

PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r4_c3_0_reequilibration"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


class TestPackage171R4DriverReadiness(unittest.TestCase):
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
        self.assertEqual(uel_hash, FROZEN_UEL_HASH, f"Frozen UEL hash violation! Expected {FROZEN_UEL_HASH}, got {uel_hash}")

    def test_r4_driver_initialization_and_damping_parameter(self):
        """Verify Package 171-R4 driver initializes correctly with omega_d = 0.5."""
        out_dir = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r4_c3_0_reequilibration/test_out"
        driver = Package171R4C6PDASDriver(
            package=PKG_DIR,
            output=out_dir,
            extractor=REPO_ROOT / "scripts/validation/extract_package148_iteration.py",
            damping_omega_d=0.5
        )
        self.assertEqual(driver.damping_omega_d, 0.5)
        self.assertEqual(driver.max_outer, 100)
        self.assertEqual(driver.memory_gb, 16)

    def test_r4_batch_authorization_and_manifest_hashes(self):
        """Verify PACKAGE_MANIFEST.json and M1_C6_PACKAGE171_R4_AUTHORIZATION.json integrity."""
        auth_p = PKG_DIR / "M1_C6_PACKAGE171_R4_AUTHORIZATION.json"
        self.assertTrue(auth_p.is_file(), "Authorization manifest missing")
        auth = json.loads(auth_p.read_text(encoding="utf-8"))

        manifest_p = PKG_DIR / "PACKAGE_MANIFEST.json"
        self.assertTrue(manifest_p.is_file(), "Package manifest missing")
        manifest = json.loads(manifest_p.read_text(encoding="utf-8"))

        # Verify all files declared in PACKAGE_MANIFEST exist and have matching lower sha256
        for fname, declared_hash in manifest["files"].items():
            fpath = PKG_DIR / fname
            self.assertTrue(fpath.is_file(), f"Declared package file missing: {fname}")
            actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
            self.assertEqual(actual_hash, declared_hash, f"Hash mismatch for {fname}")

        # Verify authorization job definition
        self.assertEqual(len(auth["jobs"]), 1)
        job = auth["jobs"][0]
        self.assertEqual(job["id"], "M1_C6_P171_R4_C3_0")
        self.assertEqual(job["cpus"], 1)
        self.assertEqual(job["memory_gb"], 16)
        self.assertEqual(job["walltime_hours"], 8)
        self.assertEqual(job["queue"], "entry_imfdfkmq")

    def test_r4_runtime_closure_and_source_dependencies(self):
        """Verify all runtime source dependencies declared in authorization exist and match hashes."""
        auth_p = PKG_DIR / "M1_C6_PACKAGE171_R4_AUTHORIZATION.json"
        auth = json.loads(auth_p.read_text(encoding="utf-8"))
        for rel_path, declared_hash in auth["runtime_source_hashes"].items():
            full_path = REPO_ROOT / rel_path
            self.assertTrue(full_path.is_file(), f"Runtime dependency missing: {rel_path}")
            actual_hash = sha256_file(full_path)
            self.assertEqual(actual_hash, declared_hash, f"Runtime hash mismatch for {rel_path}")

    def test_pbs_submission_script_structure(self):
        """Verify submit_M1_C6_P171_R4_C3_0.pbs conforms to single-rank serial policy and notification hooks."""
        pbs_p = PKG_DIR / "submit_M1_C6_P171_R4_C3_0.pbs"
        self.assertTrue(pbs_p.is_file(), "PBS script missing")
        content = pbs_p.read_text(encoding="utf-8")

        self.assertIn("#PBS -N M1_C6_P171_R4_C3_0", content)
        self.assertIn("#PBS -l select=1:ncpus=1:mem=16gb", content)
        self.assertIn("#PBS -l walltime=08:00:00", content)
        self.assertIn("#PBS -q entry_imfdfkmq", content)
        self.assertIn("job_notifications.sh", content)
        self.assertIn("notify_start", content)
        self.assertIn("driver_package171_r4_c6_coupled_pdas.py", content)
        self.assertIn("--damping-omega-d 0.5", content)


if __name__ == "__main__":
    unittest.main()
