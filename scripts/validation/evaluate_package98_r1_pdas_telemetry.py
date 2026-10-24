#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evaluate_package98_r1_pdas_telemetry.py
Evaluates Package 98 Revision 1 iteration telemetry, physical metrics, and chatter diagnostics.
"""
import json
import csv
import numpy as np
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
ledger_path = REPO_ROOT / "results/validation/mode1_f1597/pkg98_r1_pdas_subproblem_ledger.json"
energy_path = REPO_ROOT / "results/validation/mode1_f1597/pkg98_r1_uel_energy_balance.csv"

with open(ledger_path, "r", encoding="utf-8") as f:
    data = json.load(f)

records = data["records"]
print(f"Total Iterations Executed: {len(records)}")
print(f"{'Iter':4s} | {'|U|':3s} | {'|L|':4s} | {'|A|':4s} | {'Changes':7s} | {'||R_d||_A':9s} | {'Strict Heal':11s} | {'Tol Heal':8s} | {'RF2 (N)':9s}")
print("-" * 80)

for r in records:
    it = r["iteration"]
    u = r["set_sizes"]["U"]
    l = r["set_sizes"]["L"]
    a = r["set_sizes"]["A"]
    ch = r["set_changes"]
    res = r["residual_inf_norm_A_kNmm"]
    sh = r["strict_healing_count"]
    th = r["tolerance_healing_count"]
    rf2_N = r.get("rf2_kN", 0.0) * 1000.0
    print(f"{it:4d} | {u:3d} | {l:4d} | {a:4d} | {ch:7d} | {res:9.2e} | {sh:11d} | {th:8d} | {rf2_N:9.3f}")

# Force continuity comparison against donor RF2 = 112.97 N
donor_rf2_N = 112.97
last_rf2_N = records[-1]["rf2_kN"] * 1000.0
force_jump_pct = abs(last_rf2_N - donor_rf2_N) / donor_rf2_N * 100.0
print("\n" + "="*80)
print(f"Reaction Force Continuity:")
print(f"Donor RF2: {donor_rf2_N:.3f} N | Receiver RF2: {last_rf2_N:.3f} N | Jump: {force_jump_pct:.2f}% (Tolerance: <= 5.0%)")
print(f"Force Continuity Gate: {'PASS' if force_jump_pct <= 5.0 else 'FAIL'}")

# Non-overshoot
total_strict_overshoot = max(r["strict_overshoot_count"] for r in records)
print(f"Phase Bound Overshoot Count: {total_strict_overshoot} (Tolerance: 0)")
print(f"Non-Overshoot Gate: {'PASS' if total_strict_overshoot == 0 else 'FAIL'}")

# Energy continuity
if energy_path.exists():
    with open(energy_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        rows = list(reader)
        if rows:
            last_row = rows[-1]
            e_frac_kNmm = float(last_row[1]) if len(last_row) > 1 else 0.0
            donor_e_frac_kNmm = 0.00013774
            energy_jump_pct = abs(e_frac_kNmm - donor_e_frac_kNmm) / donor_e_frac_kNmm * 100.0
            print(f"Fracture Energy: {e_frac_kNmm*1e6:.3f} mJ | Donor: {donor_e_frac_kNmm*1e6:.3f} mJ | Jump: {energy_jump_pct:.2f}% (Tolerance: <= 2.0%)")
