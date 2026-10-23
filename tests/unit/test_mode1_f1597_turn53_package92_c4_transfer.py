#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn53_package92_c4_transfer.py

Unit tests verifying Package 92: Error-Driven C3 -> C4 Nonmatching State Transfer Deck.
Governing Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: 15edb78c-2f6d-454e-96af-4518fca0ce6f
Protocol Version: 2
"""
import sys
import unittest
import hashlib
import json
import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG92_DIR = REPO_ROOT / "models/pandey_kumar_mode1/92_c4_package92_error_driven_transfer"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

class TestMode1Package92C4Transfer(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PKG92_DIR.exists(), f"Package 92 directory missing: {PKG92_DIR}")
        self.inp_path = PKG92_DIR / "M1_C4_PACKAGE92_TRANSFER.inp"
        self.uel_path = PKG92_DIR / "f42_mixed_uel.for"
        self.mesh_path = PKG92_DIR / "candidate_crack_band_mesh_c4.inp"
        self.table_path = PKG92_DIR / "candidate_c4_frame6_mapped_state_table.csv"
        self.pbs_path = PKG92_DIR / "submit_M1_C4_PACKAGE92_TRANSFER.pbs"
        self.dc_path = PKG92_DIR / "run_pkg92_datacheck.sh"
        self.manifest_path = PKG92_DIR / "PACKAGE_MANIFEST.json"
        self.auth_path = PKG92_DIR / "M1_C4_PACKAGE92_TRANSFER_AUTHORIZATION.json"

    def test_file_presence_and_uel_freeze(self):
        """Verify all execution and governance files exist and UEL is 100% bitwise frozen."""
        for p in [self.inp_path, self.uel_path, self.mesh_path, self.table_path, 
                  self.pbs_path, self.dc_path, self.manifest_path, self.auth_path]:
            self.assertTrue(p.exists(), f"Required file missing: {p}")
        self.assertEqual(sha256_file(self.uel_path), FROZEN_UEL_HASH)

    def test_discretization_and_layer_structure(self):
        """Verify 4,422 quads across Layer 1 (U1), Layer 2 (U2), and Layer 3 (CPE4, UMATELEM)."""
        text = self.inp_path.read_text(encoding="utf-8")
        
        self.assertIn("*Element, type=U1, elset=PHASE_QUADS", text)
        self.assertIn("*Element, type=U2, elset=MECH_QUADS", text)
        self.assertIn("*Element, type=CPE4, elset=UMATELEM", text)
        
        # Verify companion material constants
        self.assertIn("210.0, 0.3, 4422.0", text)
        self.assertIn("*Depvar\n20", text)

        # Count Layer 3 elements (IDs 8845..13266)
        l3_section = text.split("*Element, type=CPE4, elset=UMATELEM\n")[1].split("** ==========================================================\n** SOLID SECTION")[0].strip()
        l3_lines = [l.strip() for l in l3_section.splitlines() if l.strip()]
        self.assertEqual(len(l3_lines), 4422, f"Expected 4422 Layer 3 elements, found {len(l3_lines)}")
        self.assertEqual(int(l3_lines[0].split(",")[0]), 8845)
        self.assertEqual(int(l3_lines[-1].split(",")[0]), 13266)

    def test_mapped_state_table_integrity(self):
        """Verify mapped nodal damage and Gauss-point history in the transfer table."""
        with open(self.table_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, ["record_type", "id", "val1", "val2", "val3", "val4"])
            rows = list(reader)

        node_rows = [r for r in rows if r[0] == "NODE"]
        elem_rows = [r for r in rows if r[0] == "ELEM_H"]

        self.assertEqual(len(node_rows), 4588, "Expected 4588 mapped nodes")
        self.assertEqual(len(elem_rows), 4422, "Expected 4422 mapped elements")

        d_vals = [float(r[4]) for r in node_rows]
        self.assertGreaterEqual(min(d_vals), 0.0)
        self.assertLessEqual(max(d_vals), 1.0)
        self.assertGreater(max(d_vals), 0.90, "Peak damage near crack tip must exceed 0.90")

        # Verify all integration point histories are non-negative
        for r in elem_rows:
            for val in [float(r[2]), float(r[3]), float(r[4]), float(r[5])]:
                self.assertGreaterEqual(val, 0.0)

    def test_step_sequence_and_active_set(self):
        """Verify 4 named steps and Step 4 active-set partitioning."""
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

        # Check Step 4 boundary constraints: exactly 4,151 clamped nodes
        step4_text = text.split("*Step, name=FORWARD_CONTINUATION")[1].split("*End Step")[0]
        bnd_lines = [l.strip() for l in step4_text.splitlines() if ", 3, 3," in l]
        self.assertEqual(len(bnd_lines), 4151, f"Expected 4151 clamped nodes in Step 4, found {len(bnd_lines)}")

    def test_dual_channel_notifications_in_pbs(self):
        """Verify PBS script adheres to the Mandatory Dual-Channel Notification Policy."""
        pbs_text = self.pbs_path.read_text(encoding="utf-8")
        self.assertIn("#PBS -m abe", pbs_text)
        self.assertIn("#PBS -M pr21vyci@mailserver.tu-freiberg.de", pbs_text)
        self.assertIn("job_notifications.sh", pbs_text)
        self.assertIn("notification_load_config", pbs_text)
        self.assertIn("notification_install_terminal_trap", pbs_text)
        self.assertIn("notify_start", pbs_text)

if __name__ == "__main__":
    unittest.main()
