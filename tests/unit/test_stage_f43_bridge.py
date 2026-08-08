#!/usr/bin/env python3
"""
Unit and Integration Tests for Task F43A Stage-C Native-Remeshing Bridge Foundation.
"""

import unittest
import os
import sys
import tempfile
import json
import subprocess
import shutil

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from models.generated.mode_ii.f42_mixed_element_uel.f42_deck_rebuilder import MixedDeckRebuilder
from models.generated.mode_ii.f43_stage_c_bridge.validate_f43_refined_layered_deck import validate_f43_refined_layered_deck

class TestF43AStageCBridgeFoundation(unittest.TestCase):
    def setUp(self):
        self.f43_dir = os.path.join(PROJECT_ROOT, "models", "generated", "mode_ii", "f43_stage_c_bridge")
        self.f42d_dir = os.path.join(PROJECT_ROOT, "models", "generated", "mode_ii", "f42_mixed_element_uel", "f42d_mixed_patch")

    def test_01_f43a_two_model_architecture_files_exist(self):
        """Verify F43A two-model architecture documentation files exist."""
        md_path = os.path.join(self.f43_dir, "F43A_STAGE_C_TWO_MODEL_ARCHITECTURE.md")
        json_path = os.path.join(self.f43_dir, "F43A_STAGE_C_TWO_MODEL_ARCHITECTURE.json")
        self.assertTrue(os.path.exists(md_path), "F43A_STAGE_C_TWO_MODEL_ARCHITECTURE.md must exist")
        self.assertTrue(os.path.exists(json_path), "F43A_STAGE_C_TWO_MODEL_ARCHITECTURE.json must exist")

    def test_02_f43a_remeshing_rule_config(self):
        """Verify remeshing rule config has required Pandey-Kumar pre-refinement parameters."""
        cfg_path = os.path.join(self.f43_dir, "f43_remeshing_rule_config.json")
        self.assertTrue(os.path.exists(cfg_path))
        with open(cfg_path, 'r') as f:
            cfg = json.load(f)["remeshing_rule_configuration"]
        self.assertEqual(cfg["error_indicator"], "MISESERI")
        self.assertEqual(cfg["min_element_size_mm"], 0.0075)
        self.assertEqual(cfg["max_element_size_mm"], 0.03)

    def test_03_f43a_synthetic_remeshed_deck_fixture_rebuild(self):
        """Test production rebuilder on synthetic mixed CPE4/CPE3 source deck fixture."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_inp = os.path.join(tmpdir, "F43SYNTHETIC_source.inp")
            out_inp = os.path.join(tmpdir, "F43SYNTHETIC_rebuilt.inp")
            with open(src_inp, 'w') as f:
                f.write("""*Heading
Synthetic Refined Deck Fixture
*Node
1, 0.0, 0.0
2, 1.0, 0.0
3, 0.0, 1.0
4, 1.0, 1.0
5, 2.0, 0.0
6, 2.0, 1.0
*Element, type=CPE4
1, 1, 2, 4, 3
2, 2, 5, 6, 4
*Element, type=CPE3
3, 2, 5, 4
4, 4, 5, 6
""")
            rebuilder = MixedDeckRebuilder(src_inp)
            rebuilder.parse()
            self.assertEqual(len(rebuilder.physical_elems), 4) # 2 CPE4 + 2 CPE3
            rebuilder.build_mixed_uel_deck(out_inp)

            self.assertTrue(os.path.exists(out_inp))
            with open(out_inp, 'r') as f:
                rebuilt_content = f.read()

            # Check 3-layer expansion: Nphys = 4 -> 12 elements total
            self.assertIn("properties=3", rebuilt_content.lower())
            self.assertIn("properties=5", rebuilt_content.lower())

    def test_04_f43a_gate_c1_validator(self):
        """Verify Gate C1 validator on F42MIX1.inp."""
        mix1_path = os.path.join(self.f42d_dir, "F42MIX1.inp")
        res = validate_f43_refined_layered_deck(mix1_path)
        self.assertTrue(res["valid"], f"Gate C1 validator failed on F42MIX1.inp: {res.get('errors')}")

    def test_05_f43a_gfortran_syntax_check(self):
        """Verify gfortran syntax check on f42d_mixed_uel.for."""
        for_path = os.path.join(self.f42d_dir, "f42d_mixed_uel.for")
        gfortran_bin = shutil.which("gfortran")
        if gfortran_bin:
            inc_dir = tempfile.mkdtemp()
            inc_path = os.path.join(inc_dir, "ABA_PARAM.INC")
            with open(inc_path, 'w') as f:
                f.write("      IMPLICIT REAL*8 (A-H,O-Z)\n")
            res = subprocess.run([gfortran_bin, "-fsyntax-only", "-ffixed-line-length-none", f"-I{inc_dir}", for_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            self.assertEqual(res.returncode, 0, f"gfortran syntax check failed: {res.stderr}")

if __name__ == "__main__":
    unittest.main()
