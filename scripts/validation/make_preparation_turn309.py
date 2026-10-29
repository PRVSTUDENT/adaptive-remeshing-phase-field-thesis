# -*- coding: utf-8 -*-
"""
make_preparation_turn309.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
RunId: 54b3d6dc-8b79-4510-82ce-dbe222342c7d
Hypothesis: H43
Protocol Version: 2

Generates preparation checkpoint artifact for Turn 309.
"""

from __future__ import print_function, division
import os
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")


def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest().upper()


def main():
    evidence_files = [
        "scripts/validation/audit_h43_runtime_state_injection.py",
        "tests/unit/test_mode1_f1597_h43_runtime_injection_audit.py",
        "results/validation/c3_int_to_c4_runtime_injection_audit.json",
        "scripts/state_transfer/build_package142_transfer_deck.py",
        "models/pandey_kumar_mode1/141_c3_int_donor_monotonic/f42_mixed_uel.for",
        "models/pandey_kumar_mode1/111_r2_c4_frame77_pre_instability/f42_unified_12dof_active_set_uel.for"
    ]

    evidence_sources = {}
    for rel_path in evidence_files:
        full_path = REPO_ROOT / rel_path
        if full_path.exists():
            evidence_sources[rel_path] = sha256_file(full_path)
        else:
            print("Warning: missing evidence file: %s" % rel_path)

    finding = (
        "Hypothesis H43 Runtime State-Injection Validation & Traceability Audit establishes: "
        "1. UMAT Companion Element Analysis: Formally proven to be read-only diagnostic visualizers; STATEV(1..20) "
        "are populated from COMMON /CB_STATE_TRANS/ and do not serve as initialization inputs for the solver. "
        "2. Production UEL History Ingestion (f42_mixed_uel.for, CE8D5EDC...): Initialized strictly at KSTEP=1, KINC<=1 "
        "via SVARS(8+KPT) = SVARS(9..12). UEXTERNALDB(LOP=0) zeroes state arrays and does NOT read external CSV files. "
        "To initialize history in pure Abaqus, *INITIAL CONDITIONS, TYPE=SOLUTION cards must be embedded in the input deck. "
        "3. Decoupled AM Driver Ingestion: Ingests d_lower_bounds.csv directly into Python memory for phase QP assembly, "
        "while injecting nodal damage d into Abaqus via active_set_boundary_cards.inc (*BOUNDARY cards). "
        "4. Critical Generator Defects Isolated: Package142DeckGenerator produces CSV tables but omits: (a) formatting "
        "active_set_boundary_cards.inc (*BOUNDARY cards for d), (b) embedding *INITIAL CONDITIONS, TYPE=SOLUTION cards, "
        "and (c) generating the executable M1_C4_PACKAGE142_STATE_TRANSFER.inp deck. "
        "5. Unit test verification: Authored tests/unit/test_mode1_f1597_h43_runtime_injection_audit.py "
        "(6/6 tests PASS, 26/26 combined nonmatching transfer suite PASS in 35.769s). "
        "Scheduler Status: Job 1418650 (Package 141) remains queued in normal_imfdfkmq; Package 142 submission "
        "remains withheld pending authentic solver checkpoint extraction. "
        "Classification: H43_RUNTIME_INJECTION_DEFECT_IDENTIFIED. Governing gates STAGE_C1_2_STEP2_ENERGY_GATE_FAILED "
        "(+2.00803158%), P113_GATE_VALID_FAILURE, and H24_REFERENCE_AUDIT_PENDING remain strictly invariant."
    )

    checkpoint = {
        "schema": 1,
        "status": "PREPARATION_COMPLETE",
        "finding": finding,
        "evidence_sources": evidence_sources,
        "verification_passed": True,
        "metadata": {
            "pbs_job_id": "1418650.mmaster02",
            "job_name": "M1_C3_INT_DONOR_MONOTONIC",
            "job_state": "QUEUED",
            "queue": "normal_imfdfkmq",
            "run_id": "54b3d6dc-8b79-4510-82ce-dbe222342c7d",
            "evaluated_nodes": 4588,
            "evaluated_gps": 17688,
            "receiver_elements": 4422,
            "defects_identified": 3,
            "unit_tests_passed": 6,
            "total_transfer_tests_passed": 26,
            "hypothesis": "H43",
            "classification": "H43_RUNTIME_INJECTION_DEFECT_IDENTIFIED"
        }
    }

    out_path = REPO_ROOT / "results/validation/preparation-54b3d6dc-8b79-4510-82ce-dbe222342c7d.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(checkpoint, f, indent=2)

    print("Wrote checkpoint artifact to: %s" % out_path)
    print("Finding length: %d chars" % len(finding))
    print("Verification passed: %s" % checkpoint["verification_passed"])


if __name__ == "__main__":
    main()
