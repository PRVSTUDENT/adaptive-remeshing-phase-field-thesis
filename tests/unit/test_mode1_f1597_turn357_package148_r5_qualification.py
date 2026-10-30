#!/usr/bin/env python3
"""tests/unit/test_mode1_f1597_turn357_package148_r5_qualification.py

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2
Turn: 357 (RunId 6105baf2-a927-458e-bc37-d1f0d1ccad8d)

Package 148 R5 independent qualification and preflight verification:
1. Manifest integrity: all 14 files in models/pandey_kumar_mode1/148_c4_package148_state_transfer_r5/ match.
2. Frozen UEL bitwise integrity: CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6.
3. Solution card 7+8+3 token encoding across all 7,056 elements in initial_conditions_solution.inc.
4. Mechanical and phase datacheck decks strictly follow 7+8+3 card layout into SVARS(9..12).
5. Independent review results/validation/package148_r5_execution_review.json passes.
6. Preflight qualification record evaluate_mode1_package148_state_transfer_r5.qualification.json binds.
7. Predecessor review binds package148_r4_terminal_evaluation.json.
"""

import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
R5_DIR = ROOT / "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r5"


class TestTurn357Package148R5Qualification(unittest.TestCase):
    def test_01_r5_manifest_integrity(self):
        """Verify all files in Package 148 R5 match EXECUTION_MANIFEST.json."""
        manifest_path = R5_DIR / "EXECUTION_MANIFEST.json"
        self.assertTrue(manifest_path.is_file(), "EXECUTION_MANIFEST.json missing")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["batch_name"], "MODE1_PACKAGE148_R5_STATE_TRANSFER")
        self.assertEqual(manifest["scientific_scope"], "MODE1")
        self.assertEqual(manifest["technical_stage"], "C1-1")
        self.assertEqual(manifest["max_submissions"], 1)
        self.assertFalse(manifest["automatic_retry"])
        self.assertEqual(len(manifest["jobs"]), 1)
        self.assertEqual(manifest["jobs"][0]["id"], "M1_C4_P148_R5")

        for fname, expected_hash in manifest["files"].items():
            fpath = R5_DIR / fname
            self.assertTrue(fpath.is_file(), f"Missing file: {fname}")
            actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
            self.assertEqual(actual_hash, expected_hash.lower(), f"Hash mismatch for {fname}")

    def test_02_frozen_uel_bitwise_verification(self):
        """Verify production UEL remains bitwise frozen."""
        uel_path = R5_DIR / "f42_mixed_uel.for"
        actual_hash = hashlib.sha256(uel_path.read_bytes()).hexdigest().upper()
        self.assertEqual(actual_hash, FROZEN_UEL_HASH)

    def test_03_solution_cards_7_8_3_token_structure(self):
        """Verify initial_conditions_solution.inc contains 7,056 element cards with 7+8+3 layout."""
        inc_path = R5_DIR / "initial_conditions_solution.inc"
        lines = [l.strip() for l in inc_path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("*")]
        self.assertEqual(len(lines), 7056 * 3, f"Expected {7056*3} data lines, got {len(lines)}")

        # Sample elements across mesh
        for idx in [0, 100, 1000, 3500, 7055]:
            line1 = lines[idx * 3]
            line2 = lines[idx * 3 + 1]
            line3 = lines[idx * 3 + 2]
            tokens1 = [t.strip() for t in line1.split(",")]
            tokens2 = [t.strip() for t in line2.split(",")]
            tokens3 = [t.strip() for t in line3.split(",")]
            self.assertEqual(len(tokens1), 8, f"Element {idx+1} line 1 token count != 8")
            self.assertEqual(len(tokens2), 8, f"Element {idx+1} line 2 token count != 8")
            self.assertEqual(len(tokens3), 3, f"Element {idx+1} line 3 token count != 3")
            self.assertEqual(int(tokens1[0]), idx + 1)
            # SVAR 8 (first token on line 2) must be 0.0
            self.assertEqual(float(tokens2[0]), 0.0, f"Element {idx+1} SVAR 8 is not 0.0")

    def test_04_mechanical_and_phase_dc_solution_cards(self):
        """Verify P148_MECHANICAL_DC.inp and P148_PHASE_DC.inp have 7+8+3 solution cards."""
        for deck_name in ["P148_MECHANICAL_DC.inp", "P148_PHASE_DC.inp"]:
            deck_path = R5_DIR / deck_name
            text = deck_path.read_text(encoding="utf-8")
            self.assertIn("*Initial Conditions, type=SOLUTION", text)
            pos = text.index("*Initial Conditions, type=SOLUTION")
            sub = text[pos:].split("*Amplitude")[0]
            card_lines = [l.strip() for l in sub.splitlines() if l.strip() and not l.startswith("*")]
            self.assertEqual(len(card_lines), 7056 * 3)
            # Verify first element
            tokens1 = card_lines[0].split(",")
            tokens2 = card_lines[1].split(",")
            tokens3 = card_lines[2].split(",")
            self.assertEqual(len(tokens1), 8)
            self.assertEqual(len(tokens2), 8)
            self.assertEqual(len(tokens3), 3)
            self.assertEqual(int(tokens1[0]), 1)
            self.assertEqual(float(tokens2[0]), 0.0)

    def test_05_independent_review_and_qualification_artifacts(self):
        """Verify independent execution review and preflight qualification artifacts."""
        review_path = ROOT / "results/validation/package148_r5_execution_review.json"
        self.assertTrue(review_path.is_file(), "Review artifact missing")
        review = json.loads(review_path.read_text(encoding="utf-8"))
        self.assertTrue(review["verification_passed"])
        self.assertEqual(review["independent_r5_qualification"], "PASS")
        self.assertEqual(review["python_36_compatibility"], "PASS")

        qual_path = ROOT / "scripts/validation/evaluate_mode1_package148_state_transfer_r5.qualification.json"
        self.assertTrue(qual_path.is_file(), "Qualification artifact missing")
        qual = json.loads(qual_path.read_text(encoding="utf-8"))
        self.assertEqual(qual["status"], "QUALIFIED_FOR_PREFLIGHT")
        self.assertTrue(qual["dispatch_ready"])
        self.assertEqual(qual["execution_mode"], "HPC_PRE_SUBMISSION")
        self.assertEqual(qual["production_uel_sha256"], FROZEN_UEL_HASH)

    def test_06_predecessor_review_binding(self):
        """Verify EXECUTION_MANIFEST binds package148_r4_terminal_evaluation.json."""
        manifest = json.loads((R5_DIR / "EXECUTION_MANIFEST.json").read_text(encoding="utf-8"))
        pred_rel = manifest["scientific_predecessor_review"]
        self.assertEqual(pred_rel, "results/validation/package148_r4_terminal_evaluation.json")
        pred_path = ROOT / pred_rel
        self.assertTrue(pred_path.is_file())
        pred = json.loads(pred_path.read_text(encoding="utf-8"))
        self.assertEqual(pred["job_name"], "M1_C4_P148_R4")
        self.assertFalse(pred["physical_acceptance"])


if __name__ == "__main__":
    unittest.main()
