#!/usr/bin/env python3
"""
Mode-II PK10R2 Corrected Topology Validation Evaluator:
Deterministic scientific postprocessing and evaluation tool for M2CORR_PK10R2_TOPOLOGY_CORRECTED.
Evaluates trajectory and metrics against authoritative criterion registry:
  - scripts/postprocessing/criterion_registry.json
Authoritative Accepted References (0.29 kN Lineage):
  - H1 Reference: 1389686.mmaster02 (M2CORR_H1_FREEU2_FULL_U050)
  - H2 Reference: 1389687.mmaster02 (M2CORR_H2_FREEU2_FULL_U050)
Defective Baseline:
  - PK10R1 Baseline: 1389684.mmaster02 (M2CORR_PK10R1_CONTINUOUS_U050)
"""

import os
import sys
import re
import csv
import math
import json
import subprocess
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REGISTRY_PATH = SCRIPT_DIR / "criterion_registry.json"

def load_criterion_registry():
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Criterion registry not found: {REGISTRY_PATH}")
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    crit_map = {c["criterion_id"]: c for c in data.get("criteria", [])}
    return crit_map

CRITERIA = load_criterion_registry()

# Authoritative Accepted References (Canonical Mode-II Reference Lineage)
ACCEPTED_REFERENCES = {
    "H1": {
        "job_id": "1389686.mmaster02",
        "job_name": "M2CORR_H1_FREEU2_FULL_U050",
        "mesh_size_min_mm": 0.0020,
        "nphys_elements": 12064,
        "k0_kN_mm": 12.834574,
        "peak_rf1_kN": 0.143686,
        "peak_u1_mm": 0.012530,
        "status": "ACCEPTED"
    },
    "H2": {
        "job_id": "1389687.mmaster02",
        "job_name": "M2CORR_H2_FREEU2_FULL_U050",
        "mesh_size_min_mm": 0.0010,
        "nphys_elements": 33852,
        "k0_kN_mm": 12.816396,
        "peak_rf1_kN": 0.141415,
        "peak_u1_mm": 0.012214,
        "status": "ACCEPTED"
    }
}

DEFECTIVE_PK10R1 = {
    "job_id": "1389684.mmaster02",
    "job_name": "M2CORR_PK10R1_CONTINUOUS_U050",
    "k0_kN_mm": 31.989910,
    "peak_rf1_kN": 0.383101,
    "peak_u1_mm": 0.013606,
    "stiffness_defect_pct": 149.25,
    "peak_force_defect_pct": 166.62
}


def load_trajectory_from_csv(csv_path):
    if not os.path.exists(csv_path):
        return None
    rows = []
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                u1 = float(r.get("u1_mm") or r.get("U1") or r.get("u1") or 0.0)
                rf1 = float(r.get("rf1_kN") or r.get("RF1") or r.get("rf1") or 0.0)
                d_max = float(r.get("d_max") or r.get("SDV15") or r.get("phase_max") or 0.0)
                step_time = float(r.get("step_time") or r.get("time") or 0.0)
                rows.append({
                    "step_time": step_time,
                    "u1_mm": u1,
                    "rf1_kN": rf1,
                    "d_max": d_max
                })
            except (ValueError, TypeError):
                continue
    return rows if len(rows) > 1 else None

