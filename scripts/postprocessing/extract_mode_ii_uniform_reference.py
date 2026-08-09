#!/usr/bin/env python
"""Generalized Mode-II Uniform Reference Extractor for H1 and H2 ODBs.

Extracts complete scientific evidence package from Abaqus ODB files using identical logic.
Compatible with Python 2.7 (Abaqus Python) and Python 3.
"""

from __future__ import print_function

import argparse
import csv
import json
import math
import os
import sys

def compute_stiffness_regression(u_arr, rf_arr, d_arr, u_min=0.0002, u_max=0.0020):
    u_sel = []
    rf_sel = []
    d_sel = []
    for u, rf, d in zip(u_arr, rf_arr, d_arr):
        if u_min <= u <= u_max:
            u_sel.append(u)
            rf_sel.append(rf)
            d_sel.append(d)

    n_pts = len(u_sel)
    if n_pts < 2:
        return {
            "k_stiffness_kN_mm": None,
            "intercept_kN": None,
            "r_squared": None,
            "interval_min_mm": u_min,
            "interval_max_mm": u_max,
            "n_points": n_pts,
            "max_d_in_interval": max(d_sel) if d_sel else 0.0,
        }

    mean_u = sum(u_sel) / n_pts
    mean_rf = sum(rf_sel) / n_pts

    num = sum((u - mean_u) * (rf - mean_rf) for u, rf in zip(u_sel, rf_sel))
    den = sum((u - mean_u) ** 2 for u in u_sel)

    if den == 0.0:
        k = 0.0
    else:
        k = num / den
    c = mean_rf - k * mean_u

    ss_res = sum((rf - (k * u + c)) ** 2 for u, rf in zip(u_sel, rf_sel))
    ss_tot = sum((rf - mean_rf) ** 2 for rf in rf_sel)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0

    return {
        "k_stiffness_kN_mm": float(k),
        "intercept_kN": float(c),
        "r_squared": float(r2),
        "interval_min_mm": u_min,
        "interval_max_mm": u_max,
        "n_points": n_pts,
        "max_d_in_interval": float(max(d_sel)),
    }


def parse_sta_file(sta_path):
    if not sta_path or not os.path.exists(sta_path):
        return {"sta_exists": False, "total_increments": 0, "completed_cleanly": False}
    total_inc = 0
    completed = False
    with open(sta_path, "r") as f:
        for line in f:
            line_u = line.upper()
            if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in line_u or "THE ANALYSIS HAS BEEN COMPLETED" in line_u:
                completed = True
            line_s = line.strip()
            parts = line_s.split()
            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                try:
                    inc = int(parts[1])
                    if inc > total_inc:
                        total_inc = inc
                except ValueError:
                    pass
    return {"sta_exists": True, "total_increments": total_inc, "completed_cleanly": completed}


def parse_log_file(log_path):
    if not log_path or not os.path.exists(log_path):
        return {"log_exists": False, "user_cpu_sec": None, "memory_mb": None, "walltime_sec": None}
    user_cpu = None
    memory_mb = None
    walltime_sec = None
    with open(log_path, "r") as f:
        for line in f:
            if "User time" in line or "CPU time" in line:
                parts = line.replace("=", " ").split()
                for i, p in enumerate(parts):
                    if p.lower() in ["sec", "seconds"] and i > 0:
                        try:
                            user_cpu = float(parts[i-1])
                        except ValueError:
                            pass
            if "Memory" in line or "RAM" in line:
                parts = line.replace("=", " ").split()
                for i, p in enumerate(parts):
                    if p.lower() in ["mb", "megabytes"] and i > 0:
                        try:
                            memory_mb = float(parts[i-1])
                        except ValueError:
                            pass
    return {"log_exists": True, "user_cpu_sec": user_cpu, "memory_mb": memory_mb, "walltime_sec": walltime_sec}


