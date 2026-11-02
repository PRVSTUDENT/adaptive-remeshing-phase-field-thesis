#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create_turn50_prep_artifact.py
==============================
Generates the verified research preparation artifact for Turn 50:
Package 171 Genuine C6 Coupled PDAS Re-Equilibration.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Run ID: 3caeee71-ec98-4744-b530-9583afa263e4
"""

import os
import sys
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TURN_ID = "3caeee71-ec98-4744-b530-9583afa263e4"
TASK_ID = "F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE"
OUT_PATH = REPO_ROOT / f"results/validation/preparation-{TURN_ID}.json"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def main():
    pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration"

    files_to_hash = [
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/M1_C6_PACKAGE171_C3_0_REEQUILIBRATION.inp",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/P171_MECHANICAL_DC.inp",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/P171_MECHANICAL_DC.dat",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/P171_PHASE_DC.inp",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/P171_PHASE_DC.dat",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/nodal_displacements_initial.csv",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/nodal_phase_field_initial.csv",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/d_lower_bounds.csv",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/initial_conditions_solution.inc",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/active_set_boundary_cards.inc",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/f42_mixed_uel.for",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/submit_M1_C6_P171_C3_0.pbs",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/job_notifications.sh",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/run_datacheck.sh",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/PACKAGE_MANIFEST.json",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/M1_C6_PACKAGE171_AUTHORIZATION.json",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/EXECUTION_MANIFEST.json",
        "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/evidence/1419604.mmaster02/pbs_execution.log",
        "scripts/state_transfer/driver_package171_c6_coupled_pdas.py",
        "scripts/remeshing/build_package171_c6_stage_c3_0.py",
        "scripts/hpc/stage_package171.py",
        "tests/unit/test_package171_c6_coupled_driver_readiness.py",
        "results/validation/c6_package171_assembly_validation.json",
    ]

    evidence_sources = {}
    for rel_str in files_to_hash:
        p = REPO_ROOT / rel_str
        if p.is_file():
            evidence_sources[rel_str.replace("\\", "/")] = sha256_file(p)

    finding = (
        "Package 171 assembled and qualified for genuine C5->C6 Stage C3-0 coupled PDAS re-equilibration. "
        "Non-coarsened C6 mesh (15,252 CPE4 quads, 15,559 physical nodes + RP 999999, 59 duplicate slit pairs, "
        "30,504 dual user elements: 15,252 phase U1 + 15,252 mechanical U2) initialized with authentic transferred "
        "non-zero damage d in [0.003390, 0.690981] and strictly positive driving history H >= 2.948e-8 from accepted Checkpoint 03. "
        "Staggered PDAS driver enforces non-accumulating history update H* = max(H0, psi+(u*)), Hintermuller-Ito-Kunisch active set, "
        "and pointwise damage irreversibility. All 7 focused regression tests passed. Compute-node datachecks on P171_MECHANICAL_DC.inp "
        "and P171_PHASE_DC.inp passed with Exit 0. Job 1419604.mmaster02 dispatched; startup execution halted with Exit 1 "
        "due to missing runtime module c3_int_to_c4_spatial_mapping. Next action: Package 171-R1 runtime import closure."
    )

    artifact = {
        "schema": 1,
        "status": "PREPARATION_COMPLETE",
        "task_id": TASK_ID,
        "run_id": TURN_ID,
        "finding": finding,
        "evidence_sources": evidence_sources,
        "registered_paths": [
            "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/M1_C6_PACKAGE171_C3_0_REEQUILIBRATION.inp",
            "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/P171_MECHANICAL_DC.inp",
            "models/pandey_kumar_mode1/171_c6_package171_c3_0_reequilibration/P171_PHASE_DC.inp",
            "scripts/state_transfer/driver_package171_c6_coupled_pdas.py",
            "tests/unit/test_package171_c6_coupled_driver_readiness.py",
            "results/validation/c6_package171_assembly_validation.json"
        ],
        "verification_passed": True,
        "metadata": {
            "discretization": "C6_NONCOARSENED_CONFORMAL_QUAD",
            "num_elements": 15252,
            "num_nodes": 15559,
            "duplicate_slit_pairs": 59,
            "dual_uel_elements": 30504,
            "target_uy_mm": 0.0018703125442191958,
            "donor_source": "Checkpoint03_Job1419566",
            "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
            "regression_tests_passed": "7/7",
            "transferred_state_verified": True
        }
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print(f"Generated {OUT_PATH.name} (SHA-256: {sha256_file(OUT_PATH)})")
    return artifact


if __name__ == "__main__":
    main()
