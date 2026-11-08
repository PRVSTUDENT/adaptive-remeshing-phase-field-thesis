# -*- coding: utf-8 -*-
"""
scripts/remeshing/extract_all_frames_prod.py
============================================
Task F1682: Complete ODB Frame Extraction for 20,213-Element Production Model
- Reads M1_HOLE_F1664_METHOD_A_PROD.odb (5.2 GB, Job 1421142.mmaster02)
- Iterates across all stored frames in Step-1 and Step-2 (614 frames total)
- Extracts reference node (999999) displacement U2 and reaction force RF2
- Evaluates damage field SDV1/SDV14 across all 20,213 physical elements
- High-performance array-indexed aggregation ensures 100% unique physical element accounting
- Computes complete damage statistics (max, min, mean, threshold counts d >= 0.10, 0.25, 0.50, 0.80, 0.95)
- Tracks crack tip kinematics and proximity to circular hole
- Writes full-field damage for all 20,213 physical elements at the final state
- Outputs structured frame telemetry CSV and summary JSON
"""
from __future__ import print_function
import os
import sys
import json
import csv
import math
import time

try:
    from odbAccess import openOdb
    from abaqusConstants import *
except ImportError as e:
    print("Error importing odbAccess: %s" % e)
    sys.exit(1)


def parse_element_centroids(inp_path, n_phys):
    """
    Parses node coordinates and element connectivity from INP to compute
    centroids for all physical elements 1..n_phys.
    """
    nodes = {}
    elem_centroids = {}
    print("[%s] Parsing mesh geometry from %s..." % (time.strftime('%H:%M:%S'), inp_path))
    with open(inp_path, 'r') as f:
        section = None
        for line in f:
            line = line.strip()
            if not line or line.startswith('**'):
                continue
            if line.startswith('*'):
                upper = line.upper()
                if upper.startswith('*NODE'):
                    section = 'NODE'
                elif upper.startswith('*ELEMENT') and ('TYPE=U' in upper or 'TYPE=CPE' in upper):
                    section = 'ELEMENT'
                else:
                    section = None
                continue

            if section == 'NODE':
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        nodes[nid] = (float(parts[1]), float(parts[2]))
                    except ValueError:
                        pass
            elif section == 'ELEMENT':
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        if 1 <= eid <= n_phys:
                            conn = [int(p) for p in parts[1:]]
                            pts = [nodes[n] for n in conn if n in nodes]
                            if pts:
                                cx = sum(p[0] for p in pts) / float(len(pts))
                                cy = sum(p[1] for p in pts) / float(len(pts))
                                elem_centroids[eid] = (cx, cy)
                    except ValueError:
                        pass
    print("[%s] Extracted %d centroids from INP." % (time.strftime('%H:%M:%S'), len(elem_centroids)))
    return elem_centroids


