#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnose_mode1_turn133_r6_dissipation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 133)
Investigate the origin of excessive fracture energy and damage accumulation in Package 108 Revision 6.
"""

import sys
import json
from pathlib import Path
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
sys.path.append(str(REPO_ROOT / "scripts/validation"))

from evaluate_corrected_c3_coupled_transfer_and_increment import (
    C2_INP, C2_CSV, C3_MESH_INP,
    parse_mesh, load_c2_donor_state, classify_slit_flanks,
    build_fe_interpolator, shape_functions, UEL_GP_COORDS, UEL_WEIGHTS,
    compute_plane_strain_c0, uel_driving_energy, solve_elasticity_uel
)

def main():
    print("=" * 80)
    print("TURN 133: DIAGNOSING R6 FRACTURE-ENERGY OVER-DISSIPATION")
    print("=" * 80)

    # 1. Load R6 Telemetry and Energy CSV
    pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/108_r6_c3_multi_increment_continuation"
    with open(pkg_dir / "r6_extracted_telemetry.json", "r") as f:
        r6_telem = json.load(f)

    r6_energies = []
    with open(pkg_dir / "uel_energy_balance.csv", "r") as f:
        lines = [l.strip() for l in f if l.strip()]
        header = [c.strip() for c in lines[0].split(",")]
        for l in lines[1:]:
            parts = [float(x.strip()) for x in l.split(",")]
            r6_energies.append(dict(zip(header, parts)))

    # 2. Extract step details
    step_order = r6_telem["step_order"]
    print(f"R6 Steps Total: {len(step_order)}")
    
    # 3. Print step-by-step evolution of H_max, d_max, and E_frac
    print("\nR6 Step-by-Step Energy & History Evolution:")
    print(f"{'Step':<14} | {'u [mm]':<11} | {'RF2 [N]':<9} | {'H_max [MPa]':<11} | {'d_max':<8} | {'E_frac [mJ]':<11} | {'Delta Ef [uJ]':<12}")
    print("-" * 90)

    prev_ef = None
    first_departure_step = None
    step_analysis = []

    for idx, sname in enumerate(step_order, start=1):
        st = r6_telem["steps"][sname]
        # find matching energy row
        matching = [r for r in r6_energies if int(r["Step"]) == idx]
        ef_mJ = matching[-1]["E_fracture_kNmm"] * 1000.0 if matching else 0.0
        ee_mJ = matching[-1]["E_elastic_kNmm"] * 1000.0 if matching else 0.0
        et_mJ = matching[-1]["E_total_kNmm"] * 1000.0 if matching else 0.0
        
        delta_ef_uJ = (ef_mJ - prev_ef) * 1000.0 if prev_ef is not None else 0.0
        prev_ef = ef_mJ

        row = {
            "step_index": idx,
            "step_name": sname,
            "u_mm": st["rp_u2"],
            "rf2_N": st["rp_rf2_N"],
            "h_max_MPa": st["h_max"],
            "d_max": st["d_max"],
            "e_frac_mJ": ef_mJ,
            "e_elas_mJ": ee_mJ,
            "e_total_mJ": et_mJ,
            "delta_ef_uJ": delta_ef_uJ
        }
        step_analysis.append(row)

        print(f"{sname:<14} | {st['rp_u2']:.8f} | {st['rp_rf2_N']:9.3f} | {st['h_max']:11.6f} | {st['d_max']:.6f} | {ef_mJ:11.6f} | {delta_ef_uJ:+12.3f}")

        # Detection of first departure: when E_frac or H_max departs from Turn 107 reference
        # In Turn 107 benchmark: Stage A E_frac = 0.061017 mJ, final E_frac = 0.062404 mJ (+1.388 uJ total forward dissipation)
        if first_departure_step is None and idx > 1 and ef_mJ > 0.063652:  # exceeding +2% benchmark gate
            first_departure_step = {
                "step_index": idx,
                "step_name": sname,
                "ef_mJ": ef_mJ,
                "benchmark_target_mJ": 0.062404,
                "excess_pct": (ef_mJ - 0.062404) / 0.062404 * 100.0,
                "reason": "Fracture energy exceeded the upper tolerance boundary [0.061156, 0.063652] mJ for the first time."
            }

    print("-" * 90)
    print(f"First departure from Turn 107 benchmark occurs at: Step {first_departure_step['step_index']} ({first_departure_step['step_name']})")
    print(f"  E_frac: {first_departure_step['ef_mJ']:.6f} mJ vs benchmark {first_departure_step['benchmark_target_mJ']:.6f} mJ (+{first_departure_step['excess_pct']:.2f}%)")

    # Save detailed diagnosis
    diagnosis_output = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "turn": 133,
        "analysis": "R6_FRACTURE_ENERGY_OVER_DISSIPATION_DIAGNOSIS",
        "first_departure": first_departure_step,
        "step_analysis": step_analysis,
        "turn_107_benchmark": {
            "stage_A_ef_mJ": 0.061017,
            "stage_A_rf2_N": 180.227,
            "stage_A_dmax": 0.654995,
            "forward_target_ef_mJ": 0.062404,
            "forward_target_rf2_N": 179.298,
            "forward_target_dmax": 0.675399,
            "forward_max_H_MPa": 5.241126
        }
    }

    out_file = REPO_ROOT / "results/validation/mode1_f1597/r6_energy_dissipation_diagnosis.json"
    with open(out_file, "w") as f:
        json.dump(diagnosis_output, f, indent=2)
    print(f"\nDiagnosis written to: {out_file}")

if __name__ == "__main__":
    main()
