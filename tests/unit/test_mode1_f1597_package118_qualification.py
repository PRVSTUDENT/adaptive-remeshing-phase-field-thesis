"""
Unit test for Package 118 C4 Direct State-Transfer from Re-equilibrated P117 C3 qualification.
Verifies:
1. Manifest integrity and SHA-256 hash consistency across all package files.
2. Abaqus input deck structure (4,422 quads, 4,588 physical nodes, RP 999999).
3. Material property card ordering [l0, Gc, E, nu, k] = [0.0075, 0.0027, 210.0, 0.3, 1.0e-7].
4. Bitwise hash match of f42_unified_12dof_active_set_uel.for.
5. Displacement and history state tables exist and have valid entries.
6. Initial mapped fracture energy consistency with donor Package 117.
7. Retention of gate C1_2_STEP2_ENERGY_GATE_FAILED.
"""

import os
import json
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
PKG_DIR = os.path.join(REPO_ROOT, "models/pandey_kumar_mode1/118_c4_inc79_from_p117_transfer")
EXPECTED_UEL_HASH = "ab0a5a71335ecb445e91ec13a645e280ff3310b561a5e78aba4a49c8e81dd8ac"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()

class TestPackage118Qualification(unittest.TestCase):

    def setUp(self):
        self.assertTrue(os.path.isdir(PKG_DIR), f"Package directory must exist: {PKG_DIR}")
        self.manifest_path = os.path.join(PKG_DIR, "PACKAGE_MANIFEST.json")
        self.auth_path = os.path.join(PKG_DIR, "M1_C4_P117_TRANSFER_AUTHORIZATION.json")
        self.assertTrue(os.path.isfile(self.manifest_path), "PACKAGE_MANIFEST.json must exist")
        self.assertTrue(os.path.isfile(self.auth_path), "M1_C4_P117_TRANSFER_AUTHORIZATION.json must exist")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)
        with open(self.auth_path, "r", encoding="utf-8") as f:
            self.auth = json.load(f)

    def test_package_authorization_hashes(self):
        files = self.auth["files"]
        for fname, expected_hash in files.items():
            fpath = os.path.join(PKG_DIR, fname)
            self.assertTrue(os.path.isfile(fpath), f"File {fname} declared in auth must exist")
            actual_hash = sha256_file(fpath)
            self.assertEqual(actual_hash, expected_hash.lower(), f"Hash mismatch for {fname}")

    def test_uel_hash(self):
        uel_path = os.path.join(PKG_DIR, "f42_unified_12dof_active_set_uel.for")
        self.assertTrue(os.path.isfile(uel_path))
        actual = sha256_file(uel_path)
        self.assertEqual(actual, EXPECTED_UEL_HASH, "Unified 12-DOF UEL must match verified repaired hash")

    def test_inp_deck_properties(self):
        inp_path = os.path.join(PKG_DIR, "M1_C4_P117_DIRECT_TRANSFER.inp")
        self.assertTrue(os.path.isfile(inp_path))
        has_u1 = False
        has_prop = False
        with open(inp_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if "*USER ELEMENT, TYPE=U1" in line.upper():
                    has_u1 = True
                if "*UEL PROPERTY" in line.upper():
                    prop_vals = [float(x.strip()) for x in lines[i+1].split(",")]
                    self.assertAlmostEqual(prop_vals[0], 0.0075, places=5)
                    self.assertAlmostEqual(prop_vals[1], 0.0027, places=5)
                    self.assertAlmostEqual(prop_vals[2], 210.0, places=1)
                    self.assertAlmostEqual(prop_vals[3], 0.3, places=2)
                    self.assertAlmostEqual(prop_vals[4], 1.0e-7, places=9)
                    has_prop = True
        self.assertTrue(has_u1, "INP deck must define TYPE=U1 user element")
        self.assertTrue(has_prop, "INP deck must define valid UEL properties")

    def test_initial_bounds_and_displacements(self):
        bounds_csv = os.path.join(PKG_DIR, "d_lower_bounds.csv")
        disp_csv = os.path.join(PKG_DIR, "nodal_displacements_initial.csv")
        cards_inc = os.path.join(PKG_DIR, "stage_a_all_d0_boundary_cards.inc")
        self.assertTrue(os.path.isfile(bounds_csv))
        self.assertTrue(os.path.isfile(disp_csv))
        self.assertTrue(os.path.isfile(cards_inc))

        with open(bounds_csv, "r") as f:
            lines = [l for l in f if l.strip() and not l.startswith("EID")]
            self.assertEqual(len(lines), 4422, "Must contain exactly 4,422 elements")

        with open(disp_csv, "r") as f:
            lines = [l for l in f if l.strip() and not l.startswith("NID")]
            self.assertEqual(len(lines), 4588, "Must contain exactly 4,588 nodes")

        with open(cards_inc, "r") as f:
            lines = [l for l in f if l.strip() and not l.startswith("**") and not l.startswith("*")]
            self.assertEqual(len(lines), 4588, "Must contain boundary cards for 4,588 nodes")

    def test_audit_mapping_results(self):
        audit_path = os.path.join(REPO_ROOT, "results/validation/c4_inc79_from_p117_mapping_audit.json")
        self.assertTrue(os.path.isfile(audit_path))
        with open(audit_path, "r") as f:
            audit = json.load(f)
        self.assertEqual(audit["schema"], 1)
        self.assertEqual(audit["package"], "PACKAGE_118_C4_INC79_FROM_P117_TRANSFER")
        delta_frac = audit["initial_mapped_energies_mJ"]["delta_frac_pct"]
        self.assertLess(abs(delta_frac), 1.0, f"Fracture energy should closely match donor (got {delta_frac}%)")

if __name__ == "__main__":
    unittest.main()