def run_extraction():
    odb_path = "M1_HOLE_F1664_METHOD_A_PROD.odb"
    inp_path = "PK_HOLE_F1664_METHOD_A_PROD.inp"
    out_csv = "f1682_prod_all_frames_progression.csv"
    out_json = "f1682_prod_odb_inventory.json"
    full_field_csv = "f1682_prod_final_full_damage_field.csv"
    key_states_csv = "f1682_prod_key_states_damage.csv"
    n_phys = 20213
    umat_offset = 2 * n_phys  # Companion elements: 40427..60639

    if not os.path.exists(odb_path):
        print("ODB file not found: %s" % odb_path)
        sys.exit(1)

    t0 = time.time()
    print("================================================================================")
    print("TASK F1682: ALL-FRAME EXTRACTION FOR REFINED PRODUCTION ODB")
    print("ODB: %s (%.2f MB)" % (odb_path, os.path.getsize(odb_path) / (1024.0 * 1024.0)))
    print("Physical Elements: %d, Companion Offset: %d" % (n_phys, umat_offset))
    print("================================================================================")

    # 1. Parse centroids
    elem_centroids = parse_element_centroids(inp_path, n_phys)
    if len(elem_centroids) != n_phys:
        print("Warning: Parsed %d centroids, expected %d" % (len(elem_centroids), n_phys))

    # 2. Open ODB
    print("[%s] Opening ODB in read-only mode..." % time.strftime('%H:%M:%S'))
    odb = openOdb(path=odb_path, readOnly=True)
    root = odb.rootAssembly
    steps = odb.steps
    print("[%s] ODB opened successfully. Available steps: %s" % (time.strftime('%H:%M:%S'), list(steps.keys())))

    hole_c = (0.65, 0.65)
    hole_r = 0.10
    notch_tip = (0.50, 0.50)
    rp_nid = 999999

    csv_headers = [
        "step_name", "frame_idx", "inc_num", "step_time", "total_time",
        "u2_top", "rf2_top", "w_ext",
        "d_max", "d_min", "d_mean",
        "cnt_ge_010", "cnt_ge_025", "cnt_ge_050", "cnt_ge_080", "cnt_ge_095",
        "tip_x", "tip_y", "dist_to_hole_perimeter"
    ]

    f_csv = open(out_csv, "w")
    writer = csv.writer(f_csv)
    writer.writerow(csv_headers)

    step_cumulative_time = 0.0
    total_frames_processed = 0
    w_ext = 0.0
    prev_u2 = 0.0
    prev_rf2 = 0.0

    # Preallocated buffers for O(1) array access
    elem_d = [0.0] * (n_phys + 1)
    elem_visited = [0] * (n_phys + 1)
    frame_counter = 0

    field_history = []
    final_frame_damage = {}
    key_states_records = []

    # Target key frames for full-field snapshot
    # Step 1: final frame (pre-critical endpoint)
    # Step 2: frame 50 (peak load), frame 180 (hole entry), frame 198 (secondary init),
    #         frame 220 (snap-through), frame 248 (severance), frame 557 (final)
    key_targets = {
        ("Step-1", 57): "Step1_Endpoint_PreCritical",
        ("Step-2", 50): "Peak_Reaction_Force",
        ("Step-2", 180): "Primary_Crack_Entering_Hole",
        ("Step-2", 198): "Secondary_Flank_Initiation",
        ("Step-2", 220): "Secondary_Snap_Through",
        ("Step-2", 248): "Right_Ligament_Severance",
        ("Step-2", 557): "Final_Displacement_Endpoint"
    }

    for sname in ["Step-1", "Step-2"]:
        if sname not in steps:
            print("Step '%s' not found in ODB!" % sname)
            continue

        step = steps[sname]
        n_frames = len(step.frames)
        print("[%s] Processing Step '%s' with %d frames..." % (time.strftime('%H:%M:%S'), sname, n_frames))

        for fidx, frame in enumerate(step.frames):
            frame_counter += 1
            total_frames_processed += 1
            fval = float(frame.frameValue)
            total_time = step_cumulative_time + fval

            # Read RF2 and U2 at reference node 999999
            u2_val = 0.0
            rf2_val = 0.0

            if 'U' in frame.fieldOutputs:
                u_fo = frame.fieldOutputs['U']
                for v in u_fo.values:
                    if v.nodeLabel == rp_nid:
                        u2_val = float(v.data[1])
                        break

            if 'RF' in frame.fieldOutputs:
                rf_fo = frame.fieldOutputs['RF']
                for v in rf_fo.values:
                    if v.nodeLabel == rp_nid:
                        rf2_val = float(v.data[1])
                        break

            # Trapezoidal work integration
            if total_frames_processed == 1:
                w_ext = 0.0
            else:
                du = u2_val - prev_u2
                p_avg = 0.5 * (rf2_val + prev_rf2)
                w_ext += p_avg * du
            prev_u2 = u2_val
            prev_rf2 = rf2_val

            # Reset damage buffer for this frame
            for pid in range(1, n_phys + 1):
                elem_d[pid] = 0.0

            # Determine damage field name
            dmg_field = None
            if 'SDV1' in frame.fieldOutputs:
                dmg_field = 'SDV1'
            elif 'SDV14' in frame.fieldOutputs:
                dmg_field = 'SDV14'

            if dmg_field is not None:
                fo = frame.fieldOutputs[dmg_field]
                for val in fo.values:
                    eid = val.elementLabel
                    if eid > umat_offset and eid <= umat_offset + n_phys:
                        pid = eid - umat_offset
                        if elem_visited[pid] != frame_counter:
                            elem_visited[pid] = frame_counter
                            elem_d[pid] = float(val.dataDouble if hasattr(val, 'dataDouble') else val.data)

            # Compute statistics across all 20,213 physical elements
            d_vals = elem_d[1:]
            d_max = max(d_vals)
            d_min = min(d_vals)
            d_sum = sum(d_vals)
            d_mean = d_sum / float(n_phys)

            cnt_10 = 0
            cnt_25 = 0
            cnt_50 = 0
            cnt_80 = 0
            cnt_95 = 0

            tip_x = notch_tip[0]
            tip_y = notch_tip[1]
            max_cx = 0.50

            for pid in range(1, n_phys + 1):
                d = elem_d[pid]
                if d >= 0.10: cnt_10 += 1
                if d >= 0.25: cnt_25 += 1
                if d >= 0.50:
                    cnt_50 += 1
                    if pid in elem_centroids:
                        cx, cy = elem_centroids[pid]
                        if cx > max_cx:
                            max_cx = cx
                            tip_x = cx
                            tip_y = cy
                if d >= 0.80: cnt_80 += 1
                if d >= 0.95: cnt_95 += 1

            dist_to_hole = math.hypot(tip_x - hole_c[0], tip_y - hole_c[1]) - hole_r

            # Write progression row
            writer.writerow([
                sname, fidx, frame.incrementNumber,
                "%.8e" % fval, "%.8e" % total_time,
                "%.8e" % u2_val, "%.8e" % rf2_val, "%.8e" % w_ext,
                "%.6f" % d_max, "%.6f" % d_min, "%.6f" % d_mean,
                cnt_10, cnt_25, cnt_50, cnt_80, cnt_95,
                "%.6f" % tip_x, "%.6f" % tip_y, "%.6f" % dist_to_hole
            ])

            rec = {
                "step": sname,
                "frame": fidx,
                "inc": frame.incrementNumber,
                "time": total_time,
                "u2": u2_val,
                "rf2": rf2_val,
                "w_ext": w_ext,
                "d_max": d_max,
                "d_min": d_min,
                "d_mean": d_mean,
                "cnt_ge_010": cnt_10,
                "cnt_ge_025": cnt_25,
                "cnt_ge_050": cnt_50,
                "cnt_ge_080": cnt_80,
                "cnt_ge_095": cnt_95,
                "tip_x": tip_x,
                "tip_y": tip_y,
                "dist_to_hole": dist_to_hole
            }
            field_history.append(rec)

            # Check if this is a key snapshot frame
            frame_key = (sname, fidx)
            if frame_key in key_targets:
                label = key_targets[frame_key]
                print("[%s] Storing full key-state '%s' (Step %s, frame %d, u2=%.5f mm, P=%.4f kN, d_max=%.4f, d>=0.80: %d)" % (
                    time.strftime('%H:%M:%S'), label, sname, fidx, u2_val, rf2_val, d_max, cnt_80
                ))
                for pid in range(1, n_phys + 1):
                    cx, cy = elem_centroids.get(pid, (0.0, 0.0))
                    key_states_records.append({
                        "state_label": label,
                        "step": sname,
                        "frame": fidx,
                        "u2_mm": u2_val,
                        "rf2_kN": rf2_val,
                        "phys_elem_id": pid,
                        "x": cx,
                        "y": cy,
                        "damage": elem_d[pid]
                    })

            # If final frame, store for full-field CSV
            if sname == "Step-2" and fidx == n_frames - 1:
                for pid in range(1, n_phys + 1):
                    cx, cy = elem_centroids.get(pid, (0.0, 0.0))
                    final_frame_damage[pid] = {
                        "x": cx,
                        "y": cy,
                        "damage": elem_d[pid]
                    }

            if fidx % 50 == 0 or fidx == n_frames - 1:
                print("[%s] Step %s, Frame %3d/%d: Inc %3d, u2=%.5f mm, P=%.4f kN, d_max=%.4f, cnt(d>=0.80)=%d, tip=(%.4f, %.4f)" % (
                    time.strftime('%H:%M:%S'), sname, fidx, n_frames, frame.incrementNumber,
                    u2_val, rf2_val, d_max, cnt_80, tip_x, tip_y
                ))

        step_cumulative_time += getattr(step, 'timePeriod', fval)

    f_csv.close()
    print("[%s] Wrote full frame progression to: %s (%d records)" % (time.strftime('%H:%M:%S'), out_csv, len(field_history)))

    # Write full-field damage for all 20,213 physical elements at final state
    print("[%s] Writing complete final-state damage field across all %d physical elements..." % (time.strftime('%H:%M:%S'), n_phys))
    with open(full_field_csv, "w") as f_full:
        full_writer = csv.writer(f_full)
        full_writer.writerow(["phys_elem_id", "x", "y", "damage", "is_damaged_ge_010", "is_broken_ge_080"])
        for pid in sorted(final_frame_damage.keys()):
            dat = final_frame_damage[pid]
            d = dat["damage"]
            full_writer.writerow([
                pid, "%.6f" % dat["x"], "%.6f" % dat["y"], "%.6f" % d,
                1 if d >= 0.10 else 0,
                1 if d >= 0.80 else 0
            ])
    print("[%s] Wrote full damage field to: %s" % (time.strftime('%H:%M:%S'), full_field_csv))

    # Write key states full damage CSV if records exist
    if key_states_records:
        print("[%s] Writing key states damage records (%d records)..." % (time.strftime('%H:%M:%S'), len(key_states_records)))
        with open(key_states_csv, "w") as f_ks:
            ks_writer = csv.DictWriter(f_ks, fieldnames=[
                "state_label", "step", "frame", "u2_mm", "rf2_kN",
                "phys_elem_id", "x", "y", "damage"
            ])
            ks_writer.writeheader()
            for r in key_states_records:
                ks_writer.writerow(r)
        print("[%s] Wrote key states damage to: %s" % (time.strftime('%H:%M:%S'), key_states_csv))

    # Write summary inventory JSON
    peak_rec = max(field_history, key=lambda x: x["rf2"]) if field_history else {}
    summary = {
        "odb_path": odb_path,
        "inp_path": inp_path,
        "n_phys_elements": n_phys,
        "total_frames_extracted": total_frames_processed,
        "step_counts": {sname: len(steps[sname].frames) for sname in ["Step-1", "Step-2"] if sname in steps},
        "peak_reaction_force": {
            "rf2_kN": peak_rec.get("rf2", 0.0),
            "u2_mm": peak_rec.get("u2", 0.0),
            "step": peak_rec.get("step", ""),
            "frame": peak_rec.get("frame", 0),
            "d_max": peak_rec.get("d_max", 0.0)
        },
        "final_state": {
            "u2_mm": field_history[-1].get("u2", 0.0) if field_history else 0.0,
            "rf2_kN": field_history[-1].get("rf2", 0.0) if field_history else 0.0,
            "w_ext_kNmm": field_history[-1].get("w_ext", 0.0) if field_history else 0.0,
            "d_max": field_history[-1].get("d_max", 0.0) if field_history else 0.0,
            "d_min": field_history[-1].get("d_min", 0.0) if field_history else 0.0,
            "d_mean": field_history[-1].get("d_mean", 0.0) if field_history else 0.0,
            "cnt_ge_010": field_history[-1].get("cnt_ge_010", 0) if field_history else 0,
            "cnt_ge_025": field_history[-1].get("cnt_ge_025", 0) if field_history else 0,
            "cnt_ge_050": field_history[-1].get("cnt_ge_050", 0) if field_history else 0,
            "cnt_ge_080": field_history[-1].get("cnt_ge_080", 0) if field_history else 0,
            "cnt_ge_095": field_history[-1].get("cnt_ge_095", 0) if field_history else 0
        },
        "key_states_stored": list(key_targets.values()),
        "extraction_duration_seconds": time.time() - t0
    }

    with open(out_json, "w") as f_json:
        json.dump(summary, f_json, indent=4)
    print("[%s] Wrote summary inventory to: %s" % (time.strftime('%H:%M:%S'), out_json))

    odb.close()
    print("[%s] ALL-FRAME PRODUCTION EXTRACTION COMPLETE in %.2f seconds." % (time.strftime('%H:%M:%S'), time.time() - t0))


if __name__ == "__main__":
    run_extraction()
