#!/bin/python3
"""
Raw-Byte SHA256 Audit Script for Mode-II Reference Family Decks
Task: F43MODEREF9-FINALANCHOR1
"""

import sys
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FILES_TO_AUDIT = [
    # H0
    ("H0 Input", ROOT / "models/generated/mode_ii/verification_batch/M2REF_H0_NPHYSFIX_REPRO/M2REF_H0_NPHYSFIX_REPRO.inp"),
    ("H0 UEL", ROOT / "models/generated/mode_ii/verification_batch/M2REF_H0_NPHYSFIX_REPRO/f42_mixed_uel.for"),
    ("H0 PBS", ROOT / "models/generated/mode_ii/verification_batch/M2REF_H0_NPHYSFIX_REPRO/M2REF_H0_NPHYSFIX_REPRO.pbs"),
    ("H0 Wrapper", ROOT / "models/generated/mode_ii/verification_batch/M2REF_H0_NPHYSFIX_REPRO/submit_m2ref_h0_nphysfix_repro.sh"),
    ("H0 Manifest", ROOT / "models/generated/mode_ii/verification_batch/M2REF_H0_NPHYSFIX_REPRO/M2REF_H0_NPHYSFIX_REPRO_MANIFEST.json"),
    
    # H1
    ("H1 Input", ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H1/M2REF_H1.inp"),
    ("H1 UEL", ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H1/f42_mixed_uel.for"),
    ("H1 PBS", ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H1/M2REF_H1.pbs"),
    ("H1 Wrapper", ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H1/submit_m2ref_h1.sh"),
    
    # H2
    ("H2 Input", ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H2/M2REF_H2.inp"),
    ("H2 UEL", ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H2/f42_mixed_uel.for"),
    ("H2 PBS", ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H2/M2REF_H2.pbs"),
    ("H2 Wrapper", ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H2/submit_m2ref_h2.sh"),
    
    # Batch Manifest
    ("Batch Manifest", ROOT / "models/generated/mode_ii/reference_convergence/M2REF_BATCH_MANIFEST.json"),
]

EXPECTED_H0 = {
    "H0 Input": "e86ad4b439fb93d2a43d3100e19911ed0f2df3ac25dcbe584a3b549830069268",
    "H0 UEL": "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8",
    "H0 PBS": "a1af3bc73828e0184fdb272ff2d50985bc00593bb0d905835e81e609e6a5e49b",
    "H0 Wrapper": "f54d9261b7087c16f25533a324d3f4e58e61c4a81700b4bc1fafd947a692e331",
    "H0 Manifest": "44fadd1c882a15a60facffa20202cdb35bca7b316434a6a582d3810b7ad70fdb",
}

EXPECTED_H1 = {
    "H1 Input": "94fda0134500b6ebadd7ae869f2c8909454b4112c6951b930c89ca02da907281",
    "H1 UEL": "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8",
    "H1 PBS": "273e06fbff87d6a521fb9aeab87f120070040d85109624171c7fa7cac01b5fd5",
    "H1 Wrapper": "9a39efa92a3de74d24381beab3cad3fb1125b2f7db50a6a52db59bc413ca9f80",
}

EXPECTED_H2 = {
    "H2 Input": "c3119217eb57662289971ad814c1f6c0020b15a4c10da170da91d990e774586a",
    "H2 UEL": "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8",
    "H2 PBS": "bed6926f473d185c2dfe9d55c57c4a7d0d7cb2ef1e9a8a9ff220508f4bd2e879",
    "H2 Wrapper": "b7592b020b4758ec1c68f07674b1980af392493c6d297eace9fcd1cfd7a5143b",
}


def raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    print("=== Raw-Byte vs Normalized Text SHA256 Audit ===")
    all_match = True
    results = {}

    all_expected = {**EXPECTED_H0, **EXPECTED_H1, **EXPECTED_H2}

    for label, path in FILES_TO_AUDIT:
        if not path.is_file():
            print(f"MISSING: {label} ({path})")
            all_match = False
            continue

        raw = raw_sha256(path)
        norm = normalized_sha256(path)
        expected = all_expected.get(label, "N/A")

        match_raw = (raw == expected) if expected != "N/A" else True
        match_norm = (norm == expected) if expected != "N/A" else True

        if not match_raw:
            all_match = False

        results[label] = {
            "raw_byte_hash": raw,
            "normalized_hash": norm,
            "expected_hash": expected,
            "raw_matches_expected": match_raw,
            "normalized_matches_expected": match_norm
        }

        print(f"\n[{label}]")
        print(f"  Path: {path.relative_to(ROOT)}")
        print(f"  raw_byte_hash   : {raw}")
        print(f"  normalized_hash : {norm}")
        print(f"  expected_hash   : {expected}")
        print(f"  Raw Match       : {match_raw}")

    print("\n" + "="*50)
    print(f"RAW BYTE HASH CONTRACT MATCH: {all_match}")
    print("="*50)
    return 0 if all_match else 1


if __name__ == "__main__":
    sys.exit(main())
