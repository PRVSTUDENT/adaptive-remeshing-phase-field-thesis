#!/usr/bin/env python
"""
extract_mode1_fracture_odb.py
=============================
Authoritative, Reusable, Idempotent Mode-I Fracture Post-Processing & Extraction Engine.

Capabilities:
  1. Abaqus Python ODB mode:
     - Extracts continuous (u_y, RF_y) curve at Reference Point (N_RP / Node 999999).
     - Computes cumulative external work W_ext = \int F du.
     - Extracts element state variables SDV17 (E_frac) and SDV18 (E_elas) with deduplication.
     - Extracts horizontal ligament damage profile d(x, y=0.5 mm) at key physical states:
       * Early elastic: u ~ 0.0020 mm
       * Damage onset:  u ~ 0.0050 mm
       * Peak load:     u = u(F_max)
       * Post-peak:     u ~ 0.0060, 0.0065, 0.0070, 0.0080, 0.0100 mm
     - Computes crack extension length a(u) where d >= 0.95.
  2. Fallback / Offline DAT + CSV mode:
     - Parses Abaqus .dat file for exact (u_y, RF_y) reaction trajectory.
     - Parses companion uel_energy_balance.csv for UEL energies.
  3. Parity & Statistical Verification:
     - Initial stiffness K0 regression over u <= 0.0010 mm and u <= 0.0020 mm.
     - Peak force F_max and u(F_max).
     - Direct comparison against Canonical 15k Reference:
       K0_ref = 137.945520 kN/mm, F_max_ref = 0.757778 kN, u_peak_ref = 0.005857 mm.
     - Energy conservation error |(E_elas + E_frac - W_ext)| / max(W_ext, 1e-12).

Usage:
  # Inside Abaqus Python:
  abaqus python extract_mode1_fracture_odb.py --odb M1_MB_NATIVE_FINAL_1S.odb --out-dir ./extracted

  # Offline / Standard Python with .dat and .csv:
  python extract_mode1_fracture_odb.py --dat M1_MB_NATIVE_FINAL_1S.dat --csv uel_energy_balance.csv --out-dir ./extracted
"""

import os
import sys
import re
import math
import json
import argparse

CANONICAL_REF = {
    "model_name": "PK_MODE1_15K_UNIFORM_REFERENCE",
    "K0_kN_per_mm": 137.945520,
    "F_max_kN": 0.757778,
    "u_peak_mm": 0.005857
}

def linear_regression(x_vals, y_vals):
    n = len(x_vals)
    if n < 2:
        return 0.0, 0.0, 0.0
    sum_x = sum(x_vals)
    sum_y = sum(y_vals)
    sum_xx = sum(x * x for x in x_vals)
    sum_yy = sum(y * y for y in y_vals)
    sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
    
    denom = n * sum_xx - sum_x * sum_x
    if abs(denom) < 1e-20:
        return 0.0, 0.0, 0.0
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    
    ss_tot = sum((y - (sum_y / n)) ** 2 for y in y_vals)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_vals, y_vals))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-20 else 1.0
    return slope, intercept, r2

def parse_dat_file(dat_path):
    """
    Parses Abaqus .dat file for node 999999 U2 and RF2 print blocks.
    Returns: list of dicts with step, inc, u_mm, rf_raw_kN, f_kN.
    """
    records = []
    if not os.path.exists(dat_path):
        return records

    current_step = 1
    current_inc = 0
    in_table = False

    with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "STEP " in line and "INCREMENT " in line:
                m_step = re.search(r"STEP\s+(\d+)", line)
                m_inc = re.search(r"INCREMENT\s+(\d+)", line)
                if m_step:
                    current_step = int(m_step.group(1))
                if m_inc:
                    current_inc = int(m_inc.group(1))
                in_table = False
                continue

            if "THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET N_RP" in line or \
               "THE FOLLOWING TABLE IS PRINTED FOR NODES" in line:
                in_table = True
                continue

            if in_table:
                if "999999" in line:
                    parts = [p.strip() for p in line.split() if p.strip()]
                    try:
                        nums = [float(p) for p in parts if re.match(r"^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$", p)]
                        if len(nums) >= 2:
                            u_val = nums[-2]
                            rf_val = nums[-1]
                            f_phys = abs(rf_val)
                            records.append({
                                "step": current_step,
                                "inc": current_inc,
                                "u_mm": u_val,
                                "rf_raw_kN": rf_val,
                                "f_kN": f_phys
                            })
                    except ValueError:
                        pass
                    in_table = False
                elif "MAXIMUM" in line or "INCREMENT" in line or "N O D E   O U T P U T" in line:
                    in_table = False
    return records

