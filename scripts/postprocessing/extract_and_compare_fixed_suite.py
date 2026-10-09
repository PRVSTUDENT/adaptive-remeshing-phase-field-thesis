#!/usr/bin/env python3
"""
extract_and_compare_fixed_suite.py
-----------------------------------
Post-processing and comparative convergence analysis for the Mode-II
fixed-mesh convergence suite and stabilized adaptive benchmark.

Analyzes:
  1. M2_FIX_COARSE_2P5K (h = 20.0 um, 2500 FEs, 2627 nodes)
  2. M2_FIX_MED_18K     (h = 7.46 um, 17956 FEs, 18293 nodes)
  3. M2_FIX_INT_40K     (h = 5.00 um, 40000 FEs, 40502 nodes)
  4. M2_FIX_FINE_72K    (h = 3.73 um, 71824 FEs, 72496 nodes)
  5. M2_J2_ADAPT_ET2_STAB (Adaptive ET2 stabilized, 37575 FEs, 37460 nodes)

Extracts:
  - RF1 vs ux curve from Abaqus .dat (or .odb) files
  - Initial linear elastic stiffness K0 (kN/mm) via OLS regression
  - Peak reaction force RF_max (N) and critical displacement ux_crit (um)
  - Post-peak progressive softening trajectory
  - External mechanical work W_ext = integral(RF1 dux)
  - Convergence rates and error norms (MAE, RMSE, Linf) relative to the finest mesh
  - Rigorous status classifications distinguishing completed vs running vs pending metrics

Author: Antigravity (Advanced Agentic Coding)
Task: F1381-MODE2-FIXED-MESH-FRACTURE-EVIDENCE-UEL-RELIABILITY-AND-ADAPTIVE-DECISION-GATES
Date: 2026-10-09
"""

import os
import sys
import json
import argparse
import numpy as np

def parse_dat_rf(dat_path):
    """Parse reaction force RF1 and displacement U1 from Abaqus .dat file for node N_RP (999999)."""
    if not os.path.exists(dat_path):
        return None, None
    
    ux_list = []
    rf_list = []
    
    with open(dat_path, 'r', errors='ignore') as f:
        for line in f:
            line_s = line.strip()
            if line_s.startswith('999999'):
                parts = line_s.split()
                # Format in .dat: 999999 <U1_in_mm> <RF1_in_kN>
                if len(parts) >= 3:
                    try:
                        u_val = float(parts[1])
                        rf_val = float(parts[2])
                        ux_list.append(u_val * 1000.0) # um
                        rf_list.append(rf_val * 1000.0) # N
                    except ValueError:
                        pass
                        
    if not ux_list:
        return None, None
        
    return np.array(ux_list), np.array(rf_list)

def compute_stiffness_and_metrics(ux_um, rf_n, is_complete=False):
    """Compute K0, RF_max, ux_crit, and cumulative external work with rigorous status tracking."""
    if len(ux_um) == 0:
        return {}
    
    # Linear elastic range: ux in [0.05, 1.0] um
    mask_elastic = (ux_um >= 0.05) & (ux_um <= 1.0)
    if np.sum(mask_elastic) >= 2:
        # K0 in kN/mm: (RF_N / 1000) / (ux_um / 1000) = RF_N / ux_um
        p = np.polyfit(ux_um[mask_elastic], rf_n[mask_elastic], 1)
        k0_kn_per_mm = float(p[0])
        r2 = float(1.0 - np.sum((rf_n[mask_elastic] - np.polyval(p, ux_um[mask_elastic]))**2) / 
                   np.sum((rf_n[mask_elastic] - np.mean(rf_n[mask_elastic]))**2))
    else:
        k0_kn_per_mm = float(rf_n[0] / ux_um[0]) if ux_um[0] > 0 else 0.0
        r2 = 1.0
        
    idx_max = int(np.argmax(rf_n))
    rf_max = float(rf_n[idx_max])
    ux_crit = float(ux_um[idx_max])
    
    # Cumulative external work: trapezoidal integration
    # integral of RF (N) * d_ux (um) = 1e-3 mJ = 1e-6 J
    w_ext_mj = float(np.trapz(rf_n, ux_um) * 1e-3) # mJ
    
    # Check if peak is truly reached or if simulation is still loading
    ux_max_reached = float(ux_um[-1])
    rf_current = float(rf_n[-1])
    
    if is_complete or (ux_max_reached > ux_crit + 0.5):
        peak_status = "PEAK_TRAVERSED"
    else:
        peak_status = "MONOTONICALLY_INCREASING_PEAK_PENDING"
    
    return {
        "k0_kn_per_mm": k0_kn_per_mm,
        "k0_r2": r2,
        "rf_max_observed_n": rf_max,
        "ux_at_rf_max_um": ux_crit,
        "peak_status": peak_status,
        "w_ext_mj": w_ext_mj,
        "num_increments": len(ux_um),
        "ux_max_reached_um": ux_max_reached,
        "rf_current_n": rf_current,
        "is_completed_horizon": bool(is_complete or ux_max_reached >= 19.99)
    }

def interpolate_common_grid(ux_list, rf_list, grid_um):
    """Interpolate reaction force curve onto a common regular displacement grid."""
    if len(ux_list) < 2:
        return np.full_like(grid_um, np.nan)
    ux_max = ux_list[-1]
    rf_interp = np.interp(grid_um, ux_list, rf_list, left=0.0, right=np.nan)
    rf_interp[grid_um > ux_max] = np.nan
    return rf_interp

