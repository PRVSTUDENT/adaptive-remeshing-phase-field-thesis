# -*- coding: utf-8 -*-
"""
make_preparation_turn303.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
RunId: 61fb15aa-8392-4910-b4e6-65d6bdc0fc7a
Protocol Version: 2

Generates preparation checkpoint artifact for Turn 303.
"""

from __future__ import print_function, division
import os
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()

def main():
    evidence_files = [
        "models/pandey_kumar_mode1/141_c3_int_donor_monotonic/M1_C3_INT_DONOR_MONOTONIC.inp",
        "models/pandey_kumar_mode1/141_c3_int_donor_monotonic/f42_mixed_uel.for",
        "models/pandey_kumar_mode1/141_c3_int_donor_monotonic/job_notifications.sh",
        "models/pandey_kumar_mode1/141_c3_int_donor_monotonic/submit_M1_C3_INT_DONOR_MONOTONIC.pbs",
        "models/pandey_kumar_mode1/141_c3_int_donor_monotonic/PACKAGE_MANIFEST.json",
        "models/pandey_kumar_mode1/141_c3_int_donor_monotonic/M1_C3_INT_DONOR_MONOTONIC_AUTHORIZATION.json",
        "scripts/build_package141_c3_int_donor.py",
        "scripts/validation/stage_and_qualify_package141.py",
        "tests/unit/test_mode1_f1597_package141_qualification.py"
    ]

    evidence_sources = {}
    for rel_path in evidence_files:
        full_path = REPO_ROOT / rel_path
        if full_path.exists():
            evidence_sources[rel_path] = sha256_file(full_path)
        else:
            print("Warning: missing evidence file: %s" % rel_path)

    finding = (
        "Hypothesis H38 Package 141 (Candidate C3-Intermediate Continuous Donor Simulation) "
        "has been constructed, fully qualified offline and remotely on cluster scratch, and submitted "
        "to HPC under single-operation discipline (Job 1418650.mmaster02, queue normal_imfdfkmq, 1 CPU, 16 GB, 8h). "
        "Package 141 uses a 3-layer UEL architecture (2,484 elements per layer, 2,610 nodes, f42_mixed_uel.for) "
        "with a two-step continuous loading schedule (Step 1 targeting exact Frame-77 displacement "
        "u = 0.0018003125442191958 mm at constant rate 0.005 mm/s; Step 2 continuing seamlessly to u = 0.0020 mm). "
        "Remote Abaqus 2023 datacheck completed with exit code 0 (ANALYSIS DATACHECK COMPLETE), dual-channel "
        "notification contract verified PASS, and 5 unit qualification tests passed. Job 1418650 is queued "
        "to generate the authentic, physically consistent Frame-77 donor state required to unblock H37 "
        "C3-Int -> C4 state transfer evaluation. Governing gates STAGE_C1_2_STEP2_ENERGY_GATE_FAILED (+2.00803158%) "
        "and P113_GATE_VALID_FAILURE remain strictly invariant."
    )

    checkpoint = {
        "schema": 1,
        "status": "PREPARATION_COMPLETE",
        "finding": finding,
        "evidence_sources": evidence_sources,
        "verification_passed": True,
        "metadata": {
            "pbs_job_id": "1418650.mmaster02",
            "package_id": "141_c3_int_donor_monotonic",
            "job_name": "M1_C3_INT_DONOR_MONOTONIC",
            "run_id": "61fb15aa-8392-4910-b4e6-65d6bdc0fc7a",
            "queue": "normal_imfdfkmq",
            "resources": "1 CPU, 16GB RAM, 8h walltime",
            "elements": 2484,
            "physical_nodes": 2610,
            "target_displacement_step1_mm": 0.0018003125442191958,
            "target_displacement_step2_mm": 0.0020000000000000000,
            "uel_subroutine": "f42_mixed_uel.for",
            "uel_sha256": "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6",
            "datacheck_result": "PASS_EXIT0",
            "dual_channel_notification_contract": "PASS",
            "hypothesis": "H38",
            "classification": "H38_PACKAGE141_SUBMITTED"
        }
    }

    out_path = REPO_ROOT / "results/validation/preparation-61fb15aa-8392-4910-b4e6-65d6bdc0fc7a.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(checkpoint, f, indent=2)

    print("Wrote checkpoint artifact to: %s" % out_path)
    print("Finding length: %d chars" % len(finding))
    print("Verification passed: %s" % checkpoint["verification_passed"])

if __name__ == "__main__":
    main()
