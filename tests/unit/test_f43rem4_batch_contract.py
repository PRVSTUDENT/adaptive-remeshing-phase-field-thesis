import os
import json
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BATCH_DIR = os.path.join(
    PROJECT_ROOT, "models", "generated", "mode_ii", "f43_stage_c_bridge", "remesh_sensitivity_batch"
)

class TestF43REM4BatchContract(unittest.TestCase):
    def test_01_batch_authorization_structure(self):
        auth_path = os.path.join(BATCH_DIR, "F43REM4_BATCH_AUTHORIZATION.json")
        self.assertTrue(os.path.exists(auth_path), f"Batch authorization file missing: {auth_path}")
        with open(auth_path, "r") as f:
            auth = json.load(f)
        self.assertIn("execution_authorized", auth)
        self.assertIn("submission_approved", auth)
        self.assertIn(auth["maximum_jobs_now"], [0, 3])
        self.assertEqual(auth["maximum_jobs_authorized"], 3)
        self.assertEqual(len(auth["jobs"]), 3)


    def test_02_candidate_configs_and_types(self):
        for candidate_id in ["pk1", "pk5", "mm"]:
            config_path = os.path.join(BATCH_DIR, f"remesh_sensitivity_config_{candidate_id}.json")
            self.assertTrue(os.path.exists(config_path), f"Config missing for {candidate_id}")
            with open(config_path, "r") as f:
                cfg = json.load(f)
            self.assertEqual(cfg["source_cae_sha256"], "0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa")
            self.assertEqual(cfg["predecessor_odb_sha256"], "9a5262931675d2780ccc8b6e6060dd20b817917df7cdf6e499a7a0a2d0d06eb1")
            
            rule = cfg["remeshing_rule"]
            if candidate_id in ["pk1", "pk5"]:
                self.assertIsInstance(rule["refinementFactor"], int)
                self.assertEqual(rule["refinementFactor"], 10)
            elif candidate_id == "mm":
                self.assertIsInstance(rule["meshBias"], int)
                self.assertEqual(rule["meshBias"], 1)

    def test_03_batch_manifest_and_isolation(self):
        manifest_path = os.path.join(BATCH_DIR, "F43REM4_BATCH_MANIFEST.json")
        self.assertTrue(os.path.exists(manifest_path))
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        self.assertEqual(len(manifest["candidates"]), 3)
        self.assertIn("revised_gate_c1_selection_rule", manifest)
        
        output_decks = [c["expected_output_deck"] for c in manifest["candidates"]]
        self.assertEqual(len(output_decks), len(set(output_decks)), "Output decks must be unique and isolated")

    def test_04_pbs_script_candidate_output_isolation(self):
        candidates = [("F43REM4_PK1", "runtime_pk1"), ("F43REM4_PK5", "runtime_pk5"), ("F43REM4_MM", "runtime_mm")]
        for cand_id, runtime_folder in candidates:
            pbs_path = os.path.join(BATCH_DIR, f"{cand_id}.pbs")
            self.assertTrue(os.path.exists(pbs_path), f"PBS script missing: {pbs_path}")
            with open(pbs_path, "r") as f:
                content = f.read()
            self.assertIn(f"CANDIDATE_ID=\"{cand_id}\"", content)
            self.assertIn(f"RUNTIME_DIR=\"${{BATCH_DIR}}/{runtime_folder}\"", content)
            self.assertIn("export F43REM4_BRIDGE_DIR=", content)
            self.assertIn("export F43REM4_SOURCE_CAE=", content)
            self.assertIn("export F43REM4_PREDECESSOR_ODB=", content)
            self.assertIn("export F43REM4_OUTPUT_DIR=", content)
            self.assertIn("F43REM4_PREFLIGHT_ONLY", content)

    def test_05_old_erroneous_path_regression(self):
        erroneous_path = os.path.join(BATCH_DIR, "evidence", "1385461.mmaster02", "F43PRE3_GEOM.odb")
        self.assertFalse(
            os.path.exists(erroneous_path),
            f"Erroneous path inside sensitivity batch directory must NOT exist: {erroneous_path}"
        )

    def test_06_canonical_parent_bridge_evidence_path_resolution(self):
        bridge_dir = os.path.abspath(os.path.join(BATCH_DIR, ".."))
        canonical_odb = os.path.join(bridge_dir, "evidence", "1385461.mmaster02", "F43PRE3_GEOM.odb")
        # In repository checkout or cluster environment, evidence file location is under bridge_dir/evidence
        self.assertTrue(
            os.path.exists(os.path.join(bridge_dir, "evidence")),
            f"Bridge evidence root missing: {os.path.join(bridge_dir, 'evidence')}"
        )

    def test_07_driver_path_resolution_and_preflight_contract(self):
        driver_path = os.path.abspath(os.path.join(BATCH_DIR, "..", "remesh_mode_ii_native_cae.py"))
        self.assertTrue(os.path.exists(driver_path))
        with open(driver_path, "r") as f:
            code = f.read()
        self.assertIn("F43REM4_BRIDGE_DIR", code)
        self.assertIn("F43REM4_PREDECESSOR_ODB", code)
        self.assertIn("F43REM4_SOURCE_CAE", code)
        self.assertIn("F43REM4_OUTPUT_DIR", code)
        self.assertIn("F43REM4_PREFLIGHT_ONLY", code)
        self.assertIn("_runtime_work_copy_", code)

    def test_08_scientific_parameters_frozen(self):
        pk1_cfg = json.load(open(os.path.join(BATCH_DIR, "remesh_sensitivity_config_pk1.json")))
        self.assertEqual(pk1_cfg["remeshing_rule"]["sizingMethod"], "UNIFORM_ERROR")
        self.assertEqual(pk1_cfg["remeshing_rule"]["errorTarget"], 1.0)
        self.assertEqual(pk1_cfg["remeshing_rule"]["refinementFactor"], 10)

        pk5_cfg = json.load(open(os.path.join(BATCH_DIR, "remesh_sensitivity_config_pk5.json")))
        self.assertEqual(pk5_cfg["remeshing_rule"]["sizingMethod"], "UNIFORM_ERROR")
        self.assertEqual(pk5_cfg["remeshing_rule"]["errorTarget"], 5.0)
        self.assertEqual(pk5_cfg["remeshing_rule"]["refinementFactor"], 10)

        mm_cfg = json.load(open(os.path.join(BATCH_DIR, "remesh_sensitivity_config_mm.json")))
        self.assertEqual(mm_cfg["remeshing_rule"]["sizingMethod"], "MINIMUM_MAXIMUM")
        self.assertEqual(mm_cfg["remeshing_rule"]["maxSolutionErrorTarget"], 5.0)
        self.assertEqual(mm_cfg["remeshing_rule"]["minSolutionErrorTarget"], 1.0)
        self.assertEqual(mm_cfg["remeshing_rule"]["meshBias"], 1)

if __name__ == "__main__":
    unittest.main()

