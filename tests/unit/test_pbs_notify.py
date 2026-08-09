#!/usr/bin/env python3
"""Offline unit tests for PBS Telegram notification helper and traps."""

import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PBS_NOTIFY_SH = ROOT / "scripts/hpc/pbs_notify.sh"
TELEGRAM_NOTIFY_PY = ROOT / "scripts/hpc/telegram_notify.py"


class TestPBSNotify(unittest.TestCase):
    def setUp(self) -> None:
        self.work_dir = ROOT / "tests/unit/_tmp_pbs_notify_test"
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
        self.work_dir.mkdir(parents=True)
        self.notify_log = self.work_dir / "telegram_notify.log"

    def tearDown(self) -> None:
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir, ignore_errors=True)

    def _run_bash_trap_simulation(self, sim_script_body: str, env_vars: dict | None = None) -> tuple[int, str]:
        if self.notify_log.exists():
            self.notify_log.unlink()
        script_path = self.work_dir / "sim_job.sh"

        rel_notify_sh = PBS_NOTIFY_SH.relative_to(ROOT).as_posix()
        rel_log = self.notify_log.relative_to(ROOT).as_posix()
        rel_work = self.work_dir.relative_to(ROOT).as_posix()

        full_script = f"""#!/usr/bin/env bash
PROJECT_HOME="."
export PBS_NOTIFY_LOG="{rel_log}"
export PBS_JOBID="99999.testnode"
export PBS_JOBNAME="unit_test_job"
export SCRATCH_RUN="{rel_work}"

source "{rel_notify_sh}"
pbs_notify_install_traps

{sim_script_body}
"""
        script_path.write_bytes(full_script.replace("\r\n", "\n").encode("utf-8"))

        env = dict(os.environ)
        env["PROJECT_HOME"] = "."
        env["PBS_NOTIFY_LOG"] = rel_log
        env["PBS_JOBID"] = "99999.testnode"
        env["PBS_JOBNAME"] = "unit_test_job"
        env["SCRATCH_RUN"] = rel_work
        if env_vars:
            env.update(env_vars)

        rel_script = script_path.relative_to(ROOT).as_posix()
        proc = subprocess.run(
            ["bash", rel_script],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
        )
        log_text = self.notify_log.read_text(encoding="utf-8") if self.notify_log.is_file() else ""
        return proc.returncode, log_text

    def test_begin_notification_logged(self) -> None:
        sim = """
pbs_notify_begin
exit 0
"""
        rc, log = self._run_bash_trap_simulation(sim)
        self.assertEqual(rc, 0)
        self.assertIn("EVENT: BEGIN", log)
        self.assertIn("EVENT: PASS", log)

    def test_exit_code_zero_produces_pass(self) -> None:
        sim = """
pbs_notify_begin
exit 0
"""
        rc, log = self._run_bash_trap_simulation(sim)
        self.assertEqual(rc, 0)
        self.assertIn("EVENT: PASS", log)

    def test_nonzero_exit_produces_fail(self) -> None:
        sim = """
pbs_notify_begin
exit 12
"""
        rc, log = self._run_bash_trap_simulation(sim)
        self.assertEqual(rc, 12)
        self.assertIn("EVENT: FAIL", log)


    def test_signal_exit_143_produces_aborted(self) -> None:
        sim = """
pbs_notify_begin
exit 143
"""
        rc, log = self._run_bash_trap_simulation(sim)
        self.assertEqual(rc, 143)
        self.assertIn("EVENT: ABORTED", log)

    def test_signal_exit_137_produces_aborted(self) -> None:
        sim = """
pbs_notify_begin
exit 137
"""
        rc, log = self._run_bash_trap_simulation(sim)
        self.assertEqual(rc, 137)
        self.assertIn("EVENT: ABORTED", log)

    def test_notification_failure_does_not_alter_scientific_exit_code(self) -> None:
        broken_notifier = self.work_dir / "broken_notify.py"
        broken_notifier.write_text("import sys; sys.exit(1)\n", encoding="utf-8")
        rel_broken = broken_notifier.relative_to(ROOT).as_posix()

        sim = f"""
_PBS_NOTIFIER="{rel_broken}"
pbs_notify_begin
exit 42
"""
        rc, log = self._run_bash_trap_simulation(sim)
        self.assertEqual(rc, 42)

    def test_credentials_never_in_pbs_vars_or_repo_files(self) -> None:
        repo_files = [PBS_NOTIFY_SH, TELEGRAM_NOTIFY_PY]
        for path in repo_files:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("bot_token_secret_literal", text.lower())
            self.assertFalse(re.search(r"bot\d+:[A-Za-z0-9_-]{20,}", text))


if __name__ == "__main__":
    unittest.main()
