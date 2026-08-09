#!/usr/bin/env python3
"""Provenance mapping script for historical reference jobs 1378942 and 1379393."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R2_DIR = ROOT / "runs/hpc/stage_f/mode_ii_h0/replacement_r2/evidence/1378942.mmaster02"
CORR_DIR = ROOT / "runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/replacement_r1/evidence/1379393.mmaster02"


def inspect_job(dir_path: Path, name: str):
    print(f"=== Provenance Map for {name} ({dir_path.name}) ===")
    summary_file = dir_path / "extracted/single_notch_extraction_summary.json"
    val_file = dir_path / "VALIDATION_RESULTS.json"
    rf_file = dir_path / "extracted/rf1_u1_curve.csv"

    res = {"name": name, "dir": str(dir_path)}

    if summary_file.is_file():
        s_data = json.loads(summary_file.read_text(encoding="utf-8"))
        res["node_count"] = s_data.get("node_count")
        res["layered_element_count"] = s_data.get("element_count")
        res["physical_element_count"] = s_data.get("element_count") // 3 if s_data.get("element_count") else None

    if val_file.is_file():
        v_data = json.loads(val_file.read_text(encoding="utf-8"))
        res["final_u1_mm"] = v_data.get("final_u1_mm")
        res["max_rf1_kn"] = v_data.get("max_rf1_kn")
        res["max_sdv15"] = v_data.get("max_sdv15")

    if rf_file.is_file():
        rows = list(csv.DictReader(rf_file.open(encoding="utf-8")))
        rf_vals = [float(r["rf1"]) for r in rows if "rf1" in r and r["rf1"] != ""]
        u_vals = [float(r["u1"]) for r in rows if "u1" in r and r["u1"] != ""]
        d_vals = [float(r["d_max"]) for r in rows if "d_max" in r and r["d_max"] != ""]
        if rf_vals:
            res["curve_max_rf1_kn"] = max(rf_vals)
            res["curve_final_rf1_kn"] = rf_vals[-1]
            res["curve_final_u1_mm"] = u_vals[-1]
            res["curve_max_d"] = max(d_vals)

    for k, v in res.items():
        print(f"  {k}: {v}")
    print()
    return res


def main():
    j1 = inspect_job(R2_DIR, "1378942.mmaster02")
    j2 = inspect_job(CORR_DIR, "1379393.mmaster02")


if __name__ == "__main__":
    main()
