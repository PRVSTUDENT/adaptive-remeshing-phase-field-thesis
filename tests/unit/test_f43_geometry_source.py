#!/usr/bin/env python3
"""
Unit tests for F43GEO2 geometry-backed Mode-II CAE generation and adaptivity-eligibility gate.
"""
import unittest
import os
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACKAGE_DIR = os.path.join(REPO_ROOT, "models", "generated", "mode_ii", "f43_stage_c_bridge")

class TestF43GeometrySourceContract(unittest.TestCase):

    def test_geometry_builder_script_exists(self):
        builder_path = os.path.join(PACKAGE_DIR, "build_mode_ii_native_cae.py")
        self.assertTrue(os.path.exists(builder_path), "Missing build_mode_ii_native_cae.py script")

    def test_geometry_validator_script_exists(self):
        validator_path = os.path.join(PACKAGE_DIR, "validate_f43pre2_geometry.py")
        self.assertTrue(os.path.exists(validator_path), "Missing validate_f43pre2_geometry.py script")

    def test_acceptance_criteria_file_valid(self):
        criteria_path = os.path.join(PACKAGE_DIR, "F43PRE2_ACCEPTANCE_CRITERIA.json")
        self.assertTrue(os.path.exists(criteria_path), "Missing F43PRE2_ACCEPTANCE_CRITERIA.json")
        with open(criteria_path, "r") as fp:
            data = json.load(fp)
        self.assertEqual(data["reference_preanalysis_job"], "1384674.mmaster02")
        self.assertEqual(data["reference_role"], "numerical_comparison_reference_only")
        self.assertEqual(data["acceptance_criteria"]["mesh_resolution"]["mesh_technique"], "FREE")

    def test_builder_manifest_and_geometry_validator_pass(self):
        import importlib.util
        val_path = os.path.join(PACKAGE_DIR, "validate_f43pre2_geometry.py")
        spec = importlib.util.spec_from_file_location("geo_val", val_path)
        geo_val = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(geo_val)

        passed, results = geo_val.validate_f43pre2_geometry(PACKAGE_DIR)
        self.assertTrue(passed, f"Geometry validator failed: {results.get('failures')}")
        self.assertTrue(results["orphan_mesh_prohibited"])
        self.assertTrue(results["geometry_backed_contract_valid"])
        self.assertTrue(results["deterministic_names_valid"])
        self.assertTrue(results["adaptivity_mesh_controls_valid"])
        self.assertTrue(results["reference_1384674_isolated"])
        self.assertTrue(results["cae_generated"])
        self.assertTrue(results["cae_reopen_persistence_verified"])
        self.assertTrue(results["seam_verified"])
        self.assertTrue(results["cae_eligibility_gate_passed"])

    def test_mesh_control_contract_specifies_quad_dominated(self):
        manifest_path = os.path.join(PACKAGE_DIR, "F43PRE2_SOURCE_MANIFEST.json")
        with open(manifest_path, "r") as fp:
            data = json.load(fp)
        mesh_spec = data["benchmark_spec"]["mesh"]
        self.assertEqual(mesh_spec["elem_shape"], "QUAD_DOMINATED")
        self.assertEqual(mesh_spec["technique"], "FREE")
        self.assertEqual(mesh_spec["algorithm"], "ADVANCING_FRONT")
        self.assertFalse(mesh_spec["allow_mapped"])

    def test_legacy_odb_1384674_rejected_as_direct_native_remeshing_predecessor(self):
        manifest_path = os.path.join(PACKAGE_DIR, "F43PRE2_SOURCE_MANIFEST.json")
        with open(manifest_path, "r") as fp:
            data = json.load(fp)
        self.assertNotEqual(data.get("predecessor_odb_sha256"), "3a201a6d405b92f4588e3d7e68177797706fd80ca9fa541e36ed0b10fdfb0534",
                            "Legacy ODB 1384674 must NOT be specified as direct native remeshing predecessor!")

if __name__ == "__main__":
    unittest.main()
