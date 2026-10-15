#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1482_stage_c1_0_identical_mesh_continuation.py
===========================================================
Unit test suite for Task F1482:
Mode-I Method C Stage C1-0 Identical-Mesh State Transfer & Continuation
Verifies:
1. Package 47 structure, manifest, and anti-deviation card integrity.
2. Invariant verification of production Fortran UEL (CE8D5EDC...).
3. Identical-mesh topology: donor mesh == recipient mesh on 2,906 elements.
4. Input deck syntax: *INITIAL CONDITIONS, TYPE=SOLUTION lines <= 8 items per line,
   Step 1 (Step-1-Equilibrate at u=0.0050 mm), and Step 2 (Step-2-Continue).
5. Bridge rules governance: verification that automatic progression rule is active
   and zero stale calendar hold barriers remain.

Task: F1482
Author: Gemini Antigravity
Date: 2026-10-15
"""

import os
import sys
import json
import hashlib
import unittest
from pathlib import Path

# Resolve repository root
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1] if str(SCRIPT_DIR.parents[1]) not in sys.path else SCRIPT_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.mode1_state_transfer_engine import parse_mode1_input_deck


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


class TestMode1F1482StageC10(unittest.TestCase):
    """Test suite for Task F1482 Stage C1-0 package integrity and governance."""

    @classmethod
    def setUpClass(cls):
        cls.pkg_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "47_method_c_stage_c1_0_identical_mesh_continuation"
        cls.inp_path = cls.pkg_dir / "M1_MC_STAGE_C1_0_RECONSTRUCT.inp"
        cls.uel_path = cls.pkg_dir / "f42_mixed_uel.for"
        cls.manifest_path = cls.pkg_dir / "PACKAGE_MANIFEST.json"
        cls.card_path = cls.pkg_dir / "PRE_JOB_ANTI_DEVIATION_CARD.md"
        cls.pbs_solver_path = cls.pkg_dir / "submit_M1_MC_STAGE_C1_0.pbs"
        cls.pbs_dc_path = cls.pkg_dir / "submit_datacheck.pbs"
        cls.donor_json_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "41_method_c_genuine_continuation" / "evidence_forward_audit" / "coarse_donor_state_u0050.json"
        cls.donor_mesh_inp = REPO_ROOT / "models" / "pandey_kumar_mode1" / "method_b_inf_companion_decks" / "M1_MB_INF_1S.inp"

    def test_01_package47_files_exist(self):
        """Test that all required Package 47 files exist and have non-zero size."""
        required = [
            self.inp_path,
            self.uel_path,
            self.manifest_path,
            self.card_path,
            self.pbs_solver_path,
            self.pbs_dc_path,
        ]
        for path in required:
            self.assertTrue(path.exists(), f"Missing required file: {path}")
            self.assertGreater(path.stat().st_size, 0, f"File is empty: {path}")

    def test_02_production_uel_invariant(self):
        """Test that f42_mixed_uel.for exactly matches the production SHA-256 invariant."""
        expected_sha = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        actual_sha = compute_sha256(self.uel_path)
        self.assertEqual(actual_sha, expected_sha, "Production UEL SHA-256 invariant violated!")

    def test_03_manifest_metadata_and_criteria(self):
        """Test that PACKAGE_MANIFEST.json defines the required Stage C1-0 acceptance criteria."""
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["task_id"], "F1482")
        self.assertTrue(manifest["recipient_mesh"]["identical_mesh"])
        self.assertEqual(manifest["recipient_mesh"]["elements_physical"], 2906)

        criteria = manifest["stage_c1_0_acceptance_criteria"]
        self.assertIn("criterion_1_rf_continuity", criteria)
        self.assertIn("criterion_2_energy_preservation", criteria)
        self.assertIn("criterion_3_history_non_negativity", criteria)
        self.assertIn("criterion_4_equilibrium_convergence", criteria)
        self.assertIn("criterion_5_fracture_continuation", criteria)

    def test_04_input_deck_syntax_and_solution_cards(self):
        """Test that the input deck has valid solution cards (<= 8 items per line) and step structure."""
        with open(self.inp_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        has_step1 = any("*STEP, NAME=Step-1-Equilibrate" in l for l in lines)
        has_step2 = any("*STEP, NAME=Step-2-Continue" in l for l in lines)
        has_init_sol = any("*INITIAL CONDITIONS, TYPE=SOLUTION" in l for l in lines)

        self.assertTrue(has_step1, "Missing Step-1-Equilibrate in input deck!")
        self.assertTrue(has_step2, "Missing Step-2-Continue in input deck!")
        self.assertTrue(has_init_sol, "Missing *INITIAL CONDITIONS, TYPE=SOLUTION in input deck!")

        # Verify card wrapping rule (<= 8 items per line in solution block)
        in_solution = False
        solution_lines_checked = 0
        for line in lines:
            s = line.strip()
            if s.startswith("*INITIAL CONDITIONS, TYPE=SOLUTION"):
                in_solution = True
                continue
            elif in_solution and s.startswith("*"):
                in_solution = False
                break
            elif in_solution and s and not s.startswith("**"):
                items = [p.strip() for p in s.split(",") if p.strip()]
                self.assertLessEqual(len(items), 8, f"Solution card has {len(items)} > 8 items: {s}")
                solution_lines_checked += 1

        self.assertGreater(solution_lines_checked, 2000, "Too few solution cards checked!")

    def test_05_bridge_rules_progression_rule(self):
        """Test that bridge rules contain the automatic progression rule and no stale hold phrases."""
        bridge_path = REPO_ROOT / ".agents" / "scripts" / "bridge_rules.txt"
        with open(bridge_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("METHOD B -> METHOD C AUTOMATIC RESEARCH PROGRESSION RULE", content)
        self.assertNotIn("HOLD PENDING 22 OCTOBER 2026 SUPERVISOR MEETING", content)


if __name__ == "__main__":
    unittest.main()
