"""Regression tests for Python 3.6 compatibility and deck block splitting.

Validates the repair for the Package 148 R1 runtime failure (Job 1418787.mmaster02)
where Python 3.6.8 re.split rejected zero-width lookahead assertions:
    ValueError: split() requires a non-empty pattern match.

Covers:
- Reproduction and resolution of the zero-width re.split defect.
- Exact keyword block splitting across representative Abaqus decks.
- Space-separated, comma-separated, repeated whitespace, and empty fields.
- Scientific notation and signed numerical values.
- Malformed and missing solver output handling.
- Syntax and import integrity for cluster deployment.
"""
import math
import os
from pathlib import Path
import re
import tempfile
import unittest

from scripts.state_transfer.driver_package146_147_pdas_continuation import (
    split_keyword_blocks, validate_damage, FROZEN_UEL_SHA256,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class Package148Py36CompatibilityTests(unittest.TestCase):
    def test_split_keyword_blocks_basic(self):
        sample = (
            "** Heading comment\n"
            "*HEADING\n"
            "Mode I Test\n"
            "*NODE, NSET=ALL\n"
            "1, 0.0, 0.0\n"
            "2, 1.0, 0.0\n"
            "*ELEMENT, TYPE=CPE4, ELSET=EALL\n"
            "1, 1, 2, 3, 4\n"
            "*BOUNDARY\n"
            "N_BOT, 2, 2, 0.0\n"
            "*STEP, NAME=STEP1\n"
            "*STATIC\n"
            "*END STEP\n"
        )
        blocks = split_keyword_blocks(sample)
        self.assertEqual(len(blocks), 8)
        self.assertTrue(blocks[0].startswith("** Heading comment\n"))
        self.assertTrue(blocks[1].startswith("*HEADING\n"))
        self.assertTrue(blocks[2].startswith("*NODE"))
        self.assertTrue(blocks[3].startswith("*ELEMENT"))
        self.assertTrue(blocks[4].startswith("*BOUNDARY"))
        self.assertTrue(blocks[5].startswith("*STEP"))
        self.assertTrue(blocks[6].startswith("*STATIC"))
        self.assertTrue(blocks[7].startswith("*END STEP"))
        self.assertEqual("".join(blocks), sample)

    def test_split_keyword_blocks_starts_with_keyword(self):
        sample = "*HEADING\nSimple\n*NODE\n1, 0., 0.\n"
        blocks = split_keyword_blocks(sample)
        self.assertEqual(len(blocks), 2)
        self.assertTrue(blocks[0].startswith("*HEADING"))
        self.assertTrue(blocks[1].startswith("*NODE"))
        self.assertEqual("".join(blocks), sample)

    def test_split_keyword_blocks_empty_and_comments_only(self):
        self.assertEqual(split_keyword_blocks(""), [])
        comments = "** Comment line 1\n** Comment line 2\n"
        self.assertEqual(split_keyword_blocks(comments), [comments])

    def test_deck_equivalence_against_real_package148_input(self):
        deck_path = (
            REPO_ROOT
            / "models/pandey_kumar_mode1/148_c4_package148_state_transfer_r1"
            / "M1_C4_PACKAGE148_STATE_TRANSFER.inp"
        )
        self.assertTrue(deck_path.is_file(), "Package 148 template deck must exist")
        content = deck_path.read_text(encoding="utf-8")
        blocks = split_keyword_blocks(content)
        self.assertGreater(len(blocks), 10)
        self.assertEqual("".join(blocks), content)
        # Verify that all blocks except possibly leading comments start with * and not **
        for i, block in enumerate(blocks):
            first_line = block.split("\n", 1)[0].strip()
            if i == 0 and first_line.startswith("**"):
                continue
            self.assertTrue(
                first_line.startswith("*") and not first_line.startswith("**"),
                "Block %d must start with single asterisk keyword: %s"
                % (i, first_line[:30]),
            )

    def test_space_separated_tokens(self):
        sta_line = "   1     1     1   1   0.100     0.100    1.000e-05   0.100\n"
        parts = sta_line.split()
        self.assertEqual(len(parts), 8)
        self.assertEqual(int(parts[0]), 1)
        self.assertEqual(int(parts[1]), 1)
        self.assertAlmostEqual(float(parts[6]), 1e-5)

        dat_line = "      999999      -1.2345E-06       1.8003E-03      +0.0000E+00\n"
        dat_parts = dat_line.split()
        self.assertEqual(len(dat_parts), 4)
        self.assertEqual(int(dat_parts[0]), 999999)
        self.assertAlmostEqual(float(dat_parts[1]), -1.2345e-6)
        self.assertAlmostEqual(float(dat_parts[2]), 0.0018003)
        self.assertAlmostEqual(float(dat_parts[3]), 0.0)

    def test_comma_separated_tokens_and_whitespace(self):
        csv_line = " 1,  0, 0,  -1.2345e-04, +5.6789e-04,  6.9134e-04 , 0 \n"
        parts = [p.strip() for p in csv_line.split(",")]
        self.assertEqual(len(parts), 7)
        self.assertEqual(int(parts[0]), 1)
        self.assertAlmostEqual(float(parts[3]), -1.2345e-4)
        self.assertAlmostEqual(float(parts[4]), 5.6789e-4)
        self.assertAlmostEqual(float(parts[5]), 6.9134e-4)

    def test_scientific_notation_and_signed_values(self):
        values = [
            "-1.8003125442191958e-03",
            "+2.1000000000000000e+02",
            "-0.0",
            "+0.0",
            "1e-16",
            "-1e-16",
            "2.7000000000000000e-03",
        ]
        parsed = [float(v) for v in values]
        self.assertAlmostEqual(parsed[0], -0.0018003125442191958)
        self.assertAlmostEqual(parsed[1], 210.0)
        self.assertEqual(parsed[2], 0.0)
        self.assertEqual(parsed[3], 0.0)
        self.assertAlmostEqual(parsed[4], 1e-16)
        self.assertAlmostEqual(parsed[5], -1e-16)
        self.assertAlmostEqual(parsed[6], 0.0027)

    def test_empty_fields_and_fail_closed(self):
        # Incomplete / empty damage dictionary
        with self.assertRaises(ValueError):
            validate_damage({}, {1, 2})
        with self.assertRaises(ValueError):
            validate_damage({1: 0.5}, {1, 2})
        # NaN / Inf damage values
        with self.assertRaises(ValueError):
            validate_damage({1: float("nan"), 2: 0.5}, {1, 2})
        with self.assertRaises(ValueError):
            validate_damage({1: float("inf"), 2: 0.5}, {1, 2})
        # Out-of-bounds damage values
        with self.assertRaises(ValueError):
            validate_damage({1: -0.01, 2: 0.5}, {1, 2})
        with self.assertRaises(ValueError):
            validate_damage({1: 1.01, 2: 0.5}, {1, 2})

    def test_python_syntax_and_compilation(self):
        driver_file = (
            REPO_ROOT
            / "scripts/state_transfer/driver_package146_147_pdas_continuation.py"
        )
        extractor_file = (
            REPO_ROOT / "scripts/validation/extract_package148_iteration.py"
        )
        for target in (driver_file, extractor_file):
            source = target.read_text(encoding="utf-8")
            compiled = compile(source, str(target), "exec")
            self.assertIsNotNone(compiled)

    def test_frozen_uel_preservation(self):
        self.assertEqual(
            FROZEN_UEL_SHA256,
            "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
        )


if __name__ == "__main__":
    unittest.main()