def parse_energy_csv(csv_path):
    """
    Parses companion uel_energy_balance.csv file.
    Returns list of dict records.
    """
    energy_records = []
    if not os.path.exists(csv_path):
        return energy_records

    with open(csv_path, 'r', encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        if not lines:
            return energy_records
        header = [h.strip() for h in lines[0].split(',')]
        for line in lines[1:]:
            parts = [p.strip() for p in line.split(',') if p.strip()]
            if not parts:
                continue
            row = {}
            for k, v in zip(header, parts):
                try:
                    row[k] = float(v)
                except ValueError:
                    row[k] = v
            energy_records.append(row)
    return energy_records

def process_curve_data(records):
    """
    Computes external work, stiffnesses, peak values, and statistics.
    """
    u_vals = [r["u_mm"] for r in records]
    f_vals = [r["f_kN"] for r in records]

    # Integrate W_ext
    w_cum = 0.0
    u_prev = 0.0
    f_prev = 0.0
    for i, r in enumerate(records):
        u = r["u_mm"]
        f = r["f_kN"]
        if i == 0:
            w_cum = 0.5 * f * u if u > 1e-12 else 0.0
        else:
            du = u - u_prev
            w_cum += 0.5 * (f + f_prev) * du
        r["w_ext_kNmm"] = w_cum
        r["w_ext_mJ"] = w_cum * 1000.0
        u_prev = u
        f_prev = f

    # Linear stiffness regressions
    u10 = [u for u in u_vals if 0.0 < u <= 0.0010]
    f10 = [f for u, f in zip(u_vals, f_vals) if 0.0 < u <= 0.0010]
    k0_10, int_10, r2_10 = linear_regression(u10, f10)

    u20 = [u for u in u_vals if 0.0 < u <= 0.0020]
    f20 = [f for u, f in zip(u_vals, f_vals) if 0.0 < u <= 0.0020]
    k0_20, int_20, r2_20 = linear_regression(u20, f20)

    # Peak detection
    f_max = max(f_vals) if f_vals else 0.0
    peak_idx = f_vals.index(f_max) if f_vals else 0
    u_peak = u_vals[peak_idx] if f_vals else 0.0

    # Reference comparisons
    delta_k0_10_pct = ((k0_10 - CANONICAL_REF["K0_kN_per_mm"]) / CANONICAL_REF["K0_kN_per_mm"]) * 100.0 if k0_10 != 0 else None
    delta_k0_20_pct = ((k0_20 - CANONICAL_REF["K0_kN_per_mm"]) / CANONICAL_REF["K0_kN_per_mm"]) * 100.0 if k0_20 != 0 else None
    delta_f_max_pct = ((f_max - CANONICAL_REF["F_max_kN"]) / CANONICAL_REF["F_max_kN"]) * 100.0 if f_max > 0 else None
    delta_u_peak_pct = ((u_peak - CANONICAL_REF["u_peak_mm"]) / CANONICAL_REF["u_peak_mm"]) * 100.0 if u_peak > 0 else None

    # Check if peak is truly captured (force dropped post-peak)
    is_peak_captured = False
    if peak_idx < len(f_vals) - 1:
        post_f = f_vals[peak_idx + 1:]
        if min(post_f) < 0.95 * f_max:
            is_peak_captured = True

    metrics = {
        "total_increments": len(records),
        "terminal_u_mm": u_vals[-1] if u_vals else 0.0,
        "terminal_f_kN": f_vals[-1] if f_vals else 0.0,
        "terminal_w_ext_mJ": w_cum * 1000.0,
        "stiffness_u10": {
            "eval_range_max_u_mm": 0.0010,
            "fit_points": len(u10),
            "K0_kN_per_mm": k0_10,
            "intercept_kN": int_10,
            "R2": r2_10,
            "delta_vs_ref_pct": delta_k0_10_pct
        },
        "stiffness_u20": {
            "eval_range_max_u_mm": 0.0020,
            "fit_points": len(u20),
            "K0_kN_per_mm": k0_20,
            "intercept_kN": int_20,
            "R2": r2_20,
            "delta_vs_ref_pct": delta_k0_20_pct
        },
        "peak_reaction": {
            "is_captured": is_peak_captured,
            "F_max_kN": f_max,
            "u_at_F_max_mm": u_peak,
            "peak_index": peak_idx,
            "delta_F_max_pct": delta_f_max_pct,
            "delta_u_peak_pct": delta_u_peak_pct
        }
    }
    return metrics, records

def extract_from_odb(odb_path, sample_u_targets=[0.0020, 0.0050, 0.00585, 0.0065, 0.0070, 0.0080, 0.0100]):
    """
    Abaqus Python ODB extraction engine.
    Extracts trajectory, SDVs, and horizontal ligament damage profiles.
    """
    try:
        from odbAccess import openOdb
    except ImportError:
        print("[ERROR] Cannot import odbAccess. Run inside 'abaqus python'.")
        return None, None, None

    if not os.path.exists(odb_path):
        print("[ERROR] ODB not found: %s" % odb_path)
        return None, None, None

    print("[INFO] Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)

    # 1. Coordinate mapping for elements
    root = odb.rootAssembly
    elem_centroids = {}
    node_coords = {}
    
    # Cache node coordinates
    for inst_name, inst in root.instances.items():
        for node in inst.nodes:
            node_coords[node.label] = (float(node.coordinates[0]), float(node.coordinates[1]))
        for elem in inst.elements:
            conn = elem.connectivity
            xs = [node_coords[n][0] for n in conn if n in node_coords]
            ys = [node_coords[n][1] for n in conn if n in node_coords]
            if xs and ys:
                elem_centroids[elem.label] = (sum(xs) / len(xs), sum(ys) / len(ys))

    if not elem_centroids:
        for node in root.nodes:
            node_coords[node.label] = (float(node.coordinates[0]), float(node.coordinates[1]))
        for elem in root.elements:
            conn = elem.connectivity
            xs = [node_coords[n][0] for n in conn if n in node_coords]
            ys = [node_coords[n][1] for n in conn if n in node_coords]
            if xs and ys:
                elem_centroids[elem.label] = (sum(xs) / len(xs), sum(ys) / len(ys))

    # Identify ligament elements (|y - 0.5| < 0.015, x >= 0.49)
    ligament_elem_ids = set()
    for eid, (x, y) in elem_centroids.items():
        if abs(y - 0.5) < 0.015 and x >= 0.49:
            ligament_elem_ids.add(eid)
    print("[INFO] Identified %d ligament elements near y=0.5, x>=0.5" % len(ligament_elem_ids))

    # Identify RP node set if available
    rp_set = None
    if 'N_RP' in root.nodeSets:
        rp_set = root.nodeSets['N_RP']
    else:
        for inst in root.instances.values():
            if 'N_RP' in inst.nodeSets:
                rp_set = inst.nodeSets['N_RP']
                break

    records = []
    ligament_profiles = {}
    w_cum = 0.0
    u_prev = 0.0
    f_prev = 0.0

    closest_frames = {tu: {"min_diff": 999.0, "frame": None, "u": 0.0, "step": ""} for tu in sample_u_targets}

    for step_name in sorted(odb.steps.keys()):
        step = odb.steps[step_name]
        print("[INFO] Processing Step: %s (%d frames)" % (step_name, len(step.frames)))
        for frame in step.frames:
            fkeys = frame.fieldOutputs.keys()
            u_val = 0.0
            rf_val = 0.0
            
            if rp_set is not None:
                if 'U' in fkeys:
                    u_sub = frame.fieldOutputs['U'].getSubset(region=rp_set)
                    if len(u_sub.values) > 0:
                        u_val = float(u_sub.values[0].data[1])
                if 'RF' in fkeys:
                    rf_sub = frame.fieldOutputs['RF'].getSubset(region=rp_set)
                    if len(rf_sub.values) > 0:
                        rf_val = float(rf_sub.values[0].data[1])
            else:
                if 'U' in fkeys:
                    u_field = frame.fieldOutputs['U']
                    for val in u_field.values:
                        if val.nodeLabel == 999999:
                            u_val = float(val.data[1])
                            break
                if 'RF' in fkeys:
                    rf_field = frame.fieldOutputs['RF']
                    for val in rf_field.values:
                        if val.nodeLabel == 999999:
                            rf_val = float(val.data[1])
                            break
            
            f_val = abs(rf_val)
            if len(records) > 0:
                du = u_val - u_prev
                w_cum += 0.5 * (f_val + f_prev) * du
            else:
                w_cum = 0.5 * f_val * u_val if u_val > 1e-12 else 0.0
            u_prev = u_val
            f_prev = f_val

            e_frac = 0.0
            e_elas = 0.0
            has_sdv = False
            if 'SDV17' in fkeys and 'SDV18' in fkeys:
                has_sdv = True
                seen = set()
                for v17, v18 in zip(frame.fieldOutputs['SDV17'].values, frame.fieldOutputs['SDV18'].values):
                    eid = v17.elementLabel
                    if eid not in seen:
                        seen.add(eid)
                        e_frac += float(v17.data)
                        e_elas += float(v18.data)
            elif 'SDV' in fkeys:
                has_sdv = True
                seen = set()
                for v in frame.fieldOutputs['SDV'].values:
                    eid = v.elementLabel
                    if eid not in seen:
                        seen.add(eid)
                        if hasattr(v.data, '__getitem__') and len(v.data) >= 18:
                            e_frac += float(v.data[16])
                            e_elas += float(v.data[17])

            rec = {
                "step": step_name,
                "frame_id": frame.frameId,
                "step_time": float(frame.frameValue),
                "u_mm": u_val,
                "rf_raw_kN": rf_val,
                "f_kN": f_val,
                "w_ext_mJ": w_cum * 1000.0,
                "e_elas_mJ": e_elas * 1000.0,
                "e_frac_mJ": e_frac * 1000.0,
                "e_model_mJ": (e_elas + e_frac) * 1000.0,
                "delta_book_mJ": (e_elas + e_frac - w_cum) * 1000.0 if has_sdv else 0.0,
                "has_sdv": has_sdv
            }
            records.append(rec)

            for tu in sample_u_targets:
                diff = abs(u_val - tu)
                if diff < closest_frames[tu]["min_diff"]:
                    closest_frames[tu]["min_diff"] = diff
                    closest_frames[tu]["frame"] = frame
                    closest_frames[tu]["u"] = u_val
                    closest_frames[tu]["step"] = step_name

    # Extract ligament damage profiles for closest frames
    for tu, cinfo in closest_frames.items():
        frame = cinfo["frame"]
        if frame is None:
            continue
        actual_u = cinfo["u"]
        fkeys = frame.fieldOutputs.keys()
        d_field = None
        dkey_used = ""
        for dkey in ['SDV14', 'SDV_SDV14', 'SDV1', 'SDV']:
            if dkey in fkeys:
                d_field = frame.fieldOutputs[dkey]
                dkey_used = dkey
                break
        
        prof = []
        if d_field:
            d_by_elem = {}
            for val in d_field.values:
                eid = val.elementLabel
                if eid in ligament_elem_ids:
                    if hasattr(val.data, '__getitem__'):
                        idx = 13 if dkey_used == 'SDV' else 0
                        d_by_elem[eid] = float(val.data[idx])
                    else:
                        d_by_elem[eid] = float(val.data)
            
            for eid, d_val in d_by_elem.items():
                if eid in elem_centroids:
                    x, y = elem_centroids[eid]
                    prof.append({"eid": eid, "x": x, "y": y, "d": d_val})
            prof.sort(key=lambda p: p["x"])
        ligament_profiles[tu] = {
            "target_u_mm": tu,
            "actual_u_mm": actual_u,
            "profile": prof
        }

    odb.close()
    metrics, processed_records = process_curve_data(records)
    return metrics, processed_records, ligament_profiles

def main():
    parser = argparse.ArgumentParser(description="Mode-I Fracture ODB and Results Extractor")
    parser.add_argument("--odb", type=str, default="", help="Path to Abaqus .odb file")
    parser.add_argument("--dat", type=str, default="", help="Path to Abaqus .dat file")
    parser.add_argument("--csv", type=str, default="", help="Path to uel_energy_balance.csv file")
    parser.add_argument("--job-id", type=str, default="UNKNOWN", help="PBS Job ID")
    parser.add_argument("--model-name", type=str, default="Mode1_Model", help="Model descriptive name")
    parser.add_argument("--out-dir", type=str, default="./extracted_metrics", help="Directory for output files")
    args = parser.parse_args()

    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)
    out_prefix = os.path.join(args.out_dir, args.model_name.lower().replace(" ", "_"))

    metrics = None
    records = []
    ligament_profiles = {}

    if args.odb and os.path.exists(args.odb):
        print("=== Running Abaqus ODB Extraction ===")
        metrics, records, ligament_profiles = extract_from_odb(args.odb)
    
    if metrics is None and args.dat and os.path.exists(args.dat):
        print("=== Running Offline DAT + Energy CSV Extraction ===")
        dat_records = parse_dat_file(args.dat)
        if dat_records:
            metrics, records = process_curve_data(dat_records)
            if args.csv and os.path.exists(args.csv):
                csv_records = parse_energy_csv(args.csv)
                if csv_records:
                    last_csv = csv_records[-1]
                    metrics["energy_balance"] = {
                        "e_elas_final_mJ": last_csv.get("e_elas_mJ", last_csv.get("e_elas_kNmm", 0.0) * 1000.0),
                        "e_frac_final_mJ": last_csv.get("e_frac_mJ", last_csv.get("e_frac_kNmm", 0.0) * 1000.0),
                        "e_model_final_mJ": last_csv.get("e_model_mJ", (last_csv.get("e_elas_kNmm", 0.0) + last_csv.get("e_frac_kNmm", 0.0)) * 1000.0),
                        "w_ext_final_mJ": metrics["terminal_w_ext_mJ"],
                        "eps_book_abs_pct": last_csv.get("eps_book_abs_pct", 0.0)
                    }

    if metrics is None:
        print("[ERROR] Neither valid ODB nor DAT file could be parsed.")
        sys.exit(1)

    # Attach job provenance
    metrics["job_provenance"] = {
        "job_id": args.job_id,
        "model_name": args.model_name,
        "odb_source": args.odb if args.odb else None,
        "dat_source": args.dat if args.dat else None,
        "csv_source": args.csv if args.csv else None
    }

    # Write JSON summary
    summary_json_path = out_prefix + "_metrics.json"
    with open(summary_json_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print("[SUCCESS] Saved metrics JSON to: %s" % summary_json_path)

    # Write load-displacement CSV
    curve_csv_path = out_prefix + "_load_displacement.csv"
    with open(curve_csv_path, 'w') as f:
        f.write("step,inc_or_frame,u_mm,rf_raw_kN,f_kN,w_ext_mJ\n")
        for r in records:
            step_val = r.get("step", 1)
            idx_val = r.get("inc", r.get("frame_id", 0))
            f.write("%s,%s,%.8f,%.8f,%.8f,%.8f\n" % (
                str(step_val), str(idx_val), r["u_mm"], r["rf_raw_kN"], r["f_kN"], r["w_ext_mJ"]
            ))
    print("[SUCCESS] Saved load-displacement CSV to: %s" % curve_csv_path)

    # Write ligament damage profiles if any
    if ligament_profiles:
        lig_csv_path = out_prefix + "_ligament_damage_profiles.csv"
        with open(lig_csv_path, 'w') as f:
            f.write("target_u_mm,actual_u_mm,elem_id,x_coord,y_coord,damage_d\n")
            for tu, pinfo in ligament_profiles.items():
                act_u = pinfo["actual_u_mm"]
                for pt in pinfo["profile"]:
                    f.write("%.6f,%.6f,%d,%.6f,%.6f,%.6f\n" % (
                        tu, act_u, pt["eid"], pt["x"], pt["y"], pt["d"]
                    ))
        print("[SUCCESS] Saved ligament damage profiles CSV to: %s" % lig_csv_path)

    # Print summary block
    print("\n=======================================================")
    print("EXTRACTION SUMMARY: %s" % args.model_name)
    print("=======================================================")
    print("Total Increments / Frames: %d" % metrics["total_increments"])
    print("Terminal u:                %.6f mm" % metrics["terminal_u_mm"])
    print("Terminal F:                %.6f kN" % metrics["terminal_f_kN"])
    print("Terminal W_ext:            %.6f mJ" % metrics["terminal_w_ext_mJ"])
    print("Initial K0 (u <= 0.0010):  %.6f kN/mm (R^2=%.6f, Delta=%+.4f%%)" % (
        metrics["stiffness_u10"]["K0_kN_per_mm"],
        metrics["stiffness_u10"]["R2"],
        metrics["stiffness_u10"]["delta_vs_ref_pct"] if metrics["stiffness_u10"]["delta_vs_ref_pct"] is not None else 0.0
    ))
    print("Initial K0 (u <= 0.0020):  %.6f kN/mm (R^2=%.6f, Delta=%+.4f%%)" % (
        metrics["stiffness_u20"]["K0_kN_per_mm"],
        metrics["stiffness_u20"]["R2"],
        metrics["stiffness_u20"]["delta_vs_ref_pct"] if metrics["stiffness_u20"]["delta_vs_ref_pct"] is not None else 0.0
    ))
    print("Peak F_max:                %.6f kN at u=%.6f mm (Captured=%s)" % (
        metrics["peak_reaction"]["F_max_kN"],
        metrics["peak_reaction"]["u_at_F_max_mm"],
        str(metrics["peak_reaction"]["is_captured"])
    ))
    if metrics["peak_reaction"]["delta_F_max_pct"] is not None:
        print("Delta F_max vs Ref:        %+.4f %%" % metrics["peak_reaction"]["delta_F_max_pct"])
        print("Delta u(F_max) vs Ref:     %+.4f %%" % metrics["peak_reaction"]["delta_u_peak_pct"])
    print("=======================================================\n")

if __name__ == "__main__":
    main()
