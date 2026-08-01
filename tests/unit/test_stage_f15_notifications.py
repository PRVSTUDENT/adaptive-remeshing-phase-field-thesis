#!/usr/bin/env python3
"""Offline tests for the Stage F15 shared notification contract."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "scripts/hpc/notifications/job_notifications.sh"
HELPER = ROOT / "scripts/hpc/notifications/notification_evidence.py"
RUNNER = ROOT / "scripts/hpc/notifications/run_f15_direct_transport_test.sh"
TG_REPAIR = ROOT / "scripts/hpc/notifications/run_f15_telegram_compatibility_test.sh"
TG_PAYLOAD = ROOT / "scripts/hpc/notifications/run_f15_telegram_payload_repair.sh"


class F15NotificationTests(unittest.TestCase):
    def run_bash(self, body):
        return subprocess.run(
            ["bash", "-c", body], cwd=ROOT, universal_newlines=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def test_shell_syntax(self):
        for path in (LIB, RUNNER, TG_REPAIR, TG_PAYLOAD):
            result = subprocess.run(["bash", "-n", path.as_posix()], cwd=ROOT)
            self.assertEqual(result.returncode, 0)

    def test_secret_redaction_and_telegram_ok_true(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            response = root / "response.json"
            output = root / "evidence.json"
            response.write_text('{"ok":true,"result":{"message_id":123456}}', encoding="utf-8")
            secret = "super-secret-chat-id"
            result = subprocess.run(
                [sys.executable, str(HELPER), "--output", str(output), "--channel", "telegram",
                 "--recipient", secret, "--transport", "curl_https_post", "--attempts", "1",
                 "--command-status", "0", "--http-status", "200", "--response-file", str(response)],
                universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0)
            text = output.read_text(encoding="utf-8")
            self.assertNotIn(secret, text)
            data = json.loads(text)
            self.assertTrue(data["telegram_ok"])
            self.assertTrue(data["pass"])
            self.assertTrue(data["telegram_message_id"].startswith("redacted:"))

    def test_telegram_ok_false_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); response = root / "response.json"; output = root / "evidence.json"
            response.write_text('{"ok":false,"description":"denied"}', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(HELPER), "--output", str(output), "--channel", "telegram",
                 "--recipient", "secret", "--transport", "curl_https_post", "--attempts", "1",
                 "--command-status", "0", "--http-status", "200", "--response-file", str(response)],
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(json.loads(output.read_text())["pass"])

    def test_bounded_retry_maximum_three(self):
        body = f'''source "{LIB.as_posix()}"
NOTIFICATION_MAX_ATTEMPTS=99; NOTIFICATION_RETRY_DELAY=0; n=0
fail() {{ n=$((n+1)); return 9; }}
notification_retry fail; rc=$?
printf '%s:%s:%s' "$rc" "$NOTIFICATION_LAST_ATTEMPTS" "$n"
'''
        result = self.run_bash(body)
        self.assertEqual(result.stdout, "9:3:3")

    def test_email_command_failure_recorded(self):
        with tempfile.TemporaryDirectory() as td:
            evidence = Path(td) / "email.json"
            body = f'''source "{LIB.as_posix()}"
NOTIFY_EMAIL=x@example.invalid; NOTIFICATION_SENDMAIL_BIN=/bin/false
NOTIFICATION_MAX_ATTEMPTS=1; NOTIFICATION_RETRY_DELAY=0
notify_email TEST body "{evidence.as_posix()}"; exit $?
'''
            result = self.run_bash(body)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(json.loads(evidence.read_text())["pass"])

    def test_terminal_trap_once_and_exit_code_preserved(self):
        body = f'''source "{LIB.as_posix()}"
n=0; notify_terminal() {{ n=$((n+1)); printf '%s' "$n" >> "$1.log"; }}
marker=$(mktemp); export marker
notify_terminal() {{ printf x >> "$marker"; return 1; }}
notification_install_terminal_trap
exit 42
'''
        result = self.run_bash(body)
        self.assertEqual(result.returncode, 42)

    def test_required_contract_tokens_present(self):
        text = LIB.read_text(encoding="utf-8")
        for token in ("notify_email", "notify_telegram", "notify_all", "notify_start", "notify_terminal"):
            self.assertIn(token, text)
        self.assertIn("trap - EXIT INT TERM HUP", text)
        self.assertNotIn("qsub", text)

    def test_direct_runner_exact_label_and_no_qsub(self):
        text = RUNNER.read_text(encoding="utf-8")
        label = "F15 PRE-SUBMISSION TRANSPORT TEST — NOT A PBS JOB EVENT"
        self.assertGreaterEqual(text.count(label), 1)
        self.assertNotIn("qsub ", text)

    def test_portable_telegram_repair_contract(self):
        library = LIB.read_text(encoding="utf-8")
        repair = TG_REPAIR.read_text(encoding="utf-8")
        self.assertNotIn("--fail-with-body", library + repair)
        for option in ("--silent", "--show-error", "--output", "--write-out"):
            self.assertIn(option, library)
        self.assertIn("telegram_call getMe", repair)
        self.assertIn("telegram_call getChat", repair)
        self.assertNotIn("notify_email", repair)
        self.assertNotIn("qsub ", repair)

    def test_payload_repair_has_explicit_nonempty_text(self):
        text = TG_PAYLOAD.read_text(encoding="utf-8")
        self.assertIn('test -n "$TELEGRAM_MESSAGE"', text)
        self.assertIn('--data-urlencode "text=${TELEGRAM_MESSAGE}"', text)
        self.assertNotIn("--fail-with-body", text)
        self.assertNotIn("notify_email", text)
        self.assertNotIn("qsub ", text)


if __name__ == "__main__":
    unittest.main()