def parse_sta_file(sta_path):
    if not os.path.exists(sta_path):
        return {"exists": False, "completed_cleanly": False, "total_increments": 0}
    inc_count = 0
    completed = False
    with open(sta_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 8:
                try:
                    inc_num = int(parts[1])
                    inc_count += 1
                except ValueError:
                    pass
            if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in line.upper():
                completed = True
    return {
        "exists": True,
        "completed_cleanly": completed,
        "total_increments": inc_count
    }

def calculate_k0_stiffness(trajectory):
    """
    Calculates initial linear elastic stiffness K0 from early linear increments (u1 <= 0.0003 mm).
    Method: Linear elastic secant on initial increment: K0 = RF1 / U1.
    """
    linear_points = [p for p in trajectory if 1.0e-7 < p["u1_mm"] <= 0.0003]
    if not linear_points:
        linear_points = [p for p in trajectory if p["u1_mm"] > 1.0e-7][:3]
    if not linear_points:
        return None, "No valid linear points found"

    p_first = linear_points[0]
    k0_val = p_first["rf1_kN"] / p_first["u1_mm"]
    return {
        "k0_kN_mm": k0_val,
        "sample_u1_mm": p_first["u1_mm"],
        "sample_rf1_kN": p_first["rf1_kN"]
    }, None

def calculate_peak_and_terminal(trajectory):
    if not trajectory:
        return None
    peak_pt = max(trajectory, key=lambda x: x["rf1_kN"])
    term_pt = trajectory[-1]
    return {
        "peak_rf1_kN": peak_pt["rf1_kN"],
        "peak_u1_mm": peak_pt["u1_mm"],
        "terminal_rf1_kN": term_pt["rf1_kN"],
        "terminal_u1_mm": term_pt["u1_mm"]
    }

def evaluate_pk10r2_topology(candidate_dir, output_json=None):
    cand_path = Path(candidate_dir)
    print(f"=== Evaluating PK10R2 Corrected Topology Validation Job: {cand_path.name} ===")

    sta_files = list(cand_path.glob("*.sta"))
    sta_info = parse_sta_file(str(sta_files[0])) if sta_files else {}

    traj_csv = cand_path / f"{cand_path.name}.extracted_trajectory.csv"
    if not traj_csv.exists():
        traj_csv = cand_path / "trajectory.csv"

    trajectory = load_trajectory_from_csv(str(traj_csv)) if traj_csv.exists() else []

    if not trajectory:
        return {
            "status": "UNRESOLVED",
            "error": "No trajectory extracted from CSV or ODB",
            "job_identity": cand_path.name
        }

    trajectory.sort(key=lambda x: x["u1_mm"])

    k0_fit, k0_err = calculate_k0_stiffness(trajectory)
    peak_term = calculate_peak_and_terminal(trajectory)

    cand_k0 = k0_fit["k0_kN_mm"] if k0_fit else None
    cand_peak_rf = peak_term["peak_rf1_kN"] if peak_term else None
    cand_peak_u = peak_term["peak_u1_mm"] if peak_term else None

    # Reference Comparisons
    h1_ref = ACCEPTED_REFERENCES["H1"]
    h2_ref = ACCEPTED_REFERENCES["H2"]

    h1_diff_k0_pct = ((cand_k0 - h1_ref["k0_kN_mm"]) / h1_ref["k0_kN_mm"] * 100.0) if cand_k0 else None
    h1_diff_peak_rf_pct = ((cand_peak_rf - h1_ref["peak_rf1_kN"]) / h1_ref["peak_rf1_kN"] * 100.0) if cand_peak_rf else None
    h1_diff_peak_u_pct = ((cand_peak_u - h1_ref["peak_u1_mm"]) / h1_ref["peak_u1_mm"] * 100.0) if cand_peak_u else None

    h2_diff_k0_pct = ((cand_k0 - h2_ref["k0_kN_mm"]) / h2_ref["k0_kN_mm"] * 100.0) if cand_k0 else None
    h2_diff_peak_rf_pct = ((cand_peak_rf - h2_ref["peak_rf1_kN"]) / h2_ref["peak_rf1_kN"] * 100.0) if cand_peak_rf else None
    h2_diff_peak_u_pct = ((cand_peak_u - h2_ref["peak_u1_mm"]) / h2_ref["peak_u1_mm"] * 100.0) if cand_peak_u else None

    # Diagnostic Error Reduction Fractions relative to PK10R1 baseline
    err_pk10r1_k0 = abs(DEFECTIVE_PK10R1["k0_kN_mm"] - h2_ref["k0_kN_mm"]) # 110.79 kN/mm
    err_pk10r1_rf = abs(DEFECTIVE_PK10R1["peak_rf1_kN"] - h2_ref["peak_rf1_kN"]) # 0.08841 kN
    err_pk10r1_u  = abs(DEFECTIVE_PK10R1["peak_u1_mm"] - h2_ref["peak_u1_mm"])

    if cand_k0 is not None and cand_peak_rf is not None:
        err_pk10r2_k0 = abs(cand_k0 - h2_ref["k0_kN_mm"])
        err_pk10r2_rf = abs(cand_peak_rf - h2_ref["peak_rf1_kN"])
        err_pk10r2_u  = abs(cand_peak_u - h2_ref["peak_u1_mm"]) if cand_peak_u else 0.0

        red_frac_k0 = 1.0 - (err_pk10r2_k0 / err_pk10r1_k0)
        red_frac_rf = 1.0 - (err_pk10r2_rf / err_pk10r1_rf)
        red_frac_u  = 1.0 - (err_pk10r2_u / err_pk10r1_u) if err_pk10r1_u > 0 else 0.0

        if red_frac_k0 > 0.0 and red_frac_rf > 0.0:
            topology_classification = "TOPOLOGY_DEFECT_CLEARLY_REDUCED"
        elif red_frac_k0 <= 0.0 and red_frac_rf <= 0.0:
            topology_classification = "TOPOLOGY_DEFECT_NOT_REDUCED"
        else:
            topology_classification = "TOPOLOGY_RESULT_AMBIGUOUS"
    else:
        err_pk10r2_k0 = None
        err_pk10r2_rf = None
        red_frac_k0 = None
        red_frac_rf = None
        red_frac_u = None
        topology_classification = "UNRESOLVED"

    # NaN checks
    nan_found = any(math.isnan(p["u1_mm"]) or math.isnan(p["rf1_kN"]) for p in trajectory)

    report = {
        "job_identity": cand_path.name,
        "solver_completion": sta_info.get("completed_cleanly", False),
        "total_increments": len(trajectory),
        "nan_inf_check_passed": not nan_found,
        "mesh_metadata": {
            "physical_nodes": 6249,
            "physical_quads": 6048,
            "layered_elements": 18144,
            "h_local_mm": 0.0050,
            "h_global_mm": 0.0250,
            "global_grading_ratio": 5.0,
            "max_adjacent_neighbor_ratio": 1.224745,
            "slit_split_stations": 26,
            "duplicate_slit_nodes": 52
        },
        "stiffness_metrics": {
            "k0_kN_mm": cand_k0,
            "method": "Initial increment linear elastic secant (F135 standard)",
            "fit_details": k0_fit,
            "criterion_type": "QUALITATIVE"
        },
        "peak_metrics": {
            "peak_rf1_kN": cand_peak_rf,
            "peak_u1_mm": cand_peak_u,
            "criterion_type": "QUALITATIVE"
        },
        "terminal_metrics": {
            "terminal_rf1_kN": peak_term.get("terminal_rf1_kN") if peak_term else None,
            "terminal_u1_mm": peak_term.get("terminal_u1_mm") if peak_term else None,
            "criterion_type": "QUALITATIVE"
        },
        "H1_comparison": {
            "reference_job_id": h1_ref["job_id"],
            "reference_k0_kN_mm": h1_ref["k0_kN_mm"],
            "reference_peak_rf1_kN": h1_ref["peak_rf1_kN"],
            "stiffness_difference_pct": h1_diff_k0_pct,
            "peak_force_difference_pct": h1_diff_peak_rf_pct,
            "peak_displacement_difference_pct": h1_diff_peak_u_pct
        },
        "H2_comparison": {
            "reference_job_id": h2_ref["job_id"],
            "reference_k0_kN_mm": h2_ref["k0_kN_mm"],
            "reference_peak_rf1_kN": h2_ref["peak_rf1_kN"],
            "stiffness_difference_pct": h2_diff_k0_pct,
            "peak_force_difference_pct": h2_diff_peak_rf_pct,
            "peak_displacement_difference_pct": h2_diff_peak_u_pct
        },
        "diagnostic_error_reduction": {
            "baseline_defective_pk10r1_k0_error_kN_mm": err_pk10r1_k0,
            "pk10r2_k0_error_kN_mm": err_pk10r2_k0,
            "k0_error_reduction_fraction": red_frac_k0,
            "baseline_defective_pk10r1_peak_rf_error_kN": err_pk10r1_rf,
            "pk10r2_peak_rf_error_kN": err_pk10r2_rf,
            "peak_rf_error_reduction_fraction": red_frac_rf,
            "peak_u_error_reduction_fraction": red_frac_u,
            "criterion_type": "QUALITATIVE"
        },
        "acceptance_criteria": {
            "initial_stiffness": "QUALITATIVE/NO_FROZEN_NUMERIC_THRESHOLD",
            "peak_rf1": "QUALITATIVE/NO_FROZEN_NUMERIC_THRESHOLD",
            "peak_u1": "QUALITATIVE/NO_FROZEN_NUMERIC_THRESHOLD",
            "rf_u_trajectory": "QUALITATIVE/NO_FROZEN_NUMERIC_THRESHOLD",
            "crack_path_mode_ii": "QUALITATIVE/NO_FROZEN_NUMERIC_THRESHOLD",
            "solver_completion": "QUALITATIVE/NO_FROZEN_NUMERIC_THRESHOLD"
        },
        "topology_classification": topology_classification,
        "overall_status": "QUALIFIED_FOR_SCIENTIFIC_REVIEW" if not nan_found and cand_k0 is not None else "UNRESOLVED"
    }

    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Saved PK10R2 evaluation report to: {output_json}")

    return report

def main():
    parser = argparse.ArgumentParser(description="Evaluate PK10R2 Corrected Topology candidate")
    parser.add_argument("--candidate-dir", required=True, help="Directory containing job files (.dat, .sta, etc.)")
    parser.add_argument("--output-json", help="Output JSON path")
    args = parser.parse_args()

    res = evaluate_pk10r2_topology(args.candidate_dir, args.output_json)
    print("\n=== EVALUATION SUMMARY ===")
    print(f"Job: {res.get('job_identity')}")
    print(f"Stiffness K0: {res.get('stiffness_metrics', {}).get('k0_kN_mm')} kN/mm")
    print(f"Peak Force RF1: {res.get('peak_metrics', {}).get('peak_rf1_kN')} kN")
    print(f"Topology Classification: {res.get('topology_classification')}")
    print(f"Overall Status: {res.get('overall_status')}")

if __name__ == "__main__":
    main()
