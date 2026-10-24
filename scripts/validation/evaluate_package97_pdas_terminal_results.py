#!/usr/bin/env python3
"""
Evaluate Package 97 PDAS Pilot Terminal Results.
Analyzes the 25 live Abaqus subproblem iterations, convergence history,
KKT active-set behavior, reaction force continuity, fracture energy,
and healing/overshoot diagnostics.
"""
import json
import csv
import sys
from pathlib import Path

def evaluate():
    val_dir = Path("results/validation/mode1_f1597")
    trial_path = val_dir / "pdas_trial_evaluation.json"
    ledger_path = val_dir / "pdas_subproblem_ledger.json"
    energy_path = val_dir / "uel_energy_balance.csv"

    with open(trial_path, "r", encoding="utf-8") as f:
        trial = json.load(f)

    with open(ledger_path, "r", encoding="utf-8") as f:
        ledger = json.load(f)

    records = ledger.get("records", [])
    print("=== PACKAGE 97 TERMINAL EVALUATION ===")
    print("Status: %s" % trial.get('status'))
    print("Converged: %s" % trial.get('converged'))
    print("Total Iterations: %d" % len(records))
    print("Final Set Sizes: %s" % str(trial.get('final_set_sizes')))
    print("Final Residual ||R_d||_inf,A: %.4e" % trial.get('final_residual_inf_A'))
    print("Strict Healing Nodes: %d" % trial.get('strict_healing_nodes'))
    print("Strict Overshoot Nodes: %d" % trial.get('strict_overshoot_nodes'))
    print("KKT Lower Valid: %s" % str(trial.get('kkt_lower_valid')))
    print("KKT Upper Valid: %s" % str(trial.get('kkt_upper_valid')))

    print("\n--- Iteration History Summary ---")
    print("%-5s | %-5s | %-5s | %-5s | %-8s | %-12s | %-6s | %-12s" % ("Iter", "|U|", "|L|", "|A|", "Changes", "||R_d||_A", "Heal", "RF2 (kN)"))
    print("-" * 75)
    for r in records:
        it = r.get("iteration")
        u = r.get("set_sizes", {}).get("U", 0)
        l = r.get("set_sizes", {}).get("L", 0)
        a = r.get("set_sizes", {}).get("A", 0)
        ch = r.get("set_changes", 0)
        res = r.get("residual_inf_norm_A_kNmm", 0.0)
        heal = r.get("strict_healing_count", 0)
        rf2 = r.get("rf2_kN", 0.0)
        print("%-5d | %-5d | %-5d | %-5d | %-8d | %-12.4e | %-6d | %-12.6f" % (it, u, l, a, ch, res, heal, rf2))

    if len(records) >= 6:
        last_4_a = [r.get("set_sizes", {}).get("A", 0) for r in records[-4:]]
        print("\nLast 4 Active Set Sizes: %s" % str(last_4_a))
        if last_4_a[0] == last_4_a[2] and last_4_a[1] == last_4_a[3] and last_4_a[0] != last_4_a[1]:
            print("DETECTED PERIODIC 2-CYCLE OSCILLATION: alternating between |A|=%d and |A|=%d" % (last_4_a[0], last_4_a[1]))

    if energy_path.is_file():
        print("\n--- UEL Energy Balance ---")
        with open(energy_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                print(", ".join(row))

if __name__ == "__main__":
    evaluate()
