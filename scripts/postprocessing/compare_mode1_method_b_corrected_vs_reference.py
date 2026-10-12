"""Comparison & Verification Framework: Corrected Method B vs Reference Baselines.

Task: F1431-MODE1-METHOD-B-CORRECTED-PROPAGATION-VERIFICATION-AND-SUBMISSION
Compares:
1. Canonical Fixed-Mesh 15k Reference (Job 1398090, 15,192 FE):
   - F_max = 0.7578 kN, u_peak = 0.005857 mm, K_0 = 137.95 kN/mm
   - W_ext = 2.3593 mJ (canonical reference work)
2. Original Method B Native (Job 1411934, 14,677 FE, PRE_PEAK_SOURCE_VARIANT):
   - F_max = 0.7430 kN, u_peak = 0.005727 mm, K_0 = 138.15 kN/mm
   - Stalled crack at x = 0.6123 mm, elevated plateau (0.50-0.60 kN)
   - W_ext = 3.3319 mJ (+41.2% vs canonical 15k, +17.8% vs ET2)
3. Historical Stage-14 ET2 (Job 1411895, 6,112 FE):
   - F_max = 0.7564 kN, u_peak = 0.005857 mm
   - W_ext = 2.8281 mJ
4. Corrected Method B Native (M1_MB_CORRECTED_PROPAGATION_14K, 14,483 FE, PROPAGATION_RESOLVED_VARIANT):
   - Sizing: h <= 3.75 um (l0/2) across 100% of longitudinal slices, 96.76% of corridor FEs
   - Hypothesis: Full propagation refinement eliminates the artificial crack front pinning,
     accelerating post-peak softening toward the canonical 2.36 mJ reference.
"""

import os
import json
import numpy as np

# Canonical Baseline Constants
CANONICAL_15K_REF = {
    "model": "Fixed-Mesh Reference (Job 1398090, 15,192 FE)",
    "F_max_kN": 0.757778,
    "u_peak_mm": 0.005857,
    "K_0_kN_per_mm": 137.945520,
    "W_ext_mJ": 2.3593,
    "source_status": "CANONICAL_REFERENCE_ANCHOR"
}

ORIGINAL_METHOD_B = {
    "model": "Original Method B Native (Job 1411934, 14,677 FE)",
    "variant": "PRE_PEAK_SOURCE_VARIANT",
    "F_max_kN": 0.743021,
    "u_peak_mm": 0.005727,
    "K_0_kN_per_mm": 138.15,
    "W_ext_mJ": 3.3319,
    "excess_work_vs_canonical_pct": 41.22,
    "excess_work_vs_et2_pct": 17.81,
    "corridor_h_min_um": 1.98,
    "corridor_h_max_um": 14.83,
    "under_resolved_ligament_pct": 70.0
}

HISTORICAL_ET2 = {
    "model": "Historical Stage-14 ET2 (Job 1411895, 6,112 FE)",
    "variant": "HISTORICAL_ET2_VARIANT",
    "F_max_kN": 0.7564,
    "u_peak_mm": 0.005857,
    "W_ext_mJ": 2.8281
}

CORRECTED_METHOD_B_SPEC = {
    "model": "Corrected Method B Native (M1_MB_CORRECTED_PROPAGATION_14K, 14,483 FE)",
    "variant": "PROPAGATION_RESOLVED_VARIANT",
    "deck_file": "M1_MB_CORRECTED_PROPAGATION_14K.inp",
    "deck_sha256": "1209F716971719B1A740FF92C8B5503BA9784F10D5EEDD3C5035C81D40A066E9",
    "fortran_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
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
    "execution_mode": "1-CPU serial shared memory on /scratch9/",
    "governing_hypothesis": (
        "Refining the complete propagation ligament with h <= l0/2 eliminates the artificial crack-pinning "
        "and elevated force plateau (0.50-0.60 kN) observed in original Method B, reducing total external work "
        "from 3.332 mJ toward the canonical fixed reference 2.359 mJ."
    )
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


if __name__ == "__main__":
    print_comparison_specification()
