import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
H2 = ROOT / "scripts/hpc/stage_f/05_mode_ii_h2_u020_postpeak.pbs"
MIS = ROOT / "scripts/hpc/stage_f/06_mode_ii_miseseri_corrected_pbs.pbs"
ORCH = ROOT / "scripts/hpc/stage_f/submit_stage_f4_two_job_batch.sh"


class TestStageF4RuntimeBundleReplacement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h2 = H2.read_text(encoding="utf-8")
        cls.mis = MIS.read_text(encoding="utf-8")
        cls.orch = ORCH.read_text(encoding="utf-8")

    def test_compute_scripts_have_no_git_command(self):
        for text in (self.h2, self.mis):
            self.assertIsNone(re.search(r"(?m)^\s*git\s", text))
            self.assertNotIn("PROJECT_ROOT", text)

    def test_compute_scripts_use_staged_runtime_paths(self):
        self.assertIn("runtime/scripts/postprocessing/extract_mode_ii_uniform_reference.py", self.h2)
        self.assertIn("runtime/scripts/validation/validate_mode_ii_h2_results.py", self.h2)
        self.assertIn("runtime/scripts/postprocessing/export_miseseri_preanalysis_csv.py", self.mis)
        self.assertIn("runtime/scripts/validation/validate_mode_ii_miseseri_preanalysis_results.py", self.mis)

    def test_hash_and_missing_file_fail_closed(self):
        for text in (self.h2, self.mis):
            self.assertIn("sha256sum -c", text)
            self.assertIn('write_status 20 "runtime_hash_verification_failed"', text)
            self.assertIn('write_status 21 "required_staged_file_missing"', text)
            self.assertRegex(text, r"exit 20")
            self.assertRegex(text, r"exit 21")

    def test_exit_mapping_is_complete(self):
        for text in (self.h2, self.mis):
            for code in (0, 10, 11, 12, 20, 21):
                self.assertRegex(text, rf"exit {code}\b")

    def test_miseseri_environment_contract(self):
        expected = {
            "MISESERI_AUX_CONTINUUM": "1",
            "MISESERI_DISPLACEMENT_COMPONENT": "1",
            "MISESERI_REACTION_COMPONENT": "1",
            "MISESERI_TARGET_DISPLACEMENT": "0.001",
            "MISESERI_TARGET_TOLERANCE": "0.0001",
        }
        for key, value in expected.items():
            self.assertIn(f"export {key}={value}", self.mis)
        self.assertNotIn("--odb", self.mis)

    def test_unique_short_job_names(self):
        self.assertIn("#PBS -N M2H2U20R1", self.h2)
        self.assertIn("#PBS -N M2MISER1", self.mis)
        self.assertLessEqual(len("M2H2U20R1"), 15)
        self.assertLessEqual(len("M2MISER1"), 15)

    def test_orchestrator_is_immutable_and_two_attempt_only(self):
        self.assertIn('if [[ -e "${base}" ]]', self.orch)
        self.assertNotIn('mkdir -p "${SCRATCH_A}"', self.orch)
        self.assertIn("QSUB_ATTEMPTS=1", self.orch)
        self.assertIn("QSUB_ATTEMPTS=2", self.orch)
        self.assertNotIn("retry", self.orch.lower().replace("retry_authorized", ""))
        self.assertIn('"approved_submissions"] == 2', self.orch)

    def test_runtime_is_generated_from_committed_archive(self):
        self.assertIn('git -C "${REPO_ROOT}" archive "${SOURCE_REVISION}"', self.orch)
        self.assertIn("find runtime -type f", self.orch)
        self.assertIn("RUNTIME_MANIFEST.json", self.orch)
        self.assertIn("SUBMISSION_MANIFEST.json", self.orch)


if __name__ == "__main__":
    unittest.main()
