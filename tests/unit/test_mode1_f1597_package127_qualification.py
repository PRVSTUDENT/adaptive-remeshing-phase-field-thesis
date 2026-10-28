# -*- coding: utf-8 -*-
"""
Unit Qualification Test for Package 127 (Instrumented Increment-86 AM Checkpoint Serialization)
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 257)
"""
import os
import sys
import json
import hashlib
import unittest

PKG127_DIR = os.path.join("models", "pandey_kumar_mode1", "127_c4_inc86_instrumented_checkpoint")
FROZEN_UEL_HASH = "AB0A5A71335ECB445E91EC13A645E280FF3310B561A5E78ABA4A49C8E81DD8AC"


def get_sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest().upper()


class TestPackage127Qualification(unittest.TestCase):
    def test_01_frozen_uel_integrity(self):
        """Verify frozen unified UEL source SHA-256 matches exact canonical hash."""
        uel_path = os.path.join(PKG127_DIR, "f42_unified_12dof_active_set_uel.for")
        self.assertTrue(os.path.exists(uel_path))
        self.assertEqual(get_sha256(uel_path), FROZEN_UEL_HASH)

    def test_02_mesh_and_displacement_increment(self):
        """Verify input deck prescribes target displacement u_RP = 0.001929511665 mm on C4 mesh."""
        inp_path = os.path.join(PKG127_DIR, "M1_C4_INC86_INSTRUMENTED.inp")
        self.assertTrue(os.path.exists(inp_path))
        with open(inp_path, "r") as f:
            content = f.read()
        self.assertIn("N_RP, 2, 2, 0.001929511665", content)
        self.assertIn("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=5, VARIABLES=8, UNSYMM", content)
        self.assertIn("1, 2, 3", content)
        self.assertIn("*Include, input=active_set_boundary_cards.inc", content)

    def test_03_damage_lower_bounds_physical(self):
        """Verify starting damage lower bounds from authentic C3 Inc 86 donor are in [0, 1)."""
        cards_path = os.path.join(PKG127_DIR, "stage_a_all_d0_boundary_cards.inc")
        self.assertTrue(os.path.exists(cards_path))
        nodes_count = 0
        with open(cards_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("**"):
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4 and parts[0].isdigit():
                    nodes_count += 1
                    d_val = float(parts[3])
                    self.assertGreaterEqual(d_val, 0.0)
                    self.assertLess(d_val, 1.0)
        self.assertEqual(nodes_count, 4588)

    def test_04_committed_history_nonnegative(self):
        """Verify committed history H0 for all 4,422 elements is non-negative and finite."""
        bounds_csv = os.path.join(PKG127_DIR, "d_lower_bounds.csv")
        self.assertTrue(os.path.exists(bounds_csv))
        elem_count = 0
        with open(bounds_csv, "r") as f:
            header = [h.strip() for h in f.readline().split(",")]
            h_idx = [i for i, h in enumerate(header) if h.startswith("H0_")]
            self.assertEqual(len(h_idx), 4)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split(",")]
                if parts[0].isdigit():
                    elem_count += 1
                    for idx in h_idx:
                        h_val = float(parts[idx])
                        self.assertGreaterEqual(h_val, 0.0)
        self.assertEqual(elem_count, 4422)

    def test_05_checkpoint_serialization_module(self):
        """Verify mode1_am_state_checkpoint.py is present in package and functional."""
        ckpt_py = os.path.join(PKG127_DIR, "mode1_am_state_checkpoint.py")
        self.assertTrue(os.path.exists(ckpt_py))
        # Test import
        sys.path.insert(0, PKG127_DIR)
        try:
            import mode1_am_state_checkpoint as ckpt
            self.assertTrue(hasattr(ckpt, "serialize_checkpoint"))
            self.assertTrue(hasattr(ckpt, "load_and_validate_checkpoint"))
            self.assertTrue(hasattr(ckpt, "restore_coupled_state_for_continuation"))
            self.assertEqual(ckpt.EXPECTED_NODE_COUNT, 4588)
            self.assertEqual(ckpt.EXPECTED_ELEMENT_COUNT, 4422)
            self.assertEqual(ckpt.TOTAL_GP_COUNT, 17688)
        finally:
            if PKG127_DIR in sys.path:
                sys.path.remove(PKG127_DIR)

    def test_06_pbs_dual_channel_contract(self):
        """Verify PBS execution script satisfies dual-channel notification and resource bounds."""
        pbs_path = os.path.join(PKG127_DIR, "submit_M1_C4_INC86_INSTRUMENTED.pbs")
        self.assertTrue(os.path.exists(pbs_path))
        with open(pbs_path, "r") as f:
            pbs_text = f.read()

        self.assertIn("#PBS -N M1_C4_INC86_INSTRUMENTED", pbs_text)
        self.assertIn("#PBS -q entry_imfdfkmq", pbs_text)
        self.assertIn("#PBS -m abe", pbs_text)
        self.assertIn("#PBS -M pr21vyci@mailserver.tu-freiberg.de", pbs_text)
        self.assertIn("#PBS -l select=1:ncpus=1:mem=16gb", pbs_text)
        self.assertIn("#PBS -l walltime=08:00:00", pbs_text)
        self.assertIn("#PBS -r n", pbs_text)
        self.assertIn('cd "${RUN_DIR}"', pbs_text)
        self.assertIn("notification_load_config", pbs_text)
        self.assertIn("command -v ifort", pbs_text)
        self.assertIn("module load gcc/11.4.0 intel/2024.2.0 abaqus/2023", pbs_text)
        self.assertIn("notification_install_terminal_trap", pbs_text)
        self.assertIn("notify_start", pbs_text)
        self.assertIn("abaqus python driver_c4_inc86_instrumented.py", pbs_text)

    def test_07_manifest_integrity(self):
        """Verify manifest contains all required files and hashes agree with disk."""
        manifest_path = os.path.join(PKG127_DIR, "M1_C4_INC86_INSTRUMENTED_AUTHORIZATION.json")
        self.assertTrue(os.path.exists(manifest_path))
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["schema"], 1)
        self.assertEqual(manifest["adapter"], "mode1-experimental-12dof-v1")
        self.assertEqual(manifest["scientific_scope"], "MODE1")
        self.assertEqual(manifest["batch_name"], "MODE1_C4_INC86_INSTRUMENTED_CHECKPOINT")

        for fname, expected_hash in manifest.get("files", {}).items():
            fpath = os.path.join(PKG127_DIR, fname)
            self.assertTrue(os.path.exists(fpath), "Missing file: %s" % fname)
            actual_hash = hashlib.sha256(open(fpath, "rb").read()).hexdigest().lower()
            self.assertEqual(actual_hash, expected_hash.lower(), "Hash mismatch for %s" % fname)


if __name__ == "__main__":
    unittest.main()
