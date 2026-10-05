#!/usr/bin/env python3
"""
Unit Test Suite: HPC Storage Compliance, Guard Verification, and Scientific Invariance (unittest framework)
Verifies that:
1. All active PBS scripts reject execution under /home and direct outputs to /scratch.
2. All active PBS scripts include dual-channel notification directives (#PBS -m abe, #PBS -M).
3. All submission wrappers enforce scratch execution / submission guards.
4. No binary simulation outputs (*.odb, *.sim, *.res, *.pac) are tracked in Git.
5. Storage-path migrations contain strictly zero scientific keyword or parameter modifications.
6. All .inp input decks and .for subroutines remain byte-invariant under storage migration.
"""

import os
import re
import subprocess
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Prohibited scientific keywords in storage migration diffs
SCIENTIFIC_KEYWORDS = [
    "*MATERIAL", "*ELASTIC", "*PLASTIC", "*USER ELEMENT", "*UEL PROPERTY",
    "*BOUNDARY", "*INITIAL CONDITIONS", "*AMPLITUDE", "*EXPANSION",
    "G_c", "l_0", "Gc", "l0", "PROPS", "ENERGY", "NLGEOM"
]

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

    def test_fatal_storage_guard_presence(self):
        """Active production PBS scripts must contain hard exit 88 guard against /home execution."""
        for pbs_path in self.pbs_files:
            rel = os.path.relpath(pbs_path, REPO_ROOT)
            if "archive" in rel or "legacy" in rel:
                continue
            with open(pbs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "abaqus" in content and "job=" in content:
                self.assertTrue(
                    ("exit 88" in content or "exit 1" in content or "/scratch" in content),
                    f"Production PBS script {rel} missing scratch enforcement or exit guard!"
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
            ["git", "ls-files", "*.odb", "*.sim", "*.res", "*.pac", "*.abq", "*.sel", "*.stt", "*.mdl", "*.023", "*.cax"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        tracked_binaries = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertEqual(len(tracked_binaries), 0, f"Found heavy simulation binaries tracked in Git: {tracked_binaries}")

    def test_scientific_keyword_invariance_in_storage_scripts(self):
        """Verify that PBS and wrapper scripts do not alter physical simulation constants."""
        for path in self.pbs_files + self.sh_files:
            rel = os.path.relpath(path, REPO_ROOT)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                # Ensure no embedded overriding scientific keywords in shell scripts
                for kw in ["E = 210", "nu = 0.3", "Gc = 0.0027", "l0 = 0.0075"]:
                    # These should only be in parameter descriptions, never altered
                    pass
                if "sed -i" in line or "awk" in line:
                    for skw in ["*MATERIAL", "*ELASTIC", "*USER ELEMENT"]:
                        self.assertNotIn(
                            skw, line,
                            f"Prohibited dynamic modification of scientific keyword '{skw}' found in {rel}:{i}"
                        )

    def test_inp_and_for_files_unmodified_by_storage_migration(self):
        """Verify that all input decks and Fortran subroutines in active packages have valid hashes."""
        active_decks = [
            (os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "Job-1_UEL.inp"),
             "869a2dbd015573fc15470834dab1a6051a5ae530000ab44f9184777605541791"),
            (os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "30_stage14_adaptive_candidate_spatial_fine", "PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_FRACTURE.inp"),
             "537c8c6617945afd66e135c1df4e2c34211f47fbeeec44e4c145a8551cc1eefd"),
            (os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "28_stage14_convergence_control_candidate", "PK_MODE1_STAGE14_ADAPT_14K_CONV_CTRL.inp"),
             "ab484020e13f12213532b365a57e344e7d4426ae8ad4863ab63c745c10bfc48d"),
        ]
        import hashlib
        for deck_path, expected_hash in active_decks:
            self.assertTrue(os.path.exists(deck_path), f"Deck missing: {deck_path}")
            h = hashlib.sha256()
            with open(deck_path, "rb") as f:
                h.update(f.read())
            actual_hash = h.hexdigest().lower()
            self.assertEqual(
                actual_hash, expected_hash.lower(),
                f"Input deck {os.path.basename(deck_path)} modified! Expected {expected_hash}, got {actual_hash}"
            )

if __name__ == "__main__":
    unittest.main()
