#!/usr/bin/env python3
"""Unit test for H1/H2 PBS dependency-critical exit semantics.

Parses PBS scripts for documented exit policy without executing Abaqus.
"""

import os
import re
import sys

H1 = "scripts/hpc/molnar_lc015_h1_h0025.pbs"
H2 = "scripts/hpc/molnar_lc015_h2_pub_h0010.pbs"


def check_script(path):
    fh = open(path, "r")
    try:
        text = fh.read()
    finally:
        fh.close()
    errors = []
    if "SOLVER_DEPENDENCY_STATUS" not in text:
        errors.append("{0}: missing SOLVER_DEPENDENCY_STATUS".format(path))
    if "cae_postprocess_failure_after_successful_solve" not in text:
        errors.append("{0}: missing CAE-after-solver-success classification".format(path))
    if "solver_dependency_status.txt" not in text:
        errors.append("{0}: missing solver_dependency_status.txt write".format(path))
    if "cae_postprocess_classification.txt" not in text:
        errors.append("{0}: missing cae_postprocess_classification.txt write".format(path))
    if "overall_evidence_status.txt" not in text:
        errors.append("{0}: missing overall_evidence_status.txt write".format(path))
    if not re.search(
        r"cae_postprocess_failure_after_successful_solve[\s\S]{0,400}PBS_EXIT=0",
        text,
    ):
        errors.append(
            "{0}: CAE failure path must set PBS_EXIT=0 for dependency success".format(path)
        )
    if not re.search(r"abaqus_technical_failure[\s\S]{0,400}PBS_EXIT=10", text):
        errors.append("{0}: solver failure path must set PBS_EXIT=10".format(path))
    if re.search(r"POST_RC.*\n.*exit 11", text) or re.search(
        r"CAE_RC.*\n.*exit 11", text
    ):
        errors.append(
            "{0}: still exits 11 on CAE failure (dependency-breaking)".format(path)
        )
    return errors


def main():
    errors = []
    for path in (H1, H2):
        if not os.path.isfile(path):
            errors.append("missing {0}".format(path))
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
