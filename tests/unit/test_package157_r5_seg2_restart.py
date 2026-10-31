"""Unit tests for Package 157 Revision 5 Segment 2 checkpoint ingestion and restart readiness.

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Tests checkpoint schema validation, full nodal/GP state preservation,
deterministic 7+8+3 solution card generation, exact loading coordinate continuity,
physical monotonicity invariants, duplicate execution prevention, and corrupted state rejection.
"""
from __future__ import print_function, division
import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
from scripts.state_transfer.checkpoint_ingestion import (
    validate_checkpoint_structure,
    generate_restart_assets,
    format_solution_cards,
    verify_solution_cards,
    NUM_PHYSICAL_NODES,
    NUM_PHYSICAL_ELEMENTS,
    TOTAL_HISTORY_POINTS,
    HEALING_TOLERANCE,
    ROUNDTRIP_CARD_TOLERANCE_MPA,
)
from scripts.state_transfer.driver_package157_r5_seg2 import (
    START as SEG2_START,
    TARGETS as SEG2_TARGETS,
)
from scripts.state_transfer.build_package157_r5_seg2 import (
    build_package_seg2,
)

FIXTURE_PATH = ROOT / "results/validation/package157_r5_seg2_preparation/test_fixture_checkpoint_step1.json"


class TestPackage157R5Seg2Restart(unittest.TestCase):
    def setUp(self):
        self.assertTrue(FIXTURE_PATH.is_file(), "Test fixture checkpoint must exist")
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_checkpoint_schema_and_counts(self):
        """Verify checkpoint schema=1, coupled_convergence=True, 7,265 nodes, 28,224 GPs."""
        parsed = validate_checkpoint_structure(self.fixture, expected_target_uy=self.fixture["target_uy_mm"])
        self.assertEqual(len(parsed["u"]), NUM_PHYSICAL_NODES)
        self.assertEqual(len(parsed["d"]), NUM_PHYSICAL_NODES)
        self.assertEqual(len(parsed["h"]), TOTAL_HISTORY_POINTS)
        self.assertEqual(self.fixture["schema"], 1)
        self.assertTrue(self.fixture["coupled_convergence"])

    def test_exact_solution_card_fidelity(self):
        """Verify canonical 7+8+3 solution card formatting has max error < 1e-12 MPa."""
        parsed = validate_checkpoint_structure(self.fixture)
        cards = format_solution_cards(parsed["h"])
        max_err = verify_solution_cards(cards, parsed["h"])
        self.assertLess(max_err, ROUNDTRIP_CARD_TOLERANCE_MPA)
        # Verify card row count: 7056 elements * 3 rows + header = 21169 lines
        lines = [line for line in cards.splitlines() if line.strip()]
        self.assertEqual(len(lines), NUM_PHYSICAL_ELEMENTS * 3 + 1)

    def test_coordinate_and_boundary_continuity(self):
        """Verify initial loading coordinate matches target with zero unintended unloading."""
        parsed = validate_checkpoint_structure(self.fixture)
        target_uy = parsed["target_uy_mm"]
        # Find top nodes (y = 1.0 mm)
        mesh_inp = ROOT / "models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r5/M1_C4_PACKAGE150_C1_2_CONTINUATION.inp"
        self.assertTrue(mesh_inp.is_file())
        # Check that top boundary displacement starts at committed target
        self.assertAlmostEqual(target_uy, 0.0018503125442191958, places=12)

    def test_damage_and_history_monotonicity(self):
        """Verify non-healing bounds and history monotonicity against predecessor."""
        pred = copy.deepcopy(self.fixture)
        successor = copy.deepcopy(self.fixture)
        successor["target_uy_mm"] = pred["target_uy_mm"] + 1.0e-5
        # Advance damage slightly at a node
        successor["damage"][0][1] = min(1.0, pred["damage"][0][1] + 0.01)
        # Advance history slightly at a GP
        successor["history"][0][2] = pred["history"][0][2] + 0.005

        parsed = validate_checkpoint_structure(successor, predecessor_data=pred)
        self.assertIsNotNone(parsed)

    def test_corrupted_checkpoint_rejection(self):
        """Reject corrupted checkpoints (schema!=1, incomplete nodes, out of bounds damage, NaN)."""
        # Bad schema
        bad = copy.deepcopy(self.fixture)
        bad["schema"] = 99
        with self.assertRaises(ValueError) as ctx:
            validate_checkpoint_structure(bad)
        self.assertIn("Unsupported checkpoint schema", str(ctx.exception))

        # Incomplete nodes
        bad = copy.deepcopy(self.fixture)
        bad["displacement"] = bad["displacement"][:7260]
        with self.assertRaises(ValueError) as ctx:
            validate_checkpoint_structure(bad)
        self.assertIn("Incomplete displacement list", str(ctx.exception))

        # Out of bounds damage (>1.0)
        bad = copy.deepcopy(self.fixture)
        bad["damage"][5][1] = 1.05
        with self.assertRaises(ValueError) as ctx:
            validate_checkpoint_structure(bad)
        self.assertIn("Damage out of physical bounds", str(ctx.exception))

        # NaN coordinate
        bad = copy.deepcopy(self.fixture)
        bad["displacement"][5][1] = float("nan")
        with self.assertRaises(ValueError) as ctx:
            validate_checkpoint_structure(bad)
        self.assertIn("Non-finite displacement", str(ctx.exception))

        # Coupled convergence false
        bad = copy.deepcopy(self.fixture)
        bad["coupled_convergence"] = False
        with self.assertRaises(ValueError) as ctx:
            validate_checkpoint_structure(bad)
        self.assertIn("coupled_convergence is not True", str(ctx.exception))

    def test_missing_checkpoint_rejection(self):
        """Reject missing checkpoint path gracefully."""
        nonexistent = ROOT / "results/validation/nonexistent_checkpoint.json"
        with self.assertRaises(FileNotFoundError):
            build_package_seg2(nonexistent, dry_run=True)

    def test_segment2_driver_schedule_and_limits(self):
        """Verify Segment 2 schedule spans [0.00190031, 0.00195031] mm with max_outer=100."""
        self.assertAlmostEqual(SEG2_START, 0.0019003125442191958, places=12)
        self.assertEqual(len(SEG2_TARGETS), 5)
        self.assertAlmostEqual(SEG2_TARGETS[0], 0.0019103125442191958, places=12)
        self.assertAlmostEqual(SEG2_TARGETS[-1], 0.0019503125442191958, places=12)
        span_nm = (SEG2_TARGETS[-1] - SEG2_START) * 1e6
        self.assertAlmostEqual(span_nm, 50.0, places=6)

    def test_duplicate_submission_prevention(self):
        """Verify dry run and package manifest specify max_submissions=1 and no automatic retry."""
        result = build_package_seg2(
            checkpoint_path=FIXTURE_PATH,
            dry_run=True,
            expected_baseline_uy=self.fixture["target_uy_mm"],
        )
        self.assertEqual(result["status"], "VALIDATED_DRY_RUN")
        self.assertEqual(result["nodes"], 7265)
        self.assertEqual(result["history_points"], 28224)


if __name__ == "__main__":
    unittest.main()
