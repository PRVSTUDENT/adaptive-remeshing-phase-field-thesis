import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


status_writer = load("f6_status_writer", "scripts/hpc/stage_f/write_status_json.py")


class TestStageF6Batch(unittest.TestCase):
    def test_status_writer_round_trip_and_integer_counters(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "STATUS.json"
            result = status_writer.write_status(str(path), [
                "error_count=int:0", "warning_count=int:9",
                "classification=str:pass",
            ])
            parsed = json.loads(path.read_text())
            self.assertEqual(parsed, result)
            self.assertIs(type(parsed["error_count"]), int)
            self.assertIs(type(parsed["warning_count"]), int)
            self.assertNotIn(".log", str(parsed["error_count"]))

    def test_status_writer_controlled_failure_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "STATUS.json"
            status_writer.write_status(str(path), [
                "final_exit_code=int:22", "classification=str:compiler_unavailable"
            ])
            self.assertEqual(json.loads(path.read_text())["final_exit_code"], 22)

    def test_h2_pbs_contract(self):
        text = (ROOT / "scripts/hpc/stage_f/08_mode_ii_h2_u020_full_f6.pbs").read_text()
        self.assertIn("module load gcc/11.4.0", text)
        self.assertIn("module load intel/2024.2.0", text)
        self.assertIn("module load abaqus/2023", text)
        self.assertEqual(text.count('abaqus job="${JOBNAME}"'), 1)
        self.assertNotIn("git ", text)
        for rc in ("exit 10", "exit 11", "exit 12", "exit 20", "exit 21", "exit 22"):
            self.assertIn(rc, text)

    def test_api_job_prohibits_solver(self):
        pbs = (ROOT / "scripts/hpc/stage_f/09_mode_ii_miseseri_remesh_api_f6.pbs").read_text()
        qualifier = (ROOT / "scripts/remeshing/qualify_mode_ii_native_miseseri_api.py").read_text()
        self.assertIn("abaqus cae noGUI=", pbs)
        self.assertNotIn("abaqus job=", pbs)
        self.assertNotIn("subprocess", qualifier)
        self.assertNotIn("pathlib", qualifier)
        self.assertNotIn("inspect.signature", qualifier)
        self.assertIn('"solver_execution_count": 0', qualifier)
        self.assertIn("parse_known_args", qualifier)
        self.assertTrue("F6_SOURCE_ODB" in qualifier or "F7_SOURCE_ODB" in qualifier or "SOURCE_ODB" in qualifier)

    def test_publication_rule_exact(self):
        config = json.loads((ROOT / "configs/stage_f/mode_ii_miseseri_native_remesh.yaml").read_text())
        rule = config["publication_faithful_baseline"]
        self.assertEqual(rule["variables"], ["MISESERI"])
        self.assertEqual(rule["sizingMethod"], "UNIFORM_ERROR")
        self.assertEqual(rule["errorTarget"], 1.0)
        self.assertEqual(rule["coarseningFactor"], "NOT_ALLOWED")
        self.assertEqual(rule["refinementFactor"], 10)
        self.assertEqual(config["project_selected"]["minimum_element_size_mm"], 0.001)
        self.assertEqual(config["project_selected"]["maximum_element_size_mm"], 0.010)

    def test_orchestrator_is_only_qsub_call_site_and_no_retry(self):
        text = (ROOT / "scripts/hpc/stage_f/submit_stage_f6_two_job_batch.sh").read_text()
        self.assertEqual(text.count('"${QSUB_CMD}"'), 2)
        self.assertIn("direct_manual_qsub_calls=int:0", text)
        self.assertNotIn("qdel ", text)
        self.assertNotIn("qmove ", text)
        self.assertNotIn("rerun ", text)

    def test_exact_input_hashes(self):
        import hashlib
        package = ROOT / "models/generated/mode_ii/h2_uniform_serial_u020_postpeak"
        self.assertEqual(hashlib.sha256((package / "ModeII_H2_uniform_serial.inp").read_bytes()).hexdigest(),
                         "fdcd6ee1b1d6cbfb88d59a3edfb7f1c6b35cecde736a427f6b3030b0443b10bf")
        self.assertEqual(hashlib.sha256((package / "ModeII_H2_uniform_serial.for").read_bytes()).hexdigest(),
                         "49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37")


if __name__ == "__main__":
    unittest.main()
