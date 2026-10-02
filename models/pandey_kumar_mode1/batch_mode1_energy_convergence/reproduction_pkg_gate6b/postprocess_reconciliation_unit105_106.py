"""
postprocess_reconciliation_unit105_106.py
Reconciles accepted-increment energy balances from Unit 105 (uel_energy_balance.csv)
and Unit 106 (uel_discrete_diagnostic.csv), and computes two-term bookkeeping difference.
"""
import os
import sys
import json

def parse_csv_records(csv_path):
    if not os.path.exists(csv_path):
        return []
    records = []
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        header = None
        for line in f:
            line_s = line.strip()
            if not line_s:
                continue
            parts = [p.strip() for p in line_s.split(",")]
            if header is None:
                header = parts
                continue
            try:
                row = {}
                for h, val in zip(header, parts):
                    try:
                        row[h] = float(val) if ("." in val or "E" in val or "e" in val) else int(val)
                    except ValueError:
                        row[h] = val
                records.append(row)
            except Exception:
                pass
    return records

def reconcile_unit105_106(u105_path, u106_path, w_trap_final=None):
    r105 = parse_csv_records(u105_path)
    r106 = parse_csv_records(u106_path)

    results = {
        "status": "UNKNOWN",
        "u105_record_count": len(r105),
        "u106_record_count": len(r106),
        "reconciliation_passed": False,
        "max_discrepancy_e_elas": 0.0,
        "max_discrepancy_e_frac": 0.0,
        "terminal_energies": {},
        "provisional_diagnostics": {}
    }

    if len(r105) == 0 and len(r106) == 0:
        results["status"] = "NO_CSV_RECORDS"
        return results

    # Reconcile overlapping rows
    n_match = min(len(r105), len(r106))
    max_d_elas = 0.0
    max_d_frac = 0.0
    for i in range(n_match):
        e105_elas = r105[i].get("E_elastic_kNmm", 0.0)
        e106_elas = r106[i].get("E_elas_kNmm", 0.0)
        e105_frac = r105[i].get("E_fracture_kNmm", 0.0)
        e106_frac = r106[i].get("E_frac_kNmm", 0.0)

        max_d_elas = max(max_d_elas, abs(e105_elas - e106_elas))
        max_d_frac = max(max_d_frac, abs(e105_frac - e106_frac))

    results["max_discrepancy_e_elas"] = max_d_elas
    results["max_discrepancy_e_frac"] = max_d_frac
    results["reconciliation_passed"] = (max_d_elas < 1e-12 and max_d_frac < 1e-12)

    if len(r106) > 0:
        last106 = r106[-1]
        results["terminal_energies"] = {
            "step": last106.get("Step"),
            "increment": last106.get("Increment"),
            "total_time": last106.get("TotalTime"),
            "e_elas_kNmm": last106.get("E_elas_kNmm"),
            "e_frac_kNmm": last106.get("E_frac_kNmm"),
            "e_int_kNmm": last106.get("E_int_kNmm")
        }
        results["provisional_diagnostics"] = {
            "inc_t_hist_kNmm": last106.get("Inc_T_hist_kNmm"),
            "inc_t_avg_kNmm": last106.get("Inc_T_avg_kNmm"),
            "inc_t_split_kNmm": last106.get("Inc_T_split_kNmm"),
            "cum_t_hist_kNmm": last106.get("Cum_T_hist_kNmm"),
            "cum_t_avg_kNmm": last106.get("Cum_T_avg_kNmm"),
            "cum_t_split_kNmm": last106.get("Cum_T_split_kNmm"),
            "cum_t_sum_kNmm": last106.get("Cum_T_sum_kNmm")
        }
        if w_trap_final is not None:
            e_tot = last106.get("E_int_kNmm", 0.0)
            r_book = w_trap_final - e_tot
            results["terminal_energies"]["w_trap_kNmm"] = w_trap_final
            results["terminal_energies"]["r_bookkeeping_kNmm"] = r_book
            results["terminal_energies"]["r_bookkeeping_pct"] = (r_book / w_trap_final * 100.0) if w_trap_final > 0 else 0.0

    results["status"] = "SUCCESS" if results["reconciliation_passed"] else "MISMATCH"
    return results

if __name__ == "__main__":
    print("Unit 105/106 Reconciliation Module loaded successfully.")
