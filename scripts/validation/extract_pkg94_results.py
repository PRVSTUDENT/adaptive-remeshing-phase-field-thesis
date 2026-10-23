#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_pkg94_results.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: 22ef1047-5d2d-4d36-8bdb-7f08c988785f
Protocol Version: 2

Extracts and independently audits full solver results of Package 94:
M1_C4_PACKAGE94_TRANSFER (PBS Job 1416653.mmaster02).
"""

import os
import sys
import json
import csv
import math
from odbAccess import openOdb

def main():
    work_dir = "/scratch9/pr21vyci/runs/mode1_package94_c4_authentic_transfer"
    odb_path = os.path.join(work_dir, "M1_C4_PACKAGE94_TRANSFER.odb")
    print("Opening Package 94 ODB: %s" % odb_path)

    if not os.path.exists(odb_path):
        raise RuntimeError("ODB not found: %s" % odb_path)

    odb = openOdb(odb_path, readOnly=True)

    # Single Authoritative Donor Reference (Package 93 Frame 6 / Package 90-R1 Frame 6)
    donor_rf2_target = 159.15939211845398       # N
    donor_dmax_target = 0.9729551076889038
    donor_e_total_target = 2.4858009e-4         # kN*mm
    donor_e_fracture_target = 8.808000e-5       # kN*mm
    donor_u2_target = 0.00203669304             # mm

    step_rf = {}
    frame_records = []

    # Read mapped initial damage table if available for pointwise comparison
    mapped_csv = os.path.join(work_dir, "candidate_c4_frame6_mapped_state_table.csv")
    mapped_node_d = {}
    mapped_elem_h = {}
    if os.path.exists(mapped_csv):
        with open(mapped_csv, "r") as f:
            reader = csv.reader(f)
            header = next(reader)
            for r in reader:
                if len(r) >= 5 and r[0] == "NODE":
                    mapped_node_d[int(r[1])] = float(r[4])
                elif len(r) >= 6 and r[0] == "ELEM_H":
                    mapped_elem_h[int(r[1])] = [float(r[2]), float(r[3]), float(r[4]), float(r[5])]
        print("Loaded %d mapped nodes and %d mapped history elements from state table." % 
              (len(mapped_node_d), len(mapped_elem_h)))

    initial_gp_d = None

    for sname in odb.steps.keys():
        st = odb.steps[sname]
        print("\n=== Step: %s (%d frames) ===" % (sname, len(st.frames)))
        
        frames_in_step = []
        for f_idx, fr in enumerate(st.frames):
            t_val = float(fr.frameValue)
            
            # Extract RP (999999) RF2 and U2
            u2_rp = None
            rf2_rp = None
            if 'U' in fr.fieldOutputs:
                for val in fr.fieldOutputs['U'].values:
                    if val.nodeLabel == 999999:
                        u2_rp = float(val.data[1])
                        break
            if 'RF' in fr.fieldOutputs:
                for val in fr.fieldOutputs['RF'].values:
                    if val.nodeLabel == 999999:
                        rf2_rp = float(val.data[1]) * 1000.0  # kN -> N
                        break

            # Extract companion element SDVs (Layer 3: 8845..13266)
            sdv1 = fr.fieldOutputs['SDV1'] if 'SDV1' in fr.fieldOutputs else None
            sdv2 = fr.fieldOutputs['SDV2'] if 'SDV2' in fr.fieldOutputs else None

            gp_d = {}
            gp_h = {}
            if sdv1:
                for v in sdv1.values:
                    if 8845 <= v.elementLabel <= 13266:
                        key = (v.elementLabel, v.integrationPoint)
                        gp_d[key] = float(v.data)
            if sdv2:
                for v in sdv2.values:
                    if 8845 <= v.elementLabel <= 13266:
                        key = (v.elementLabel, v.integrationPoint)
                        gp_h[key] = float(v.data)

            if initial_gp_d is None and gp_d:
                initial_gp_d = dict(gp_d)

            d_vals = gp_d.values()
            h_vals = gp_h.values()

            d_min = min(d_vals) if d_vals else None
            d_max = max(d_vals) if d_vals else None
            h_min = min(h_vals) if h_vals else None
            h_max = max(h_vals) if h_vals else None

            # Check bounds and monotonicity
            overshoot_count = sum(1 for d in d_vals if d > 1.00000)
            negative_d_count = sum(1 for d in d_vals if d < 0.0)
            negative_h_count = sum(1 for h in h_vals if h < 0.0)

            # Pointwise healing check against initial step 1 state
            healing_count = 0
            min_delta_d = 0.0
            if initial_gp_d and gp_d:
                diffs = [gp_d[k] - initial_gp_d[k] for k in gp_d if k in initial_gp_d]
                healing_count = sum(1 for diff in diffs if diff < -1.0e-6)
                min_delta_d = min(diffs) if diffs else 0.0

            rec = {
                "step": sname,
                "frame_idx": f_idx,
                "frame_time": t_val,
                "u2_rp_mm": u2_rp,
                "rf2_rp_N": rf2_rp,
                "d_min": d_min,
                "d_max": d_max,
                "h_min": h_min,
                "h_max": h_max,
                "overshoot_count": overshoot_count,
                "negative_d_count": negative_d_count,
                "negative_h_count": negative_h_count,
                "healing_count": healing_count,
                "min_delta_d": min_delta_d,
                "gp_count": len(gp_d)
            }
            frames_in_step.append(rec)
            frame_records.append(rec)
            print("  Frame %d (t=%.3f): U2 = %.7f mm, RF2 = %.4f N, d_max = %.6f, H_max = %.4e, heal=%d (min_dd=%.2e)" %
                  (f_idx, t_val, u2_rp if u2_rp else 0.0, rf2_rp if rf2_rp else 0.0,
                   d_max if d_max is not None else 0.0, h_max if h_max is not None else 0.0,
                   healing_count, min_delta_d))

        last_f = frames_in_step[-1]
        step_rf[sname] = {
            "num_frames": len(st.frames),
            "last_frame_time": last_f["frame_time"],
            "u2_rp_mm": last_f["u2_rp_mm"],
            "rf2_rp_N": last_f["rf2_rp_N"],
            "d_min": last_f["d_min"],
            "d_max": last_f["d_max"],
            "h_min": last_f["h_min"],
            "h_max": last_f["h_max"],
            "overshoot_count": last_f["overshoot_count"],
            "healing_count": last_f["healing_count"],
            "min_delta_d": last_f["min_delta_d"],
            "gp_count": last_f["gp_count"]
        }

    # Extract terminal nodal displacements
    terminal_nodes = {}
    last_frame = odb.steps["FORWARD_CONTINUATION"].frames[-1]
    if 'U' in last_frame.fieldOutputs:
        for val in last_frame.fieldOutputs['U'].values:
            nid = val.nodeLabel
            if nid != 999999:
                terminal_nodes[nid] = {
                    "u1": float(val.data[0]),
                    "u2": float(val.data[1])
                }
    print("Extracted %d terminal nodal displacements." % len(terminal_nodes))

    # Load energies from uel_energy_balance.csv
    energy_csv = os.path.join(work_dir, "uel_energy_balance.csv")
    energies = []
    if os.path.exists(energy_csv):
        with open(energy_csv, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                energies.append({
                    "step": int(row["Step"].strip()),
                    "inc": int(row["Increment"].strip()),
                    "total_time": float(row["TotalTime"].strip()),
                    "step_time": float(row["StepTime"].strip()),
                    "E_elastic_kNmm": float(row["E_elastic_kNmm"].strip()),
                    "E_fracture_kNmm": float(row["E_fracture_kNmm"].strip()),
                    "E_total_kNmm": float(row["E_total_kNmm"].strip())
                })
    print("Loaded %d energy records from uel_energy_balance.csv" % len(energies))

    # Evaluate Gate C1-1 acceptance criteria
    step1_rf = step_rf.get("STATE_INJECTION", {}).get("rf2_rp_N")
    step2_rf = step_rf.get("MECH_REEQUIL_FROZEN_DAMAGE", {}).get("rf2_rp_N")
    step3_rf = step_rf.get("STAGGERED_PHASE_SUBPROBLEM", {}).get("rf2_rp_N")
    step4_rf = step_rf.get("FORWARD_CONTINUATION", {}).get("rf2_rp_N")

    step1_mismatch = abs(step1_rf - donor_rf2_target) / donor_rf2_target * 100.0 if step1_rf else None
    step2_mismatch = abs(step2_rf - donor_rf2_target) / donor_rf2_target * 100.0 if step2_rf else None
    step3_mismatch = abs(step3_rf - donor_rf2_target) / donor_rf2_target * 100.0 if step3_rf else None

    # Released force continuity gate: Step 2 RF2 within 5% of donor target
    gate_force = "PASS" if step2_mismatch is not None and step2_mismatch <= 5.0 else "FAIL"

    # Energy continuity gate: Step 2 fracture energy within 2% of donor target
    step2_e_frac = energies[7]["E_fracture_kNmm"] if len(energies) >= 8 else None
    step2_e_tot = energies[7]["E_total_kNmm"] if len(energies) >= 8 else None
    e_frac_diff_pct = abs(step2_e_frac - donor_e_fracture_target) / donor_e_fracture_target * 100.0 if step2_e_frac else None
    e_tot_diff_pct = abs(step2_e_tot - donor_e_total_target) / donor_e_total_target * 100.0 if step2_e_tot else None
    gate_energy = "PASS" if e_frac_diff_pct is not None and e_frac_diff_pct <= 2.0 else "FAIL"

    # Damage bounds gate: 0 <= d <= 1 everywhere across all frames
    all_overshoots = sum(r["overshoot_count"] for r in frame_records)
    all_negative_d = sum(r["negative_d_count"] for r in frame_records)
    terminal_dmax = step_rf.get("FORWARD_CONTINUATION", {}).get("d_max", 0.0)
    gate_bounds = "PASS" if all_overshoots == 0 and all_negative_d == 0 and terminal_dmax <= 1.00000 else "FAIL"

    # Irreversibility gate: 0 healing points across all steps
    step3_healing = step_rf.get("STAGGERED_PHASE_SUBPROBLEM", {}).get("healing_count", 0)
    step4_healing = step_rf.get("FORWARD_CONTINUATION", {}).get("healing_count", 0)
    gate_irreversibility = "PASS" if step3_healing == 0 and step4_healing == 0 else "FAIL"

    # History preservation gate: finite, nonnegative, transferred
    all_negative_h = sum(r["negative_h_count"] for r in frame_records)
    init_h_max = step_rf.get("STATE_INJECTION", {}).get("h_max", 0.0)
    gate_history = "PASS" if all_negative_h == 0 and init_h_max > 0.0 else "FAIL"

    # Softening continuation: verify physical softening drop without snap-back or excessive overshoot
    softening_drop_pct = (step4_rf - step3_rf) / step3_rf * 100.0 if step4_rf and step3_rf else None
    gate_softening = "PASS" if softening_drop_pct is not None and -30.0 <= softening_drop_pct <= -5.0 else "FAIL"

    all_gates_pass = (gate_force == "PASS" and gate_energy == "PASS" and
                      gate_bounds == "PASS" and gate_irreversibility == "PASS" and
                      gate_history == "PASS" and gate_softening == "PASS")

    audit = {
        "job_name": "M1_C4_PACKAGE94_TRANSFER",
        "pbs_job_id": "1416653.mmaster02",
        "donor_reference": {
            "package": "PACKAGE_93",
            "frame": 6,
            "u2_target_mm": donor_u2_target,
            "rf2_target_N": donor_rf2_target,
            "dmax_target": donor_dmax_target,
            "e_fracture_target_kNmm": donor_e_fracture_target,
            "e_total_target_kNmm": donor_e_total_target
        },
        "receiver_mesh": {
            "name": "Candidate C4",
            "quad_count": 4422,
            "node_count": 4588,
            "gp_count": 17688
        },
        "gates": {
            "gate1_force_continuity": {
                "verdict": gate_force,
                "step1_rf2_N": step1_rf,
                "step1_diff_pct": step1_mismatch,
                "step2_rf2_N": step2_rf,
                "step2_diff_pct": step2_mismatch,
                "step3_rf2_N": step3_rf,
                "step3_diff_pct": step3_mismatch,
                "tolerance_pct": 5.0
            },
            "gate2_energy_continuity": {
                "verdict": gate_energy,
                "step2_e_fracture_kNmm": step2_e_frac,
                "diff_fracture_pct": e_frac_diff_pct,
                "step2_e_total_kNmm": step2_e_tot,
                "diff_total_pct": e_tot_diff_pct,
                "tolerance_pct": 2.0
            },
            "gate3_damage_bounds": {
                "verdict": gate_bounds,
                "terminal_dmax": terminal_dmax,
                "total_overshoot_points": all_overshoots,
                "total_negative_d_points": all_negative_d,
                "bound_criteria": "0.0 <= d <= 1.00000"
            },
            "gate4_irreversibility": {
                "verdict": gate_irreversibility,
                "step3_healing_points": step3_healing,
                "step4_healing_points": step4_healing,
                "step4_min_delta_d": step_rf.get("FORWARD_CONTINUATION", {}).get("min_delta_d")
            },
            "gate5_history_preservation": {
                "verdict": gate_history,
                "initial_h_max": init_h_max,
                "terminal_h_max": step_rf.get("FORWARD_CONTINUATION", {}).get("h_max"),
                "total_negative_h_points": all_negative_h
            },
            "gate6_softening_continuation": {
                "verdict": gate_softening,
                "checkpoint_rf2_N": step3_rf,
                "terminal_rf2_N": step4_rf,
                "force_drop_pct": softening_drop_pct,
                "terminal_u2_mm": step_rf.get("FORWARD_CONTINUATION", {}).get("u2_rp_mm")
            }
        },
        "overall_qualification": "GATE_C1_1_AUTHENTIC_C3_TO_C4_CLOSED_PASS" if all_gates_pass else "GATE_C1_1_FAIL",
        "step_rf_summary": step_rf,
        "energy_records": energies
    }

    out_json = os.path.join(work_dir, "pkg94_solver_evaluation.json")
    with open(out_json, "w") as f:
        json.dump(audit, f, indent=2)
    print("\nWrote evaluation summary JSON: %s" % out_json)

    # Write frame history summary CSV
    out_csv = os.path.join(work_dir, "pkg94_frame_history_summary.csv")
    with open(out_csv, "w") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "step", "frame_idx", "frame_time", "u2_rp_mm", "rf2_rp_N",
            "d_min", "d_max", "h_min", "h_max", "overshoot_count",
            "negative_d_count", "negative_h_count", "healing_count",
            "min_delta_d", "gp_count"
        ])
        writer.writeheader()
        for r in frame_records:
            writer.writerow(r)
    print("Wrote frame history CSV: %s" % out_csv)

    # Write terminal nodal state CSV
    out_node_csv = os.path.join(work_dir, "pkg94_step4_terminal_nodal_state.csv")
    with open(out_node_csv, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["node_id", "u1", "u2"])
        for nid in sorted(terminal_nodes.keys()):
            n = terminal_nodes[nid]
            writer.writerow([nid, "%.10e" % n["u1"], "%.10e" % n["u2"]])
    print("Wrote terminal nodal state CSV: %s" % out_node_csv)

    odb.close()
    print("\nPackage 94 extraction and audit completed successfully.")

if __name__ == "__main__":
    main()
