#!/usr/bin/env python3
"""
Unit test suite for Stage 15B: Mode-II Paper-Grounded UEL Preanalysis
Governing Reference: Pandey & Kumar (2025) CMES, Section 4.2, Figs. 6b, 12b.
"""

import os
import unittest
import hashlib

class TestStage15BMode2UelPreanalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cls.pkg_dir = os.path.join(cls.repo_root, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis")
        cls.inp_path = os.path.join(cls.pkg_dir, "Job-1_UEL.inp")
        cls.for_path = os.path.join(cls.pkg_dir, "f42_mixed_uel.for")
        cls.manifest_path = os.path.join(cls.pkg_dir, "PACKAGE_MANIFEST.json")

    def test_package_files_exist(self):
        """Verify all mandatory package files exist in package 06."""
        self.assertTrue(os.path.exists(self.inp_path), "Job-1_UEL.inp missing")
        self.assertTrue(os.path.exists(self.for_path), "f42_mixed_uel.for missing")
        self.assertTrue(os.path.exists(self.manifest_path), "PACKAGE_MANIFEST.json missing")

    def test_fortran_subroutine_hash(self):
        """Verify authoritative f42_mixed_uel.for SHA-256 hash."""
        h = hashlib.sha256()
        with open(self.for_path, "rb") as f:
            h.update(f.read())
        expected = "fa48cb4d38bac9d772ff5ed1465175cef363b1ab6fabe2cffebbdf11d3e2a854"
        self.assertEqual(h.hexdigest().lower(), expected.lower(), "f42_mixed_uel.for hash mismatch")

    def test_deck_mesh_and_layered_structure(self):
        """Verify physical element count (2960), node count (3036), and 3-layer architecture."""
        nodes = set()
        u1_count = 0
        u2_count = 0
        u3_count = 0
        u4_count = 0
        cpe4_count = 0
        cpe3_count = 0
        
        in_node = False
        in_elem = False
        elem_type = None

        with open(self.inp_path, "r") as f:
            for line in f:
                l = line.strip()
                if not l or l.startswith("**"):
                    continue
                if l.startswith("*"):
                    lower = l.lower()
                    if lower.startswith("*node") and not lower.startswith("*node output") and not lower.startswith("*node print"):
                        in_node = True
                        in_elem = False
                        continue
                    elif lower.startswith("*element") and not lower.startswith("*element output"):
                        in_node = False
                        in_elem = True
                        for t in ["u1", "u2", "u3", "u4", "cpe4", "cpe3"]:
                            if ("type=" + t) in lower:
                                elem_type = t.upper()
                                break
                        continue
                    else:
                        in_node = False
                        in_elem = False
                        continue

                if in_node:
                    nid = int(l.split(",")[0])
                    nodes.add(nid)
                elif in_elem:
                    if elem_type == "U1": u1_count += 1
                    elif elem_type == "U2": u2_count += 1
                    elif elem_type == "U3": u3_count += 1
                    elif elem_type == "U4": u4_count += 1
                    elif elem_type == "CPE4": cpe4_count += 1
                    elif elem_type == "CPE3": cpe3_count += 1

        self.assertEqual(len(nodes) - 1, 3036, "Physical nodes count mismatch (excluding RP 999999)")
        self.assertEqual(u1_count, 2860, "U1 quad count mismatch")
        self.assertEqual(u3_count, 100, "U3 tri count mismatch")
        self.assertEqual(u1_count + u3_count, 2960, "Layer 1 physical elements mismatch")
        self.assertEqual(u2_count + u4_count, 2960, "Layer 2 physical elements mismatch")
        self.assertEqual(cpe4_count + cpe3_count, 2960, "Layer 3 physical elements mismatch")

    def test_abi_contract_and_property_alignment(self):
        """Verify UEL property contract matches ABI (l0=0.015, Gc=0.0027, E=210, nu=0.3, k=1e-7, N_phys=2960)."""
        uel_prop_found = False
        with open(self.inp_path, "r") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if "*uel property" in line.lower() and "phase_elem" in line.lower():
                prop_line = lines[i+1].strip()
                uel_prop_found = True
                parts = [float(p.strip()) for p in prop_line.split(",")]
                self.assertAlmostEqual(parts[0], 0.015, msg="l0 mismatch")
                self.assertAlmostEqual(parts[1], 0.0027, msg="Gc mismatch")
                self.assertAlmostEqual(parts[2], 210.0, msg="E mismatch")
                self.assertAlmostEqual(parts[3], 0.3, msg="nu mismatch")
                self.assertAlmostEqual(parts[4], 1.0e-7, msg="k mismatch")
                self.assertAlmostEqual(parts[5], 2960.0, msg="N_phys mismatch")
                break
        self.assertTrue(uel_prop_found, "UEL Property card for PHASE_ELEM not found")

    def test_miseseri_output_request(self):
        """Verify MISESERI is requested on All_elem."""
        miseseri_requested = False
        with open(self.inp_path, "r") as f:
            content = f.read()
        self.assertIn("MISESERI", content, "MISESERI output request missing")
        self.assertIn("elset=All_elem", content, "All_elem output set missing")

if __name__ == "__main__":
    unittest.main()
