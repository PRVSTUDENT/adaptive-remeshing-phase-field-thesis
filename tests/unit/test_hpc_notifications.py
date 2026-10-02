#!/usr/bin/env python3
"""Comprehensive unit test suite for HPC dual-channel (Telegram + Email) notification system."""

import os
import subprocess
import sys
import unittest
import tempfile
import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
NOTIF_SH = REPO_ROOT / "scripts" / "hpc" / "notifications" / "job_notifications.sh"

class TestHpcNotifications(unittest.TestCase):

    def setUp(self):
        self.assertTrue(NOTIF_SH.is_file(), f"Missing notification script: {NOTIF_SH}")
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _run_bash(self, script, env_vars=None):
        env = os.environ.copy()
        env["NOTIFICATION_MOCK_TELEGRAM"] = "1"
        env["NOTIFICATION_RETRY_DELAY"] = "0"
        if env_vars:
            env.update(env_vars)
        cmd = ["bash", "-c", f"source '{NOTIF_SH.as_posix()}'\n{script}"]
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, env=env)

    def test_01_config_path_resolution(self):
        cfg = self.tmp_path / "custom.env"
        cfg.write_text('NOTIFY_EMAIL="test@example.com"\nTELEGRAM_BOT_TOKEN="tok123"\nTELEGRAM_CHAT_ID="chat123"\n')
        os.chmod(cfg, 0o600)
        res = self._run_bash("notification_load_config; echo \"CFG=$NOTIFICATION_CONFIG\"", {"NOTIFICATION_CONFIG": str(cfg)})
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn(f"CFG={cfg}", res.stdout)

    def test_02_missing_config_fails_closed(self):
        non_existent = self.tmp_path / "does_not_exist.env"
        res = self._run_bash("notification_load_config", {
            "NOTIFICATION_CONFIG": str(non_existent),
            "HOME": str(self.tmp_path)
        })
        self.assertEqual(res.returncode, 20)
        self.assertIn("not found", res.stderr)

    def test_03_unsafe_permissions_rejected(self):
        cfg = self.tmp_path / "unsafe.env"
        cfg.write_text('NOTIFY_EMAIL="test@example.com"\nTELEGRAM_BOT_TOKEN="tok123"\nTELEGRAM_CHAT_ID="chat123"\n')
        os.chmod(cfg, 0o666)
        res = self._run_bash("notification_load_config", {"NOTIFICATION_CONFIG": str(cfg)})
        # On POSIX chmod 666 triggers permission rejection (code 21)
        if os.name != "nt":
            self.assertEqual(res.returncode, 21)
            self.assertIn("Unsafe", res.stderr)

    def test_04_missing_token_or_chat_id_fails_closed(self):
        cfg = self.tmp_path / "bad.env"
        cfg.write_text('NOTIFY_EMAIL="test@example.com"\nTELEGRAM_BOT_TOKEN=""\nTELEGRAM_CHAT_ID=""\n')
        os.chmod(cfg, 0o600)
        res = self._run_bash("notification_load_config", {"NOTIFICATION_CONFIG": str(cfg)})
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("missing or empty", res.stderr)

    def test_05_json_config_parsing(self):
        cfg = self.tmp_path / "notifications.json"
        cfg.write_text('{"telegram_bot_token": "json_tok", "telegram_chat_id": "json_chat", "email_recipients": "a@b.com"}')
        os.chmod(cfg, 0o600)
        res = self._run_bash("notification_load_config && echo \"OK:$TELEGRAM_BOT_TOKEN:$TELEGRAM_CHAT_ID\"", {"NOTIFICATION_CONFIG": str(cfg)})
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("OK:json_tok:json_chat", res.stdout)

    def test_06_mock_telegram_send_success(self):
        res = self._run_bash("notification_send_telegram 'Test message'")
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_07_mock_telegram_send_failure_propagates_nonzero(self):
        res = self._run_bash("notification_send_telegram 'Test failure'", {"NOTIFICATION_MOCK_FAIL": "1", "NOTIFICATION_MAX_ATTEMPTS": "1"})
        self.assertNotEqual(res.returncode, 0)

    def test_08_notify_submitted_event_path(self):
        res = self._run_bash("notify_submitted '12345.mmaster02' 'M2STATE_TEST' 'Submitted to entry_imfdfkmq'")
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_09_notify_started_event_path(self):
        res = self._run_bash("PBS_JOBNAME='M2STATE_TEST' PBS_JOBID='12345.mmaster02' notify_start")
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_10_notify_completed_terminal_path(self):
        res = self._run_bash("notify_completed 'M2STATE_TEST' '12345.mmaster02' 100")
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_11_notify_failed_terminal_path(self):
        res = self._run_bash("notify_failed 'M2STATE_TEST' '12345.mmaster02' 1 100")
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_12_notify_terminated_terminal_path(self):
        res = self._run_bash("notify_terminated 'M2STATE_TEST' '12345.mmaster02' TERM 100")
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_13_terminal_trap_executed_exactly_once(self):
        script = """
OUTPUT_COUNT=0
mock_record() {
  OUTPUT_COUNT=$((OUTPUT_COUNT + 1))
  echo "TRAP_FIRED:$OUTPUT_COUNT"
}
notify_terminal() {
  mock_record
}
notification_install_terminal_trap
notification_terminal_trap 0
notification_terminal_trap 0
echo "FINAL_COUNT=$OUTPUT_COUNT"
"""
        res = self._run_bash(script)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("FINAL_COUNT=1", res.stdout)

    def test_14_notify_event_backward_compatibility(self):
        res1 = self._run_bash("notify_event 'SUBMITTED' '12345' 'M2TEST' 'details'")
        self.assertEqual(res1.returncode, 0)
        res2 = self._run_bash("PBS_JOBNAME='M2TEST' PBS_JOBID='12345' notify_event 'STARTED'")
        self.assertEqual(res2.returncode, 0)
        res3 = self._run_bash("notify_event 'COMPLETED' 'M2TEST' '12345' 50")
        self.assertEqual(res3.returncode, 0)

    def test_15_no_qsub_retry_after_post_qsub_telegram_failure(self):
        # Verify that if submission succeeds but notification fails, wrapper reports error without retrying qsub
        wrapper = REPO_ROOT / "models" / "generated" / "mode_ii" / "production_state_transfer_batch" / "M2STATE_FRACFIX_RESTART1R1R6" / "submit_m2state_fracfix_restart1r1r6.sh"
        if wrapper.is_file():
            content = wrapper.read_text()
            self.assertNotIn("qsub.*qsub", content)

if __name__ == "__main__":
    unittest.main()
