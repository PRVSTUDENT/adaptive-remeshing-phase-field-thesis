#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn52_package91_replay.py

Unit tests verifying Package 91: Instrumented C3 Replay for Authentic Gauss-Point History Recovery.
Governing Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: 2f22e848-495a-4355-b555-682cc793227e
Protocol Version: 2
"""
import unittest
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG91_DIR = REPO_ROOT / "models/pandey_kumar_mode1/91_c3_package91_instrumented_replay"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

class TestMode1Package91InstrumentedReplay(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PKG91_DIR.exists(), f"Package 91 directory missing: {PKG91_DIR}")
        self.inp_path = PKG91_DIR / "M1_C3_PACKAGE91_INSTRUMENTED_REPLAY.inp"
        self.uel_path = PKG91_DIR / "f42_mixed_uel.for"
        self.pbs_path = PKG91_DIR / "submit_M1_C3_PACKAGE91_INSTRUMENTED_REPLAY.pbs"
        self.dc_path = PKG91_DIR / "run_pkg91_datacheck.sh"
        self.manifest_path = PKG91_DIR / "PACKAGE_MANIFEST.json"
        self.auth_path = PKG91_DIR / "M1_C3_PACKAGE91_INSTRUMENTED_REPLAY_AUTHORIZATION.json"

    def test_file_presence_and_integrity(self):
        """Verify all required execution and qualification artifacts exist."""
        for p in [self.inp_path, self.uel_path, self.pbs_path, self.dc_path, self.manifest_path, self.auth_path]:
            self.assertTrue(p.exists(), f"Required file missing: {p}")
        
        # Verify 100% bitwise frozen UEL
        uel_hash = sha256_file(self.uel_path)
        self.assertEqual(uel_hash, FROZEN_UEL_HASH, "f42_mixed_uel.for must be 100% bitwise identical to frozen baseline!")

    def test_deck_structure_and_companion_elements(self):
        """Verify Layer 1, Layer 2, and Layer 3 companion elements in the input deck."""
        text = self.inp_path.read_text(encoding="utf-8")
        
        # Check Layer 1 (U1)
        self.assertIn("*Element, type=U1, elset=PHASE_QUADS", text)
        # Check Layer 2 (U2)
        self.assertIn("*Element, type=U2, elset=MECH_QUADS", text)
        # Check Layer 3 (CPE4, UMATELEM)
        self.assertIn("*Element, type=CPE4, elset=UMATELEM", text)
        
        # Check companion material definition
        self.assertIn("*Solid Section, elset=UMATELEM, material=DUMMY_MAT", text)
        self.assertIn("*Material, name=DUMMY_MAT", text)
        self.assertIn("*User Material, constants=3", text)
        self.assertIn("210.0, 0.3, 2650.0", text)
        self.assertIn("*Depvar", text)

        # Count Layer 3 elements (IDs 5301..7950)
        l3_section = text.split("*Element, type=CPE4, elset=UMATELEM\n")[1].split("** ==========================================================\n** SOLID SECTION")[0].strip()
        l3_lines = [l.strip() for l in l3_section.splitlines() if l.strip()]
        self.assertEqual(len(l3_lines), 2650, f"Expected 2650 Layer 3 elements, found {len(l3_lines)}")

        # Verify element numbering
        first_elem = int(l3_lines[0].split(",")[0])
        last_elem = int(l3_lines[-1].split(",")[0])
        self.assertEqual(first_elem, 5301)
        self.assertEqual(last_elem, 7950)

    def test_step_sequence_and_history_output(self):
        """Verify 4 steps and Step 4 companion SDV element output."""
        text = self.inp_path.read_text(encoding="utf-8")
        
        step_names = []
        for line in text.splitlines():
            if line.upper().startswith("*STEP,"):
                for part in line.split(","):
                    if "NAME=" in part.upper():
                        step_names.append(part.split("=")[1].strip())
        
        expected_steps = [
            "STATE_INJECTION",
            "MECH_REEQUIL_FROZEN_DAMAGE",
            "STAGGERED_PHASE_SUBPROBLEM",
            "FORWARD_CONTINUATION"
        ]
        self.assertEqual(step_names, expected_steps)

        # Verify Step 4 has Element Output for UMATELEM with SDV
        step4_text = text.split("*Step, name=FORWARD_CONTINUATION")[1]
        self.assertIn("*Element Output, elset=UMATELEM", step4_text)
        self.assertIn("SDV", step4_text)

    def test_step4_active_set_irreversibility_protection(self):
        """Verify Step 4 clamps behind-tip nodes to prevent interface diffusion and healing."""
        text = self.inp_path.read_text(encoding="utf-8")
        step4_text = text.split("*Step, name=FORWARD_CONTINUATION")[1].split("*End Step")[0]
        
        # Extract DOF 3 boundary lines in Step 4
        bnd_lines = [l.strip() for l in step4_text.splitlines() if ", 3, 3," in l]
        # Should have 2,420 clamped nodes
        self.assertEqual(len(bnd_lines), 2420, f"Expected 2420 clamped nodes in Step 4, found {len(bnd_lines)}")
        
        clamped_nids = set(int(l.split(",")[0].strip()) for l in bnd_lines)
        
        # Critical test: behind-tip nodes 1794, 1795, 1796 MUST be clamped to prevent delta_d = -0.000169 healing
        self.assertIn(1794, clamped_nids, "Node 1794 behind slit tip must be clamped to prevent healing")
        self.assertIn(1795, clamped_nids, "Node 1795 behind slit tip must be clamped to prevent healing")
        self.assertIn(1796, clamped_nids, "Node 1796 behind slit tip must be clamped to prevent healing")

    def test_dual_channel_notifications_in_pbs(self):
        """Verify PBS script adheres to the Mandatory Dual-Channel Notification Policy."""
        pbs_text = self.pbs_path.read_text(encoding="utf-8")
        self.assertIn("#PBS -m abe", pbs_text)
        self.assertIn("#PBS -M pr21vyci@mailserver.tu-freiberg.de", pbs_text)
        self.assertIn("job_notifications.sh", pbs_text)
        self.assertIn("notification_load_config", pbs_text)
        self.assertIn("notification_install_terminal_trap", pbs_text)
        self.assertIn("notify_start", pbs_text)

    def test_manifest_and_authorization_consistency(self):
        """Verify package manifest and authorization JSON schemas and hashes."""
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        with open(self.auth_path, "r", encoding="utf-8") as f:
            auth = json.load(f)

        self.assertEqual(manifest["job_name"], "M1_C3_PACKAGE91_INSTRUMENTED_REPLAY")
        self.assertEqual(manifest["resources"]["cpus"], 1)
        self.assertEqual(manifest["resources"]["memory_gb"], 8)
        self.assertEqual(manifest["discretization"]["total_gauss_points"], 10600)
        self.assertEqual(manifest["user_subroutine_sha256"], FROZEN_UEL_HASH)
        self.assertEqual(manifest["input_deck_sha256"], sha256_file(self.inp_path))
        self.assertEqual(auth["jobs"][0]["id"], "M1_C3_PACKAGE91_INSTRUMENTED_REPLAY")

if __name__ == "__main__":
    unittest.main()
