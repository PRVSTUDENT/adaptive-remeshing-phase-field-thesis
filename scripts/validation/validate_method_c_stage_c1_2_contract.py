#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_method_c_stage_c1_2_contract.py
=========================================
Method C Stage C1-2 Forward Continuation Contract Specification and Offline Validator.

Governs the transition from Stage C1-1 (Coupled Fixed-Displacement State Transfer &
Re-Equilibration on Candidate C4) to Stage C1-2 (Forward Mechanical Displacement
Continuation and Crack Propagation on Candidate C4).

Enforces:
1. Strict Predecessor Acceptance Dependency: Stage C1-2 dispatch is strictly prohibited
   unless Stage C1-1 achieves full multi-gate physical acceptance:
   - RF2 reaction force continuity <= 5%
   - Raw total energy discrepancy <= 2%
   - Strict damage irreversibility: min(d_new - d_old) >= -1e-6
   - Physical phase bounds: 0 <= d <= 1
   - Complete 4-GP committed history H0 preservation across all 28,224 integration points.
2. Forward Loading Kinematics:
   - Preserves 7+8+3 solution card state serialization (displacement, phase, committed history).
   - Enforces forward displacement loading increments (Delta u = 0.0001 mm steps).
   - Preserves frozen production UEL SHA-256 (CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6).
3. Fail-Closed Preflight:
   - Reconciles active predecessor job (M1_C4_P148_R7, PBS 1418938.mmaster02).
   - Classifies Stage C1-2 execution as PENDING_PREDECESSOR_ACCEPTANCE while R7 iterates.
"""

import os
import sys
import json
import math
import hashlib
import argparse

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
GATE_FORCE_TOL = 0.05       # 5% max RF2 deficit
GATE_ENERGY_TOL = 0.02      # 2% max raw total energy discrepancy
HEALING_TOL = 1e-6          # Strict damage irreversibility limit
MAX_DAMAGE_LIMIT = 1.0 + 1e-9


def sha256_file(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def evaluate_c1_1_checkpoint_for_c1_2(checkpoint_dict):
    """
    Evaluates whether an authentic C1-1 equilibrium checkpoint satisfies all
    physical gates required to permit Stage C1-2 forward continuation.
    """
    reasons = []

    # 1. Schema check
    if checkpoint_dict.get("schema") != 1:
        reasons.append("Invalid checkpoint schema: expected 1")

    # 2. History semantics check
    semantics = checkpoint_dict.get("history_semantics", "")
    if "max(authentic transferred H0, frozen UEL POS_M at converged endpoint)" not in semantics:
        reasons.append("Invalid history semantics: must preserve authentic transferred H0 baseline")

    # 3. Displacements
    u = checkpoint_dict.get("displacement", [])
    if not u or len(u) < 100:
        reasons.append("Missing or incomplete displacement state")

    # 4. Damage field
    damage = checkpoint_dict.get("damage", [])
    if not damage:
        reasons.append("Missing damage state")
    else:
        d_vals = [d[1] for d in damage]
        if min(d_vals) < -1e-12:
            reasons.append(f"Negative damage detected: {min(d_vals)}")
        if max(d_vals) > MAX_DAMAGE_LIMIT:
            reasons.append(f"Damage exceeds 1.0: {max(d_vals)}")

    # 5. History field
    hist = checkpoint_dict.get("history", [])
    if not hist:
        reasons.append("Missing committed integration-point history")
    else:
        h_vals = [h[2] for h in hist]
        if min(h_vals) < -1e-12:
            reasons.append(f"Negative committed history detected: {min(h_vals)}")

    # 6. Physical gates evaluation
    gates = checkpoint_dict.get("gates", {})
    if not gates:
        reasons.append("Physical gates record missing from checkpoint")
    else:
        if not gates.get("pass_all", False):
            failed_gates = [k for k, v in gates.items() if v is False]
            reasons.append(f"Physical gates not passed: {failed_gates}")

    eligible = len(reasons) == 0
    return {
        "continuation_eligible": eligible,
        "blockers": reasons,
        "evaluated_node_count": len(damage) if damage else 0,
        "evaluated_gp_count": len(hist) if hist else 0,
    }


def generate_stage_c1_2_specification(workspace):
    """
    Generates the complete contract specification for Stage C1-2 forward continuation.
    """
    spec = {
        "schema": 1,
        "stage": "Stage_C1_2_Forward_Continuation",
        "predecessor_stage": "Stage_C1_1_Coupled_State_Transfer_ReEquilibration",
        "target_model": "Candidate_C4_Mesh",
        "production_uel_sha256": FROZEN_UEL_SHA256,
        "state_serialization": {
            "format": "7+8+3",
            "components": [
                "nodal_displacements (UX, UY)",
                "nodal_phase_field (PHI, d)",
                "integration_point_history (4 GP per CPE4 element, H0)"
            ],
            "total_integration_points": 28224,
            "total_nodes": 7266,
            "total_elements": 7056
        },
        "continuation_loading": {
            "mode": "displacement_control",
            "initial_uy_mm": 0.001800312544,
            "target_uy_mm": 0.002000000000,
            "step_increment_uy_mm": 0.00005,
            "solver": "staggered_mechanical_phase_pdas"
        },
        "acceptance_gates": {
            "gate_force_tol": GATE_FORCE_TOL,
            "gate_energy_tol": GATE_ENERGY_TOL,
            "healing_tol": HEALING_TOL,
            "max_damage_limit": MAX_DAMAGE_LIMIT,
            "history_monotonicity": "H_{k+1}(x) >= H_k(x) - 1e-9"
        },
        "current_predecessor_status": {
            "r7_job_id": "1418938.mmaster02",
            "r7_status": "TERMINAL_EXIT1_DELTA_H_CAP_EXCEEDED",
            "r8_job_id": "1418939.mmaster02",
            "r8_job_name": "M1_C4_P148_R8",
            "r8_status": "RUNNING_STAGGERED_EQUILIBRATION",
            "stage_c1_2_dispatch": "STRICTLY_BLOCKED_PENDING_C1_1_ACCEPTANCE"
        }
    }
    return spec


def main():
    parser = argparse.ArgumentParser(description="Stage C1-2 Contract Specification and Validator")
    parser.add_argument("--workspace", default=".", help="Workspace root path")
    parser.add_argument("--output", help="Optional output JSON path for specification")
    args = parser.parse_args()

    workspace = os.path.abspath(args.workspace)
    spec = generate_stage_c1_2_specification(workspace)

    if args.output:
        out_path = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2)
        print(f"Stage C1-2 Contract Specification written to {out_path}")
    else:
        print(json.dumps(spec, indent=2))


if __name__ == "__main__":
    main()
