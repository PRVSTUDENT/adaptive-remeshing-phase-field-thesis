"""Comparison & Verification Framework: Corrected Method B vs Reference Baselines.

Task: F1434-MODE1-LICENSE-CLEARANCE-AND-EXECUTION
Compares:
1. Canonical Fixed-Mesh 15k Reference (Job 1398090, 15,192 FE):
   - F_max = 0.7578 kN, u_peak = 0.005857 mm, K_0 = 137.95 kN/mm
   - W_ext = 2.3593 mJ (canonical reference work across u in [0.0, 0.0100] mm)
2. Original Method B Native (Job 1411934, 14,677 FE, PRE_PEAK_SOURCE_VARIANT):
   - F_max = 0.7430 kN, u_peak = 0.005727 mm, K_0 = 137.89 kN/mm
   - Stalled crack at x = 0.6123 mm, elevated plateau (0.50-0.60 kN)
   - W_ext = 3.3319 mJ (+41.2% vs canonical 15k, +17.8% vs ET2 across u in [0.0, 0.0100] mm)
3. Historical Stage-14 ET2 (Job 1411895, 6,112 FE):
   - F_max = 0.7564 kN, u_peak = 0.005857 mm, K_0 = 137.98 kN/mm
   - W_ext = 2.8281 mJ (+19.9% vs canonical 15k across u in [0.0, 0.0100] mm)
4. Corrected Method B Native (M1_MB_CORRECTED_PROPAGATION_14K, 14,483 FE, PROPAGATION_RESOLVED_VARIANT):
   - Sizing: h <= 3.75 um (l0/2) across 100% of longitudinal slices, 96.76% of corridor FEs
   - Governing Hypothesis: Full propagation ligament refinement eliminates artificial crack-pinning
     and elevated force plateau, restoring softening toward the canonical 2.359 mJ reference.
"""

import os
import json
import numpy as np
import pandas as pd

# Canonical Baseline Constants
CANONICAL_15K_REF = {
    "model": "Fixed-Mesh Reference (Job 1398090, 15,192 FE)",
    "F_max_kN": 0.757778,
    "u_peak_mm": 0.005857,
    "K_0_kN_per_mm": 137.945520,
    "W_ext_mJ": 2.3593,
    "source_status": "CANONICAL_REFERENCE_ANCHOR",
    "displacement_horizon_mm": 0.0100
}

ORIGINAL_METHOD_B = {
    "model": "Original Method B Native (Job 1411934, 14,677 FE)",
    "variant": "PRE_PEAK_SOURCE_VARIANT",
    "F_max_kN": 0.743021,
    "u_peak_mm": 0.005727,
    "K_0_kN_per_mm": 137.891881,
    "W_ext_mJ": 3.331934,
    "excess_work_vs_canonical_pct": 41.225,
    "excess_work_vs_et2_pct": 17.815,
    "corridor_h_min_um": 1.98,
    "corridor_h_max_um": 14.83,
    "under_resolved_ligament_pct": 70.0,
    "displacement_horizon_mm": 0.0100
}

HISTORICAL_ET2 = {
    "model": "Historical Stage-14 ET2 (Job 1411895, 6,112 FE)",
    "variant": "HISTORICAL_ET2_VARIANT",
    "F_max_kN": 0.756367,
    "u_peak_mm": 0.005841,
    "K_0_kN_per_mm": 137.977065,
    "W_ext_mJ": 2.828116,
    "excess_work_vs_canonical_pct": 19.871,
    "displacement_horizon_mm": 0.0100
}

CORRECTED_METHOD_B_SPEC = {
    "model": "Corrected Method B Native (M1_MB_CORRECTED_PROPAGATION_14K, 14,483 FE)",
    "variant": "PROPAGATION_RESOLVED_VARIANT",
    "deck_file": "M1_MB_CORRECTED_PROPAGATION_14K.inp",
    "deck_sha256": "1209F716971719B1A740FF92C8B5503BA9784F10D5EEDD3C5035C81D40A066E9",
    "fortran_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "pbs_script_sha256": "06DE87F62676D9CA35B8B69106881004D2F6B48459966405779EC04E2FC66172",
    "base_elements": 14483,
    "layered_elements": 43449,
    "mesh_nodes": 14456,
    "corridor_elements": 5126,
    "corridor_h_median_um": 1.977,
    "corridor_h_min_um": 1.017,
    "corridor_h_max_um": 8.528,
    "pct_corridor_h_le_3p75um": 96.76,
    "pct_corridor_h_le_7p50um": 99.84,
    "longitudinal_coverage_pct": 100.0,
    "execution_mode": "1-CPU serial shared memory on /scratch9/ (queue entry_imfdfkmq)",
    "displacement_horizon_mm": 0.0100,
    "governing_hypothesis": (
        "Refining the complete propagation ligament with h <= l0/2 eliminates the artificial crack-pinning "
        "and elevated force plateau (0.50-0.60 kN) observed in original Method B, reducing total external work "
        "from 3.332 mJ toward the canonical fixed reference 2.359 mJ."
    )
}


