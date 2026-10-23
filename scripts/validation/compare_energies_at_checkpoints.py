#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import csv
import json

def load_energy_csv(path):
    rows = []
    with open(path, 'r') as f:
        reader = csv.reader(f)
        header = [h.strip() for h in next(reader)]
        for line in reader:
            if not line:
                continue
            rows.append({
                "step": int(line[0].strip()),
                "inc": int(line[1].strip()),
                "time": float(line[2].strip()),
                "e_elas": float(line[4].strip()),
                "e_frac": float(line[5].strip()),
                "e_total": float(line[6].strip())
            })
    return rows

def find_closest(rows, t_target):
    return min(rows, key=lambda r: abs(r["time"] - t_target))

def main():
    p76_path = "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_1416301/uel_energy_balance.csv"
    p87_path = "models/pandey_kumar_mode1/87_c2_virgin_mesh_control/uel_energy_balance.csv"
    p76_rows = load_energy_csv(p76_path)
    p87_rows = load_energy_csv(p87_path)

    with open("results/validation/mode1_f1597/p76_p87_checkpoint_candidates.json", "r") as fp:
        cdata = json.load(fp)

    print("%-10s %-10s %-12s %-12s %-10s %-12s %-12s %-10s %-10s" %
          ("u (mm)", "Donor t(s)", "Donor RF2", "C2 RF2", "RF Diff%", "Donor E_f", "C2 E_f", "Ef Diff%", "Eel Diff%"))
    print("-" * 105)

    all_res = []
    for c in cdata["comparisons"]:
        u = c["u_mm"]
        dt = c["donor_time"]
        rf_d = c["donor_rf2_N"]
        rf_c = c["c2_interp_rf2_N"]
        rf_diff = c["rf2_diff_pct"]

        d_row = find_closest(p76_rows, dt)
        c2_row = find_closest(p87_rows, dt)

        ef_d = d_row["e_frac"] * 1e6
        ef_c = c2_row["e_frac"] * 1e6
        ef_diff = 100.0 * (ef_c - ef_d) / ef_d if ef_d > 0 else 0.0

        eel_d = d_row["e_elas"] * 1e6
        eel_c = c2_row["e_elas"] * 1e6
        eel_diff = 100.0 * (eel_c - eel_d) / eel_d

        print("%-10.7f %-10.6f %-12.4f %-12.4f %-+10.2f %-12.4f %-12.4f %-+10.2f %-+10.2f" %
              (u, dt, rf_d, rf_c, rf_diff, ef_d, ef_c, ef_diff, eel_diff))

        all_res.append({
            "u_mm": u,
            "donor_time": dt,
            "donor_rf2_N": rf_d,
            "c2_interp_rf2_N": rf_c,
            "rf2_diff_pct": rf_diff,
            "donor_e_frac_uJ": ef_d,
            "c2_e_frac_uJ": ef_c,
            "e_frac_diff_pct": ef_diff,
            "donor_e_elas_uJ": eel_d,
            "c2_e_elas_uJ": eel_c,
            "e_elas_diff_pct": eel_diff
        })

    with open("results/validation/mode1_f1597/candidate_energy_comparison.json", "w") as fp:
        json.dump(all_res, fp, indent=2)

if __name__ == '__main__':
    main()
