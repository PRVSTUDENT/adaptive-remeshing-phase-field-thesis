import json
import os
import re
import subprocess
import sys
import unittest

class TestStageF39Batch(unittest.TestCase):

    def setUp(self):
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.pkg_dir = os.path.join(self.repo_root, "models", "generated", "mode_ii", "f39_abaqus_cae_kernel_startup_diagnostic")
        self.wrapper_path = os.path.join(self.repo_root, "scripts", "hpc", "stage_f", "submit_stage_f39_cae_kernel_diagnostic.sh")
        self.validator_path = os.path.join(self.repo_root, "scripts", "validation", "validate_f39_cae_kernel_startup_gate.py")

    def test_minimal_probe_has_no_file_dependency(self):
        probe_path = os.path.join(self.pkg_dir, "runtime", "minimal_cae_kernel_probe.py")
        self.assertTrue(os.path.exists(probe_path))
        with open(probe_path, "r") as f:
            content = f.read()
            self.assertNotIn("__file__", content)

    def test_minimal_probe_has_no_model_import(self):
        probe_path = os.path.join(self.pkg_dir, "runtime", "minimal_cae_kernel_probe.py")
        with open(probe_path, "r") as f:
            content = f.read()
            for prohibited in ["import mdb", "from abaqus import", "import part", "import assembly", "import mesh"]:
                self.assertNotIn(prohibited, content)

    def test_env_collector_redaction(self):
        collector_path = os.path.join(self.pkg_dir, "runtime", "collect_launcher_environment.py")
        with open(collector_path, "r") as f:
            content = f.read()
            self.assertIn("[REDACTED]", content)
            self.assertIn("WHITELISTED_VARS", content)

    def test_evidence_report_disjoint_sets(self):
        gen_rep_path = os.path.join(self.pkg_dir, "runtime", "generate_missing_evidence_report.py")
        with open(gen_rep_path, "r") as f:
            content = f.read()
            self.assertIn("missing_files = [f for f in EXPECTED_EVIDENCE_FILES", content)
            self.assertIn("existing_files = [f for f in EXPECTED_EVIDENCE_FILES", content)

    def test_pbs_trap_preserves_first_failure(self):
        pbs_path = os.path.join(self.pkg_dir, "M2RMKERN1.pbs")
        with open(pbs_path, "r") as f:
            content = f.read()
            self.assertIn("trap - EXIT", content)
            self.assertIn('exit "$first_failure"', content)

    def test_pbs_mandatory_evidence_dir(self):
        pbs_path = os.path.join(self.pkg_dir, "M2RMKERN1.pbs")
        with open(pbs_path, "r") as f:
            content = f.read()
            self.assertIn("F39_EVIDENCE_DIR", content)

    def test_pbs_invokes_runtime_validator(self):
        pbs_path = os.path.join(self.pkg_dir, "M2RMKERN1.pbs")
        with open(pbs_path, "r") as f:
            content = f.read()
            self.assertIn("validate_f39_runtime_audits.py", content)

    def test_package_manifest_completeness(self):
        man_path = os.path.join(self.pkg_dir, "PACKAGE_MANIFEST.json")
        with open(man_path, "r") as f:
            manifest = json.load(f)
            pkg_files = manifest.get("package_files", {})
            self.assertIn("M2RMKERN1.pbs", pkg_files)
            self.assertIn("runtime/collect_launcher_environment.py", pkg_files)
            self.assertIn("runtime/generate_missing_evidence_report.py", pkg_files)
            self.assertIn("runtime/minimal_cae_kernel_probe.py", pkg_files)
            self.assertIn("runtime/validate_f39_runtime_audits.py", pkg_files)

    def test_wrapper_single_qsub(self):
        with open(self.wrapper_path, "r") as f:
            content = f.read()
            qsubs = re.findall(r"\bqsub\b", content)
            self.assertEqual(len(qsubs), 1)

    def test_submission_gates_default_closed(self):
        with open(self.wrapper_path, "r") as f:
            content = f.read()
            self.assertIn('F39_ALLOW_SUBMISSION:-false', content)
            self.assertIn('F39_AUTHORIZE_M2RMKERN1:-false', content)

    def test_f38_files_preserved(self):
        f38_dir = os.path.join(self.repo_root, "models", "generated", "mode_ii", "f38_comprehensive_cae_diagnostic_matrix")
        self.assertTrue(os.path.exists(os.path.join(f38_dir, "M2RMDIAG1.pbs")))
        self.assertTrue(os.path.exists(os.path.join(f38_dir, "PACKAGE_MANIFEST.json")))

    def test_static_gate_validator_passes(self):
        res = subprocess.run([sys.executable, self.validator_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(res.returncode, 0, "Static validator failed: " + res.stdout + res.stderr)

if __name__ == "__main__":
    unittest.main()
