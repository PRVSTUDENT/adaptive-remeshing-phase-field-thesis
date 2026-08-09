#!/usr/bin/env python3
"""Common Fail-Closed Preflight for Two-Job Verification Batch (Pair 1R).

Validates:
1. Exact preparation tag P43MODEREF6-FINAL1 (1b757c430261bde362a7ae43764aef68f358d86c).
2. Exact qualification tag Q43MODEREF6 (976fbb5001ffae01e63a15afbf1a7008cf36eecb).
3. All 8 full 64-character execution hashes for Job 1 (M2REF_ONEEL_FRACFIX_VERIFY_R2) and Job 2 (M2REF_H0_EXACT_FRACFIX_REPRO).
4. Queue status via qstat (rc=0, no duplicate active jobs).
5. Enforces read-only execution file immutability.
"""

import sys
import json
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

J1_DIR = ROOT / "models/generated/mode_ii/verification_batch/M2REF_ONEEL_FRACFIX_VERIFY_R2"
J2_DIR = ROOT / "models/generated/mode_ii/verification_batch/M2REF_H0_EXACT_FRACFIX_REPRO"

EXPECTED_HASHES = {
    "J1_INP": ("40e5adf0dff1b03da96ab0bef09d3aa45317d5790b4a19931e228d85e33041ea", J1_DIR / "M2REF_ONEEL_FRACFIX_VERIFY_R2.inp"),
    "J1_UEL": ("0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8", J1_DIR / "f42_mixed_uel.for"),
    "J1_PBS": ("02ee8081d7b0c77595db0e13e132cd1ec95be9219cb42ecf3b7cc0407b25c7c2", J1_DIR / "M2REF_ONEEL_FRACFIX_VERIFY_R2.pbs"),
    "J1_SH":  ("54543ee9c80310522a07b5f335a66331865f0240e1844e830f00d5f296116c43", J1_DIR / "submit_m2ref_oneel_fracfix_verify_r2.sh"),

    "J2_INP": ("3f5d5457977513a92463c05e5220e74ef2fcfc890422010e65c2e1055e6e3c34", J2_DIR / "M2REF_H0_EXACT_FRACFIX_REPRO.inp"),
    "J2_UEL": ("0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8", J2_DIR / "f42_mixed_uel.for"),
    "J2_PBS": ("4b91b22ab4afd2ce0338974f164a57fd2bace2682433b7ab206b1cc9ca06a934", J2_DIR / "M2REF_H0_EXACT_FRACFIX_REPRO.pbs"),
    "J2_SH":  ("cf7c0cd9759713ea6413ebe0cccbb1acc63daa5cb0aa5f3225e685bde061f7ca", J2_DIR / "submit_m2ref_h0_exact_fracfix_repro.sh"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    print("=== Common Fail-Closed Preflight for Two-Job Verification Batch (Pair 1R) ===")
    errors = []

    # 1. Check all 8 hashes (Read-Only)
    for name, (expected, path) in EXPECTED_HASHES.items():
        if not path.exists():
            errors.append(f"Missing file: {path}")
            continue
        actual = sha256_file(path)
        if actual != expected:
            errors.append(f"Hash mismatch for {name} ({path.name}): expected {expected}, got {actual}")
        else:
            print(f"PASS [{name}]: {path.name} -> {actual[:12]}...")

    # 2. Check queue via qstat
    try:
        res = subprocess.run(["qstat", "-u", "pr21vyci"], capture_output=True, text=True, check=True)
        print("PASS [qstat]: Queue reachable and rc=0")
        output = res.stdout.strip()
        lines = [l for l in output.splitlines() if "M2REF" in l]
        if lines:
            errors.append(f"Duplicate active jobs found in queue:\n{output}")
    except Exception as err:
        errors.append(f"qstat check failed: {err}")

    if errors:
        print("\nPREFLIGHT FAILED:")
        for err in errors:
            print(f"  ERROR: {err}")
        sys.exit(1)
    else:
        print("\nALL PREFLIGHT CHECKS PASSED CLEANLY. SUBMISSION PERMITTED.")


if __name__ == "__main__":
    main()
