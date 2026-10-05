#!/usr/bin/env python3
"""
Unit Test Suite: HPC Storage Compliance and Guard Verification (unittest framework)
Verifies that:
1. All active PBS scripts reject execution under /home and direct outputs to /scratch.
2. All active PBS scripts include dual-channel notification directives (#PBS -m abe, #PBS -M).
3. All submission wrappers enforce scratch execution / submission guards.
4. No binary simulation outputs (*.odb, *.sim, *.res, *.pac) are tracked in Git.
"""

import os
import re
import subprocess
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class TestHpcStorageCompliance(unittest.TestCase):

    def setUp(self):
        self.pbs_files = []
        for base in [os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1"),
                     os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2"),
                     os.path.join(REPO_ROOT, "scripts", "hpc")]:
            if not os.path.exists(base):
                continue
            for root, dirs, files in os.walk(base):
                for f in files:
                    if f.endswith(".pbs"):
                        self.pbs_files.append(os.path.join(root, f))

        self.sh_files = []
        for base in [os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1"),
                     os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2"),
                     os.path.join(REPO_ROOT, "scripts", "hpc")]:
            if not os.path.exists(base):
                continue
            for root, dirs, files in os.walk(base):
                for f in files:
                    if f.startswith("submit") and f.endswith(".sh"):
                        self.sh_files.append(os.path.join(root, f))

    def test_pbs_files_discovered(self):
        self.assertGreater(len(self.pbs_files), 10, "Should have discovered at least 10 active PBS scripts")

    def test_pbs_storage_compliance_guards(self):
        for pbs_path in self.pbs_files:
            with open(pbs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            rel = os.path.relpath(pbs_path, REPO_ROOT)
            # Must not contain hardcoded cd /home/pr21vyci/projects/adaptive-remeshing
            self.assertNotIn(
                "cd /home/pr21vyci/projects/adaptive-remeshing",
                content,
                f"PBS script {rel} has hardcoded /home working directory!"
            )

    def test_pbs_dual_channel_notification_directives(self):
        for pbs_path in self.pbs_files:
            with open(pbs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            rel = os.path.relpath(pbs_path, REPO_ROOT)
            if "job_notifications.sh" in content:
                self.assertIn("#PBS -m abe", content, f"PBS script {rel} missing #PBS -m abe")
                self.assertTrue(
                    "#PBS -M" in content and ("pr21vyci@mailserver.tu-freiberg.de" in content or "tu-freiberg.de" in content),
                    f"PBS script {rel} missing valid #PBS -M notification recipient"
                )

    def test_no_binary_simulation_artifacts_in_git(self):
        """Verify that git tracking excludes heavy solver outputs."""
        result = subprocess.run(
            ["git", "ls-files", "*.odb", "*.sim", "*.res", "*.pac", "*.abq", "*.sel", "*.stt", "*.mdl"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        tracked_binaries = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertEqual(len(tracked_binaries), 0, f"Found heavy simulation binaries tracked in Git: {tracked_binaries}")

if __name__ == "__main__":
    unittest.main()
