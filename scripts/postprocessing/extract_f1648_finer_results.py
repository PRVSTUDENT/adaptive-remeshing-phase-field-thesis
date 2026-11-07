# -*- coding: utf-8 -*-
"""Extract reaction forces, energies, and work-energy balance from F1648 finer-mesh run."""
import os
import re
import csv
import json
import numpy as np

def extract_f1648_dat(dat_path, out_csv_path):
    """Extract RF2 vs U2 from Abaqus .dat file for node 999999."""
    inc_pattern = re.compile(r"^\s*INCREMENT\s+(\d+)\s+SUMMARY")
    step_pattern = re.compile(r"^\s*STEP\s+(\d+)\s+INCREMENT\s+(\d+)")
    rp_pattern = re.compile(r"^\s*999999\s+([0-9.E+-]+)\s+([0-9.E+-]+)")

    rows = []
    current_step = 1
    current_inc = 0

    with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m_step = step_pattern.search(line)
            if m_step:
                current_step = int(m_step.group(1))
                current_inc = int(m_step.group(2))
                continue
            m_inc = inc_pattern.search(line)
            if m_inc:
                current_inc = int(m_inc.group(1))
                continue
            m_rp = rp_pattern.search(line)
            if m_rp:
                u2 = float(m_rp.group(1))
                rf2 = float(m_rp.group(2))
                rows.append({
                    "step": current_step,
                    "increment": current_inc,
                    "u2_mm": u2,
                    "rf2_kN": rf2
                })

    with open(out_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["step", "increment", "u2_mm", "rf2_kN"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Extracted {len(rows)} load-displacement records to {out_csv_path}")
    return rows

def compute_f1648_metrics(rf_rows, energy_csv_path, out_json_path):
    """Compute peak load, post-peak drop, energy balance, and work-energy residual."""
    u = np.array([r["u2_mm"] for r in rf_rows])
    rf = np.array([r["rf2_kN"] for r in rf_rows])

    # External work via trapezoidal integration
    w_ext = np.trapz(rf, u)  # kN mm = J

    # Find peak
    idx_peak = np.argmax(rf)
    f_max = rf[idx_peak]
    u_peak = u[idx_peak]
    step_peak = rf_rows[idx_peak]["step"]
    inc_peak = rf_rows[idx_peak]["increment"]

    # Post-peak softening
    if idx_peak < len(rf) - 1:
        f_terminal = rf[-1]
        u_terminal = u[-1]
        softening_drop_pct = (f_max - f_terminal) / f_max * 100.0
    else:
        f_terminal = f_max
        u_terminal = u_peak
        softening_drop_pct = 0.0

    # Initial elastic stiffness (first 10 increments of Step 1)
    step1_mask = np.array([r["step"] == 1 for r in rf_rows])
    if np.sum(step1_mask) >= 5:
        u_step1 = u[step1_mask][:10]
        rf_step1 = rf[step1_mask][:10]
        k0 = float(np.polyfit(u_step1, rf_step1, 1)[0])
    else:
        k0 = 0.0

    # Energy balance from CSV
    energy_records = []
    if os.path.exists(energy_csv_path):
        with open(energy_csv_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                energy_records.append({
                    "step": int(row["Step"]),
                    "increment": int(row["Increment"]),
                    "total_time": float(row["TotalTime"]),
                    "e_elastic_kNmm": float(row["E_elastic_kNmm"]),
                    "e_fracture_kNmm": float(row["E_fracture_kNmm"]),
                    "e_total_kNmm": float(row["E_total_kNmm"]),
                })

    metrics = {
        "total_records": len(rf_rows),
        "peak_force_kN": float(f_max),
        "u_at_peak_mm": float(u_peak),
        "step_at_peak": int(step_peak),
        "increment_at_peak": int(inc_peak),
        "terminal_force_kN": float(f_terminal),
        "terminal_u_mm": float(u_terminal),
        "softening_drop_percent": float(softening_drop_pct),
        "initial_stiffness_kN_per_mm": float(k0),
        "external_work_total_kNmm": float(w_ext),
        "energy_records_count": len(energy_records)
    }

    if energy_records:
        last_e = energy_records[-1]
        e_elas = last_e["e_elastic_kNmm"]
        e_frac = last_e["e_fracture_kNmm"]
        e_tot = last_e["e_total_kNmm"]
        work_energy_err_pct = abs(w_ext - e_tot) / e_tot * 100.0 if e_tot > 0 else 0.0
        internal_cons_err = abs(e_elas + e_frac - e_tot) / e_tot if e_tot > 0 else 0.0

        metrics["terminal_energy"] = {
            "e_elastic_kNmm": e_elas,
            "e_fracture_kNmm": e_frac,
            "e_total_kNmm": e_tot,
            "work_energy_residual_percent": float(work_energy_err_pct),
            "internal_conservation_relative_error": float(internal_cons_err)
        }

    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"Metrics written to {out_json_path}")
    print(f"  F_max = {f_max:.6f} kN at u = {u_peak:.6f} mm (Step {step_peak}, Inc {inc_peak})")
    print(f"  Terminal F = {f_terminal:.6f} kN (Softening drop: {softening_drop_pct:.2f}%)")
    print(f"  External work W_ext = {w_ext:.6e} kN mm")
    if "terminal_energy" in metrics:
        print(f"  E_total = {metrics['terminal_energy']['e_total_kNmm']:.6e} kN mm")
        print(f"  Work-Energy error = {metrics['terminal_energy']['work_energy_residual_percent']:.4f}%")

    return metrics

if __name__ == "__main__":
    import sys
    dat_file = sys.argv[1] if len(sys.argv) > 1 else "results/validation/f1648_PK_HOLE_METHOD_A_FINER.dat"
    csv_file = sys.argv[2] if len(sys.argv) > 2 else "results/validation/f1648_finer_rf_displacement.csv"
    energy_csv = sys.argv[3] if len(sys.argv) > 3 else "results/validation/f1648_uel_energy_balance.csv"
    json_out = sys.argv[4] if len(sys.argv) > 4 else "results/validation/f1648_finer_metrics.json"

    if os.path.exists(dat_file):
        rows = extract_f1648_dat(dat_file, csv_file)
        compute_f1648_metrics(rows, energy_csv, json_out)
    else:
        print(f"File not found: {dat_file}")
