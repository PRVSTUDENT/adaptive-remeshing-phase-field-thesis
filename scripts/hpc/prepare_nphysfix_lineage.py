#!/usr/bin/env python3
"""Prepare Corrected H0/H1/H2 Lineage and Compute Exact Hashes.

Task: F43MODEREF8-NPHYSFIX-PREP1 (Sections 12, 13, 16)

Generates:
- M2REF_H0_NPHYSFIX_REPRO (NPHYS = 3930)
- M2REF_H1 (M2REF_H1_FRACFIX, NPHYS = 12064)
- M2REF_H2 (M2REF_H2_FRACFIX, NPHYS = 33852)

Computes and prints full 64-character SHA256 hashes for input, UEL, PBS, wrapper, manifest.
"""

import sys
import os
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.model_generation.build_mode_ii_nphysfix_h0_deck import build_package as build_h0
from scripts.model_generation.build_mode_ii_uniform_reference_batch import main as build_reference_batch
from scripts.validation.validate_nphys_producer_consumer_contract import audit_deck_nphys, DECKS_TO_VALIDATE


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    print("=== Step 1: Building Corrected H0 Package ===")
    h0_manifest = build_h0("M2REF_H0_NPHYSFIX_REPRO")
    print("H0 Package Built successfully.")

    print("\n=== Step 2: Building Uniform Reference Batch (H1 & H2) ===")
    build_reference_batch()
    print("Reference Batch Built successfully.")

    print("\n=== Step 3: Validating All Decks Against NPHYS Contract ===")
    all_pass = True
    for name, deck_path, expected_nphys in DECKS_TO_VALIDATE:
        res = audit_deck_nphys(deck_path, expected_nphys)
        status = "PASS" if res["overall_pass"] else "FAIL"
        print(f"  Deck '{name}': {status} (NPHYS={res['u2_property_nphys_value']}, P1 Match: {res['p1_index_match']})")
        if not res["overall_pass"]:
            all_pass = False

    if not all_pass:
        print("ERROR: NPHYS contract validation failed!")
        sys.exit(1)

    print("\n=== Step 4: Computing Execution Hashes ===")
    base_dir = ROOT / "models/generated/mode_ii"
    
    h0_dir = base_dir / "verification_batch/M2REF_H0_NPHYSFIX_REPRO"
    h1_dir = base_dir / "reference_convergence/M2REF_H1"
    h2_dir = base_dir / "reference_convergence/M2REF_H2"

    hashes = {
        "H0": {
            "input_sha256": sha256_file(h0_dir / "M2REF_H0_NPHYSFIX_REPRO.inp"),
            "uel_sha256": sha256_file(h0_dir / "f42_mixed_uel.for"),
            "pbs_sha256": sha256_file(h0_dir / "M2REF_H0_NPHYSFIX_REPRO.pbs"),
            "wrapper_sha256": sha256_file(h0_dir / "submit_m2ref_h0_nphysfix_repro.sh"),
            "manifest_sha256": sha256_file(h0_dir / "M2REF_H0_NPHYSFIX_REPRO_MANIFEST.json"),
        },
        "H1": {
            "input_sha256": sha256_file(h1_dir / "M2REF_H1.inp"),
            "uel_sha256": sha256_file(h1_dir / "f42_mixed_uel.for"),
            "pbs_sha256": sha256_file(h1_dir / "M2REF_H1.pbs"),
            "wrapper_sha256": sha256_file(h1_dir / "submit_m2ref_h1.sh"),
            "manifest_sha256": sha256_file(base_dir / "reference_convergence/M2REF_BATCH_MANIFEST.json"),
        },
        "H2": {
            "input_sha256": sha256_file(h2_dir / "M2REF_H2.inp"),
            "uel_sha256": sha256_file(h2_dir / "f42_mixed_uel.for"),
            "pbs_sha256": sha256_file(h2_dir / "M2REF_H2.pbs"),
            "wrapper_sha256": sha256_file(h2_dir / "submit_m2ref_h2.sh"),
            "manifest_sha256": sha256_file(base_dir / "reference_convergence/M2REF_BATCH_MANIFEST.json"),
        }
    }

    print(json.dumps(hashes, indent=2))

    summary_file = ROOT / "models/generated/mode_ii/F43MODEREF8_EXECUTION_HASHES.json"
    summary_file.write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    print(f"\nSaved execution hashes to: {summary_file}")


if __name__ == "__main__":
    main()
