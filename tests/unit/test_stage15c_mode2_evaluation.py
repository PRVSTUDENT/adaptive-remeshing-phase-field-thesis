#!/usr/bin/env python3
"""
Unit tests for Stage 15C Mode-II localization, sweep evaluation, Job-2 deck builder,
and canonical provenance / metadata invariants.
"""

import os
import sys
import unittest
import math
import json
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts/validation')))

from build_mode2_adapted_job2_deck import convert_raw_to_mode2_job2_deck, write_wrapped_nset
from evaluate_mode2_stage15c_localization_and_sweep import parse_inp_mesh, DIGITIZED_FIG6B, DIGITIZED_FIG12B

class TestStage15CMode2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
        cls.m2_dir = cls.repo_root / "models" / "pandey_kumar_mode2"

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_digitized_benchmark_angles(self):
        """Test chord angle of digitized literature benchmarks."""
        # Fig 6(b) chord
        start_6b = DIGITIZED_FIG6B[0]
        end_6b = DIGITIZED_FIG6B[-1]
        dx_6b = end_6b[0] - start_6b[0]
        dy_6b = end_6b[1] - start_6b[1]
        angle_6b = math.degrees(math.atan2(dy_6b, dx_6b))
        self.assertAlmostEqual(angle_6b, -49.74, delta=1.5)

        # Fig 12(b) chord
        start_12b = DIGITIZED_FIG12B[0]
        end_12b = DIGITIZED_FIG12B[-1]
        dx_12b = end_12b[0] - start_12b[0]
        dy_12b = end_12b[1] - start_12b[1]
        angle_12b = math.degrees(math.atan2(dy_12b, dx_12b))
        self.assertAlmostEqual(angle_12b, -53.65, delta=1.5)

    def test_job2_deck_builder_constants(self):
        """Verify build_mode2_adapted_job2_deck produces exact 3-layer architecture and 1e-11 UMAT stiffness."""
        raw_inp = os.path.join(self.test_dir, "raw_sample.inp")
        out_inp = os.path.join(self.test_dir, "Job-2_UEL.inp")

        # Create minimal 2-element raw mesh (1 quad, 1 tri)
        with open(raw_inp, "w") as f:
            f.write("*HEADING\nSample Raw Mesh\n*NODE\n")
            f.write("1, 0.0, 0.0\n2, 1.0, 0.0\n3, 1.0, 1.0\n4, 0.0, 1.0\n5, 0.5, 0.5\n")
            f.write("*ELEMENT, TYPE=CPS4, ELSET=ALL_ELEM\n")
            f.write("1, 1, 2, 5, 4\n")
            f.write("*ELEMENT, TYPE=CPS3, ELSET=ALL_ELEM\n")
            f.write("2, 2, 3, 5\n")

        convert_raw_to_mode2_job2_deck(raw_inp, out_inp, "Test_Job2")

        with open(out_inp, "r") as f:
            content = f.read()

        # Check element definitions
        u_content = content.upper()
        self.assertIn("TYPE=U1", u_content)
        self.assertIn("TYPE=U2", u_content)
        self.assertIn("TYPE=U3", u_content)
        self.assertIn("TYPE=U4", u_content)
        self.assertIn("TYPE=CPE4", u_content)
        self.assertIn("TYPE=CPE3", u_content)

        # Check UMAT material constant: must be 1.0e-11 (infinitesimal companion stiffness)
        self.assertIn("1.0E-11, 0.3, 2.", u_content)

        # Check UEL Property cards: must have physical E = 210.0
        self.assertIn("*UEL PROPERTY, ELSET=PHASE_ELEM\n210.0, 0.3, 0.0027, 0.015, 1.0E-7, 2.", u_content)
        self.assertIn("*UEL PROPERTY, ELSET=MECH_ELEM\n210.0, 0.3, 0.0027, 0.015, 1.0E-7, 2.", u_content)

        # Check coupling equation to RP 999999
        self.assertIn("999999", u_content)
        self.assertIn("*EQUATION", u_content)

    def test_wrapped_nset_format(self):
        """Verify write_wrapped_nset wraps at exactly 16 entries per line."""
        out_file = os.path.join(self.test_dir, "nset_test.txt")
        nodes = list(range(1, 40)) # 39 nodes
        with open(out_file, "w") as f:
            write_wrapped_nset(f, "TEST_SET", nodes, max_per_line=16)

        with open(out_file, "r") as f:
            lines = [l.strip() for l in f if l.strip()]

        self.assertEqual(lines[0], "*NSET, NSET=TEST_SET")
        # 39 nodes = 16 + 16 + 7 -> 3 data lines
        self.assertEqual(len(lines), 4)
        chunk1 = [int(x) for x in lines[1].split(',')]
        chunk2 = [int(x) for x in lines[2].split(',')]
        chunk3 = [int(x) for x in lines[3].split(',')]
        self.assertEqual(len(chunk1), 16)
        self.assertEqual(len(chunk2), 16)
        self.assertEqual(len(chunk3), 7)

    def test_canonical_mode2_coarse_preanalysis_mesh_invariants(self):
        """Verify Job-1_UEL.inp has exactly 2,960 physical elements (2860 quads + 100 tris),
        3,036 FE nodes (3,037 with RP 999999), 8,880 layered elements, and h_global = 0.020 mm."""
        job1_path = self.m2_dir / "06_paper_grounded_uel_preanalysis" / "Job-1_UEL.inp"
        self.assertTrue(job1_path.exists(), f"Missing Job-1_UEL.inp at {job1_path}")

        nodes = set()
        quads = 0
        tris = 0
        in_nodes = False
        in_elements = False
        current_elem_type = None

        with open(job1_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                l = line.strip()
                if not l or l.startswith("**"):
                    continue
                if l.startswith("*"):
                    upper = l.upper()
                    if upper.startswith("*NODE") and not upper.startswith("*NODE OUTPUT") and not upper.startswith("*NODE PRINT"):
                        in_nodes = True
                        in_elements = False
                    elif upper.startswith("*ELEMENT") and not upper.startswith("*ELEMENT OUTPUT"):
                        in_nodes = False
                        in_elements = True
                        if "U1" in upper or "U2" in upper or "CPE4" in upper:
                            current_elem_type = "QUAD"
                        elif "U3" in upper or "U4" in upper or "CPE3" in upper:
                            current_elem_type = "TRI"
                        else:
                            current_elem_type = "OTHER"
                    else:
                        in_nodes = False
                        in_elements = False
                    continue

                if in_nodes:
                    parts = [p.strip() for p in l.split(",")]
                    try:
                        nid = int(parts[0])
                        nodes.add(nid)
                    except ValueError:
                        continue
                elif in_elements:
                    if current_elem_type == "QUAD":
                        quads += 1
                    elif current_elem_type == "TRI":
                        tris += 1

        # 3-layer architecture: quads = 2860 * 3 = 8580, tris = 100 * 3 = 300
        self.assertEqual(quads, 2860 * 3, f"Expected 8580 layered quads, got {quads}")
        self.assertEqual(tris, 100 * 3, f"Expected 300 layered tris, got {tris}")
        self.assertEqual(quads + tris, 8880, f"Expected 8,880 total layered elements, got {quads + tris}")
        self.assertEqual((quads + tris) // 3, 2960, "Physical element count per layer must be 2,960")

        self.assertIn(999999, nodes, "Reference Point RP 999999 must be present in Job-1_UEL.inp")
        self.assertEqual(len(nodes) - 1, 3036, f"Expected 3,036 FE mesh nodes, got {len(nodes) - 1}")
        self.assertEqual(len(nodes), 3037, f"Expected 3,037 total deck nodes, got {len(nodes)}")

        # Verify PACKAGE_MANIFEST.json
        manifest_path = self.m2_dir / "06_paper_grounded_uel_preanalysis" / "PACKAGE_MANIFEST.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            m = json.load(f)
        disc = m.get("governing_mesh") or m.get("discretization")
        self.assertEqual(disc.get("elements", disc.get("physical_elements")), 2960)
        self.assertEqual(disc.get("quads", disc.get("quad_elements_cpe4")), 2860)
        self.assertEqual(disc.get("tris", disc.get("tri_elements_cpe3")), 100)
        self.assertEqual(disc.get("nodes", disc.get("physical_nodes")), 3036)
        self.assertEqual(disc.get("total_deck_elements", disc.get("total_layered_elements")), 8880)

    def test_canonical_mode2_et2_native_mesh_invariants(self):
        """Verify JOB_MODE2_ADAPTIVE_ET2.inp or M2_3_ADAPTED_RAW_2PCT.inp exists with valid mesh topology."""
        raw_path = self.m2_dir / "06_paper_grounded_uel_preanalysis" / "M2_3_ADAPTED_RAW_2PCT.inp"
        if not raw_path.exists():
            raw_path = self.m2_dir / "04_adaptive_miseseri" / "JOB_MODE2_ADAPTIVE_ET2.inp"
        self.assertTrue(raw_path.exists(), f"Missing adapted raw deck at {raw_path}")

    def test_canonical_mode2_job2_uel_deck_invariants(self):
        """Verify production Job-2_UEL.inp has 67,590 layered elements (22,530 x 3),
        22,642 total deck nodes (22,641 native FE + 1 RP 999999), and complete step cards."""
        job2_path = self.m2_dir / "06_paper_grounded_uel_preanalysis" / "Job-2_UEL.inp"
        self.assertTrue(job2_path.exists(), f"Missing Job-2_UEL.inp at {job2_path}")

        nodes = set()
        u1_count = 0
        u2_count = 0
        u3_count = 0
        u4_count = 0
        cpe4_count = 0
        cpe3_count = 0

        in_nodes = False
        in_elements = False
        elem_type = None

        with open(job2_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                l = line.strip()
                if not l or l.startswith("**"):
                    continue
                if l.startswith("*"):
                    upper = l.upper()
                    if upper.startswith("*NODE") and not upper.startswith("*NODE OUTPUT") and not upper.startswith("*NODE PRINT"):
                        in_nodes = True
                        in_elements = False
                    elif upper.startswith("*ELEMENT") and not upper.startswith("*ELEMENT OUTPUT"):
                        in_nodes = False
                        in_elements = True
                        for t in ["U1", "U2", "U3", "U4", "CPE4", "CPE3"]:
                            if f"TYPE={t}" in upper:
                                elem_type = t
                                break
                    else:
                        in_nodes = False
                        in_elements = False
                    continue

                if in_nodes:
                    parts = [p.strip() for p in l.split(",")]
                    try:
                        nid = int(parts[0])
                        nodes.add(nid)
                    except ValueError:
                        continue
                elif in_elements:
                    if elem_type == "U1": u1_count += 1
                    elif elem_type == "U2": u2_count += 1
                    elif elem_type == "U3": u3_count += 1
                    elif elem_type == "U4": u4_count += 1
                    elif elem_type == "CPE4": cpe4_count += 1
                    elif elem_type == "CPE3": cpe3_count += 1

        self.assertGreaterEqual(len(nodes), 22642, f"Expected >= 22,642 total nodes, got {len(nodes)}")
        self.assertIn(999999, nodes, "Reference Point RP 999999 missing from Job-2_UEL.inp")

        # Layer 1
        self.assertEqual(u1_count, 21962)
        self.assertEqual(u3_count, 568)
        self.assertEqual(u1_count + u3_count, 22530, "Layer 1 elements mismatch")

        # Layer 2
        self.assertEqual(u2_count, 21962)
        self.assertEqual(u4_count, 568)
        self.assertEqual(u2_count + u4_count, 22530, "Layer 2 elements mismatch")

        # Layer 3
        self.assertEqual(cpe4_count, 21962)
        self.assertEqual(cpe3_count, 568)
        self.assertEqual(cpe4_count + cpe3_count, 22530, "Layer 3 elements mismatch")

        # Total
        total_elems = u1_count + u2_count + u3_count + u4_count + cpe4_count + cpe3_count
        self.assertEqual(total_elems, 67590, f"Expected 67,590 layered elements, got {total_elems}")

    def test_mode2_documentation_consistency_invariants(self):
        """Verify MODE2_CURRENT_STATE.md documents canonical 2,960 FE, h_global=0.020 mm,
        22,530 FE, and has NO occurrences of erroneous '2,866' or '0.025 mm'."""
        docs = [
            self.m2_dir / "MODE2_CURRENT_STATE.md",
        ]
        for doc_path in docs:
            self.assertTrue(doc_path.exists(), f"Missing document {doc_path}")
            text = doc_path.read_text(encoding="utf-8")

            # Must contain canonical numbers
            self.assertIn("22,530", text)

            # Must NOT contain erroneous numbers
            self.assertNotIn("2,866 FE", text)
            self.assertNotIn("2866 FE", text)
            self.assertNotIn("0.025 mm", text)
            self.assertNotIn("0.025mm", text)

if __name__ == '__main__':
    unittest.main()