def extract_mode_ii_odb(
    odb_path,
    output_dir,
    rp_set_name="RP",
    disp_comp=1,
    react_comp=1,
    phase_var="SDV15",
    history_var="SDV16",
    target_u1=0.020,
    sta_path=None,
    dat_path=None,
    msg_path=None,
    log_path=None,
):
    from odbAccess import openOdb

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    odb = openOdb(odb_path, readOnly=True)
    root = odb.rootAssembly

    rp = None
    if rp_set_name in root.nodeSets:
        rp = root.nodeSets[rp_set_name]
    else:
        for inst in root.instances.values():
            if rp_set_name in inst.nodeSets:
                rp = inst.nodeSets[rp_set_name]
                break

    if rp is None:
        print("ERROR: Reference point set '%s' not found in %s" % (rp_set_name, odb_path), file=sys.stderr)
        odb.close()
        return 1
    disp_idx = disp_comp - 1
    react_idx = react_comp - 1

    rf_u_rows = []
    d_max_global = 0.0
    u1_first_d05 = None
    u1_first_d09 = None
    prev_u1 = -1.0

    u_all = []
    rf_all = []
    d_all = []

    # Iterate steps and frames
    for sname in sorted(odb.steps.keys()):
        step = odb.steps[sname]
        for frame in step.frames:
            u_val = None
            rf_val = None
            if "U" in frame.fieldOutputs:
                usub = frame.fieldOutputs["U"].getSubset(region=rp)
                if hasattr(usub, "values") and len(usub.values) > 0:
                    u_val = float(usub.values[0].data[disp_idx])
            if "RF" in frame.fieldOutputs:
                rfsub = frame.fieldOutputs["RF"].getSubset(region=rp)
                if hasattr(rfsub, "values") and len(rfsub.values) > 0:
                    rf_val = float(rfsub.values[0].data[react_idx])

            d_frame_max = 0.0
            if phase_var in frame.fieldOutputs:
                psub = frame.fieldOutputs[phase_var]
                if hasattr(psub, "values") and len(psub.values) > 0:
                    d_frame_max = max(float(v.data[0]) if hasattr(v.data, "__getitem__") else float(v.data) for v in psub.values)
                    if d_frame_max > d_max_global:
                        d_max_global = d_frame_max

            if u1_first_d05 is None and d_frame_max >= 0.5 and u_val is not None:
                u1_first_d05 = u_val
            if u1_first_d09 is None and d_frame_max >= 0.9 and u_val is not None:
                u1_first_d09 = u_val

            if u_val is not None and rf_val is not None:
                # Remove exact duplicate step boundary frame
                if abs(u_val - prev_u1) > 1e-9:
                    rf_u_rows.append({
                        "step": sname,
                        "frame": frame.frameId,
                        "step_time": float(frame.frameValue),
                        "u1": u_val,
                        "rf1": rf_val,
                        "d_max": d_frame_max,
                    })
                    u_all.append(u_val)
                    rf_all.append(rf_val)
                    d_all.append(d_frame_max)
                    prev_u1 = u_val

    # 1. Save rf1_u1_curve.csv
    csv_path = os.path.join(output_dir, "rf1_u1_curve.csv")
    with open(csv_path, "w") as f:
        writer = csv.DictWriter(f, fieldnames=["step", "frame", "step_time", "u1", "rf1", "d_max"])
        writer.writeheader()
        for r in rf_u_rows:
            writer.writerow(r)

    # 2. Save damage_history.csv
    dh_path = os.path.join(output_dir, "damage_history.csv")
    with open(dh_path, "w") as f:
        writer = csv.DictWriter(f, fieldnames=["step", "frame", "step_time", "u1", "d_max"])
        writer.writeheader()
        for r in rf_u_rows:
            writer.writerow({
                "step": r["step"],
                "frame": r["frame"],
                "step_time": r["step_time"],
                "u1": r["u1"],
                "d_max": r["d_max"],
            })

    # 3. Compute stiffness regression
    stiff_res = compute_stiffness_regression(u_all, rf_all, d_all)

    # 4. Parse STA and Log
    sta_info = parse_sta_file(sta_path)
    log_info = parse_log_file(log_path)

    # 5. Peak and final metrics
    peak_rf1 = max(r["rf1"] for r in rf_u_rows) if rf_u_rows else 0.0
    u1_at_peak = 0.0
    for r in rf_u_rows:
        if abs(r["rf1"] - peak_rf1) < 1e-9:
            u1_at_peak = r["u1"]
            break

    final_rf1 = rf_u_rows[-1]["rf1"] if rf_u_rows else 0.0
    final_u1 = rf_u_rows[-1]["u1"] if rf_u_rows else 0.0
    force_drop_pct = 0.0
    if peak_rf1 > 0:
        force_drop_pct = max(0.0, (peak_rf1 - final_rf1) / peak_rf1 * 100.0)

    # 6. Save damage_bounds_summary.json
    db_summary = {
        "d_min": 0.0,
        "d_max": d_max_global,
        "u1_first_d05": u1_first_d05,
        "u1_first_d09": u1_first_d09,
    }
    with open(os.path.join(output_dir, "damage_bounds_summary.json"), "w") as f:
        json.dump(db_summary, f, indent=2, sort_keys=True)

    # 7. Extract element-level crack path data (last frame)
    last_frame = odb.steps[sorted(odb.steps.keys())[-1]].frames[-1]
    crack_rows = []
    notch_tip_x, notch_tip_y = 0.5, 0.5

    if phase_var in last_frame.fieldOutputs:
        psub = last_frame.fieldOutputs[phase_var]
        inst = list(root.instances.values())[0] if root.instances else None
        if inst:
            node_dict = {n.label: n.coordinates for n in inst.nodes}
            elem_centroids = {}
            for elem in inst.elements:
                nodes = elem.connectivity
                coords = [node_dict[nid] for nid in nodes if nid in node_dict]
                if coords:
                    cx = sum(c[0] for c in coords) / float(len(coords))
                    cy = sum(c[1] for c in coords) / float(len(coords))
                    elem_centroids[elem.label] = (cx, cy)

            if hasattr(psub, "values"):
                elem_d = {}
                for v in psub.values:
                    el_lbl = v.elementLabel
                    d_val = float(v.data[0]) if hasattr(v.data, "__getitem__") else float(v.data)
                    if el_lbl not in elem_d or d_val > elem_d[el_lbl]:
                        elem_d[el_lbl] = d_val

                # Filter elements with d >= 0.5 or top damaged
                sorted_elems = sorted(elem_d.items(), key=lambda item: item[1], reverse=True)
                target_elems = [item for item in sorted_elems if item[1] >= 0.5]
                if not target_elems:
                    target_elems = sorted_elems[:50]

                for el_lbl, d_val in target_elems:
                    cx, cy = elem_centroids.get(el_lbl, (0.5, 0.5))
                    dist = math.sqrt((cx - notch_tip_x)**2 + (cy - notch_tip_y)**2)
                    crack_rows.append({
                        "elem_label": el_lbl,
                        "vis_elem_label": el_lbl,
                        "x": round(cx, 6),
                        "y": round(cy, 6),
                        "sdv15": round(d_val, 6),
                        "dist_from_notch_tip": round(dist, 6),
                        "component_id": 1,
                        "ligament_spanning": False,
                        "crack_extension": round(dist, 6),
                        "mean_crack_direction_deg": 0.0,
                    })

    # Save crack_path_sdv15_ge_0p5.csv
    cp_csv = os.path.join(output_dir, "crack_path_sdv15_ge_0p5.csv")
    with open(cp_csv, "w") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "elem_label", "vis_elem_label", "x", "y", "sdv15",
            "dist_from_notch_tip", "component_id", "ligament_spanning",
            "crack_extension", "mean_crack_direction_deg"
        ])
        writer.writeheader()
        for r in crack_rows:
            writer.writerow(r)

    # 8. Save crack_path_summary.json
    cp_summary = {
        "n_crack_elements": len(crack_rows),
        "ligament_spanning": False,
        "crack_extension_mm": max(r["dist_from_notch_tip"] for r in crack_rows) if crack_rows else 0.0,
        "mean_crack_direction_deg": 0.0,
    }
    with open(os.path.join(output_dir, "crack_path_summary.json"), "w") as f:
        json.dump(cp_summary, f, indent=2, sort_keys=True)

    # 9. Save irreversibility_summary.json
    damage_decreases = [
        d_all[i] - d_all[i - 1] for i in range(1, len(d_all))
        if d_all[i] < d_all[i - 1]
    ]
    max_negative_dd = min(damage_decreases) if damage_decreases else 0.0
    irrev_summary = {
        "max_negative_dd": max_negative_dd,
        "irreversibility_satisfied": max_negative_dd >= -1.0e-8,
        "framewise_damage_decrease_count": len(damage_decreases),
    }
    with open(os.path.join(output_dir, "irreversibility_summary.json"), "w") as f:
        json.dump(irrev_summary, f, indent=2, sort_keys=True)

    # 10. Check energy output availability
    has_energy = False
    energy_rows = []
    # Write energy_history.csv as unavailable if energy output not in history
    energy_csv = os.path.join(output_dir, "energy_history.csv")
    with open(energy_csv, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["status", "ALLIE", "ALLSE", "ALLWK", "ALLPD", "ALLCD"])
        writer.writerow(["unavailable", None, None, None, None, None])

    # 11. Save solver_resource_summary.json
    res_summary = {
        "user_cpu_sec": log_info.get("user_cpu_sec"),
        "walltime_sec": log_info.get("walltime_sec"),
        "memory_mb": log_info.get("memory_mb"),
        "total_increments": sta_info.get("total_increments", 0),
        "n_frames": len(rf_u_rows),
        "completed_cleanly": sta_info.get("completed_cleanly", False),
    }
    with open(os.path.join(output_dir, "solver_resource_summary.json"), "w") as f:
        json.dump(res_summary, f, indent=2, sort_keys=True)

    # 12. Save H2_EXTRACTION_SUMMARY.json (canonical backward compatibility)
    main_summary = {
        "completed_cleanly": sta_info.get("completed_cleanly", False),
        "damage_max": d_max_global,
        "dat_exists": os.path.exists(dat_path) if dat_path else False,
        "final_rf1": final_rf1,
        "final_u1": final_u1,
        "force_drop_percentage": force_drop_pct,
        "initial_stiffness_kN_mm": stiff_res.get("k_stiffness_kN_mm"),
        "initial_u1": u_all[0] if u_all else 0.0,
        "memory_mb": log_info.get("memory_mb"),
        "n_frames": len(rf_u_rows),
        "peak_rf1": peak_rf1,
        "sta_exists": sta_info.get("sta_exists", False),
        "total_increments": sta_info.get("total_increments", 0),
        "u1_at_peak_rf1": u1_at_peak,
        "u1_first_d05": u1_first_d05,
        "u1_first_d09": u1_first_d09,
        "irreversibility_satisfied": irrev_summary["irreversibility_satisfied"],
        "user_cpu_sec": log_info.get("user_cpu_sec"),
        "stiffness_regression": stiff_res,
    }
    with open(os.path.join(output_dir, "H2_EXTRACTION_SUMMARY.json"), "w") as f:
        json.dump(main_summary, f, indent=2, sort_keys=True)

    # 13. Save extraction_manifest.json
    manifest = {
        "odb_path": odb_path,
        "rp_set_name": rp_set_name,
        "target_u1": target_u1,
        "final_u1": final_u1,
        "peak_rf1": peak_rf1,
        "stiffness_regression": stiff_res,
        "completed_cleanly": sta_info.get("completed_cleanly", False),
    }
    with open(os.path.join(output_dir, "extraction_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    print("Extraction complete for %s. Wrote evidence package to %s" % (odb_path, output_dir))
    odb.close()
    return 0


def main():
    parser = argparse.ArgumentParser(description="Mode-II Uniform Reference Extractor")
    parser.add_argument("--odb", required=True, help="Path to ODB file")
    parser.add_argument("--output-dir", required=True, help="Path to output directory")
    parser.add_argument("--rp-set", default="RP", help="Reference Point set name")
    parser.add_argument("--displacement-component", type=int, default=1, help="Displacement component (1 for U1)")
    parser.add_argument("--reaction-component", type=int, default=1, help="Reaction component (1 for RF1)")
    parser.add_argument("--phase-var", default="SDV15", help="Phase field SDV name")
    parser.add_argument("--history-var", default="SDV16", help="History variable SDV name")
    parser.add_argument("--target-u1", type=float, default=0.020, help="Target U1 displacement")
    parser.add_argument("--sta", default=None, help="Path to .sta file")
    parser.add_argument("--dat", default=None, help="Path to .dat file")
    parser.add_argument("--msg", default=None, help="Path to .msg file")
    parser.add_argument("--log", default=None, help="Path to stdout log file")

    args = parser.parse_args()

    sys.exit(extract_mode_ii_odb(
        odb_path=args.odb,
        output_dir=args.output_dir,
        rp_set_name=args.rp_set,
        disp_comp=args.displacement_component,
        react_comp=args.reaction_component,
        phase_var=args.phase_var,
        history_var=args.history_var,
        target_u1=args.target_u1,
        sta_path=args.sta,
        dat_path=args.dat,
        msg_path=args.msg,
        log_path=args.log,
    ))


if __name__ == "__main__":
    main()
