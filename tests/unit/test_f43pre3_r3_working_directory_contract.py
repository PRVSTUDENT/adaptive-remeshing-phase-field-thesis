import os
import sys
import shutil
import tempfile
import subprocess
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACKAGE_DIR = os.path.join(REPO_ROOT, "models", "generated", "mode_ii", "f43_stage_c_bridge")
WRAPPER_PATH = os.path.join(PACKAGE_DIR, "submit_f43pre3_geom.sh")
PBS_PATH = os.path.join(PACKAGE_DIR, "F43PRE3_GEOM.pbs")

class TestF43PRE3R3WorkingDirectoryContract(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_f43pre3_r3_wd_")
        self.fake_bin_dir = os.path.join(self.temp_dir, "bin")
        os.makedirs(self.fake_bin_dir, exist_ok=True)
        
        # Create fake qsub that records PWD, ARGS, and returns mock job ID
        self.fake_qsub_log = os.path.join(self.temp_dir, "qsub_recorded.log")
        fake_qsub = os.path.join(self.fake_bin_dir, "qsub")
        with open(fake_qsub, "w") as f:
            f.write(f"""#!/bin/bash
echo "PWD=$(pwd)" >> "{self.fake_qsub_log}"
echo "ARGS=$*" >> "{self.fake_qsub_log}"
echo "1385999.mmaster02"
""")
        os.chmod(fake_qsub, 0o755)

        # Create fake qstat that returns empty (no running jobs)
        fake_qstat = os.path.join(self.fake_bin_dir, "qstat")
        with open(fake_qstat, "w") as f:
            f.write("""#!/bin/bash
echo "Job ID Username Queue Jobname SessID NDS TSK Memory Time S Time"
""")
        os.chmod(fake_qstat, 0o755)

        # Build env with fake_bin_dir prepended to PATH
        self.env = os.environ.copy()
        self.env["PATH"] = f"{self.fake_bin_dir}:{self.env.get('PATH', '')}"
        self.env["F43PRE3_SUBMISSION_APPROVED"] = "1"
        self.env["MAX_SUBMISSIONS"] = "1"
        self.env["AUTOMATIC_RETRY"] = "false"
        self.env["REPLACEMENT_AUTHORIZED"] = "false"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_A_wrapper_invoked_from_repository_root(self):
        res = subprocess.run(
            ["bash", WRAPPER_PATH],
            cwd=REPO_ROOT,
            env=self.env,
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0, f"Wrapper failed: {res.stderr}")
        self.assertTrue(os.path.exists(self.fake_qsub_log), "qsub log not found")
        
        with open(self.fake_qsub_log, "r") as f:
            log_content = f.read()
        
        # Realpath canonicalization for cross-platform comparison (e.g. /mnt/d vs /d)
        recorded_pwd = None
        for line in log_content.splitlines():
            if line.startswith("PWD="):
                recorded_pwd = line.split("=", 1)[1]
        
        self.assertIsNotNone(recorded_pwd, "No PWD recorded by qsub")
        self.assertEqual(os.path.realpath(recorded_pwd), os.path.realpath(PACKAGE_DIR),
                         f"Recorded qsub CWD {recorded_pwd} != expected PACKAGE_DIR {PACKAGE_DIR}")

    def test_B_wrapper_invoked_from_arbitrary_temp_dir(self):
        unrelated_dir = os.path.join(self.temp_dir, "unrelated_workspace")
        os.makedirs(unrelated_dir, exist_ok=True)
        
        res = subprocess.run(
            ["bash", WRAPPER_PATH],
            cwd=unrelated_dir,
            env=self.env,
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0, f"Wrapper failed from arbitrary dir: {res.stderr}")
        
        with open(self.fake_qsub_log, "r") as f:
            log_content = f.read()
            
        recorded_pwd = None
        for line in log_content.splitlines():
            if line.startswith("PWD="):
                recorded_pwd = line.split("=", 1)[1]
                
        self.assertEqual(os.path.realpath(recorded_pwd), os.path.realpath(PACKAGE_DIR))

    def test_C_pbs_presolver_shell_portion_with_valid_pbs_o_workdir(self):
        # Create isolated mock package directory in temp_dir to avoid dirtying tracked repo
        mock_pkg = os.path.join(self.temp_dir, "mock_pkg")
        shutil.copytree(PACKAGE_DIR, mock_pkg)

        fake_abaqus = os.path.join(self.fake_bin_dir, "abaqus")
        with open(fake_abaqus, "w") as f:
            f.write("""#!/bin/bash
touch F43PRE3_GEOM.odb
exit 0
""")
        os.chmod(fake_abaqus, 0o755)

        fake_module = os.path.join(self.fake_bin_dir, "module")
        with open(fake_module, "w") as f:
            f.write("""#!/bin/bash
echo "Module command mock"
""")
        os.chmod(fake_module, 0o755)

        pbs_env = self.env.copy()
        pbs_env["PBS_O_WORKDIR"] = mock_pkg
        pbs_env["PBS_JOBID"] = "1385999.mmaster02"

        res = subprocess.run(
            ["bash", os.path.join(mock_pkg, "F43PRE3_GEOM.pbs")],
            cwd=self.temp_dir,
            env=pbs_env,
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0, f"PBS script failed: {res.stdout}\n{res.stderr}")
        self.assertIn("[F43PRE3_GEOM] working_directory =", res.stdout)
        self.assertIn("10d4fb75cc97d92fbb1491361624e92f4cc4269ed40e4420164af28ed15207ee", res.stdout)

    def test_D_pbs_script_executed_from_scheduler_spool_directory(self):
        # Create isolated mock package directory in temp_dir
        mock_pkg = os.path.join(self.temp_dir, "mock_pkg_spool")
        shutil.copytree(PACKAGE_DIR, mock_pkg)

        spool_dir = os.path.join(self.temp_dir, "var", "spool", "pbs", "spool")
        os.makedirs(spool_dir, exist_ok=True)
        spool_pbs = os.path.join(spool_dir, "1385460.OU")
        shutil.copy(os.path.join(mock_pkg, "F43PRE3_GEOM.pbs"), spool_pbs)

        fake_abaqus = os.path.join(self.fake_bin_dir, "abaqus")
        with open(fake_abaqus, "w") as f:
            f.write("""#!/bin/bash
touch F43PRE3_GEOM.odb
exit 0
""")
        os.chmod(fake_abaqus, 0o755)

        fake_module = os.path.join(self.fake_bin_dir, "module")
        with open(fake_module, "w") as f:
            f.write("""#!/bin/bash
echo "Module command mock"
""")
        os.chmod(fake_module, 0o755)

        pbs_env = self.env.copy()
        pbs_env["PBS_O_WORKDIR"] = mock_pkg
        pbs_env["PBS_JOBID"] = "1385460.mmaster02"

        res = subprocess.run(
            ["bash", spool_pbs],
            cwd=spool_dir,
            env=pbs_env,
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0, f"Spooled PBS script failed: {res.stdout}\n{res.stderr}")
        self.assertIn("PBS_SPOOL_DIR =", res.stdout)
        self.assertIn(os.path.realpath(mock_pkg), res.stdout)


    def test_E_historical_1385460_failure_mode_prevention(self):
        # Verify that running PBS without changing directory to PACKAGE_DIR fails if PBS_O_WORKDIR points to repo root
        fake_module = os.path.join(self.fake_bin_dir, "module")
        with open(fake_module, "w") as f:
            f.write("echo mock")
        os.chmod(fake_module, 0o755)

        bad_env = self.env.copy()
        bad_env["PBS_O_WORKDIR"] = REPO_ROOT

        res = subprocess.run(
            ["bash", PBS_PATH],
            cwd=REPO_ROOT,
            env=bad_env,
            capture_output=True,
            text=True
        )
        self.assertNotEqual(res.returncode, 0, "PBS script should fail closed when PBS_O_WORKDIR is repo root")
        self.assertIn("F43PRE3_GEOM.inp missing", res.stderr)

    def test_F_negative_contract_missing_pbs_o_workdir(self):
        bad_env = self.env.copy()
        if "PBS_O_WORKDIR" in bad_env:
            del bad_env["PBS_O_WORKDIR"]

        res = subprocess.run(
            ["bash", PBS_PATH],
            cwd=PACKAGE_DIR,
            env=bad_env,
            capture_output=True,
            text=True
        )
        self.assertNotEqual(res.returncode, 0, "PBS script must fail if PBS_O_WORKDIR is missing")
        self.assertIn("PBS_O_WORKDIR is required", res.stderr)

    def test_G_negative_contract_input_sha_mismatch(self):
        # Create temp package dir with corrupted input file
        corrupt_pkg = os.path.join(self.temp_dir, "corrupt_pkg")
        shutil.copytree(PACKAGE_DIR, corrupt_pkg)
        with open(os.path.join(corrupt_pkg, "F43PRE3_GEOM.inp"), "a") as f:
            f.write("\n** CORRUPTED LINE\n")

        fake_module = os.path.join(self.fake_bin_dir, "module")
        with open(fake_module, "w") as f:
            f.write("echo mock")
        os.chmod(fake_module, 0o755)



        bad_env = self.env.copy()
        bad_env["PBS_O_WORKDIR"] = corrupt_pkg

        res = subprocess.run(
            ["bash", os.path.join(corrupt_pkg, "F43PRE3_GEOM.pbs")],
            cwd=corrupt_pkg,
            env=bad_env,
            capture_output=True,
            text=True
        )
        self.assertNotEqual(res.returncode, 0, "PBS script must fail on input deck SHA mismatch")
        self.assertIn("Input deck SHA mismatch", res.stderr)

if __name__ == "__main__":
    unittest.main()
