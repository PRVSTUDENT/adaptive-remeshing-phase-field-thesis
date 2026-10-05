#!/usr/bin/env python3
"""
Unit tests for Stage 15C Mode-II localization, sweep evaluation, and Job-2 deck builder.
"""

import os
import sys
import unittest
import math
import tempfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts/validation')))

from build_mode2_adapted_job2_deck import convert_raw_to_mode2_job2_deck, write_wrapped_nset
from evaluate_mode2_stage15c_localization_and_sweep import parse_inp_mesh, DIGITIZED_FIG6B, DIGITIZED_FIG12B

class TestStage15CMode2(unittest.TestCase):
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
        self.assertIn("*USER ELEMENT, TYPE=U1", content)
        self.assertIn("*USER ELEMENT, TYPE=U2", content)
        self.assertIn("*USER ELEMENT, TYPE=U3", content)
        self.assertIn("*USER ELEMENT, TYPE=U4", content)
        self.assertIn("*ELEMENT, TYPE=CPE4", content)
        self.assertIn("*ELEMENT, TYPE=CPE3", content)

        # Check UMAT material constant: must be 1.0e-11 (infinitesimal companion stiffness)
        self.assertIn("*USER MATERIAL, CONSTANTS=3\n1.0e-11, 0.3, 2.", content)

        # Check UEL Property cards: must have physical E = 210.0
        self.assertIn("*UEL PROPERTY, ELSET=PHASE_ELEM\n0.015, 0.0027, 210.0, 0.3, 1.0e-7, 2.", content)
        self.assertIn("*UEL PROPERTY, ELSET=MECH_ELEM\n0.015, 0.0027, 210.0, 0.3, 1.0e-7, 2.", content)

        # Check coupling equation to RP 999999
        self.assertIn("999999", content)
        self.assertIn("*EQUATION", content)

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

if __name__ == '__main__':
    unittest.main()
