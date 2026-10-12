#!/usr/bin/env python3
"""
Method C Gate C1 Telemetry Extractor & Scientific Evaluation Script
Parses .sta, .dat, and uel_energy_balance.csv from the continuation run
and generates structured JSON evaluation and load-displacement CSV.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any

def parse_sta_file(sta_path: Path) -> Dict[str, Any]:
    total_incs = 0
    step1_incs = 0
    step2_incs = 0
    cutbacks = 0
    severe_discon = 0
    last_step = 1
    last_time = 0.0

    if not sta_path.exists():
        return {"status": "MISSING", "error": f"File not found: {sta_path}"}

    with open(sta_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 10 and parts[0].isdigit() and parts[1].isdigit():
                step = int(parts[0])
                inc = int(parts[1])
                att = int(parts[2])
                sd = int(parts[3])
                tot_time = float(parts[6])

                total_incs += 1
                if step == 1:
                    step1_incs += 1
                elif step == 2:
                    step2_incs += 1
                if att > 1:
                    cutbacks += (att - 1)
                severe_discon += sd
                last_step = step
                last_time = tot_time

    return {
        "status": "PARSED",
        "total_increments": total_incs,
        "step1_increments": step1_incs,
        "step2_increments": step2_incs,
        "cutbacks": cutbacks,
        "severe_discontinuities": severe_discon,
        "final_step": last_step,
        "final_time": last_time,
    }

def parse_dat_file(dat_path: Path) -> List[Dict[str, float]]:
    records = []
    current_step = 1

    if not dat_path.exists():
        return records

    with open(dat_path, "r", encoding="utf-8") as f:
        for line in f:
            if "STEP 1" in line or "Step-1" in line:
                current_step = 1
            elif "STEP 2" in line or "Step-2" in line:
                current_step = 2

            if "999999" in line:
                parts = line.split()
                if len(parts) >= 3 and parts[0] == "999999":
                    try:
                        u2 = float(parts[1])
                        rf2 = float(parts[2])
                        records.append({
                            "step": current_step,
                            "u2_mm": u2,
                            "rf2_kn": rf2,
                        })
                    except ValueError:
                        pass
    return records

def parse_energy_csv(energy_path: Path) -> List[Dict[str, float]]:
    records = []
    if not energy_path.exists():
        return records

    with open(energy_path, "r", encoding="utf-8") as f:
        header = None
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if header is None:
                header = parts
                continue
            if len(parts) >= 7:
                try:
                    records.append({
                        "step": int(parts[0]),
                        "increment": int(parts[1]),
                        "total_time": float(parts[2]),
                        "step_time": float(parts[3]),
                        "e_elastic_knmm": float(parts[4]),
                        "e_fracture_knmm": float(parts[5]),
                        "e_total_knmm": float(parts[6]),
                    })
                except ValueError:
                    pass
    return records

def main():
    parser = argparse.ArgumentParser(description="Extract Method C Gate C1 continuation results")
    parser.add_argument("--run_dir", type=str, required=True, help="Path to run directory containing solver files")
    parser.add_argument("--output_json", type=str, default="c1_continuation_evaluation.json", help="Output JSON path")
    parser.add_argument("--output_csv", type=str, default="c1_load_displacement.csv", help="Output load-displacement CSV path")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    sta_path = run_dir / "M1_RECIP_2906_CONTINUATION.sta"
    dat_path = run_dir / "M1_RECIP_2906_CONTINUATION.dat"
    energy_path = run_dir / "uel_energy_balance.csv"

    print(f"Parsing run directory: {run_dir}")
    sta_summary = parse_sta_file(sta_path)
    rf_records = parse_dat_file(dat_path)
    energy_records = parse_energy_csv(energy_path)

    print(f"  STA: {sta_summary.get('status')}, {sta_summary.get('total_increments', 0)} increments, {sta_summary.get('cutbacks', 0)} cutbacks")
    print(f"  DAT: {len(rf_records)} RP force-displacement records")
    print(f"  Energy: {len(energy_records)} energy balance records")

    # Metrics evaluation
    step1_pts = [r for r in rf_records if r["step"] == 1]
    step2_pts = [r for r in rf_records if r["step"] == 2]

    k0_reload = None
    rf_handoff = None
    if step1_pts:
        rf_handoff = step1_pts[-1]["rf2_kn"]
        u_handoff = step1_pts[-1]["u2_mm"]
        if u_handoff > 0:
            k0_reload = rf_handoff / u_handoff

    f_max = None
    u_at_fmax = None
    f_final = None
    if step2_pts:
        peak = max(step2_pts, key=lambda r: r["rf2_kn"])
        f_max = peak["rf2_kn"]
        u_at_fmax = peak["u2_mm"]
        f_final = step2_pts[-1]["rf2_kn"]

    evaluation = {
        "gate": "METHOD_C_GATE_C1_SINGLE_CYCLE_VERIFICATION",
        "solver_telemetry": sta_summary,
        "metrics": {
            "step1_reload": {
                "num_points": len(step1_pts),
                "handoff_displacement_mm": step1_pts[-1]["u2_mm"] if step1_pts else None,
                "handoff_reaction_force_kn": rf_handoff,
                "effective_reload_stiffness_k0_kn_per_mm": k0_reload,
            },
            "step2_continuation": {
                "num_points": len(step2_pts),
                "peak_force_fmax_kn": f_max,
                "displacement_at_peak_mm": u_at_fmax,
                "final_force_kn": f_final,
            },
            "energy_balance": {
                "num_records": len(energy_records),
                "initial_fracture_energy_knmm": energy_records[0]["e_fracture_knmm"] if energy_records else None,
                "final_fracture_energy_knmm": energy_records[-1]["e_fracture_knmm"] if energy_records else None,
                "final_elastic_energy_knmm": energy_records[-1]["e_elastic_knmm"] if energy_records else None,
                "final_total_energy_knmm": energy_records[-1]["e_total_knmm"] if energy_records else None,
            }
        }
    }

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, indent=2)
    print(f"Evaluation written to: {args.output_json}")

    with open(args.output_csv, "w", encoding="utf-8") as f:
        f.write("step,u2_mm,rf2_kn\n")
        for r in rf_records:
            f.write(f"{r['step']},{r['u2_mm']:.10e},{r['rf2_kn']:.10e}\n")
    print(f"Force-displacement CSV written to: {args.output_csv}")

if __name__ == "__main__":
    main()
