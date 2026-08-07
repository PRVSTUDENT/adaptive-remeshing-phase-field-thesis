#!/bin/env python3
"""Unit test suite for F43PRE3_GEOM preanalysis package."""

import os
import sys
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = ROOT / "models" / "generated" / "mode_ii" / "f43_stage_c_bridge"
sys.path.insert(0, str(PKG_DIR))

from validate_f43pre3_geom_runtime import validate_f43pre3_geom

class TestStageF43PRE3Geom(unittest.TestCase):
    """Unit test suite for F43PRE3_GEOM preanalysis package."""

    def test_manifest_structure_and_lineage(self):
        manifest_path = PKG_DIR / "F43PRE3_SOURCE_MANIFEST.json"
        self.assertTrue(manifest_path.exists(), "F43PRE3_SOURCE_MANIFEST.json must exist")
        
        with open(manifest_path, "r") as f:
            m = json.load(f)

        self.assertEqual(m["task_id"], "F43PRE3_GEOM")
        self.assertEqual(m["cae_lineage"], "abaqus_2023_native")
        self.assertEqual(m["cae_source_sha256"], "0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa")
        self.assertEqual(m["inp_sha256"], "10d4fb75cc97d92fbb1491361624e92f4cc4269ed40e4420164af28ed15207ee")
        self.assertEqual(m["mesh_element_count"], 3716)
        self.assertEqual(m["mesh_node_count"], 3800)
        self.assertEqual(m["cpe4_count"], 3600)
        self.assertEqual(m["cpe3_count"], 116)
        
        pre2_prov = m.get("pre2_provenance", {})
        self.assertEqual(pre2_prov.get("cae_sha256"), "889c15ba6621ae8435324473bb385cb0da6a62866dd8c996865806b876c051ff")
        self.assertEqual(pre2_prov.get("status"), "historical_reference_only")
        self.assertEqual(pre2_prov.get("predecessor_odb_role"), "numerical_comparison_reference_only")

    def test_input_deck_physics_content(self):
        inp_path = PKG_DIR / "F43PRE3_GEOM.inp"
        self.assertTrue(inp_path.exists(), "F43PRE3_GEOM.inp must exist")

        content = inp_path.read_text().upper()

        self.assertIn("210000", content, "E must equal 210000 MPa")
        self.assertIn("0.3", content, "nu must equal 0.3")
        self.assertIn("0.001", content, "Displacement endpoint must equal 0.001 mm")
        self.assertIn("MISESERI", content, "MISESERI output request must be present")
        self.assertIn("MISESAVG", content, "MISESAVG output request must be present")
        self.assertIn("EVOL", content, "EVOL output request must be present")
        self.assertIn("S", content, "S output request must be present")
        self.assertIn("U", content, "U output request must be present")
        self.assertIn("RF", content, "RF output request must be present")

    def test_pbs_and_wrapper_contracts(self):
        pbs_path = PKG_DIR / "F43PRE3_GEOM.pbs"
        self.assertTrue(pbs_path.exists(), "F43PRE3_GEOM.pbs must exist")
        pbs_content = pbs_path.read_text()
        self.assertIn("#PBS -N F43PRE3_GEOM", pbs_content)
        self.assertIn("#PBS -q entry_imfdfkmq", pbs_content)
        self.assertIn("mem=8gb", pbs_content)
        self.assertIn("walltime=00:30:00", pbs_content)
        self.assertIn("abaqus job=F43PRE3_GEOM input=F43PRE3_GEOM.inp interactive", pbs_content)

        wrapper_path = PKG_DIR / "submit_f43pre3_geom.sh"
        self.assertTrue(wrapper_path.exists(), "submit_f43pre3_geom.sh must exist")
        wrapper_content = wrapper_path.read_text()
        self.assertIn("MAX_SUBMISSIONS", wrapper_content)
        self.assertIn("AUTOMATIC_RETRY", wrapper_content)
        self.assertIn("REPLACEMENT_AUTHORIZED", wrapper_content)
        self.assertIn("F43PRE3_SUBMISSION_APPROVED", wrapper_content)

    def test_acceptance_criteria(self):
        criteria_path = PKG_DIR / "F43PRE3_ACCEPTANCE_CRITERIA.json"
        self.assertTrue(criteria_path.exists(), "F43PRE3_ACCEPTANCE_CRITERIA.json must exist")
        with open(criteria_path, "r") as f:
            c = json.load(f)
        sc = c.get("solver_acceptance_criteria", {})
        self.assertEqual(sc.get("abaqus_exit_code_must_equal"), 0)
        self.assertEqual(sc.get("target_displacement_mm"), 0.001)
        self.assertIn("MISESERI", sc.get("required_field_outputs", []))
        self.assertIn("MISESAVG", sc.get("required_field_outputs", []))

    def test_static_validator_pass(self):
        res = validate_f43pre3_geom(str(PKG_DIR))
        self.assertTrue(res["overall_passed"], f"Static validator failed: {res.get('failures')}")

if __name__ == "__main__":
    unittest.main()
