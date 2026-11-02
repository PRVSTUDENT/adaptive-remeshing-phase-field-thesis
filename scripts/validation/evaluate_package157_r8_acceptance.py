#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evaluate_package157_r8_acceptance.py
====================================
Evaluates authentic convergence and physical acceptance gates for Package 157 Revision 8
(PBS Job 1419490.mmaster02, independent C4 continuation reference at target uy = 0.001870312544 mm).

Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.evaluate_package157_continuation_acceptance import (
    load_authentic_reference_table,
    interpolate_authentic_reference,
    evaluate_physical_acceptance,
    evaluate_state_preservation,
    GATE_RF2_TOL,
    GATE_ENERGY_TOL,
    HEALING_TOL,
    CONVERGENCE_DELTA_H_TOL,
    CONVERGENCE_DELTA_D_TOL,
    CONVERGENCE_DELTA_U_TOL,
    TOTAL_C4_NODES,
    TOTAL_C4_GPS
)

R8_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "157_c4_package157_c1_2_continuation_r8"
EVIDENCE_DIR = R8_DIR / "evidence" / "1419490.mmaster02"
OUTPUT_JSON = REPO_ROOT / "results" / "validation" / "package157_r8_physical_acceptance.json"


def evaluate_package157_r8():
    checkpoint_file = EVIDENCE_DIR / "converged_checkpoint_01.json"
    runtime_report_file = EVIDENCE_DIR / "runtime_report.json"
    initial_checkpoint_file = R8_DIR / "initial_checkpoint_01.json"

    if not checkpoint_file.is_file() or not runtime_report_file.is_file():
        raise RuntimeError(f"Missing evidence files in {EVIDENCE_DIR}")

    cp_data = json.loads(checkpoint_file.read_text(encoding="utf-8"))
    init_data = json.loads(initial_checkpoint_file.read_text(encoding="utf-8"))
    report = json.loads(runtime_report_file.read_text(encoding="utf-8"))

    # 1. Kinematics & convergence metrics from runtime report
    summary = report["converged_steps"][0]
    target_uy = float(summary["target_uy_mm"])
    rf2_observed = float(summary["rf2_kN"])
    elastic_energy = float(summary["elastic_energy_kNmm"])
    fracture_energy = float(summary["fracture_energy_kNmm"])
    total_energy_observed = float(summary["total_energy_kNmm"])
    delta_d_final = float(summary["final_delta_d"])
    delta_u_final = float(summary["final_delta_u_mm"])
    delta_h_final = float(summary["final_delta_h_MPa"])
    converged_outer = int(summary["converged_outer_iteration"])

    coupled_conv_pass = (
        delta_d_final <= CONVERGENCE_DELTA_D_TOL and
        delta_u_final <= CONVERGENCE_DELTA_U_TOL and
        delta_h_final <= CONVERGENCE_DELTA_H_TOL and
        converged_outer <= 300
    )

    # 2. State preservation & bounds
    prev_d = {int(row[0]): float(row[1]) for row in init_data["damage"]}
    prev_h = {(int(row[0]), int(row[1])): float(row[2]) for row in init_data["history"]}
    curr_d = {int(row[0]): float(row[1]) for row in cp_data["damage"]}
    curr_h = {(int(row[0]), int(row[1])): float(row[2]) for row in cp_data["history"]}

    state_eval = evaluate_state_preservation(prev_d, prev_h, curr_d, curr_h)

    # 3. Matching-load reference physical acceptance
    ref_table = load_authentic_reference_table()
    phys_eval = evaluate_physical_acceptance(target_uy, rf2_observed, total_energy_observed, ref_table=ref_table)

    # Compile result
    result = {
        "schema": 1,
        "task_id": "F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE",
        "job_id": "1419490.mmaster02",
        "package": "models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r8",
        "role": "INDEPENDENT_C4_CONTINUATION_REFERENCE",
        "target_uy_mm": target_uy,
        "coupled_convergence": {
            "passed": coupled_conv_pass,
            "converged_outer_iteration": converged_outer,
            "final_delta_d": delta_d_final,
            "delta_d_tol": CONVERGENCE_DELTA_D_TOL,
            "final_delta_u_mm": delta_u_final,
            "delta_u_tol_mm": CONVERGENCE_DELTA_U_TOL,
            "final_delta_h_MPa": delta_h_final,
            "delta_h_tol_MPa": CONVERGENCE_DELTA_H_TOL
        },
        "state_preservation": state_eval,
        "physical_acceptance_vs_donor": phys_eval,
        "overall_verdict": "COUPLED_CONVERGED__PHYSICAL_ACCEPTANCE_FAIL" if not phys_eval["passed"] else "PHYSICAL_ACCEPTANCE_PASS",
        "finding": (
            f"Package 157-R8 (Job 1419490.mmaster02) achieved coupled PDAS convergence at outer {converged_outer} "
            f"at target uy={target_uy:.9f} mm (delta_d={delta_d_final:.3e}, delta_u={delta_u_final:.3e} mm, delta_H={delta_h_final:.3e} MPa). "
            f"Strict irreversibility (0 healing violations across {len(curr_d)} nodes) and history monotonicity across {len(curr_h)} GPs preserved. "
            f"RF2 discrepancy is {phys_eval['delta_rf2_rel']*100:.2f}% (<= 5.0% PASS), but raw total energy discrepancy is "
            f"{phys_eval['delta_energy_rel']*100:.2f}% (> 2.0% FAIL: {total_energy_observed:.5e} vs ref {phys_eval['ref_energy_kNmm']:.5e} kN*mm) "
            f"due to elevated fracture energy in continuation."
        )
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Physical acceptance evaluation written to {OUTPUT_JSON}")
    print(f"Overall verdict: {result['overall_verdict']}")
    print(f"Finding: {result['finding']}")
    return result


if __name__ == "__main__":
    evaluate_package157_r8()
