#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_energy_consistent_transfer.py
Tests gradient-preserving energy-consistent correction for C4 -> C5 state transfer.
"""

import sys
import math
from pathlib import Path
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.diagnose_c4_c5_energy_transfer import load_mesh_and_damage, compute_fracture_energy

TARGET_E_FRAC = 0.00013773671 # Package 94 Step 4 Frame 7 target

def main():
    c5_mesh_inp = REPO_ROOT / "models/pandey_kumar_mode1/96_c5_package96_authentic_transfer/candidate_crack_band_mesh_c5.inp"
    c5_mapped_csv = REPO_ROOT / "models/pandey_kumar_mode1/96_c5_package96_authentic_transfer/candidate_c5_frame7_mapped_state_table.csv"

    nodes, elems, raw_damage = load_mesh_and_damage(c5_mesh_inp, c5_mapped_csv, is_mapped_csv=True)

    # Baseline
    res0 = compute_fracture_energy(nodes, elems, raw_damage)
    diff0 = (res0['e_total'] - TARGET_E_FRAC) / TARGET_E_FRAC * 100.0
    print(f"Raw Mapped C5 E_frac: {res0['e_total']:.10e} kN*mm (mismatch: {diff0:+.4f}%)")

    # Test Method 2: d_corr = d + c * d * (1 - d)
    # We want to find c such that compute_fracture_energy matches TARGET_E_FRAC
    # Let's test a range of c values:
    print("\nScanning correction parameter c:")
    best_c = 0.0
    best_diff = 100.0

    for c in np.linspace(0.0, 0.05, 21):
        corr_damage = {}
        overshoots = 0
        for nid, d in raw_damage.items():
            if d >= 0.9990:
                corr_d = d # lock wake
            else:
                corr_d = d + c * d * (1.0 - d)
            corr_d = max(0.0, min(1.0, corr_d))
            if corr_d > 1.00000:
                overshoots += 1
            corr_damage[nid] = corr_d

        res = compute_fracture_energy(nodes, elems, corr_damage)
        diff = (res['e_total'] - TARGET_E_FRAC) / TARGET_E_FRAC * 100.0
        print(f"  c = {c:.4f}: E_frac = {res['e_total']:.10e} kN*mm (diff: {diff:+.4f}%, overshoots: {overshoots})")
        if abs(diff) < abs(best_diff):
            best_diff = diff
            best_c = c

    print(f"\nOptimal c = {best_c:.4f} with mismatch {best_diff:+.4f}%")

    # Fine-tune c with Brent's method / secant
    def objective(c_val):
        corr_damage = {}
        for nid, d in raw_damage.items():
            if d >= 0.9990:
                corr_d = d
            else:
                corr_d = d + c_val * d * (1.0 - d)
            corr_d = max(0.0, min(1.0, corr_d))
            corr_damage[nid] = corr_d
        res = compute_fracture_energy(nodes, elems, corr_damage)
        return res['e_total'] - TARGET_E_FRAC

    c_low = 0.0
    c_high = 0.03
    f_low = objective(c_low)
    f_high = objective(c_high)

    for _ in range(10):
        c_mid = c_low - f_low * (c_high - c_low) / (f_high - f_low)
        f_mid = objective(c_mid)
        if abs(f_mid) < 1e-12:
            break
        if f_mid * f_low < 0:
            c_high = c_mid
            f_high = f_mid
        else:
            c_low = c_mid
            f_low = f_mid

    c_exact = c_mid
    corr_damage = {}
    overshoots = 0
    for nid, d in raw_damage.items():
        if d >= 0.9990:
            corr_d = d
        else:
            corr_d = d + c_exact * d * (1.0 - d)
        corr_d = max(0.0, min(1.0, corr_d))
        if corr_d > 1.00000:
            overshoots += 1
        corr_damage[nid] = corr_d
    res_exact = compute_fracture_energy(nodes, elems, corr_damage)
    final_diff = (res_exact['e_total'] - TARGET_E_FRAC) / TARGET_E_FRAC * 100.0

    print(f"\nExact fine-tuned c = {c_exact:.8f}:")
    print(f"  Target E_frac:  {TARGET_E_FRAC:.10e} kN*mm")
    print(f"  Corrected C5:   {res_exact['e_total']:.10e} kN*mm")
    print(f"  Potential:      {res_exact['e_pot']:.10e} kN*mm")
    print(f"  Gradient:       {res_exact['e_grad']:.10e} kN*mm")
    print(f"  Mismatch:       {final_diff:+.6f}%")
    print(f"  Max damage:     {max(corr_damage.values()):.8f}")
    print(f"  Overshoots:     {overshoots}")

if __name__ == "__main__":
    main()
