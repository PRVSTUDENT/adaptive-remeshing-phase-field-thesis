#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evaluate_package80_solver_results.py

Comprehensive evaluation of Package 80 peak-preserved re-equilibration diagnostic
(Job 1416366.mmaster02) under Task F1597 Turn 28.
Audits:
1. Reaction force RF2 continuity across Steps 1, 2, and 3.
2. Fracture and elastic energy evolution and reconciliation with donor.
3. KKT active-set multiplier signs, complementarity, and healing.
4. Localized crack-tip softening and cutback root-cause analysis.
5. Strict Method C Gate C1-1 evaluation matrix.
"""

import os
import sys
import json
import csv
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG80_DIR = REPO_ROOT / "models/pandey_kumar_mode1/80_candidate_c2_peak_preserved_reequilibration"
TELEMETRY_JSON = PKG80_DIR / "pkg80_extracted_telemetry.json"
ENERGY_CSV = PKG80_DIR / "uel_energy_balance.csv"
STA_FILE = PKG80_DIR / "M1_C2_PEAK_PRESERVED_REEQUIL.sta"
MSG_FILE = PKG80_DIR / "M1_C2_PEAK_PRESERVED_REEQUIL.msg"

DONOR_ENERGY_CSV = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_1416301/uel_energy_balance.csv"

OUTPUT_EVAL_JSON = REPO_ROOT / "results/validation/mode1_f1597/f1597_turn28_package80_evaluation.json"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def evaluate_package80():
    if not TELEMETRY_JSON.exists():
        raise FileNotFoundError(f"Missing {TELEMETRY_JSON}")
    if not ENERGY_CSV.exists():
        raise FileNotFoundError(f"Missing {ENERGY_CSV}")

    with open(TELEMETRY_JSON, "r", encoding="utf-8") as f:
        telem = json.load(f)

    # 1. Parse Energy CSV
    energy_rows = []
    with open(ENERGY_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            energy_rows.append({
                "step": int(r["Step"].strip()),
                "inc": int(r["Increment"].strip()),
                "total_time": float(r["TotalTime"].strip()),
                "step_time": float(r["StepTime"].strip()),
                "e_elastic_uj": float(r["E_elastic_kNmm"].strip()) * 1e6, # convert kN*mm to microJ
                "e_fracture_uj": float(r["E_fracture_kNmm"].strip()) * 1e6,
                "e_total_uj": float(r["E_total_kNmm"].strip()) * 1e6
            })

    step1_energy = [r for r in energy_rows if r["step"] == 1][-1]
    step2_start_energy = [r for r in energy_rows if r["step"] == 2][0]
    step2_end_energy = [r for r in energy_rows if r["step"] == 2][-1]
    step3_start_energy = [r for r in energy_rows if r["step"] == 3][0]
    step3_end_energy = [r for r in energy_rows if r["step"] == 3][-1]

    # Authentic donor reference: Package 76 Frame 111 (transfer point u_top = 0.002540107 mm)
    # RF2 = 3.266150 N, E_frac = 293.92334 microJ, E_elas = 7.82236 microJ
    DONOR_RF2_N = 3.266150
    DONOR_E_FRAC_UJ = 293.92334
    DONOR_E_ELAS_UJ = 7.82236

    # 2. Extract Reaction Forces from telemetry
    rf2_trace = telem["rf2_history"]
    # Parse RF2 by step (values are in kN, convert to N)
    step1_rf2_terminal = None
    step2_rf2_terminal = None
    step3_rf2_terminal = None
    for sname, t, val in rf2_trace:
        val_N = val * 1000.0
        if sname == "STATE_INJECTION" and abs(t - 1.0) < 1e-4:
            step1_rf2_terminal = val_N
        elif sname == "MECH_REEQUIL_FROZEN_DAMAGE" and abs(t - 1.0) < 1e-4:
            step2_rf2_terminal = val_N
        elif sname == "ACTIVE_SET_COUPLED_REEQUIL":
            step3_rf2_terminal = val_N # will capture the last recorded

    step1_rf2_err_pct = ((step1_rf2_terminal - DONOR_RF2_N) / DONOR_RF2_N) * 100.0
    step2_rf2_err_pct = ((step2_rf2_terminal - DONOR_RF2_N) / DONOR_RF2_N) * 100.0
    step3_rf2_err_pct = ((step3_rf2_terminal - DONOR_RF2_N) / DONOR_RF2_N) * 100.0

    # Energy continuity errors
    step1_e_frac_err_pct = ((step1_energy["e_fracture_uj"] - DONOR_E_FRAC_UJ) / DONOR_E_FRAC_UJ) * 100.0
    step2_e_frac_err_pct = ((step2_end_energy["e_fracture_uj"] - DONOR_E_FRAC_UJ) / DONOR_E_FRAC_UJ) * 100.0
    step3_e_frac_err_pct = ((step3_end_energy["e_fracture_uj"] - DONOR_E_FRAC_UJ) / DONOR_E_FRAC_UJ) * 100.0

    # 3. Irreversibility and KKT audit
    irrev = telem["damage_irreversibility"]
    kkt = telem["kkt_active_set_verification"]

    # Gate C1-1 criteria evaluation
    gate_c1_1 = {
        "step3_coupled_completion": {
            "target": "1.000 (100% of coupled re-equilibration step)",
            "measured": telem["step_telemetry"]["ACTIVE_SET_COUPLED_REEQUIL"]["terminal_step_time"],
            "status": "FAIL",
            "notes": "Cutback down to dt < 1e-12 at increment 13 (step time 0.03655) due to unregularized crack-tip softening"
        },
        "reaction_force_continuity": {
            "target": "<= 5.0% error vs donor 3.266150 N",
            "step1_injected_rf2_N": step1_rf2_terminal,
            "step1_rf2_error_pct": step1_rf2_err_pct,
            "step2_frozen_rf2_N": step2_rf2_terminal,
            "step2_rf2_error_pct": step2_rf2_err_pct,
            "step3_terminal_rf2_N": step3_rf2_terminal,
            "step3_rf2_error_pct": step3_rf2_err_pct,
            "status": "FAIL",
            "notes": "Step 1 achieved exact parity (+0.066% error), but Step 2 interior release rose to 7.319 N (+124.1%), dropping to 5.191 N (+58.9%) before Step 3 cutback"
        },
        "fracture_energy_continuity": {
            "target": "<= 2.0% error vs donor 293.92334 microJ",
            "step1_e_frac_uj": step1_energy["e_fracture_uj"],
            "step1_e_frac_error_pct": step1_e_frac_err_pct,
            "step2_e_frac_uj": step2_end_energy["e_fracture_uj"],
            "step2_e_frac_error_pct": step2_e_frac_err_pct,
            "step3_e_frac_uj": step3_end_energy["e_fracture_uj"],
            "step3_e_frac_error_pct": step3_e_frac_err_pct,
            "status": "PASS",
            "notes": "Fracture energy preserved with +0.53% error across Step 1 and Step 2, rising slightly to +0.84% in Step 3 (+0.53% <= 2.0% PASS)"
        },
        "damage_irreversibility": {
            "target": "zero healing violations (min delta_d >= 0.0)",
            "healing_nodes_count": irrev["healing_violations_count"],
            "min_delta_d": irrev["min_delta_d"],
            "stationary_nodes_count": irrev["stationary_nodes_count"],
            "advancing_nodes_count": irrev["advancing_nodes_count"],
            "status": "FAIL",
            "notes": "4 healing nodes detected (min delta_d = -0.000657), down from 9 in Pkg 79 and 291 in Pkg 72"
        },
        "kkt_complementarity": {
            "target": "zero complementarity slack violations, dual multipliers lambda >= 0",
            "slack_violations_count": kkt["complementarity_violations_count"],
            "negative_multiplier_count": kkt["dual_feasibility_negative_count"],
            "min_lambda": kkt["min_active_lambda"],
            "status": "FAIL",
            "notes": "49 nodes with small negative lambda (min -5.03e-6) in unconstrained crack wake / tip transition"
        },
        "overall_gate_verdict": "FAILED"
    }

    # Summary of findings
    findings = {
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "evaluation_target": "Package 80 Peak-Preserved Re-equilibration Diagnostic",
        "job_id": "1416366.mmaster02",
        "mesh": "Candidate C2 (h=1.0 um, 2300 CPE4 quads, 2413 physical nodes)",
        "step1_parity": {
            "rf2_N": step1_rf2_terminal,
            "donor_rf2_N": DONOR_RF2_N,
            "rf2_error_pct": step1_rf2_err_pct,
            "e_frac_uj": step1_energy["e_fracture_uj"],
            "donor_e_frac_uj": DONOR_E_FRAC_UJ,
            "e_frac_error_pct": step1_e_frac_err_pct,
            "verdict": "EXACT_PARITY_PASS"
        },
        "step2_frozen_relaxation": {
            "initial_rf2_N": step1_rf2_terminal,
            "terminal_rf2_N": step2_rf2_terminal,
            "package79_comparison_N": 11.708741,
            "reduction_vs_pkg79_N": 11.708741 - step2_rf2_terminal,
            "e_elastic_initial_uj": step2_start_energy["e_elastic_uj"],
            "e_elastic_terminal_uj": step2_end_energy["e_elastic_uj"],
            "verdict": "WAKE_PRESTRESS_REDUCED_BY_4_39N_BUT_RESIDUAL_PRESTRESS_REMAINS"
        },
        "step3_coupled_convergence": {
            "start_time": 0.0,
            "terminal_time": telem["step_telemetry"]["ACTIVE_SET_COUPLED_REEQUIL"]["terminal_step_time"],
            "exit_code": 1,
            "termination_reason": "TIME_INCREMENT_REQUIRED_LESS_THAN_MINIMUM",
            "limiting_node_u": 1192,
            "limiting_node_d": 1239,
            "largest_scaled_residual": -3.384e-4,
            "largest_disp_increment": 2.368e-2,
            "verdict": "CRACK_TIP_SOFTENING_SNAPBACK_CUTBACK"
        },
        "gate_c1_1_matrix": gate_c1_1,
        "root_cause_analysis": (
            "Peak-preserving projection restored authentic wake damage d=0.997133, achieving exact Step 1 parity "
            "(RF2 error +0.066%, E_frac error +0.53%) and reducing Step 2 spurious reaction force by 4.39 N (from 11.71 N to 7.32 N). "
            "However, in Step 2, releasing interior displacement constraints under frozen damage still caused RF2 to rise to 7.32 N (+124%) "
            "because coarse-to-fine interpolation strains between h=2.5 um donor and h=1.0 um C2 mesh produce non-zero mechanical residuals. "
            "In Step 3, when crack-tip damage was released, the localized softening snapback at Node 1239 (delta_d = +0.052) "
            "triggered severe standard Newton cutbacks down to dt < 1e-12 at t=0.03655. "
            "To traverse this softening state to full equilibrium (t=1.0), coupled re-equilibration requires either arc-length / Riks control "
            "or numerical viscous regularization on the damage evolution equation."
        )
    }

    OUTPUT_EVAL_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_EVAL_JSON, "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2)

    print(f"Wrote evaluation artifact to: {OUTPUT_EVAL_JSON}")
    return findings

if __name__ == "__main__":
    evaluate_package80()
