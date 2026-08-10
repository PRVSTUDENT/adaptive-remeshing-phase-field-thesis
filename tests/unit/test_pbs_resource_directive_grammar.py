#!/bin/env python3
"""Fail-Closed PBS Resource Directive Grammar Regression Test for Mode-II Pair-2.

Verifies that PBS resource directives strictly conform to OpenPBS grammar rules:
1. Rejects embedded spaces in memory resource tokens (e.g., 'mem=8 GB')
2. Rejects invalid spacing around equals sign (e.g., 'mem =8gb', 'mem= 8gb')
3. Rejects empty memory values, invalid memory units, and duplicate memory specs
4. Asserts that actual M2REF_H1_FRACFIX and M2REF_H2_FRACFIX PBS scripts pass.
"""

import unittest
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
H1_PBS = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H1_FRACFIX/M2REF_H1_FRACFIX.pbs"
H2_PBS = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX/M2REF_H2_FRACFIX.pbs"

MEM_RESOURCE_REGEX = re.compile(r"^mem=(\d+)(b|kb|mb|gb|tb)$")


def validate_pbs_resource_grammar_text(text: str) -> bool:
    """Validate resource directive grammar in a PBS script text."""
    found_select = False
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("#PBS -l"):
            continue

        raw_spec = line[7:].strip()
        if raw_spec.startswith("select="):
            found_select = True
            tokens = raw_spec.split(":")
            mem_found = 0
            for token in tokens:
                token = token.strip()
                if token.startswith("select="):
                    val = token.split("=")[1].strip()
                    if not val.isdigit():
                        raise ValueError(f"Invalid select value: {val}")
                elif token.startswith("ncpus="):
                    val = token.split("=")[1].strip()
                    if not val.isdigit():
                        raise ValueError(f"Invalid ncpus value: {val}")
                elif token.startswith("mem"):
                    mem_found += 1
                    # Strict regex check on mem token: NO SPACES ALLOWED
                    if not MEM_RESOURCE_REGEX.match(token):
                        raise ValueError(f"Invalid mem resource directive token syntax: {token!r}")
            if mem_found != 1:
                raise ValueError(f"PBS select spec must contain exactly 1 mem token, found {mem_found}")

    if not found_select:
        raise ValueError("No '#PBS -l select=...' directive found")

    return True


def validate_pbs_file_resource_contract(path: Path) -> bool:
    if not path.exists():
        raise FileNotFoundError(f"PBS file missing: {path}")
    text = path.read_text(encoding="utf-8")
    return validate_pbs_resource_grammar_text(text)


class TestPBSResourceDirectiveGrammar(unittest.TestCase):

    def test_h1_pbs_resource_grammar_pass(self):
        self.assertTrue(H1_PBS.exists(), f"H1 PBS missing: {H1_PBS}")
        self.assertTrue(validate_pbs_file_resource_contract(H1_PBS))

    def test_h2_pbs_resource_grammar_pass(self):
        self.assertTrue(H2_PBS.exists(), f"H2 PBS missing: {H2_PBS}")
        self.assertTrue(validate_pbs_file_resource_contract(H2_PBS))

    def test_reject_embedded_space_in_mem(self):
        bad_text = "#!/bin/bash\n#PBS -l select=1:ncpus=1:mem=8 GB\n#PBS -l walltime=02:00:00\n"
        with self.assertRaises(ValueError) as ctx:
            validate_pbs_resource_grammar_text(bad_text)
        self.assertIn("Invalid mem resource directive token syntax", str(ctx.exception))

    def test_reject_space_before_equals(self):
        bad_text = "#!/bin/bash\n#PBS -l select=1:ncpus=1:mem =8gb\n#PBS -l walltime=02:00:00\n"
        with self.assertRaises(ValueError):
            validate_pbs_resource_grammar_text(bad_text)

    def test_reject_space_after_equals(self):
        bad_text = "#!/bin/bash\n#PBS -l select=1:ncpus=1:mem= 8gb\n#PBS -l walltime=02:00:00\n"
        with self.assertRaises(ValueError):
            validate_pbs_resource_grammar_text(bad_text)

    def test_reject_empty_mem_value(self):
        bad_text = "#!/bin/bash\n#PBS -l select=1:ncpus=1:mem=\n#PBS -l walltime=02:00:00\n"
        with self.assertRaises(ValueError):
            validate_pbs_resource_grammar_text(bad_text)

    def test_reject_unsupported_unit_token(self):
        bad_text = "#!/bin/bash\n#PBS -l select=1:ncpus=1:mem=8foo\n#PBS -l walltime=02:00:00\n"
        with self.assertRaises(ValueError):
            validate_pbs_resource_grammar_text(bad_text)

    def test_reject_duplicate_mem_directives(self):
        bad_text = "#!/bin/bash\n#PBS -l select=1:ncpus=1:mem=8gb:mem=16gb\n#PBS -l walltime=02:00:00\n"
        with self.assertRaises(ValueError):
            validate_pbs_resource_grammar_text(bad_text)

    def test_accept_valid_canonical_select_directives(self):
        valid_1 = "#!/bin/bash\n#PBS -l select=1:ncpus=1:mem=8gb\n#PBS -l walltime=02:00:00\n"
        valid_2 = "#!/bin/bash\n#PBS -l select=1:ncpus=1:mem=16gb\n#PBS -l walltime=04:00:00\n"
        self.assertTrue(validate_pbs_resource_grammar_text(valid_1))
        self.assertTrue(validate_pbs_resource_grammar_text(valid_2))


if __name__ == "__main__":
    unittest.main()
