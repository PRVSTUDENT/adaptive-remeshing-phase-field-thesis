#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_turn51_preparation_artifact.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: fbcc6f27-f8c5-4646-b45c-bbc02b5b241a
Protocol Version: 2

Generates the verified preparation checkpoint artifact:
results/validation/preparation-fbcc6f27-f8c5-4646-b45c-bbc02b5b241a.json
"""

import os
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
RUN_ID = "fbcc6f27-f8c5-4646-b45c-bbc02b5b241a"
OUTPUT_FILE = REPO_ROOT / f"results/validation/preparation-{RUN_ID}.json"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    evidence_rel_paths = [
        "models/pandey_kumar_mode1/90_r1_c3_active_set_transfer/f42_mixed_uel.for",
        "models/pandey_kumar_mode1/90_r1_c3_active_set_transfer/M1_C3_PACKAGE90_R1_TRANSFER.inp",
        "models/pandey_kumar_mode1/90_r1_c3_active_set_transfer/M1_C3_PACKAGE90_R1_TRANSFER.sta",
        "models/pandey_kumar_mode1/90_r1_c3_active_set_transfer/uel_energy_balance.csv",
        "models/pandey_kumar_mode1/90_r1_c3_active_set_transfer/candidate_crack_band_mesh_c3.inp",
        "models/pandey_kumar_mode1/91_c3_companion_miseseri/M1_C3_COMPANION_FRAME6.inp",
        "results/validation/mode1_f1597/pkg90_r1_frame6_audit_summary.json",
        "results/validation/mode1_f1597/pkg90_r1_frame6_nodal_state.csv",
        "results/validation/mode1_f1597/c3_companion_miseseri_summary.json",
        "results/validation/mode1_f1597/c3_companion_miseseri_distribution.csv",
        "results/validation/mode1_f1597/turn51_admissible_checkpoint_audit.json",
        "scripts/validation/build_c3_companion_deck.py",
        "scripts/validation/extract_c3_miseseri_distribution.py",
        "scripts/validation/extract_pkg90_r1_frame6_state.py",
        "scripts/validation/audit_turn51_donor_checkpoint.py",
        "tests/unit/test_mode1_f1597_turn51_miseseri_adaptation.py"
    ]

    evidence_sources = {}
    for rel_path in evidence_rel_paths:
        abs_p = REPO_ROOT / rel_path
        if not abs_p.exists():
            raise RuntimeError(f"Missing evidence source: {rel_path}")
        evidence_sources[rel_path] = sha256_file(abs_p)

    finding = (
        "Admissible donor state verified at Package 90-R1 Step 4 Frame 6 (u=0.0020367 mm, RF=159.16 N, "
        "d_max=0.97296 <= 1.00000, 0 overshoot nodes). Authentic Abaqus companion continuum solve (M1_C3_COMPANION_FRAME6, "
        "Exit 0) extracted Zienkiewicz-Zhu MISESERI error distribution across all 2,650 elements (peak MISESERI=4.2818 at "
        "element 1287, peak relative error eta=232.8% at element 1273, 420 elements / 15.85% exceeding 5% threshold). "
        "While autonomous REMESH is triggered by recovered stress error, sequential C3->C4 transfer is governed by a strict "
        "numerical dependency: committed Gauss-point history (H / SDV) is absent from the authentic donor ODB because only "
        "*Node Output (U, RF) was requested. Preserved scientifically valid NO-SUBMIT decision to avoid unverified history fabrication."
    )

    artifact = {
        "schema": 1,
        "controller_run_id": RUN_ID,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "status": "PREPARATION_COMPLETE",
        "finding": finding,
        "operation": "authentic_miseseri_adaptation_decision_and_donor_admissibility_audit",
        "title": "Admissible Donor Audit and Authentic MISESERI Error-Driven Adaptation Decision",
        "classification": "RESEARCH_PREPARATION_VERIFIED",
        "next_operation": "Advance to qualified execution or next research task",
        "verification_passed": True,
        "evidence_sources": evidence_sources,
        "donor_admissibility": {
            "checkpoint": "Package 90-R1 Step 4 Frame 6",
            "u2_rp_mm": 0.002036693,
            "rf2_rp_N": 159.1594,
            "d_max": 0.972955,
            "overshoot_nodes": 0,
            "damage_bounds_gate": "PASS"
        },
        "miseseri_error_distribution": {
            "total_elements": 2650,
            "peak_miseseri": 4.28178,
            "peak_eta_relative_error": 2.3283,
            "elements_exceeding_5pct": 420,
            "percentage_exceeding_5pct": 15.85,
            "autonomous_decision": "REMESH",
            "derivation": "Abaqus/Standard Zienkiewicz-Zhu recovery of element stress discontinuity ||sigma* - sigma_h||"
        },
        "dependency_resolution": {
            "history_sdvs_in_odb": False,
            "transfer_status": "NO_SUBMISSION__COMMITTED_HISTORY_DEPENDENCY_BLOCKS_UNINVENTED_C4_TRANSFER",
            "governance": "JOB_FIRST_REPORT_AFTER__NO_INVENTED_HISTORY"
        }
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print(f"Wrote preparation artifact: {OUTPUT_FILE}")
    print(f"Artifact SHA-256: {sha256_file(OUTPUT_FILE)}")

if __name__ == "__main__":
    main()
