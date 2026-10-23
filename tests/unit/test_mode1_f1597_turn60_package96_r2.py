#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn60_package96_r2.py
Unit test suite for Mode-I Method C Stage C1-2 Package 96-R2:
Inequality-Constrained State Transfer and Forward Continuation.
"""

import unittest
import hashlib
import json
import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/96_r2_c5_package96_r2_constrained_transfer"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

class TestPackage96R2(unittest.TestCase):
    def setUp(self):
        self.pkg_dir = PKG_DIR
        self.manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
        self.auth_path = PKG_DIR / "M1_C5_PACKAGE96_R2_TRANSFER_AUTHORIZATION.json"
        self.inp_path = PKG_DIR / "M1_C5_PACKAGE96_R2_TRANSFER.inp"
        self.pbs_path = PKG_DIR / "submit_M1_C5_PACKAGE96_R2_TRANSFER.pbs"
        self.state_table_path = PKG_DIR / "candidate_c5_frame7_mapped_state_table.csv"
        self.uel_path = PKG_DIR / "f42_mixed_uel.for"

    def test_frozen_uel_integrity(self):
        self.assertTrue(self.uel_path.exists())
        actual_hash = sha256_file(self.uel_path)
        self.assertEqual(actual_hash, FROZEN_UEL_HASH, "Frozen UEL hash mismatch!")

    def test_package_files_exist_and_hashes(self):
        self.assertTrue(self.manifest_path.exists())
        self.assertTrue(self.auth_path.exists())
        self.assertTrue(self.inp_path.exists())
        self.assertTrue(self.pbs_path.exists())
        self.assertTrue(self.state_table_path.exists())

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        for fname, recorded_hash in manifest["files"].items():
            fpath = self.pkg_dir / fname
            self.assertTrue(fpath.exists(), f"File {fname} missing from package!")
            self.assertEqual(sha256_file(fpath), recorded_hash, f"Hash mismatch for {fname}")

    def test_state_table_bounds_and_preservation(self):
        nodes = {}
        elem_h = {}
        with open(self.state_table_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            for r in reader:
                if r[0] == "NODE":
                    nid = int(r[1])
                    u1 = float(r[2])
                    u2 = float(r[3])
                    d = float(r[4])
                    raw_d = float(r[5])
                    nodes[nid] = (u1, u2, d, raw_d)
                elif r[0] == "ELEM_H":
                    eid = int(r[1])
                    h = [float(r[2]), float(r[3]), float(r[4]), float(r[5])]
                    elem_h[eid] = h

        self.assertEqual(len(nodes), 4610)
        self.assertEqual(len(elem_h), 4440)

        # Bounds checks
        all_d = [n[2] for n in nodes.values()]
        self.assertLessEqual(max(all_d), 1.00000000, "Damage exceeds 1.00000000!")
        self.assertGreaterEqual(min(all_d), 0.0, "Damage is negative!")

        # Irreversibility check against raw donor interpolation
        for nid, (u1, u2, d, raw_d) in nodes.items():
            self.assertGreaterEqual(d, raw_d - 1e-6, f"Node {nid} has healing: d={d} < raw_d={raw_d}")

        # History checks
        for eid, h_list in elem_h.items():
            self.assertEqual(len(h_list), 4)
            for ip_idx, h_val in enumerate(h_list):
                self.assertGreaterEqual(h_val, 0.0, f"Element {eid} IP {ip_idx} has negative H: {h_val}")

    def test_step4_active_set_partitioning(self):
        with open(self.inp_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        step4_idx = -1
        for i, l in enumerate(lines):
            if "*STEP, NAME=FORWARD_CONTINUATION" in l.upper():
                step4_idx = i
                break
        self.assertNotEqual(step4_idx, -1, "FORWARD_CONTINUATION step not found!")

        # Parse boundary conditions in Step 4
        clamped_bcs = {}
        in_bc = False
        for l in lines[step4_idx:]:
            u = l.strip().upper()
            if u.startswith("*BOUNDARY"):
                in_bc = True
                continue
            if u.startswith("*") and in_bc:
                if not u.startswith("**"):
                    break
            if in_bc:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 4 and parts[0].isdigit():
                    nid = int(parts[0])
                    dof_start = int(parts[1])
                    dof_end = int(parts[2])
                    val = float(parts[3])
                    if dof_start == 3 and dof_end == 3:
                        clamped_bcs[nid] = val

        self.assertEqual(len(clamped_bcs), 3808, f"Expected 3808 clamped nodes in Step 4, got {len(clamped_bcs)}")
        # Check upper bound clamp
        u_clamped = [nid for nid, val in clamped_bcs.items() if abs(val - 1.0) < 1e-6]
        self.assertEqual(len(u_clamped), 73, f"Expected 73 nodes in U clamped to 1.0, got {len(u_clamped)}")
        # Check free nodes count
        free_count = 4610 - len(clamped_bcs)
        self.assertEqual(free_count, 802, f"Expected 802 free nodes in Step 4, got {free_count}")

    def test_pbs_and_datacheck_scripts(self):
        pbs_bytes = self.pbs_path.read_bytes()
        self.assertNotIn(b"\r\n", pbs_bytes, "PBS script must use pure LF newlines!")
        self.assertIn(b"#PBS -m abe", pbs_bytes)
        self.assertIn(b"notification_install_terminal_trap", pbs_bytes)

        dc_path = PKG_DIR / "run_pkg96_r2_datacheck.sh"
        self.assertTrue(dc_path.exists())
        dc_bytes = dc_path.read_bytes()
        self.assertNotIn(b"\r\n", dc_bytes, "Datacheck script must use pure LF newlines!")

if __name__ == "__main__":
    unittest.main()
