import os
import sys
import tempfile
import stat
import subprocess
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACKAGE_DIR = os.path.join(REPO_ROOT, "models", "generated", "mode_ii", "f43_stage_c_bridge")
WRAPPER_PATH = os.path.join(PACKAGE_DIR, "submit_f43pre3_geom.sh")

class TestFakeQsubMailContract(unittest.TestCase):

    def test_fake_qsub_receives_mail_options(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            args_log = os.path.join(tmp_dir, "qsub_args.log")
            fake_qsub = os.path.join(tmp_dir, "qsub")
            
            with open(fake_qsub, "w") as f:
                f.write("#!/bin/bash\n")
                f.write('echo "$@" > "{}"\n'.format(args_log))
                f.write('echo "999999.mmaster02"\n')
                f.write('exit 0\n')
            
            os.chmod(fake_qsub, stat.S_IRWXU)

            fake_qstat = os.path.join(tmp_dir, "qstat")
            with open(fake_qstat, "w") as f:
                f.write("#!/bin/bash\n")
                f.write('if [ "${1:-}" = "-u" ]; then exit 0; fi\n')
                f.write('echo "Job_Name = F43PRE3_GEOM"\n')
                f.write('echo "Mail_Points = abe"\n')
                f.write('echo "Mail_Users = pr21vyci@mailserver.tu-freiberg.de,Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de"\n')
                f.write('exit 0\n')
            
            os.chmod(fake_qstat, stat.S_IRWXU)

            env = os.environ.copy()
            env["PATH"] = "{}:{}".format(tmp_dir, env.get("PATH", ""))
            env["F43PRE3_SUBMISSION_APPROVED"] = "1"
            env["MAX_SUBMISSIONS"] = "1"
            env["REPLACEMENT_AUTHORIZED"] = "1"
            env["AUTOMATIC_RETRY"] = "false"
            env["DRY_RUN"] = "0"
            env["EXPECTED_PREP_SHA"] = "P43PRE3-R4"
            env["EXPECTED_QUAL_SHA"] = "Q43PRE3-R4"

            res = subprocess.run(
                ["bash", WRAPPER_PATH],
                cwd=PACKAGE_DIR,
                env=env,
                capture_output=True,
                text=True
            )

            self.assertEqual(res.returncode, 0, f"Wrapper failed with stdout: {res.stdout}, stderr: {res.stderr}")
            
            with open(args_log, "r") as f:
                qsub_args = f.read().strip()

            self.assertIn("-m abe", qsub_args, f"qsub missing -m abe flag. Got: {qsub_args}")
            self.assertIn("-M pr21vyci@mailserver.tu-freiberg.de,Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de", qsub_args, f"qsub missing both email recipients in -M. Got: {qsub_args}")

if __name__ == "__main__":
    unittest.main()
