# -*- coding: utf-8 -*-
"""
scripts/remeshing/extract_f1678_prod_results.py
==============================================
Extracts reaction force P(u), displacement, damage fields, crack trajectory,
and energy balance from M1_HOLE_F1664_METHOD_A_PROD.odb on HPC cluster.

Usage via Abaqus Python on cluster:
    abaqus python extract_f1678_prod_results.py \
        --odb M1_HOLE_F1664_METHOD_A_PROD.odb \
        --energy-csv uel_energy_balance.csv \
        --n-phys 20213 \
        --out-summary f1678_prod_summary.json \
        --out-rf-csv f1678_prod_rf_u.csv \
        --out-crack-csv f1678_prod_crack_path.csv
"""
from __future__ import print_function
import os
import sys
import json
import csv
import math

try:
    import odbAccess
    from abaqusConstants import *
    ABAQUS_AVAILABLE = True
except ImportError:
    ABAQUS_AVAILABLE = False


def run_extraction(odb_path, energy_csv_path, n_phys, out_summary_path, out_rf_csv_path, out_crack_csv_path):
    if not os.path.exists(odb_path):
        raise RuntimeError("ODB file not found: %s" % odb_path)

    import time
    t0 = time.time()
    print("[%s] Opening ODB: %s" % (time.strftime('%H:%M:%S'), odb_path))
    odb = odbAccess.openOdb(odb_path, readOnly=True)
    ra = odb.rootAssembly
    print("[%s] ODB opened successfully in %.2f seconds." % (time.strftime('%H:%M:%S'), time.time() - t0))

    # Companion element offset: 2 * n_phys
    umat_offset = 2 * n_phys  # Physical elements: 1..n_phys; Companion UMAT elements: (2*n_phys+1)..(3*n_phys)

    # 1. Reaction Force and Displacement at Reference Node 999999
    rp_nid = 999999
    rf_u_history = []
    total_frames = 0
    max_rf2 = -1e9
    peak_record = None

    steps = odb.steps
    print("Available steps in ODB: %s" % list(steps.keys()))

    for sname in steps.keys():
        st = steps[sname]
        print("Processing Step %s (%d frames)..." % (sname, len(st.frames)))
        total_frames += len(st.frames)

        for fidx, frame in enumerate(st.frames):
            t_total = float(frame.frameValue)
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

            rec = {
                "step": sname,
                "frame": fidx,
                "time": t_total,
                "u2": u2_val,
                "rf2": rf2_val
            }
            rf_u_history.append(rec)
            if rf2_val > max_rf2:
                max_rf2 = rf2_val
                peak_record = rec

    # Calculate External Work W_ext = \int P du via trapezoidal integration
    w_ext = 0.0
    for i in range(1, len(rf_u_history)):
        du = rf_u_history[i]['u2'] - rf_u_history[i-1]['u2']
        p_avg = 0.5 * (rf_u_history[i]['rf2'] + rf_u_history[i-1]['rf2'])
        w_ext += p_avg * du
        rf_u_history[i]['w_ext'] = w_ext
    if rf_u_history:
        rf_u_history[0]['w_ext'] = 0.0

    # Write RF-U history to CSV
    with open(out_rf_csv_path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["step", "frame", "time", "u2_mm", "rf2_kN", "w_ext_kNmm"])
        for r in rf_u_history:
            writer.writerow([r["step"], r["frame"], "%.8e" % r["time"], "%.8e" % r["u2"], "%.8e" % r["rf2"], "%.8e" % r.get("w_ext", 0.0)])
    print("Wrote RF-U history to: %s (%d records)" % (out_rf_csv_path, len(rf_u_history)))

    if peak_record is not None:
        print("Peak Reaction Force: P_max = %.6f kN at u2 = %.6f mm (Step %s, frame %d)" % (
            peak_record["rf2"], peak_record["u2"], peak_record["step"], peak_record["frame"]
        ))

    # 2. Extract Element Centroid Coordinates for Physical Elements
    element_coords = {}
    inp_candidates = ['PK_HOLE_F1664_METHOD_A_PROD.inp', 'PK_HOLE_F1664_METHOD_A_ADAPT_PHYS.inp']
    inp_found = None
    for cand in inp_candidates:
        if os.path.exists(cand):
            inp_found = cand
            break

    if inp_found:
        print("[%s] Fast parsing element centroids from INP: %s" % (time.strftime('%H:%M:%S'), inp_found))
        nodes = {}
        with open(inp_found, 'r') as f:
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
                            # Physical elements are 1..n_phys
                            if 1 <= eid <= n_phys:
                                conn = [int(p) for p in parts[1:]]
                                pts = [nodes[n] for n in conn if n in nodes]
                                if pts:
                                    cx = sum(p[0] for p in pts) / float(len(pts))
                                    cy = sum(p[1] for p in pts) / float(len(pts))
                                    element_coords[eid] = (cx, cy)
                        except ValueError:
                            pass
        print("[%s] Extracted %d centroids from INP." % (time.strftime('%H:%M:%S'), len(element_coords)))
    else:
        for inst_name, instance in ra.instances.items():
            node_coords = {n.label: n.coordinates for n in instance.nodes}
            for elem in instance.elements:
                elem_id = elem.label
                if elem_id > umat_offset and elem_id <= umat_offset + n_phys:
                    phys_id = elem_id - umat_offset
                    pts = [node_coords[nid] for nid in elem.connectivity if nid in node_coords]
                    if pts:
                        cx = sum(p[0] for p in pts) / float(len(pts))
                        cy = sum(p[1] for p in pts) / float(len(pts))
                        element_coords[phys_id] = (cx, cy)

    # 3. Analyze Key Frames (Step-1 end, Peak load, Final frame)
    key_frame_targets = {}
    if 'Step-1' in steps and len(steps['Step-1'].frames) > 0:
        key_frame_targets['step1_end'] = (steps['Step-1'].frames[-1], "Step-1 end (u2=0.0050 mm)")
    if peak_record is not None and peak_record['step'] in steps:
        key_frame_targets['peak_load'] = (steps[peak_record['step']].frames[peak_record['frame']], "Peak reaction force frame")
    last_sname = list(steps.keys())[-1]
    if len(steps[last_sname].frames) > 0:
        key_frame_targets['final_frame'] = (steps[last_sname].frames[-1], "Final simulation frame")

    frame_audits = {}
    crack_elements = []

    for kf_name, (frame, desc) in key_frame_targets.items():
        fields = frame.fieldOutputs
        d_vals = []
        h_vals = []
        d_ge_05 = 0
        d_ge_08 = 0
        d_ge_09 = 0
        d_ge_095 = 0

        # Check SDV1 / SDV14 for phase damage
        dmg_field = 'SDV1' if 'SDV1' in fields else ('SDV14' if 'SDV14' in fields else None)
        hist_field = 'SDV2' if 'SDV2' in fields else ('SDV16' if 'SDV16' in fields else None)

        if dmg_field is not None:
            for val in fields[dmg_field].values:
                eid = val.elementLabel
                if eid > umat_offset and eid <= umat_offset + n_phys:
                    phys_id = eid - umat_offset
                    d_val = float(val.dataDouble if hasattr(val, 'dataDouble') else val.data)
                    d_vals.append(d_val)
                    if d_val >= 0.50: d_ge_05 += 1
                    if d_val >= 0.80: d_ge_08 += 1
                    if d_val >= 0.90: d_ge_09 += 1
                    if d_val >= 0.95: d_ge_095 += 1

                    if kf_name == 'final_frame' and d_val >= 0.80 and phys_id in element_coords:
                        cx, cy = element_coords[phys_id]
                        crack_elements.append({
                            'phys_elem_id': phys_id,
                            'x': cx,
                            'y': cy,
                            'damage': d_val
                        })

        if hist_field is not None:
            for val in fields[hist_field].values:
                eid = val.elementLabel
                if eid > umat_offset and eid <= umat_offset + n_phys:
                    h_val = float(val.dataDouble if hasattr(val, 'dataDouble') else val.data)
                    h_vals.append(h_val)

        frame_audits[kf_name] = {
            "description": desc,
            "step_time": float(frame.frameValue),
            "d_max": max(d_vals) if d_vals else 0.0,
            "d_min": min(d_vals) if d_vals else 0.0,
            "h_max": max(h_vals) if h_vals else 0.0,
            "count_d_ge_0.50": d_ge_05,
            "count_d_ge_0.80": d_ge_08,
            "count_d_ge_0.90": d_ge_09,
            "count_d_ge_0.95": d_ge_095
        }
        print("Key frame [%s]: d_max=%.4f, d>=0.80: %d, d>=0.95: %d" % (
            kf_name, frame_audits[kf_name]["d_max"], d_ge_08, d_ge_095
        ))

    # Write crack path CSV
    if crack_elements:
        with open(out_crack_csv_path, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=['phys_elem_id', 'x', 'y', 'damage'])
            writer.writeheader()
            for c in crack_elements:
                writer.writerow(c)
        print("Wrote crack path to: %s (%d elements)" % (out_crack_csv_path, len(crack_elements)))

    # 4. Ingest uel_energy_balance.csv if available
    energy_records = []
    final_e_elastic = 0.0
    final_e_fracture = 0.0
    final_e_total = 0.0
    if os.path.exists(energy_csv_path):
        print("Reading UEL energy balance: %s" % energy_csv_path)
        with open(energy_csv_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('Step'):
                    continue
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 7:
                    try:
                        kstep = int(parts[0])
                        kinc = int(parts[1])
                        ttot = float(parts[2])
                        tstep = float(parts[3])
                        e_elas = float(parts[4])
                        e_frac = float(parts[5])
                        e_tot = float(parts[6])
                        energy_records.append({
                            'step': kstep,
                            'inc': kinc,
                            'total_time': ttot,
                            'step_time': tstep,
                            'e_elastic_kNmm': e_elas,
                            'e_fracture_kNmm': e_frac,
                            'e_total_kNmm': e_tot
                        })
                    except ValueError:
                        pass
        if energy_records:
            final_e_elastic = energy_records[-1]['e_elastic_kNmm']
            final_e_fracture = energy_records[-1]['e_fracture_kNmm']
            final_e_total = energy_records[-1]['e_total_kNmm']
            print("Final UEL energies: E_elas=%.6e, E_frac=%.6e, E_tot=%.6e" % (
                final_e_elastic, final_e_fracture, final_e_total
            ))

    # Energy Balance discrepancy: delta_E = W_ext - E_total
    delta_e = w_ext - final_e_total
    energy_discrepancy_pct = (abs(delta_e) / w_ext * 100.0) if w_ext > 1e-12 else 0.0

    # Crack Trajectory Analysis
    trajectory_metrics = {}
    if crack_elements:
        primary_crack = [e for e in crack_elements if e['x'] <= 0.65 and e['y'] >= 0.49]
        secondary_crack = [e for e in crack_elements if e['x'] >= 0.65]
        avg_y_primary = sum(e['y'] for e in primary_crack) / float(len(primary_crack)) if primary_crack else 0.0
        trajectory_metrics = {
            "total_broken_elements": len(crack_elements),
            "primary_crack_elements": len(primary_crack),
            "secondary_crack_elements": len(secondary_crack),
            "deflection_toward_hole_verified": avg_y_primary > 0.505,
            "avg_y_primary": avg_y_primary,
            "max_x_crack": max(e['x'] for e in crack_elements),
            "right_flank_initiation": len(secondary_crack) > 0
        }

    # Compile Final Summary JSON
    summary = {
        "odb_path": odb_path,
        "n_physical_elements": n_phys,
        "total_frames": total_frames,
        "peak_reaction_force_kN": peak_record["rf2"] if peak_record else 0.0,
        "peak_displacement_mm": peak_record["u2"] if peak_record else 0.0,
        "final_displacement_mm": rf_u_history[-1]["u2"] if rf_u_history else 0.0,
        "final_reaction_force_kN": rf_u_history[-1]["rf2"] if rf_u_history else 0.0,
        "external_work_w_ext_kNmm": w_ext,
        "final_e_elastic_kNmm": final_e_elastic,
        "final_e_fracture_kNmm": final_e_fracture,
        "final_e_total_kNmm": final_e_total,
        "energy_balance_discrepancy_delta_E_kNmm": delta_e,
        "energy_balance_discrepancy_pct": energy_discrepancy_pct,
        "key_frames": frame_audits,
        "trajectory": trajectory_metrics,
        "energy_records_count": len(energy_records)
    }

    with open(out_summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print("Wrote extraction summary to: %s" % out_summary_path)

    odb.close()
    print("Extraction completed successfully.")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Extract production results from Abaqus ODB.")
    parser.add_argument('--odb', required=True, help="Path to ODB file")
    parser.add_argument('--energy-csv', default='uel_energy_balance.csv', help="Path to UEL energy balance CSV")
    parser.add_argument('--n-phys', type=int, default=20213, help="Number of physical elements")
    parser.add_argument('--out-summary', default='f1678_prod_summary.json', help="Output summary JSON")
    parser.add_argument('--out-rf-csv', default='f1678_prod_rf_u.csv', help="Output RF-U CSV")
    parser.add_argument('--out-crack-csv', default='f1678_prod_crack_path.csv', help="Output crack CSV")
    args = parser.parse_args()

    run_extraction(
        odb_path=args.odb,
        energy_csv_path=args.energy_csv,
        n_phys=args.n_phys,
        out_summary_path=args.out_summary,
        out_rf_csv_path=args.out_rf_csv,
        out_crack_csv_path=args.out_crack_csv
    )
