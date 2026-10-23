#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_pkg90_results.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Extracts full solver telemetry, force-displacement response, and terminal state
from Package 90 ODB: /scratch9/pr21vyci/runs/mode1_package90_c3_transfer/M1_C3_PACKAGE90_TRANSFER.odb
"""

import os
import sys
import json
import csv
from odbAccess import openOdb

def get_history_series(step, region_filter, var_name):
    for hreg_name, hreg in step.historyRegions.items():
        if any(rf in hreg_name for rf in region_filter):
            if var_name in hreg.historyOutputs:
                return [(float(t), float(v)) for t, v in hreg.historyOutputs[var_name].data]
    return []

def main():
    work_dir = "/scratch9/pr21vyci/runs/mode1_package90_c3_transfer"
    odb_path = os.path.join(work_dir, "M1_C3_PACKAGE90_TRANSFER.odb")
    print("Opening Package 90 ODB: %s" % odb_path)

    if not os.path.exists(odb_path):
        raise RuntimeError("ODB not found: %s" % odb_path)

    odb = openOdb(odb_path, readOnly=True)
    step_results = {}
    rf2_trace = []
    u2_trace = []

    # Reference values: Package 89 Terminal State
    PKG89_TERMINAL_RF2_N = 169.5991
    PKG89_TERMINAL_U2_MM = 0.00201510735
    PKG89_TERMINAL_E_FRAC_UJ = 76.07036
    PKG89_TERMINAL_E_ELAS_UJ = 170.87750

    for sname in ['STATE_INJECTION', 'MECH_REEQUIL_FROZEN_DAMAGE', 'STAGGERED_PHASE_SUBPROBLEM', 'FORWARD_CONTINUATION']:
        if sname not in odb.steps:
            print("Step %s not found in ODB!" % sname)
            continue
        step = odb.steps[sname]
        total_frames = len(step.frames)
        print("\n--- Step %s (%d frames) ---" % (sname, total_frames))

        rf2_hist = get_history_series(step, ['999999', 'N_RP'], 'RF2')
        u2_hist = get_history_series(step, ['999999', 'N_RP'], 'U2')

        frames_data = []
        for fidx, f in enumerate(step.frames):
            t_val = float(f.frameValue)
            fid = int(f.frameId)

            u2_rp = None
            rf2_rp = None
            if 'U' in f.fieldOutputs:
                for val in f.fieldOutputs['U'].values:
                    if val.nodeLabel == 999999:
                        u2_rp = float(val.data[1])
                        break
            if 'RF' in f.fieldOutputs:
                for val in f.fieldOutputs['RF'].values:
                    if val.nodeLabel == 999999:
                        rf2_rp = float(val.data[1]) * 1000.0  # kN -> N
                        break

            if rf2_rp is None and rf2_hist:
                closest = min(rf2_hist, key=lambda x: abs(x[0] - t_val))
                if abs(closest[0] - t_val) < 1e-4:
                    rf2_rp = closest[1] * 1000.0
            if u2_rp is None and u2_hist:
                closest = min(u2_hist, key=lambda x: abs(x[0] - t_val))
                if abs(closest[0] - t_val) < 1e-4:
                    u2_rp = closest[1]

            d_vals = []
            if 'U' in f.fieldOutputs:
                for val in f.fieldOutputs['U'].values:
                    if val.nodeLabel != 999999:
                        if len(val.data) >= 3:
                            d_vals.append(float(val.data[2]))

            d_max = max(d_vals) if d_vals else 0.0

            frame_entry = {
                "frame_id": fid,
                "step_time": t_val,
                "u2_mm": u2_rp,
                "rf2_N": rf2_rp,
                "d_max": d_max
            }
            frames_data.append(frame_entry)

            if rf2_rp is not None and u2_rp is not None:
                rf2_trace.append(rf2_rp)
                u2_trace.append(u2_rp)
                print("  Frame %d: t=%.4f, U2=%.7f mm, RF2=%.4f N, d_max=%.5f" %
                      (fid, t_val, u2_rp, rf2_rp, d_max))

        step_results[sname] = {
            "total_frames": total_frames,
            "frames": frames_data,
            "final_rf2_N": frames_data[-1]["rf2_N"] if frames_data else None,
            "final_d_max": frames_data[-1]["d_max"] if frames_data else None,
            "final_u2_mm": frames_data[-1]["u2_mm"] if frames_data else None
        }

    # Extract terminal nodal displacements and damage for continuation / verification
    fwd_step = odb.steps['FORWARD_CONTINUATION']
    last_fwd_frame = fwd_step.frames[-1]

    terminal_nodal = []
    if 'U' in last_fwd_frame.fieldOutputs:
        for val in last_fwd_frame.fieldOutputs['U'].values:
            if val.nodeLabel != 999999:
                u1 = float(val.data[0])
                u2 = float(val.data[1])
                d = float(val.data[2]) if len(val.data) >= 3 else 0.0
                terminal_nodal.append({
                    "node_id": val.nodeLabel,
                    "u1": u1,
                    "u2": u2,
                    "damage": d
                })

    # Write CSV of terminal nodal state
    csv_out = os.path.join(work_dir, "pkg90_terminal_nodal_state.csv")
    with open(csv_out, "w") as f:
        writer = csv.DictWriter(f, fieldnames=["node_id", "u1", "u2", "damage"])
        writer.writeheader()
        for r in terminal_nodal:
            writer.writerow(r)
    print("Wrote terminal nodal state CSV: %s (%d nodes)" % (csv_out, len(terminal_nodal)))

    # Force continuity checks
    step1_rf2 = step_results.get("STATE_INJECTION", {}).get("final_rf2_N")
    step2_rf2 = step_results.get("MECH_REEQUIL_FROZEN_DAMAGE", {}).get("final_rf2_N")
    step3_rf2 = step_results.get("STAGGERED_PHASE_SUBPROBLEM", {}).get("final_rf2_N")
    step4_rf2 = step_results.get("FORWARD_CONTINUATION", {}).get("final_rf2_N")

    step1_discrepancy_pct = ((step1_rf2 - PKG89_TERMINAL_RF2_N) / PKG89_TERMINAL_RF2_N * 100.0) if step1_rf2 else None
    step2_discrepancy_pct = ((step2_rf2 - PKG89_TERMINAL_RF2_N) / PKG89_TERMINAL_RF2_N * 100.0) if step2_rf2 else None

    # Load uel_energy_balance.csv
    energy_entries = []
    eb_path = os.path.join(work_dir, "uel_energy_balance.csv")
    if os.path.exists(eb_path):
        with open(eb_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                energy_entries.append({
                    "step": int(row["Step"].strip()),
                    "inc": int(row["Increment"].strip()),
                    "step_time": float(row["StepTime"].strip()),
                    "e_elastic_uJ": float(row["E_elastic_kNmm"].strip()) * 1e6,
                    "e_fracture_uJ": float(row["E_fracture_kNmm"].strip()) * 1e6,
                    "e_total_uJ": float(row["E_total_kNmm"].strip()) * 1e6
                })

    step1_e_frac = energy_entries[0]["e_fracture_uJ"] if energy_entries else None
    delta_e_frac_pct = ((step1_e_frac - PKG89_TERMINAL_E_FRAC_UJ) / PKG89_TERMINAL_E_FRAC_UJ * 100.0) if step1_e_frac else None

    summary = {
        "status": "PACKAGE90_TELEMETRY_SUCCESS",
        "job_name": "M1_C3_PACKAGE90_TRANSFER",
        "reference_pkg89_terminal": {
            "u2_mm": PKG89_TERMINAL_U2_MM,
            "rf2_N": PKG89_TERMINAL_RF2_N,
            "e_fracture_uJ": PKG89_TERMINAL_E_FRAC_UJ,
            "e_elastic_uJ": PKG89_TERMINAL_E_ELAS_UJ
        },
        "step1_state_injection": {
            "rf2_N": step1_rf2,
            "discrepancy_vs_pkg89_pct": step1_discrepancy_pct,
            "e_fracture_uJ": step1_e_frac,
            "delta_fracture_energy_pct": delta_e_frac_pct,
            "meets_5pct_force_gate": abs(step1_discrepancy_pct) <= 5.0 if step1_discrepancy_pct is not None else False
        },
        "step2_mech_reequilibration": {
            "rf2_N": step2_rf2,
            "discrepancy_vs_pkg89_pct": step2_discrepancy_pct,
            "meets_5pct_force_gate": abs(step2_discrepancy_pct) <= 5.0 if step2_discrepancy_pct is not None else False
        },
        "step3_staggered_phase": {
            "rf2_N": step3_rf2,
            "d_max": step_results.get("STAGGERED_PHASE_SUBPROBLEM", {}).get("final_d_max")
        },
        "step4_forward_continuation": {
            "final_u2_mm": step_results.get("FORWARD_CONTINUATION", {}).get("final_u2_mm"),
            "final_rf2_N": step4_rf2,
            "final_d_max": step_results.get("FORWARD_CONTINUATION", {}).get("final_d_max"),
            "softening_observed": step4_rf2 < step3_rf2 if (step4_rf2 and step3_rf2) else None
        },
        "steps": step_results,
        "energy_balance": energy_entries
    }

    out_json = os.path.join(work_dir, "pkg90_telemetry_summary.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print("Wrote telemetry summary: %s" % out_json)

    odb.close()

if __name__ == "__main__":
    main()
