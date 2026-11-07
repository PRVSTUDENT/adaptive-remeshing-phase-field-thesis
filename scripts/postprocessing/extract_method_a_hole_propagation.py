# -*- coding: utf-8 -*-
"""Extract comprehensive crack propagation telemetry from Method A hole adapted ODB.

Optimized for fast execution (< 20 seconds).
Extracts:
1. Step-1 final frame and Step-2 sample frames (d_max, H_max, damage distribution)
2. Final frame damage field and elements in crack band (d >= 0.8, d >= 0.9)
3. Coordinates and deflection of crack path toward the hole at (0.65, 0.65)
4. Energy balance across all steps from uel_energy_balance.csv

Run via Abaqus Python:
    abaqus python extract_method_a_hole_propagation.py --odb PK_HOLE_METHOD_A_PROP.odb --n-phys 52447
"""
from __future__ import print_function
import os
import sys
import json
import csv
import math

try:
    from odbAccess import openOdb
except ImportError:
    openOdb = None

def run_extraction(odb_path, output_dir='.', n_phys=52447):
    if openOdb is None:
        raise RuntimeError("odbAccess not available; run this script with 'abaqus python'.")

    print("Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)

    summary = {
        'odb_path': odb_path,
        'n_physical_elements': n_phys,
        'steps': {},
        'crack_trajectory': {},
        'crack_deflection_detected': False,
        'energy_summary': {}
    }

    umat_offset = 2 * n_phys  # Visualizer elements are 104,895 to 157,341
    instance = odb.rootAssembly.instances.values()[0] if odb.rootAssembly.instances else None

    # Step names
    step_names = list(odb.steps.keys())
    print("Found steps: %s" % str(step_names))

    frame_telemetry = []

    for s_name in step_names:
        step = odb.steps[s_name]
        num_frames = len(step.frames)
        print("Step %s: %d frames" % (s_name, num_frames))
        summary['steps'][s_name] = {
            'num_frames': num_frames,
            'time_period': float(step.timePeriod) if hasattr(step, 'timePeriod') else None,
            'frame_summaries': []
        }

        # Select representative frames to sample
        if s_name == 'Step-1':
            sample_indices = [0, num_frames - 1] if num_frames > 1 else [0]
        else:
            # Targeted key frames: start, peak load (14), post-peak softening (25), ligament severing (47), secondary reloading (100, 150), final frame
            key_candidates = [0, 14, 25, 47, 75, 100, 150, num_frames - 1]
            sample_indices = sorted(list(set([idx for idx in key_candidates if 0 <= idx < num_frames])))

        for f_idx in sample_indices:
            frame = step.frames[f_idx]
            t_val = float(frame.frameValue)
            fields = frame.fieldOutputs

            max_d = 0.0
            min_d = 1.0
            max_h = 0.0
            d_ge_05 = 0
            d_ge_08 = 0
            d_ge_09 = 0
            d_ge_095 = 0

            if 'SDV1' in fields and 'SDV2' in fields:
                sdv1_vals = fields['SDV1'].values
                sdv2_vals = fields['SDV2'].values
                for i in range(len(sdv1_vals)):
                    val1 = sdv1_vals[i]
                    elem_id = val1.elementLabel
                    if elem_id > umat_offset and elem_id <= umat_offset + n_phys:
                        val2 = sdv2_vals[i]
                        d_val = float(val1.dataDouble if hasattr(val1, 'dataDouble') else val1.data)
                        h_val = float(val2.dataDouble if hasattr(val2, 'dataDouble') else val2.data)
                        if d_val > max_d:
                            max_d = d_val
                        if d_val < min_d:
                            min_d = d_val
                        if h_val > max_h:
                            max_h = h_val
                        if d_val >= 0.50:
                            d_ge_05 += 1
                        if d_val >= 0.80:
                            d_ge_08 += 1
                        if d_val >= 0.90:
                            d_ge_09 += 1
                        if d_val >= 0.95:
                            d_ge_095 += 1

            frame_info = {
                'step': s_name,
                'frame_index': f_idx,
                'step_time': t_val,
                'd_max': max_d,
                'd_min': min_d,
                'h_max': max_h,
                'count_d_ge_0.5': d_ge_05,
                'count_d_ge_0.8': d_ge_08,
                'count_d_ge_0.9': d_ge_09,
                'count_d_ge_0.95': d_ge_095
            }
            summary['steps'][s_name]['frame_summaries'].append(frame_info)
            frame_telemetry.append(frame_info)

    # Detailed crack path analysis on final available frame
    last_step_name = step_names[-1]
    last_step = odb.steps[last_step_name]
    last_frame = last_step.frames[-1]
    last_fields = last_frame.fieldOutputs

    crack_elements = []
    if 'SDV1' in last_fields and 'SDV2' in last_fields:
        sdv1_vals = last_fields['SDV1'].values
        sdv2_vals = last_fields['SDV2'].values

        # Only get node coords for elements that have d >= 0.50
        damaged_elem_ids = set()
        damaged_data = {}
        for i in range(len(sdv1_vals)):
            val1 = sdv1_vals[i]
            elem_id = val1.elementLabel
            if elem_id > umat_offset and elem_id <= umat_offset + n_phys:
                d_val = float(val1.dataDouble if hasattr(val1, 'dataDouble') else val1.data)
                if d_val >= 0.50:
                    val2 = sdv2_vals[i]
                    h_val = float(val2.dataDouble if hasattr(val2, 'dataDouble') else val2.data)
                    phys_id = elem_id - umat_offset
                    damaged_elem_ids.add(phys_id)
                    damaged_data[phys_id] = (d_val, h_val, val1.integrationPoint)

        print("Damaged elements with d >= 0.50: %d" % len(damaged_elem_ids))

        # Look up node coords only for damaged elements
        if damaged_elem_ids and instance:
            # Map node labels needed
            needed_nodes = set()
            elem_conn = {}
            for elem in instance.elements:
                if elem.label in damaged_elem_ids:
                    elem_conn[elem.label] = elem.connectivity
                    for n in elem.connectivity:
                        needed_nodes.add(n)

            node_coords = {}
            for node in instance.nodes:
                if node.label in needed_nodes:
                    node_coords[node.label] = (float(node.coordinates[0]), float(node.coordinates[1]))

            for phys_id in damaged_elem_ids:
                conn = elem_conn.get(phys_id, ())
                if conn:
                    cx = sum(node_coords[n][0] for n in conn if n in node_coords) / len(conn)
                    cy = sum(node_coords[n][1] for n in conn if n in node_coords) / len(conn)
                    d_val, h_val, ip = damaged_data[phys_id]
                    crack_elements.append({
                        'phys_elem_id': phys_id,
                        'ip': ip,
                        'x': cx,
                        'y': cy,
                        'damage': d_val,
                        'history': h_val
                    })

    # Sort by x coordinate
    crack_elements.sort(key=lambda item: item['x'])

    # Analyze crack deflection
    # Initial notch ends at (0.50, 0.50). Hole center at (0.65, 0.65), radius = 0.10.
    advanced_crack = [e for e in crack_elements if e['x'] > 0.50 and e['damage'] >= 0.80]
    max_crack_x = 0.50
    y_at_max_crack_x = 0.50
    avg_y_ahead = 0.50
    deflection_observed = False

    if advanced_crack:
        max_crack_x = max(e['x'] for e in advanced_crack)
        tip_elements = [e for e in advanced_crack if e['x'] >= max_crack_x - 0.020]
        if tip_elements:
            y_at_max_crack_x = sum(e['y'] for e in tip_elements) / len(tip_elements)
        avg_y_ahead = sum(e['y'] for e in advanced_crack) / len(advanced_crack)
        # Check if crack has deflected upward toward the off-axis hole (y > 0.505)
        if y_at_max_crack_x > 0.505 or avg_y_ahead > 0.505:
            deflection_observed = True

    summary['crack_trajectory'] = {
        'notch_tip': [0.50, 0.50],
        'hole_center': [0.65, 0.65],
        'hole_radius': 0.10,
        'crack_elements_count': len(crack_elements),
        'fully_damaged_elements_count': len(advanced_crack),
        'max_crack_x': max_crack_x,
        'y_at_max_crack_x': y_at_max_crack_x,
        'avg_y_crack': avg_y_ahead,
        'deflection_toward_hole': deflection_observed
    }
    summary['crack_deflection_detected'] = deflection_observed

    # Read energy balance CSV if present
    energy_csv_path = os.path.join(os.path.dirname(odb_path) or '.', 'uel_energy_balance.csv')
    energy_rows = []
    if os.path.exists(energy_csv_path):
        print("Reading energy balance from: %s" % energy_csv_path)
        with open(energy_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                energy_rows.append({
                    'step': int(row.get('Step', 0)),
                    'increment': int(row.get('Increment', 0)),
                    'total_time': float(row.get('TotalTime', 0.0)),
                    'step_time': float(row.get('StepTime', 0.0)),
                    'e_elastic_kNmm': float(row.get('E_elastic_kNmm', 0.0)),
                    'e_fracture_kNmm': float(row.get('E_fracture_kNmm', 0.0)),
                    'e_total_kNmm': float(row.get('E_total_kNmm', 0.0))
                })

    if energy_rows:
        summary['energy_summary'] = {
            'initial': energy_rows[0],
            'step1_final': [r for r in energy_rows if r['step'] == 1][-1] if any(r['step'] == 1 for r in energy_rows) else None,
            'final': energy_rows[-1],
            'total_steps': len(set(r['step'] for r in energy_rows)),
            'total_increments': len(energy_rows)
        }

    # Save summary JSON
    out_json = os.path.join(output_dir, 'f1645_propagation_extracted_summary.json')
    with open(out_json, 'w') as f:
        json.dump(summary, f, indent=2)
    print("Summary written to: %s" % out_json)

    # Save crack path CSV
    out_csv = os.path.join(output_dir, 'f1645_propagation_crack_path.csv')
    with open(out_csv, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['phys_elem_id', 'ip', 'x', 'y', 'damage', 'history'])
        writer.writeheader()
        for r in crack_elements:
            writer.writerow(r)
    print("Crack path elements written to: %s (count: %d)" % (out_csv, len(crack_elements)))

    # Save frame evolution CSV
    out_frames_csv = os.path.join(output_dir, 'f1645_propagation_frame_evolution.csv')
    with open(out_frames_csv, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['step', 'frame_index', 'step_time', 'd_max', 'd_min', 'h_max',
                                              'count_d_ge_0.5', 'count_d_ge_0.8', 'count_d_ge_0.9', 'count_d_ge_0.95'])
        writer.writeheader()
        for r in frame_telemetry:
            writer.writerow(r)
    print("Frame evolution written to: %s" % out_frames_csv)

    odb.close()
    print("Extraction complete.")

if __name__ == '__main__':
    odb_file = 'PK_HOLE_METHOD_A_PROP.odb'
    out_dir = '.'
    n_phys = 52447

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--odb' and i + 1 < len(sys.argv):
            odb_file = sys.argv[i+1]
            i += 2
        elif arg == '--out-dir' and i + 1 < len(sys.argv):
            out_dir = sys.argv[i+1]
            i += 2
        elif arg == '--n-phys' and i + 1 < len(sys.argv):
            n_phys = int(sys.argv[i+1])
            i += 2
        else:
            if not arg.startswith('--') and i == 1:
                odb_file = arg
            i += 1

    run_extraction(odb_file, out_dir, n_phys)