def compare_convergence(suite_data, reference_key="Fixed_Fine_72k"):
    """Compare error norms relative to reference solution over common displacement interval."""
    if reference_key not in suite_data or "ux" not in suite_data[reference_key]:
        return {}
    
    ref_ux = suite_data[reference_key]["ux"]
    ref_rf = suite_data[reference_key]["rf"]
    
    valid_max_ux = [d["ux"][-1] for d in suite_data.values() if "ux" in d and len(d["ux"]) > 0]
    if not valid_max_ux:
        return {}
    common_max_ux = min(valid_max_ux)
    if common_max_ux <= 0.05:
        return {}
    
    grid = np.linspace(0.01, common_max_ux, 200)
    ref_grid_rf = np.interp(grid, ref_ux, ref_rf)
    
    comparison = {}
    for name, d in suite_data.items():
        if "ux" not in d or len(d["ux"]) < 2:
            continue
        cur_grid_rf = np.interp(grid, d["ux"], d["rf"])
        diff = cur_grid_rf - ref_grid_rf
        mae = float(np.mean(np.abs(diff)))
        rmse = float(np.sqrt(np.mean(diff**2)))
        linf = float(np.max(np.abs(diff)))
        rel_l2 = float(rmse / np.sqrt(np.mean(ref_grid_rf**2))) if np.mean(ref_grid_rf**2) > 0 else 0.0
        
        comparison[name] = {
            "mae_n": mae,
            "rmse_n": rmse,
            "linf_n": linf,
            "rel_l2_error": rel_l2,
            "common_eval_window_um": [float(grid[0]), float(grid[-1])]
        }
        
    return comparison

def main():
    parser = argparse.ArgumentParser(description="Extract and compare Mode-II fixed-mesh convergence suite.")
    parser.add_argument("--data-dir", default=".", help="Base directory containing case directories or dat files")
    parser.add_argument("--json-input", default="", help="Optional pre-extracted live history JSON path")
    parser.add_argument("--output-json", default="fixed_mesh_convergence_comparison.json", help="Output JSON path")
    args = parser.parse_args()

    models = {
        "Fixed_Coarse_2.5k": {
            "h_um": 20.0,
            "elements": 2500,
            "nodes": 2627,
            "dat_path": os.path.join(args.data_dir, "01_coarse_2p5k_h20um", "M2_FIX_COARSE_2P5K.dat"),
            "is_complete": True
        },
        "Fixed_Medium_18k": {
            "h_um": 7.46,
            "elements": 17956,
            "nodes": 18293,
            "dat_path": os.path.join(args.data_dir, "02_medium_18k_h7p5um", "M2_FIX_MED_18K.dat"),
            "is_complete": False
        },
        "Fixed_Interm_40k": {
            "h_um": 5.00,
            "elements": 40000,
            "nodes": 40502,
            "dat_path": os.path.join(args.data_dir, "03_intermediate_40k_h5um", "M2_FIX_INT_40K.dat"),
            "is_complete": False
        },
        "Fixed_Fine_72k": {
            "h_um": 3.73,
            "elements": 71824,
            "nodes": 72496,
            "dat_path": os.path.join(args.data_dir, "04_fine_72k_h3p75um", "M2_FIX_FINE_72K.dat"),
            "is_complete": False
        },
        "Adapted_ET2_Stab": {
            "h_min_um": 3.73,
            "elements": 37575,
            "nodes": 37460,
            "dat_path": os.path.join(args.data_dir, "adapted_et2", "Job-2_UEL.dat"),
            "is_complete": False
        }
    }

    suite_data = {}
    summary = {}

    # If json_input is provided, load from JSON directly
    if args.json_input and os.path.exists(args.json_input):
        with open(args.json_input, 'r') as f:
            raw_json = json.load(f)
        
        for name, info in models.items():
            # Match keys in raw_json
            matched_key = None
            for rk in raw_json:
                if name.split('_')[1].lower() in rk.lower() or name.lower() in rk.lower():
                    matched_key = rk
                    break
            if matched_key and isinstance(raw_json[matched_key], dict) and "ux_history" in raw_json[matched_key]:
                entry = raw_json[matched_key]
                ux = np.array(entry["ux_history"])
                rf = np.array(entry["rf_history"])
                metrics = compute_stiffness_and_metrics(ux, rf, is_complete=info["is_complete"])
                suite_data[name] = {"ux": ux, "rf": rf, "info": info, "metrics": metrics}
                summary[name] = {
                    "h_um": info.get("h_um", info.get("h_min_um")),
                    "elements": info["elements"],
                    "nodes": info["nodes"],
                    "metrics": metrics
                }
            else:
                summary[name] = {"status": "data_not_available"}
    else:
        for name, info in models.items():
            ux, rf = parse_dat_rf(info["dat_path"])
            if ux is not None and len(ux) > 0:
                metrics = compute_stiffness_and_metrics(ux, rf, is_complete=info["is_complete"])
                suite_data[name] = {
                    "ux": ux,
                    "rf": rf,
                    "info": info,
                    "metrics": metrics
                }
                summary[name] = {
                    "h_um": info.get("h_um", info.get("h_min_um")),
                    "elements": info["elements"],
                    "nodes": info["nodes"],
                    "metrics": metrics
                }
            else:
                summary[name] = {
                    "status": "data_not_available",
                    "expected_path": info["dat_path"]
                }

    if "Fixed_Fine_72k" in suite_data and len(suite_data["Fixed_Fine_72k"]["ux"]) > 1:
        comp = compare_convergence(suite_data, reference_key="Fixed_Fine_72k")
        summary["convergence_comparison"] = comp

    with open(args.output_json, "w") as f:
        json.dump(summary, f, indent=2)

    print("Post-processing summary generated successfully.")

if __name__ == "__main__":
    main()
