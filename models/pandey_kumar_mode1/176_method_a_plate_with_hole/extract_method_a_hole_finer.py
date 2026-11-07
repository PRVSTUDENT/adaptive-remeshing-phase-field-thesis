# -*- coding: utf-8 -*-
"""Extract comprehensive physical state from Method A hole finer-mesh ODB.

Run via Abaqus Python on cluster:
    abaqus python extract_method_a_hole_finer.py --odb PK_HOLE_METHOD_A_FINER.odb --n-phys 69903
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

def run_extraction(odb_path, output_dir='.', n_phys=69903):
    if openOdb is None:
        raise RuntimeError("odbAccess not available; run this script with 'abaqus python'.")

    print("Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)

    summary = {
        'odb_path': odb_path,
        'n_physical_elements': n_phys,
        'steps': {}
    }

    umat_offset = 2 * n_phys  # Elements 139,807 to 209,709 are companion visualizer

    for step_name in odb.steps.keys():
        step = odb.steps[step_name]
        num_frames = len(step.frames)
        print("Step: %s, Number of frames: %d" % (step_name, num_frames))

        step_summary = {
            'step_name': step_name,
            'num_frames': num_frames,
            'frame_summaries': []
        }

        # Sample initial, middle, peak, and last frames
        frames_to_sample = [0]
        if num_frames > 1:
            frames_to_sample.append(num_frames - 1)
        if num_frames > 10:
            frames_to_sample.extend([num_frames // 4, num_frames // 2, 3 * num_frames // 4])
        frames_to_sample = sorted(list(set(frames_to_sample)))

        for f_idx in frames_to_sample:
            frame = step.frames[f_idx]
            fields = frame.fieldOutputs

            max_d = 0.0
            min_d = 1.0
            max_h = 0.0
            min_h = 0.0
            d_above_05 = 0
            d_above_08 = 0
            d_above_09 = 0
            d_above_095 = 0

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

                        if d_val > max_d: max_d = d_val
                        if d_val < min_d: min_d = d_val
                        if h_val > max_h: max_h = h_val
                        if h_val < min_h: min_h = h_val

                        if d_val >= 0.50: d_above_05 += 1
                        if d_val >= 0.80: d_above_08 += 1
                        if d_val >= 0.90: d_above_09 += 1
                        if d_val >= 0.95: d_above_095 += 1

            step_summary['frame_summaries'].append({
                'frame_index': f_idx,
                'step_time': float(frame.frameValue),
                'd_max': max_d,
                'd_min': min_d,
                'h_max': max_h,
                'count_d_ge_0.5': d_above_05,
                'count_d_ge_0.8': d_above_08,
                'count_d_ge_0.9': d_above_09,
                'count_d_ge_0.95': d_above_095
            })

        summary['steps'][step_name] = step_summary

    # Extract crack trajectory coordinates from final frame of last step
    last_step_name = odb.steps.keys()[-1]
    last_step = odb.steps[last_step_name]
    last_frame = last_step.frames[-1]

    root_assembly = odb.rootAssembly
    element_coords = {}
    for inst_name, instance in root_assembly.instances.items():
        node_coords = {n.label: n.coordinates for n in instance.nodes}
        for elem in instance.elements:
            elem_id = elem.label
            if elem_id > umat_offset and elem_id <= umat_offset + n_phys:
                phys_id = elem_id - umat_offset
                pts = [node_coords[nid] for nid in elem.connectivity if nid in node_coords]
                if pts:
                    cx = sum(p[0] for p in pts) / len(pts)
                    cy = sum(p[1] for p in pts) / len(pts)
                    element_coords[phys_id] = (cx, cy)

    crack_elements = []
    if 'SDV1' in last_frame.fieldOutputs:
        for val in last_frame.fieldOutputs['SDV1'].values:
            eid = val.elementLabel
            if eid > umat_offset and eid <= umat_offset + n_phys:
                phys_id = eid - umat_offset
                d_val = float(val.dataDouble if hasattr(val, 'dataDouble') else val.data)
                if d_val >= 0.80 and phys_id in element_coords:
                    cx, cy = element_coords[phys_id]
                    crack_elements.append({
                        'phys_elem_id': phys_id,
                        'x': cx,
                        'y': cy,
                        'damage': d_val
                    })

    summary['crack_elements_count'] = len(crack_elements)
    if crack_elements:
        avg_y = sum(e['y'] for e in crack_elements) / len(crack_elements)
        max_x = max(e['x'] for e in crack_elements)
        y_at_max_x = [e['y'] for e in crack_elements if e['x'] == max_x][0]
        summary['crack_trajectory'] = {
            'deflection_toward_hole': (avg_y > 0.505),
            'avg_y_crack': avg_y,
            'max_crack_x': max_x,
            'y_at_max_crack_x': y_at_max_x,
            'notch_tip': [0.50, 0.50],
            'hole_center': [0.65, 0.65],
            'hole_radius': 0.10
        }

    # Save summary
    out_json = os.path.join(output_dir, 'f1648_finer_extracted_summary.json')
    with open(out_json, 'w') as f:
        json.dump(summary, f, indent=2)
    print("Summary written to: %s" % out_json)

    # Save crack path CSV
    out_csv = os.path.join(output_dir, 'f1648_finer_crack_path.csv')
    with open(out_csv, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['phys_elem_id', 'x', 'y', 'damage'])
        writer.writeheader()
        for c in crack_elements:
            writer.writerow(c)
    print("Crack path elements written to: %s (count: %d)" % (out_csv, len(crack_elements)))

    odb.close()
    print("Extraction complete.")

if __name__ == '__main__':
    odb_file = 'PK_HOLE_METHOD_A_FINER.odb'
    out_dir = '.'
    n_phys = 69903

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
