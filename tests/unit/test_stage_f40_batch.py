import json
import os
import re
import subprocess
import sys
import unittest

class TestStageF40Batch(unittest.TestCase):

    def setUp(self):
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.pkg_dir = os.path.join(self.repo_root, "models", "generated", "mode_ii", "f40_f38_cae_invocation_model_building_bisect")
        self.wrapper_path = os.path.join(self.repo_root, "scripts", "hpc", "stage_f", "submit_stage_f40_cae_bisect.sh")
        self.validator_path = os.path.join(self.repo_root, "scripts", "validation", "validate_f40_cae_bisect_gate.py")

    def test_runner_has_no_file_dependency(self):
        runner_path = os.path.join(self.pkg_dir, "runtime", "f40_cae_bisection_runner.py")
        self.assertTrue(os.path.exists(runner_path))
        with open(runner_path, "r") as f:
            content = f.read()
            self.assertNotIn("__file__", content)

    def test_contract_delta_auditor_exists(self):
        delta_path = os.path.join(self.pkg_dir, "runtime", "f40_invocation_contract_delta.py")
        self.assertTrue(os.path.exists(delta_path))

    def test_pbs_queue_and_resource_directives(self):
        pbs_path = os.path.join(self.pkg_dir, "M2RMBISECT1.pbs")
        with open(pbs_path, "r") as f:
            content = f.read()
            self.assertIn("#PBS -q entry_imfdfkmq", content)
            self.assertIn("#PBS -l select=1:ncpus=1:mpiprocs=1:ompthreads=1:mem=8gb", content)

    def test_pbs_trap_preserves_first_failure(self):
        pbs_path = os.path.join(self.pkg_dir, "M2RMBISECT1.pbs")
        with open(pbs_path, "r") as f:
            content = f.read()
            self.assertIn("trap - EXIT", content)
            self.assertIn('exit "$first_failure"', content)

    def test_pbs_mandatory_evidence_dir(self):
        pbs_path = os.path.join(self.pkg_dir, "M2RMBISECT1.pbs")
        with open(pbs_path, "r") as f:
            content = f.read()
            self.assertIn("F40_EVIDENCE_DIR", content)

    def test_evidence_report_disjoint_sets(self):
        gen_rep_path = os.path.join(self.pkg_dir, "runtime", "generate_missing_evidence_report.py")
        with open(gen_rep_path, "r") as f:
            content = f.read()
            self.assertIn("missing_files = [f for f in EXPECTED_EVIDENCE_FILES", content)
            self.assertIn("existing_files = [f for f in EXPECTED_EVIDENCE_FILES", content)

    def test_package_manifest_completeness(self):
        man_path = os.path.join(self.pkg_dir, "PACKAGE_MANIFEST.json")
        with open(man_path, "r") as f:
            manifest = json.load(f)
            pkg_files = manifest.get("package_files", {})
            self.assertIn("M2RMBISECT1.pbs", pkg_files)
            self.assertIn("runtime/f40_cae_bisection_runner.py", pkg_files)
            self.assertIn("runtime/f40_invocation_contract_delta.py", pkg_files)
            self.assertIn("runtime/generate_missing_evidence_report.py", pkg_files)
            self.assertIn("runtime/source_deck.inp", pkg_files)
            self.assertIn("runtime/validate_f40_runtime_audits.py", pkg_files)

    def test_wrapper_single_qsub(self):
        with open(self.wrapper_path, "r") as f:
            content = f.read()
            qsubs = re.findall(r"^\s*JOB_ID=\$\(qsub\b", content, re.MULTILINE)
            self.assertEqual(len(qsubs), 1)

    def test_submission_gates_default_closed(self):
        with open(self.wrapper_path, "r") as f:
            content = f.read()
            self.assertIn('F40_ALLOW_SUBMISSION:-false', content)
            self.assertIn('F40_AUTHORIZE_M2RMBISECT1:-false', content)

    def test_f38_f39_preservation(self):
        f38_dir = os.path.join(self.repo_root, "models", "generated", "mode_ii", "f38_comprehensive_cae_diagnostic_matrix")
        f39_dir = os.path.join(self.repo_root, "models", "generated", "mode_ii", "f39_abaqus_cae_kernel_startup_diagnostic")
        self.assertTrue(os.path.exists(os.path.join(f38_dir, "M2RMDIAG1.pbs")))
        self.assertTrue(os.path.exists(os.path.join(f39_dir, "M2RMKERN1.pbs")))

    def test_static_gate_validator_passes(self):
        res = subprocess.run([sys.executable, self.validator_path], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, "Static validator failed: " + res.stdout + res.stderr)

if __name__ == "__main__":
    unittest.main()
