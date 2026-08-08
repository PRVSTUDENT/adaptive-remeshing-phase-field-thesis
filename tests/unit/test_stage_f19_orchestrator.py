import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/hpc/stage_f/submit_stage_f19_three_job_batch.sh"
PACKAGES = (
    ROOT / "models/generated/mode_ii/f19_penalty_active_rollback_control",
    ROOT / "models/generated/mode_ii/f19_penalty_active_rollback_forced",
    ROOT / "models/generated/mode_ii/f19_native_adaptive_region_repair",
)


class StageF19OrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="f19-orchestrator-"))
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.log = self.tmp / "qsub.log"
        self.count = self.tmp / "qsub.count"
        mock = self.bin / "qsub"
        mock.write_text(
            """#!/bin/bash
set -u
n=0; [ ! -f \"$MOCK_COUNT\" ] || n=$(cat \"$MOCK_COUNT\")
n=$((n+1)); printf '%s\\n' \"$n\" >\"$MOCK_COUNT\"
{ printf 'CALL=%s\\n' \"$n\"; for arg in \"$@\"; do printf 'ARG=%s\\n' \"$arg\"; done; } >>\"$MOCK_LOG\"
[ \"${MOCK_FAIL_CALL:-0}\" != \"$n\" ] || exit \"${MOCK_FAIL_RC:-73}\"
case \"${MOCK_RESPONSE_KIND:-valid}\" in
 valid) printf '%s.mmaster02\\n' \"$((900000+n))\" ;;
 empty) : ;;
 whitespace) printf '   \\n' ;;
 diagnostic) printf 'submission rejected\\n' ;;
 multiline) printf '900001.mmaster02\\nextra\\n' ;;
 malformed) printf 'job-id?\\n' ;;
esac
""",
            encoding="utf-8",
        )
        mock.chmod(mock.stat().st_mode | stat.S_IXUSR)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def env(self):
        env = os.environ.copy()
        env.update({
            "PATH": str(self.bin) + os.pathsep + env["PATH"],
            "MOCK_LOG": str(self.log),
            "MOCK_COUNT": str(self.count),
            "F19_ACTIVATE_SUBMISSION": "1",
            "F19_EXPLICIT_AUTHORIZATION": "1",
            "F19_CONTROL_PACKAGE_DIR": str(PACKAGES[0]),
            "F19_FORCED_PACKAGE_DIR": str(PACKAGES[1]),
            "F19_ADAPTIVE_PACKAGE_DIR": str(PACKAGES[2]),
            "F19_EVIDENCE_ROOT": str(self.tmp / "evidence"),
            "UNRELATED_SECRET": "must-not-be-exported",
        })
        return env

    def run_script(self, changes=None):
        self.log.unlink(missing_ok=True)
        self.count.unlink(missing_ok=True)
        env = self.env()
        env.update(changes or {})
        result = subprocess.run(["bash", str(SCRIPT)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        records = []
        if self.log.exists():
            for block in self.log.read_text(encoding="utf-8").split("CALL=")[1:]:
                lines = block.splitlines()
                records.append([line[4:] for line in lines[1:] if line.startswith("ARG=")])
        accounting = json.loads(result.stdout.splitlines()[-1])
        return result, records, accounting

    def test_success_exact_argv_and_dependency(self):
        result, calls, accounting = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(calls), 3)
        names = ("M2IRRROLLCTL5.pbs", "M2IRRROLLFORCE5.pbs", "M2RMREG6.pbs")
        lanes = ("control", "forced", "adaptive")
        for i, (package, name, lane) in enumerate(zip(PACKAGES, names, lanes)):
            exported = f"F19_PACKAGE_DIR={package},F19_EVIDENCE_DIR={self.tmp / 'evidence' / lane}"
            expected = ["-v", exported]
            if i == 2:
                expected += ["-W", "depend=afterany:900001.mmaster02"]
            expected += [str(package / name)]
            self.assertEqual(calls[i], expected)
            self.assertNotIn("-V", calls[i])
            self.assertNotIn("UNRELATED_SECRET", " ".join(calls[i]))
            self.assertEqual(set(calls[i][1].split(",")[j].split("=", 1)[0] for j in range(2)),
                             {"F19_PACKAGE_DIR", "F19_EVIDENCE_DIR"})
        self.assertEqual((accounting["qsub_attempts"], accounting["successful_submissions"], accounting["failed_qsub_attempts"]), (3, 3, 0))

    def test_activation_gates_make_zero_calls(self):
        for key, value in (("F19_ACTIVATE_SUBMISSION", "0"), ("F19_EXPLICIT_AUTHORIZATION", "0")):
            with self.subTest(key=key):
                result, calls, accounting = self.run_script({key: value})
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, [])
                self.assertEqual(accounting["qsub_attempts"], 0)

    def test_unsafe_and_missing_paths_make_zero_calls(self):
        cases = {
            "relative_package": {"F19_CONTROL_PACKAGE_DIR": "relative"},
            "relative_evidence": {"F19_EVIDENCE_ROOT": "relative"},
            "comma": {"F19_EVIDENCE_ROOT": str(self.tmp / "bad,path")},
            "newline": {"F19_EVIDENCE_ROOT": str(self.tmp / "bad\npath")},
            "missing": {"F19_CONTROL_PACKAGE_DIR": str(self.tmp / "missing")},
        }
        for name, changes in cases.items():
            with self.subTest(name=name):
                result, calls, accounting = self.run_script(changes)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, [])
                self.assertEqual(accounting["qsub_attempts"], 0)

    def test_unreadable_pbs_makes_zero_calls(self):
        if os.geteuid() == 0:
            self.skipTest("root can read permission-zero files")
        package = self.tmp / "package"
        shutil.copytree(PACKAGES[0], package)
        pbs = package / "M2IRRROLLCTL5.pbs"
        pbs.chmod(0)
        result, calls, accounting = self.run_script({"F19_CONTROL_PACKAGE_DIR": str(package)})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])
        self.assertEqual(accounting["qsub_attempts"], 0)

    def test_invalid_qsub_responses_stop_after_first_call(self):
        for kind in ("empty", "whitespace", "diagnostic", "multiline", "malformed"):
            with self.subTest(kind=kind):
                result, calls, accounting = self.run_script({"MOCK_RESPONSE_KIND": kind})
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(len(calls), 1)
                self.assertEqual((accounting["qsub_attempts"], accounting["successful_submissions"], accounting["failed_qsub_attempts"]), (1, 0, 1))

    def test_each_qsub_failure_stops_without_retry(self):
        for selected in (1, 2, 3):
            with self.subTest(selected=selected):
                result, calls, accounting = self.run_script({"MOCK_FAIL_CALL": str(selected)})
                self.assertEqual(result.returncode, 73)
                self.assertEqual(len(calls), selected)
                self.assertLessEqual(len(calls), 3)
                self.assertEqual(accounting["qsub_attempts"], selected)
                self.assertEqual(accounting["successful_submissions"], selected - 1)
                self.assertEqual(accounting["failed_qsub_attempts"], 1)
                if selected == 1:
                    self.assertFalse(any("M2RMREG6.pbs" in " ".join(call) for call in calls))


if __name__ == "__main__":
    unittest.main()
