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
        self.assertFalse(auth["execution_authorized"])
        self.assertFalse(auth["submission_approved"])
        self.assertEqual(auth["maximum_jobs_now"], 0)
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
                self.assertEqual(rule["meshBias"], 0)

    def test_03_batch_manifest_and_isolation(self):
        manifest_path = os.path.join(BATCH_DIR, "F43REM4_BATCH_MANIFEST.json")
        self.assertTrue(os.path.exists(manifest_path))
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        self.assertEqual(len(manifest["candidates"]), 3)
        self.assertIn("revised_gate_c1_selection_rule", manifest)
        
        output_decks = [c["expected_output_deck"] for c in manifest["candidates"]]
        self.assertEqual(len(output_decks), len(set(output_decks)), "Output decks must be unique and isolated")

if __name__ == "__main__":
    unittest.main()
