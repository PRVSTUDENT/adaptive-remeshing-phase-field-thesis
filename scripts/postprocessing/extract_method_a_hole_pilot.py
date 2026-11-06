# -*- coding: utf-8 -*-
"""Extract comprehensive physical state from Method A hole pilot ODB.

Run via Abaqus Python:
    abaqus python extract_method_a_hole_pilot.py --odb PK_HOLE_METHOD_A_PROD.odb
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

def run_extraction(odb_path, output_dir='.'):
    if openOdb is None:
        raise RuntimeError("odbAccess not available; run this script with 'abaqus python'.")

    print("Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)

    summary = {
        'odb_path': odb_path,
        'steps': []
    }

    step_name = 'Step-1'
    if step_name not in odb.steps:
        # Fallback to first step
        step_name = odb.steps.keys()[0]

    step = odb.steps[step_name]
    num_frames = len(step.frames)
    print("Step: %s, Number of frames: %d" % (step_name, num_frames))

    # 1. Extract RF2 vs U2 history from history output or field output
    history_records = []
    # Check if energy history is available
    energy_history = {}
    for region_name, region in step.historyRegions.items():
        for var_name, h_out in region.historyOutputs.items():
            energy_history[var_name] = h_out.data

    # Extract RF2 and U2
    # In historyRegions: Node NSET_TOP_DISP
    rf2_data = None
    u2_data = None
    for region_name, region in step.historyRegions.items():
        if 'RF2' in region.historyOutputs:
            rf2_data = region.historyOutputs['RF2'].data
        if 'U2' in region.historyOutputs:
            u2_data = region.historyOutputs['U2'].data

    # Also extract frame-by-frame field metrics
    last_frame = step.frames[-1]
    print("Processing final frame (frame %d, time = %f)..." % (len(step.frames)-1, float(last_frame.frameValue)))

    # Companion layer offset for 46,747 physical elements
    n_phys = 46747
    umat_offset = 2 * n_phys  # Elements 93,495 to 140,241 are companion visualizer

    # Extract field outputs from final frame
    fields = last_frame.fieldOutputs

    max_d = 0.0
    min_d = 1.0
    max_h = 0.0
    min_h = 0.0
    d_above_001 = 0
    d_above_01 = 0
    d_above_05 = 0
    d_above_09 = 0
    total_samples = 0

    element_field_records = []

    if 'SDV1' in fields and 'SDV2' in fields:
        sdv1_field = fields['SDV1']
        sdv2_field = fields['SDV2']
        sdv1_vals = sdv1_field.values
        sdv2_vals = sdv2_field.values

        for i in range(len(sdv1_vals)):
            val1 = sdv1_vals[i]
            val2 = sdv2_vals[i]
            elem_id = val1.elementLabel
            # Only consider companion visualizer elements
            if elem_id > umat_offset and elem_id <= umat_offset + n_phys:
                phys_elem_id = elem_id - umat_offset
                d_val = float(val1.dataDouble if hasattr(val1, 'dataDouble') else val1.data)
                h_val = float(val2.dataDouble if hasattr(val2, 'dataDouble') else val2.data)

                if d_val > max_d:
                    max_d = d_val
                if d_val < min_d:
                    min_d = d_val
                if h_val > max_h:
                    max_h = h_val
                if h_val < min_h:
                    min_h = h_val

                if d_val >= 0.01:
                    d_above_001 += 1
                if d_val >= 0.10:
                    d_above_01 += 1
                if d_val >= 0.50:
                    d_above_05 += 1
                if d_val >= 0.90:
                    d_above_09 += 1
                total_samples += 1

                # Record elements with non-trivial damage for spatial mapping
                if d_val >= 0.005:
                    element_field_records.append({
                        'phys_elem_id': phys_elem_id,
                        'ip': val1.integrationPoint,
                        'damage': d_val,
                        'history': h_val
                    })

    # Read energy balance CSV if present in same directory
    energy_csv_path = os.path.join(os.path.dirname(odb_path) or '.', 'uel_energy_balance.csv')
    last_energy = {}
    if os.path.exists(energy_csv_path):
        with open(energy_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                last_energy = {
                    'step': int(row.get('Step', 0)),
                    'increment': int(row.get('Increment', 0)),
                    'total_time': float(row.get('TotalTime', 0.0)),
                    'step_time': float(row.get('StepTime', 0.0)),
                    'e_elastic_kNmm': float(row.get('E_elastic_kNmm', 0.0)),
                    'e_fracture_kNmm': float(row.get('E_fracture_kNmm', 0.0)),
                    'e_total_kNmm': float(row.get('E_total_kNmm', 0.0))
                }

    summary['final_frame'] = {
        'frame_index': len(step.frames) - 1,
        'step_time': float(last_frame.frameValue),
        'total_samples': total_samples,
        'damage_max': max_d,
        'damage_min': min_d,
        'history_max': max_h,
        'history_min': min_h,
        'counts': {
            'd_ge_0.01': d_above_001,
            'd_ge_0.10': d_above_01,
            'd_ge_0.50': d_above_05,
            'd_ge_0.90': d_above_09
        },
        'energy_balance': last_energy,
        'physical_acceptance': {
            'damage_bounds_valid': (min_d >= -1e-6 and max_d <= 1.0 + 1e-6),
            'history_nonnegative': (min_h >= -1e-9),
            'damage_initiation_detected': (max_d > 0.01)
        }
    }

    # Save summary JSON
    out_json = os.path.join(output_dir, 'f1642_pilot_extracted_summary.json')
    with open(out_json, 'w') as f:
        json.dump(summary, f, indent=2)
    print("Summary written to: %s" % out_json)

    # Save non-trivial damage elements CSV
    out_csv = os.path.join(output_dir, 'f1642_pilot_localized_damage.csv')
    with open(out_csv, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['phys_elem_id', 'ip', 'damage', 'history'])
        writer.writeheader()
        for r in element_field_records:
            writer.writerow(r)
    print("Localized damage elements written to: %s (count: %d)" % (out_csv, len(element_field_records)))

    odb.close()
    print("Extraction complete.")

if __name__ == '__main__':
    odb_file = sys.argv[1] if len(sys.argv) > 1 else 'PK_HOLE_METHOD_A_PROD.odb'
    out_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    run_extraction(odb_file, out_dir)
