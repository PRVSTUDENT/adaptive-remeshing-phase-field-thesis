#!/usr/bin/env python3
"""
Offline Unit Test Suite for F43REM2_NATIVE Native Adaptive Remeshing Preparation.
"""

import sys
import os
import json
import hashlib
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
PKG_DIR = ROOT_DIR / "models" / "generated" / "mode_ii" / "f43_stage_c_bridge"

sys.path.insert(0, str(PKG_DIR))
from validate_f43rem2_native import validate_f43rem2_native, get_sha256

class TestStageF43REM2Native(unittest.TestCase):
    
    def test_manifest_schema_and_frozen_hashes(self):
        manifest_path = PKG_DIR / "F43REM2_NATIVE_MANIFEST.json"
        self.assertTrue(manifest_path.exists(), "F43REM2_NATIVE_MANIFEST.json must exist")
        
        with open(manifest_path, "r") as f:
            m = json.load(f)
            
        self.assertEqual(m["task_id"], "F43REM2_NATIVE")
        self.assertEqual(m["predecessor_job"], "1385392.mmaster02")
        self.assertEqual(m["predecessor_odb_sha256"], "85339f45937cf5d2c57f169fa71b3e55f066082e6525aa3c20a370f058c4cf72")
        self.assertEqual(m["source_cae_sha256"], "889c15ba6621ae8435324473bb385cb0da6a62866dd8c996865806b876c051ff")
        self.assertEqual(m["source_cae_open_in_place"], "forbidden")
        self.assertTrue(m["runtime_work_copy_required"])
        
        remesh_params = m["remesh_parameters"]
        self.assertEqual(remesh_params["minElementSize_mm"], 0.0075)
        self.assertEqual(remesh_params["maxElementSize_mm"], 0.03)
        self.assertEqual(remesh_params["length_scale_l0_mm"], 0.015)
        self.assertEqual(remesh_params["min_h_over_l0"], 0.5)

    def test_source_cae_hash_integrity(self):
        cae_path = PKG_DIR / "ModeII_Geometry_Source.cae"
        self.assertTrue(cae_path.exists(), "ModeII_Geometry_Source.cae must exist")
        actual_sha = get_sha256(str(cae_path))
        expected_sha = "889c15ba6621ae8435324473bb385cb0da6a62866dd8c996865806b876c051ff"
        self.assertEqual(actual_sha.lower(), expected_sha.lower(), "CAE source hash mismatch")

    def test_execution_authorization_boundary_closed(self):
        manifest_path = PKG_DIR / "F43REM2_NATIVE_MANIFEST.json"
        with open(manifest_path, "r") as f:
            m = json.load(f)
            
        self.assertFalse(m["execution_authorized"], "execution_authorized must be false")
        self.assertFalse(m["submission_approved"], "submission_approved must be false")
        self.assertEqual(m["maximum_jobs_now"], 0, "maximum_jobs_now must be 0")
        self.assertEqual(m["maximum_future_submissions"], 0, "maximum_future_submissions must be 0")

    def test_reference_1384674_odb_rejected(self):
        ref_odb_sha = "3a201a6d405b92f4588e3d7e68177797706fd80ca9fa541e36ed0b10fdfb0534"
        manifest_path = PKG_DIR / "F43REM2_NATIVE_MANIFEST.json"
        with open(manifest_path, "r") as f:
            m = json.load(f)
            
        self.assertNotEqual(m["predecessor_odb_sha256"], ref_odb_sha, "Reference ODB 1384674 must be rejected for native remeshing")

    def test_static_validator_passes(self):
        res = validate_f43rem2_native(str(PKG_DIR))
        self.assertTrue(res["overall_passed"], f"Static validator failed: {res.get('failures')}")

if __name__ == "__main__":
    unittest.main()
