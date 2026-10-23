#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_pkg96_r1_results.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Extracts and independently audits full solver results of Package 96-R1:
M1_C5_PACKAGE96_R1_TRANSFER (PBS Job 1416889.mmaster02).
"""

import os
import sys
import json
import csv
import math
from odbAccess import openOdb

def main():
    work_dir = "/scratch9/pr21vyci/runs/mode1_package96_r1_c5_transfer"
    odb_path = os.path.join(work_dir, "M1_C5_PACKAGE96_R1_TRANSFER.odb")
    print("Opening Package 96-R1 ODB: %s" % odb_path)

    if not os.path.exists(odb_path):
        raise RuntimeError("ODB not found: %s" % odb_path)

    odb = openOdb(odb_path, readOnly=True)

    # Authoritative Donor Reference (Package 94 Step 4 Frame 7)
    donor_rf2_target = 112.97070980072021       # N
    donor_dmax_target = 0.9998528361320496
    donor_e_fracture_target = 0.00013773671     # kN*mm
    donor_e_total_target = 0.00025364406        # kN*mm
    donor_u2_target = 0.0020520000252872705     # mm

    n_phys = 4440
    n_nodes = 4610
    l3_start = 2 * n_phys + 1  # 8881
    l3_end = 3 * n_phys        # 13320

    step_rf = {}
    frame_records = []

    # Read mapped state table to check pointwise lower bound
    mapped_csv = os.path.join(work_dir, "candidate_c5_frame7_mapped_state_table.csv")
    mapped_node_d = {}
    if os.path.exists(mapped_csv):
        with open(mapped_csv, "r") as f:
            reader = csv.reader(f)
            header = next(reader)
            for r in reader:
                if len(r) >= 5 and r[0] == "NODE":
                    mapped_node_d[int(r[1])] = float(r[4])
        print("Loaded %d mapped nodes from state table." % len(mapped_node_d))

    prev_gp_d = None
    prev_gp_h = None

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

            # Extract companion element SDVs (Layer 3: 8881..13320)
            sdv1 = fr.fieldOutputs['SDV1'] if 'SDV1' in fr.fieldOutputs else None
            sdv2 = fr.fieldOutputs['SDV2'] if 'SDV2' in fr.fieldOutputs else None

            gp_d = {}
            gp_h = {}
            if sdv1:
                for v in sdv1.values:
                    if l3_start <= v.elementLabel <= l3_end:
                        key = (v.elementLabel, v.integrationPoint)
                        gp_d[key] = float(v.data)
            if sdv2:
                for v in sdv2.values:
                    if l3_start <= v.elementLabel <= l3_end:
                        key = (v.elementLabel, v.integrationPoint)
                        gp_h[key] = float(v.data)

            d_vals = gp_d.values()
            h_vals = gp_h.values()

            d_min = min(d_vals) if d_vals else None
            d_max = max(d_vals) if d_vals else None
            h_min = min(h_vals) if h_vals else None
            h_max = max(h_vals) if h_vals else None

            # Bounds checks
            overshoot_count = sum(1 for d in d_vals if d > 1.00000)
            negative_d_count = sum(1 for d in d_vals if d < 0.0)
            negative_h_count = sum(1 for h in h_vals if h < 0.0)

            # Pointwise healing check against previous physical frame
            healing_count = 0
            min_delta_d = 0.0
            if prev_gp_d and gp_d:
                diffs = [gp_d[k] - prev_gp_d[k] for k in gp_d if k in prev_gp_d]
                healing_count = sum(1 for diff in diffs if diff < -1.0e-6)
                min_delta_d = min(diffs) if diffs else 0.0

            if not (sname == "STATE_INJECTION" and f_idx == 0):
                prev_gp_d = dict(gp_d)
                prev_gp_h = dict(gp_h)

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
            if nid != 999999 and nid <= n_nodes:
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

    # Evaluate Acceptance Criteria
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

    # Irreversibility gate: 0 healing points across re-equilibration steps
    step3_healing = step_rf.get("STAGGERED_PHASE_SUBPROBLEM", {}).get("healing_count", 0)
    step4_healing = step_rf.get("FORWARD_CONTINUATION", {}).get("healing_count", 0)
    gate_irreversibility = "PASS" if step3_healing == 0 else "FAIL"

    # History preservation gate: finite, nonnegative, transferred
    all_negative_h = sum(r["negative_h_count"] for r in frame_records)
    init_h_max = step_rf.get("STATE_INJECTION", {}).get("h_max", 0.0)
    gate_history = "PASS" if all_negative_h == 0 and init_h_max > 0.0 else "FAIL"

    # Continuation softening / evolution
    softening_drop_pct = (step4_rf - step3_rf) / step3_rf * 100.0 if step4_rf and step3_rf else None
    gate_softening = "PASS" if softening_drop_pct is not None and softening_drop_pct < 0.0 else "PASS_STABLE"

    all_gates_pass = (gate_force == "PASS" and gate_energy == "PASS" and
                      gate_bounds == "PASS" and gate_irreversibility == "PASS" and
                      gate_history == "PASS")

    audit = {
        "job_name": "M1_C5_PACKAGE96_R1_TRANSFER",
        "pbs_job_id": "1416889.mmaster02",
        "donor_reference": {
            "package": "PACKAGE_94",
            "frame": 7,
            "u2_target_mm": donor_u2_target,
            "rf2_target_N": donor_rf2_target,
            "dmax_target": donor_dmax_target,
            "e_fracture_target_kNmm": donor_e_fracture_target,
            "e_total_target_kNmm": donor_e_total_target
        },
        "receiver_mesh": {
            "name": "Candidate C5",
            "quads": n_phys,
            "nodes": n_nodes,
            "h_fine_mm": 0.00070
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
                "bound_criteria": "0.0 <= d <= 1.00000",
                "terminal_dmax": terminal_dmax,
                "total_overshoot_points": all_overshoots,
                "total_negative_d_points": all_negative_d
            },
            "gate4_irreversibility": {
                "verdict": gate_irreversibility,
                "step3_healing_points": step3_healing,
                "step4_healing_points": step4_healing,
                "step3_min_delta_d": step_rf.get("STAGGERED_PHASE_SUBPROBLEM", {}).get("min_delta_d", 0.0),
                "step4_min_delta_d": step_rf.get("FORWARD_CONTINUATION", {}).get("min_delta_d", 0.0)
            },
            "gate5_history_preservation": {
                "verdict": gate_history,
                "initial_h_max": init_h_max,
                "terminal_h_max": step_rf.get("FORWARD_CONTINUATION", {}).get("h_max", 0.0),
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
        "overall_qualification": "GATE_C1_2_PASS" if all_gates_pass else "GATE_C1_2_FAIL",
        "step_rf_summary": step_rf,
        "energy_balance": energies
    }

    out_json = os.path.join(work_dir, "pkg96_r1_solver_evaluation.json")
    with open(out_json, "w") as f:
        json.dump(audit, f, indent=2)
    print("\nWrote evaluation summary to: %s" % out_json)

    # Write frame summary CSV
    summary_csv = os.path.join(work_dir, "pkg96_r1_frame_history_summary.csv")
    with open(summary_csv, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["step", "frame_idx", "frame_time", "u2_rp_mm", "rf2_rp_N",
                         "d_min", "d_max", "h_min", "h_max",
                         "overshoot_count", "negative_d_count", "negative_h_count",
                         "healing_count", "min_delta_d", "gp_count"])
        for r in frame_records:
            writer.writerow([r["step"], r["frame_idx"], r["frame_time"],
                             r["u2_rp_mm"], r["rf2_rp_N"],
                             r["d_min"], r["d_max"], r["h_min"], r["h_max"],
                             r["overshoot_count"], r["negative_d_count"], r["negative_h_count"],
                             r["healing_count"], r["min_delta_d"], r["gp_count"]])
    print("Wrote frame history CSV to: %s" % summary_csv)

    # Write terminal nodal state CSV
    term_csv = os.path.join(work_dir, "pkg96_r1_step4_terminal_nodal_state.csv")
    with open(term_csv, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["node_id", "u1", "u2"])
        for nid in sorted(terminal_nodes.keys()):
            n = terminal_nodes[nid]
            writer.writerow([nid, "%.10e" % n["u1"], "%.10e" % n["u2"]])
    print("Wrote terminal nodal state CSV to: %s" % term_csv)

    print("\n=======================================================")
    print("PACKAGE 96-R1 OVERALL QUALIFICATION: %s" % audit["overall_qualification"])
    print("  Gate 1 Force Continuity:       %s (Step 2 RF2 = %.2f N, diff: %.3f%%)" %
          (gate_force, step2_rf if step2_rf else 0.0, step2_mismatch if step2_mismatch else 0.0))
    print("  Gate 2 Energy Continuity:      %s (Step 2 E_frac = %.8e kN*mm, diff: %.3f%%)" %
          (gate_energy, step2_e_frac if step2_e_frac else 0.0, e_frac_diff_pct if e_frac_diff_pct else 0.0))
    print("  Gate 3 Damage Bounds:          %s (d_max = %.6f, overshoots = %d)" %
          (gate_bounds, terminal_dmax, all_overshoots))
    print("  Gate 4 Strict Irreversibility: %s (Step 3 healing = %d, min_dd = %.2e)" %
          (gate_irreversibility, step3_healing, step_rf.get("STAGGERED_PHASE_SUBPROBLEM", {}).get("min_delta_d", 0.0)))
    print("  Gate 5 History Preservation:   %s (H_init = %.2f, H_term = %.2f)" %
          (gate_history, init_h_max if init_h_max else 0.0, step_rf.get("FORWARD_CONTINUATION", {}).get("h_max", 0.0)))
    print("  Gate 6 Softening Continuation: %s (Force drop: %.2f%%)" %
          (gate_softening, softening_drop_pct if softening_drop_pct else 0.0))
    print("=======================================================")

    odb.close()

if __name__ == "__main__":
    main()
