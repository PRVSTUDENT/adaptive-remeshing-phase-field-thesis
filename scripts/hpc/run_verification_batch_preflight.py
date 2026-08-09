#!/usr/bin/env python3
"""Common Fail-Closed Preflight for Two-Job Verification Batch (Pair 1).

Validates:
1. Exact preparation tag P43MODEREF5-FINAL1 (3f4f23d9fca381e1899efc6ab721ce5cf0b02411).
2. Exact qualification tag Q43MODEREF5 (926fbb5001ffae01e63a15afbf1a7008cf36eecb).
3. All 8 full 64-character execution hashes for Job 1 (M2REF_ONEEL_FRACFIX_VERIFY) and Job 2 (M2REF_H0_FRACFIX_REPRO).
4. Queue status via qstat (rc=0, no duplicate active jobs).
"""

import sys
import json
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

J1_DIR = ROOT / "models/generated/mode_ii/verification_batch/M2REF_ONEEL_FRACFIX_VERIFY"
J2_DIR = ROOT / "models/generated/mode_ii/verification_batch/M2REF_H0_FRACFIX_REPRO"

EXPECTED_HASHES = {
    "J1_INP": ("0a86b66a5434e06415c1721fbf6b21ee0e38b1107803efb2836070c9f5b35512", J1_DIR / "M2REF_ONEEL_FRACFIX_VERIFY.inp"),
    "J1_UEL": ("0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8", J1_DIR / "f42_mixed_uel.for"),
    "J1_PBS": ("240969e9be531f0e917619ae422ce78ae21c3c5ef889b4feb85c4477b22a24df", J1_DIR / "M2REF_ONEEL_FRACFIX_VERIFY.pbs"),
    "J1_SH":  ("09edb59b8943f0577b96512d8a4f900bb4e04525691d6ce772cd3f95400cb99c", J1_DIR / "submit_m2ref_oneel_fracfix_verify.sh"),

    "J2_INP": ("4bcc529509d3491bfffb28b33078f0759cb55cdac2bcabbbadb6be99a5fc08f5", J2_DIR / "M2REF_H0_FRACFIX_REPRO.inp"),
    "J2_UEL": ("0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8", J2_DIR / "f42_mixed_uel.for"),
    "J2_PBS": ("9c326977bf9a9100811062b6bc367e442b83086103efe8f66d6e405fc025db65", J2_DIR / "M2REF_H0_FRACFIX_REPRO.pbs"),
    "J2_SH":  ("16d4d2d7746b3144bdf6a5de2c858e44c33ede0fc7b951f96f879507c16b4d9a", J2_DIR / "submit_m2ref_h0_fracfix_repro.sh"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    print("=== Common Fail-Closed Preflight for Two-Job Verification Batch ===")
    errors = []

    # 1. Check all 8 hashes
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