def load_harvested_historical_evidence(harvest_dir=None):
    """Load and verify authenticated lightweight CSV/JSON files from Job 1411934 and Job 1411895."""
    if harvest_dir is None:
        harvest_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "runs", "mode1", "harvest_results_f1416"
        )

    native_fu = os.path.join(harvest_dir, "m1_mb_native_14k_1s_load_displacement.csv")
    et2_fu = os.path.join(harvest_dir, "m1_mb_et2_6k_1s_load_displacement.csv")

    results = {}
    if os.path.isfile(native_fu):
        df_nat = pd.read_csv(native_fu)
        trapz_fn = getattr(np, 'trapezoid', getattr(np, 'trapz', None))
        w_ext_nat = trapz_fn(df_nat['f_kN'], df_nat['u_mm']) * 1000.0  # kN*mm -> mJ
        results["native_14k"] = {
            "rows": len(df_nat),
            "u_final_mm": float(df_nat['u_mm'].iloc[-1]),
            "f_max_kN": float(df_nat['f_kN'].max()),
            "u_at_f_max_mm": float(df_nat.loc[df_nat['f_kN'].idxmax(), 'u_mm']),
            "f_final_kN": float(df_nat['f_kN'].iloc[-1]),
            "w_ext_mJ": float(w_ext_nat)
        }

    if os.path.isfile(et2_fu):
        df_et2 = pd.read_csv(et2_fu)
        trapz_fn = getattr(np, 'trapezoid', getattr(np, 'trapz', None))
        w_ext_et2 = trapz_fn(df_et2['f_kN'], df_et2['u_mm']) * 1000.0  # kN*mm -> mJ
        results["et2_6k"] = {
            "rows": len(df_et2),
            "u_final_mm": float(df_et2['u_mm'].iloc[-1]),
            "f_max_kN": float(df_et2['f_kN'].max()),
            "u_at_f_max_mm": float(df_et2.loc[df_et2['f_kN'].idxmax(), 'u_mm']),
            "f_final_kN": float(df_et2['f_kN'].iloc[-1]),
            "w_ext_mJ": float(w_ext_et2)
        }

    return results


def evaluate_corrected_evidence(fu_df):
    """Compute standard metrics on a newly extracted load-displacement dataframe."""
    u_col = 'u_mm' if 'u_mm' in fu_df.columns else fu_df.columns[0]
    f_col = 'f_kN' if 'f_kN' in fu_df.columns else fu_df.columns[1]

    u = fu_df[u_col].values
    f = fu_df[f_col].values

    # Initial stiffness K0 (linear fit for u <= 0.001 mm)
    mask_elastic = u <= 0.0010
    if np.sum(mask_elastic) >= 10:
        poly = np.polyfit(u[mask_elastic], f[mask_elastic], 1)
        k0 = poly[0]
    else:
        k0 = float('nan')

    idx_peak = np.argmax(f)
    f_max = f[idx_peak]
    u_peak = u[idx_peak]

    trapz_fn = getattr(np, 'trapezoid', getattr(np, 'trapz', None))
    w_ext = trapz_fn(f, u) * 1000.0  # mJ

    # Post-peak plateau metrics (u = 0.0070 mm and u = 0.0080 mm)
    idx_0070 = np.argmin(np.abs(u - 0.0070))
    idx_0080 = np.argmin(np.abs(u - 0.0080))
    f_0070 = f[idx_0070]
    f_0080 = f[idx_0080]

    return {
        "K0_kN_per_mm": float(k0),
        "F_max_kN": float(f_max),
        "u_peak_mm": float(u_peak),
        "W_ext_mJ": float(w_ext),
        "F_at_0p0070_kN": float(f_0070),
        "F_at_0p0080_kN": float(f_0080),
        "F_final_kN": float(f[-1]),
        "u_final_mm": float(u[-1]),
        "total_increments": len(u)
    }


def print_comparison_specification():
    print("================================================================================")
    print("MODE-I METHOD B COMPARISON FRAMEWORK SPECIFICATION")
    print("================================================================================")
    print("\n1. Canonical Reference Anchor:")
    for k, v in CANONICAL_15K_REF.items():
        print(f"   {k}: {v}")

    print("\n2. Original Method B (PRE_PEAK_SOURCE_VARIANT):")
    for k, v in ORIGINAL_METHOD_B.items():
        print(f"   {k}: {v}")

    print("\n3. Historical Stage-14 ET2 Reference:")
    for k, v in HISTORICAL_ET2.items():
        print(f"   {k}: {v}")

    print("\n4. Corrected Method B Candidate (PROPAGATION_RESOLVED_VARIANT):")
    for k, v in CORRECTED_METHOD_B_SPEC.items():
        print(f"   {k}: {v}")

    hist_ev = load_harvested_historical_evidence()
    if hist_ev:
        print("\n5. Authenticated Historical Evidence Loaded:")
        for mod, d in hist_ev.items():
            print(f"   [{mod}]: F_max = {d['f_max_kN']:.6f} kN, W_ext = {d['w_ext_mJ']:.4f} mJ, u_final = {d['u_final_mm']:.6f} mm")


if __name__ == "__main__":
    print_comparison_specification()
