import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


def to_posix_path(path: Path) -> str:
    path_str = str(path).replace('\\', '/')
    if len(path_str) > 1 and path_str[1] == ':':
        drive = path_str[0].lower()
        return f"/mnt/{drive}{path_str[2:]}"
    return path_str


class TestF43REM4BatchSpoolAndConcurrency(unittest.TestCase):
    """Unit and regression tests for F43REM4 PBS spool directory resolution and concurrency guards."""

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.batch_dir = self.repo_root / "models" / "generated" / "mode_ii" / "f43_stage_c_bridge" / "remesh_sensitivity_batch"
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_spool_path_resolution_pk1(self):
        self._run_spool_path_test("F43REM4_PK1.pbs", "runtime_pk1")

    def test_spool_path_resolution_pk5(self):
        self._run_spool_path_test("F43REM4_PK5.pbs", "runtime_pk5")

    def test_spool_path_resolution_mm(self):
        self._run_spool_path_test("F43REM4_MM.pbs", "runtime_mm")

    def _run_spool_path_test(self, pbs_script_name, runtime_dir_name):
        spool_dir = Path(self.tmp_dir) / "var" / "spool" / "pbs" / "mom_priv" / "jobs"
        spool_dir.mkdir(parents=True, exist_ok=True)
        spool_script = spool_dir / f"{pbs_script_name}.SC"
        
        src_pbs = self.batch_dir / pbs_script_name
        shutil.copy(src_pbs, spool_script)

        posix_batch = to_posix_path(self.batch_dir)
        posix_script = to_posix_path(spool_script)
        cmd_str = f"export PBS_JOBID='9999999.mmaster02'; export PBS_O_WORKDIR='{posix_batch}'; export F43REM4_PREFLIGHT_ONLY=1; bash '{posix_script}'"

        proc = subprocess.run(
            ["bash", "-c", cmd_str],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        out = proc.stdout + "\n" + proc.stderr
        self.assertEqual(proc.returncode, 0, f"PBS script failed with output:\n{out}")
        self.assertIn(f"Resolved BATCH_DIR: {posix_batch}", out)
        
        # Verify no runtime directory was created beneath spool_dir
        spool_runtime = spool_dir / runtime_dir_name
        self.assertFalse(spool_runtime.exists(), f"Directory {spool_runtime} must not be created beneath spool path")

    def test_spool_path_fail_closed_missing_workdir(self):
        spool_dir = Path(self.tmp_dir) / "var" / "spool" / "pbs" / "mom_priv" / "jobs"
        spool_dir.mkdir(parents=True, exist_ok=True)
        spool_script = spool_dir / "F43REM4_PK1.pbs.SC"
        
        shutil.copy(self.batch_dir / "F43REM4_PK1.pbs", spool_script)

        posix_script = to_posix_path(spool_script)
        cmd_str = f"export PBS_JOBID='9999999.mmaster02'; unset PBS_O_WORKDIR; export F43REM4_PREFLIGHT_ONLY=1; bash '{posix_script}'"

        proc = subprocess.run(
            ["bash", "-c", cmd_str],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("PBS_O_WORKDIR is missing or empty", proc.stderr + proc.stdout)

    def test_fake_qsub_concurrency_guard(self):
        fake_bin_dir = Path(self.tmp_dir) / "bin"
        fake_bin_dir.mkdir(parents=True, exist_ok=True)
        fake_qsub = fake_bin_dir / "qsub"
        fake_qstat = fake_bin_dir / "qstat"
        qsub_log = Path(self.tmp_dir) / "qsub_invocations.log"

        posix_qsub_log = to_posix_path(qsub_log)
        # Create a mock qsub script recording arguments and returning synthetic job IDs with LF line endings
        qsub_content = f"#!/bin/bash\necho \"$@\" >> \"{posix_qsub_log}\"\ncount=$(wc -l < \"{posix_qsub_log}\")\necho \"138557${{count}}.mmaster02\"\n"
        with open(fake_qsub, "w", newline="\n", encoding="utf-8") as f:
            f.write(qsub_content)
        fake_qsub.chmod(0o755)

        with open(fake_qstat, "w", newline="\n", encoding="utf-8") as f:
            f.write("#!/bin/bash\necho 'Job ID Username Queue Jobname SessID NDS TSK Memory Time S Time'\nexit 0\n")
        fake_qstat.chmod(0o755)

        # Create temporary authorization JSON with execution_authorized=True for wrapper test
        auth_json = self.batch_dir / "F43REM4_BATCH_AUTHORIZATION.json"
        orig_auth = auth_json.read_text(encoding="utf-8")
        auth_data = json.loads(orig_auth)
        auth_data["execution_authorized"] = True
        auth_data["submission_approved"] = True
        auth_data["maximum_jobs_now"] = 3
        auth_data["maximum_jobs_authorized"] = 3
        
        try:
            auth_json.write_text(json.dumps(auth_data, indent=2), encoding="utf-8")

            posix_fake_bin = to_posix_path(fake_bin_dir)
            posix_wrapper = to_posix_path(self.batch_dir / "submit_f43rem4_sensitivity_batch.sh")
            cmd_str = f"export PATH=\"{posix_fake_bin}:/usr/local/bin:/usr/bin:/bin\"; export DRY_RUN=0; export USER=testuser; bash \"{posix_wrapper}\""

            proc = subprocess.run(
                ["bash", "-c", cmd_str],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            self.assertEqual(proc.returncode, 0, f"Wrapper failed with output:\n{proc.stdout}\n{proc.stderr}")

            invocations = qsub_log.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(invocations), 3, "Exactly 3 qsub calls must be issued")

            # Check dependency arguments
            self.assertNotIn("-W depend", invocations[0], "PK1 must have no dependency")
            self.assertNotIn("-W depend", invocations[1], "PK5 must have no dependency")
            self.assertIn("-W depend=afterany:1385571.mmaster02", invocations[2], "MM must carry depend=afterany:JOB1_ID")

        finally:
            auth_json.write_text(orig_auth, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
