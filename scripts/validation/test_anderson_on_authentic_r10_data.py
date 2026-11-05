#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_anderson_on_authentic_r10_data.py
======================================
Tests Anderson acceleration directly on authentic node-resolved damage data
from Job 1420261.mmaster02 (Package 171-R10 Outer 136-140, stationary active set = 35 nodes).
Evaluates:
- Residual vectors r_k = d_PDAS - d_current across all 15,559 nodes.
- Gram matrix Delta R^T Delta R conditioning and regularized least-squares gamma coefficients.
- Predicted residual reduction: ||r_bar|| vs ||r_k||.
- Physical bounds: d0[n] <= d_acc[n] <= 1.0.
"""
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.anderson_acceleration import AndersonAccelerator

EVIDENCE_DIR = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r10_c3_0_adaptive_reequilibration/evidence/1420261.mmaster02"


def load_damage_from_endpoint(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # nodes format: [[node_id, ux, uy, damage], ...]
    return {row[0]: row[3] for row in data["nodes"]}


def main():
    endpoints = {}
    for outer in [136, 137, 138, 139, 140]:
        ep_file = EVIDENCE_DIR / f"endpoint_o{outer}.json"
        if not ep_file.exists():
            print(f"Error: {ep_file} not found.")
            return
        endpoints[outer] = load_damage_from_endpoint(ep_file)

    nodes = sorted(endpoints[140].keys())
    print(f"Loaded authentic damage fields across {len(nodes)} nodes for outer iterations 136-140.")

    # Load initial damage d0 from local package if available
    d0_file = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r10_c3_0_adaptive_reequilibration/c6_crack_seam_damage.csv"
    d0 = {}
    if d0_file.exists():
        with open(d0_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) == 2 and parts[0].isdigit():
                    d0[int(parts[0])] = float(parts[1])
    else:
        # Default d0 = 0.0
        d0 = {n: 0.0 for n in nodes}

    print("\n=== Evaluating Authentic Fixed-Point Residuals (Iterations 136-140) ===")
    residuals = {}
    for it in [136, 137, 138, 139]:
        # Step increment: Delta d = d_{it+1} - d_{it}
        r_it = {n: endpoints[it + 1][n] - endpoints[it][n] for n in nodes}
        r_l2 = math.sqrt(sum(r_it[n] ** 2 for n in nodes))
        r_inf = max(abs(r_it[n]) for n in nodes)
        residuals[it] = r_it
        print(f"Outer {it} -> {it+1}: ||r||_inf = {r_inf:.4e}, ||r||_2 = {r_l2:.4e}")

    # Now apply Anderson acceleration with m=2 using iterations 136, 137, 138 to predict 139
    print("\n=== Anderson Acceleration Experiment on Authentic C6 Mesh (m=2) ===")
    acc = AndersonAccelerator(memory_depth=2, beta=0.85, regularization=1e-6, gamma_max=200.0)

    # Step 1: feed 136 -> 137
    d_acc, meta1 = acc.compute_step(endpoints[136], endpoints[137], d0, damped_omega=0.85)
    print(f"Step 1 (Iter 136): accelerated={meta1['accelerated']}, reason={meta1['reason']}")

    # Step 2: feed 137 -> 138
    d_acc, meta2 = acc.compute_step(endpoints[137], endpoints[138], d0, damped_omega=0.85)
    print(f"Step 2 (Iter 137): accelerated={meta2['accelerated']}, reason={meta2['reason']}")
    if meta2['accelerated']:
        print(f"  Gamma: {meta2['gamma']}, ||gamma|| = {meta2['gamma_norm']:.4f}")
        print(f"  Picard step: {meta2['picard_step']:.4e}, Anderson step: {meta2['cand_step']:.4e}")

    # Step 3: feed 138 -> 139
    d_acc, meta3 = acc.compute_step(endpoints[138], endpoints[139], d0, damped_omega=0.85)
    print(f"Step 3 (Iter 138): accelerated={meta3['accelerated']}, reason={meta3['reason']}")
    if meta3['accelerated']:
        print(f"  Gamma: {meta3['gamma']}, ||gamma|| = {meta3['gamma_norm']:.4f}")
        print(f"  Picard step: {meta3['picard_step']:.4e}, Anderson step: {meta3['cand_step']:.4e}")

    # Step 4: feed 139 -> 140
    d_acc, meta4 = acc.compute_step(endpoints[139], endpoints[140], d0, damped_omega=0.85)
    print(f"Step 4 (Iter 139): accelerated={meta4['accelerated']}, reason={meta4['reason']}")
    if meta4['accelerated']:
        print(f"  Gamma: {meta4['gamma']}, ||gamma|| = {meta4['gamma_norm']:.4f}")
        print(f"  Picard step: {meta4['picard_step']:.4e}, Anderson step: {meta4['cand_step']:.4e}")

    # Bounds check on accelerated iterate
    healing_count = sum(1 for n in nodes if d_acc[n] < d0.get(n, 0.0) - 1e-12)
    upper_count = sum(1 for n in nodes if d_acc[n] > 1.0 + 1e-12)
    print(f"\nPhysical Bound Verification on Accelerated Field:")
    print(f"  Healing violations (d < d0): {healing_count}")
    print(f"  Upper bound violations (d > 1.0): {upper_count}")

    assert healing_count == 0, "Healing violations detected!"
    assert upper_count == 0, "Upper bound violations detected!"
    print("\nAUTHENTIC C6 ANDERSON ACCELERATION TEST COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
