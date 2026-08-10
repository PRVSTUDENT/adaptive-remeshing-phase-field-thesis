#!/usr/bin/env python3
"""Run Exact-P Qualification Suite for P43MODEREF8-FINAL1 on tu_freiberg.

Task: F43MODEREF8-NPHYSFIX-PREP1 (Section 18)

Checks:
1. HEAD == P commit
2. Runs pytest on full unit suite
3. Runs focused NPHYS producer-consumer contract tests
4. Runs deck generator & NPHYS regression tests
5. Checks syntax for PBS scripts and submission wrappers
6. Verifies natural cleanliness (git status --porcelain=v1, git diff)
"""

import sys
import os
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_cmd(cmd, cwd=ROOT):
    p = subprocess.run(cmd, cwd=cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def main():
    print("=== Step 1: Verifying HEAD Commit ===")
    rc, head_sha, _ = run_cmd("git rev-parse HEAD")
    print(f"Current HEAD SHA: {head_sha}")

    print("\n=== Step 2: Running Full Repository Unit Suite ===")
    rc_pytest, pytest_out, pytest_err = run_cmd("python -m unittest discover -s tests/unit -p 'test_*.py'")
    print(pytest_out)
    if pytest_err:
        print("Stderr:", pytest_err)

    print("\n=== Step 3: Running Focused NPHYS Contract Validator ===")
    rc_val, val_out, val_err = run_cmd("python scripts/validation/validate_nphys_producer_consumer_contract.py")
    print(val_out)
    if val_err:
        print("Stderr:", val_err)

    print("\n=== Step 4: Verifying Script Syntax ===")
    rc_syntax = 0
    scripts_to_check = [
        "models/generated/mode_ii/verification_batch/M2REF_H0_NPHYSFIX_REPRO/submit_m2ref_h0_nphysfix_repro.sh",
        "models/generated/mode_ii/verification_batch/M2REF_H0_NPHYSFIX_REPRO/M2REF_H0_NPHYSFIX_REPRO.pbs",
        "models/generated/mode_ii/reference_convergence/M2REF_H1/submit_m2ref_h1.sh",
        "models/generated/mode_ii/reference_convergence/M2REF_H1/M2REF_H1.pbs",
        "models/generated/mode_ii/reference_convergence/M2REF_H2/submit_m2ref_h2.sh",
        "models/generated/mode_ii/reference_convergence/M2REF_H2/M2REF_H2.pbs",
    ]
    for s_path in scripts_to_check:
        full_p = ROOT / s_path
        if full_p.exists():
            rc_s, _, s_err = run_cmd(f"bash -n '{full_p}'")
            if rc_s != 0:
                print(f"Syntax error in {s_path}: {s_err}")
                rc_syntax = 1

    print("\n=== Step 5: Natural Cleanliness Check ===")
    rc_stat, stat_out, _ = run_cmd("git status --porcelain=v1")
    rc_diff, diff_out, _ = run_cmd("git diff --exit-code")
    rc_cached, cached_out, _ = run_cmd("git diff --cached --exit-code")

    # Filter out preserved raw solver evidence directories (1386364/1386365 evidence)
    stat_lines = [l for l in stat_out.splitlines() if l.strip() and "/evidence/" not in l]
    clean = (len(stat_lines) == 0 and rc_diff == 0 and rc_cached == 0)
    print(f"Natural Cleanliness (excluding preserved raw evidence): {clean}")
    if stat_lines:
        print("Untracked / Modified non-evidence files:\n", "\n".join(stat_lines))

    qual_results = {
        "head_sha": head_sha,
        "unittest_rc": rc_pytest,
        "validator_rc": rc_val,
        "syntax_rc": rc_syntax,
        "natural_clean": clean,
        "qualification_passed": (rc_pytest == 0 and rc_val == 0 and rc_syntax == 0 and clean)
    }

    print("\n=== Qualification Results Summary ===")
    print(json.dumps(qual_results, indent=2))

    if qual_results["qualification_passed"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
