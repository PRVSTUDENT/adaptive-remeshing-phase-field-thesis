#!/usr/bin/env python3
"""Unit test for H1/H2 PBS dependency-critical exit semantics.

Parses PBS scripts for documented exit policy without executing Abaqus.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

H1 = Path("scripts/hpc/molnar_lc015_h1_h0025.pbs")
H2 = Path("scripts/hpc/molnar_lc015_h2_pub_h0010.pbs")


def check_script(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors = []
    if "SOLVER_DEPENDENCY_STATUS" not in text:
        errors.append(f"{path}: missing SOLVER_DEPENDENCY_STATUS")
    if "cae_postprocess_failure_after_successful_solve" not in text:
        errors.append(f"{path}: missing CAE-after-solver-success classification")
    if "solver_dependency_status.txt" not in text:
        errors.append(f"{path}: missing solver_dependency_status.txt write")
    if "cae_postprocess_classification.txt" not in text:
        errors.append(f"{path}: missing cae_postprocess_classification.txt write")
    if "overall_evidence_status.txt" not in text:
        errors.append(f"{path}: missing overall_evidence_status.txt write")
    # After CAE failure path should set PBS_EXIT=0
    if not re.search(
        r"cae_postprocess_failure_after_successful_solve[\s\S]{0,400}PBS_EXIT=0",
        text,
    ):
        errors.append(f"{path}: CAE failure path must set PBS_EXIT=0 for dependency success")
    # Solver failure must still be nonzero
    if not re.search(
        r"abaqus_technical_failure[\s\S]{0,400}PBS_EXIT=10",
        text,
    ):
        errors.append(f"{path}: solver failure path must set PBS_EXIT=10")
    # Must not exit 11 on CAE failure anymore
    if re.search(r"POST_RC.*\n.*exit 11", text) or re.search(
        r"CAE_RC.*\n.*exit 11", text
    ):
        errors.append(f"{path}: still exits 11 on CAE failure (dependency-breaking)")
    return errors


def main() -> int:
    errors = []
    for path in (H1, H2):
        if not path.exists():
            errors.append(f"missing {path}")
            continue
        errors.extend(check_script(path))
    if errors:
        print("DEPENDENCY_POLICY_FAIL")
        for e in errors:
            print(e)
        return 2
    print("DEPENDENCY_POLICY_PASS")
    print("solver failure -> nonzero")
    print("solver success + CAE success -> zero")
    print("solver success + CAE failure -> zero with separate CAE failure status")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
