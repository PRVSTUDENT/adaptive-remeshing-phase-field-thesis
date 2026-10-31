#!/usr/bin/env python3
"""
verify_package157_r4_registration_handoff.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: 885e4ba5-38dc-432e-abf2-4aaee364f925
Protocol Version: 2

Package 157 R4 Execution Registration and Final Handoff:
1. Reconciles authentic Step-1 solution cards (step1_committed_solution_initial.inc).
2. Verifies 28,224-GP history equivalence (8.9706e-14 MPa max discrepancy, 0 healing).
3. Verifies Step-1 equilibrium baseline (uy = 0.001850312544 mm, RF2 = 0.18501 kN).
4. Verifies frozen production UEL SHA-256 (CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6).
5. Inspects Controller-Operations.ps1 to determine registration status.
6. Emits definitive registration-status receipt: REGISTRATION_PENDING_REVIEW.
"""

import json
import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
AUTH_INC_SHA256 = "306ABF3C09FAA9CB9CEA37F48B8E93A8509C0FF0D0258E9B47667367D9808F60"


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def main():
    inc_path = REPO_ROOT / "results/validation/step1_committed_solution_initial.inc"
    history_audit_path = REPO_ROOT / "results/validation/authentic_step1_history_audit.json"
    full_history_path = REPO_ROOT / "results/validation/step1_equilibrium_checkpoint_1419113_full_history.json"
    endpoint_path = REPO_ROOT / "results/validation/step1_equilibrium_checkpoint_1419113_endpoint.json"
    uel_path = REPO_ROOT / "models/pandey_kumar_mode1/156_c5_package156_c2_0_re_equilibration/f42_mixed_uel.for"
    controller_ops_path = REPO_ROOT / "scripts/controller/Controller-Operations.ps1"
    output_receipt_path = REPO_ROOT / "results/validation/package157_r4_registration_status_receipt.json"

    # 1. Verify authentic solution cards
    assert inc_path.is_file(), f"Missing {inc_path}"
    real_inc_sha256 = compute_sha256(inc_path)
    assert real_inc_sha256 == AUTH_INC_SHA256, f"Hash mismatch for {inc_path}"

    # 2. Verify history audit
    with open(history_audit_path, "r", encoding="utf-8") as f:
        audit_data = json.load(f)
    assert audit_data["provenance_outcome"] == "AUTHENTIC_HISTORY_VERIFIED"
    assert audit_data["comparison_metrics"]["total_gauss_points_compared"] == 28224
    assert audit_data["comparison_metrics"]["max_absolute_difference_MPa"] < 1e-12
    assert audit_data["comparison_metrics"]["monotonicity_violations_count"] == 0

    # 3. Verify endpoint
    with open(endpoint_path, "r", encoding="utf-8") as f:
        ep_data = json.load(f)
    assert abs(float(ep_data["rp_u2"]) - 0.0018503125442191958) < 1e-12
    assert abs(float(ep_data["rf2_kN"]) - 0.18500999876) < 1e-6

    # 4. Verify frozen UEL
    assert compute_sha256(uel_path) == FROZEN_UEL_SHA256

    # 5. Check Controller-Operations.ps1
    with open(controller_ops_path, "r", encoding="utf-8") as f:
        ops_text = f.read()
    op_present = "execute_mode1_package157_c1_2_r4_adaptive_continuation" in ops_text

    registration_outcome = "REGISTERED_AND_ALLOWED" if op_present else "REGISTRATION_PENDING_REVIEW"

    # 6. Locked experiment definition
    experiment_definition = {
        "candidate_experiment_id": "M1_C4_P150_C1_2_R4",
        "target_package": "models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r4",
        "baseline_displacement_uy_mm": 0.0018503125442191958,
        "reaction_force_rf2_kN": 0.18500999876,
        "initial_forward_substeps_nm": [10.0, 10.0, 10.0, 10.0, 10.0],
        "initial_forward_targets_mm": [
            0.0018603125442191958,
            0.0018703125442191958,
            0.0018803125442191958,
            0.0018903125442191959,
            0.0019003125442191957
        ],
        "final_continuation_ceiling_mm": 0.002000000000,
        "minimum_subdivision_increment_nm": 5.0,
        "acceptance_criteria": {
            "delta_H_tol_MPa": 1e-6,
            "delta_d_tol": 1e-5,
            "delta_u_tol_mm": 1e-9,
            "signed_kkt_tol_MPa": 1e-6,
            "zero_damage_healing_enforced": True,
            "monotonic_history_enforced": True,
            "reaction_force_discrepancy_pct_max": 5.0,
            "energy_discrepancy_pct_max": 2.0
        }
    }

    receipt = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "run_id": "885e4ba5-38dc-432e-abf2-4aaee364f925",
        "registration_status": registration_outcome,
        "target_operation_id": "execute_mode1_package157_c1_2_r4_adaptive_continuation",
        "present_in_controller_operations": op_present,
        "scientific_review_ref": "results/validation/package157_r4_scientific_review_and_registration_handoff.json",
        "authentic_history_audit_ref": "results/validation/authentic_step1_history_audit.json",
        "authentic_solution_cards": "results/validation/step1_committed_solution_initial.inc",
        "authentic_solution_cards_sha256": real_inc_sha256,
        "frozen_uel_sha256": FROZEN_UEL_SHA256,
        "frozen_uel_verified": True,
        "locked_experiment_definition": experiment_definition,
        "registration_prerequisite": (
            "Add execute_mode1_package157_c1_2_r4_adaptive_continuation to scripts/controller/Controller-Operations.ps1 "
            "with its manifest and execution script binding prior to execution turn dispatch."
            if not op_present else "None: fully registered and allowed."
        ),
        "verified_hashes": {
            "results/validation/step1_committed_solution_initial.inc": real_inc_sha256,
            "results/validation/authentic_step1_history_audit.json": compute_sha256(history_audit_path),
            "results/validation/step1_equilibrium_checkpoint_1419113_full_history.json": compute_sha256(full_history_path),
            "results/validation/step1_equilibrium_checkpoint_1419113_endpoint.json": compute_sha256(endpoint_path),
            "models/pandey_kumar_mode1/156_c5_package156_c2_0_re_equilibration/f42_mixed_uel.for": FROZEN_UEL_SHA256
        }
    }

    with open(output_receipt_path, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)

    return receipt


if __name__ == "__main__":
    res = main()
    print("Registration Handoff Verified:", res["registration_status"], "Operation:", res["target_operation_id"])
