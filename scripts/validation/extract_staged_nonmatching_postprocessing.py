#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Post-processing extraction for completed job 1390279.mmaster02 (M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL).
Extracts:
1. Complete step-by-step solver progress and accounting from .sta and .msg.
2. Full force-displacement curve (RF1 vs U1, d_max) across all 4 steps from .odb.
3. Saves postprocessing_summary.json and force_displacement_curve.csv.
"""

from odbAccess import openOdb
import os
import sys
import json
import csv

def parse_sta_file(sta_path):
    increments = []
    if not os.path.exists(sta_path):
        return increments
    
    with open(sta_path, 'r') as fp:
        lines = fp.readlines()
        
    for line in lines:
        parts = line.split()
        if len(parts) >= 8:
            try:
                step_id = int(parts[0])
                inc_id = int(parts[1].replace('U', ''))
                severe_disc = int(parts[2].replace('U', '')) if parts[2].replace('U', '').isdigit() else 0
                equil_iter = int(parts[3])
                total_iter = int(parts[4])
                total_time = float(parts[6])
                inc_time = float(parts[8]) if len(parts) > 8 else float(parts[7])
                is_cutback = 'U' in line
                increments.append({
                    'step': step_id,
                    'increment': inc_id,
                    'severe_disc_iter': severe_disc,
                    'equil_iter': equil_iter,
                    'total_iter': total_iter,
                    'total_time': total_time,
                    'inc_time': inc_time,
                    'is_cutback': is_cutback,
                    'raw_line': line.strip()
                })
            except (ValueError, IndexError):
                continue
    return increments

def parse_msg_file(msg_path):
    stats = {
        'total_cpu_sec': 0.0,
        'wallclock_sec': 0.0,
        'total_iterations': 0,
        'cutbacks_count': 0,
        'error_messages': 0,
        'warning_messages': 0
    }
    if not os.path.exists(msg_path):
        return stats
        
    with open(msg_path, 'r') as fp:
        for line in fp:
            if 'TOTAL CPU TIME (SEC)' in line:
                try:
                    stats['total_cpu_sec'] = float(line.split('=')[1].strip())
                except:
                    pass
            elif 'WALLCLOCK TIME (SEC)' in line:
                try:
                    stats['wallclock_sec'] = float(line.split('=')[1].strip())
                except:
                    pass
            elif 'ERROR MESSAGES' in line:
                try:
                    stats['error_messages'] = int(line.split()[0])
                except:
                    pass
            elif 'WARNING MESSAGES DURING ANALYSIS' in line:
                try:
                    stats['warning_messages'] = int(line.split()[0])
                except:
                    pass
            elif 'TIME INCREMENT MAY NOT BE SMALLER THAN' in line or 'INCREMENT IS CUT BACK' in line:
                stats['cutbacks_count'] += 1
    return stats

def extract_curve(odb_path, csv_path):
    odb = openOdb(odb_path, readOnly=True)
    rows = []
    
    for s_name in ['STATE_INSTALL', 'MECH_EQUILIBRATION', 'PHASE_RELEASE', 'CONTINUATION']:
        if s_name in odb.steps:
            step = odb.steps[s_name]
            for f_idx, f in enumerate(step.frames):
                u1_top = 0.0
                d_max = 0.0
                if 'U' in f.fieldOutputs:
                    for v in f.fieldOutputs['U'].values:
                        if v.data[0] > u1_top:
                            u1_top = v.data[0]
                        if len(v.data) >= 3 and v.data[2] > d_max:
                            d_max = v.data[2]
                rf1_bot = 0.0
                if 'RF' in f.fieldOutputs:
                    rf1_bot = abs(sum(v.data[0] for v in f.fieldOutputs['RF'].values if v.data[0] < 0))
                rows.append([s_name, f_idx, f.frameValue, u1_top, rf1_bot, d_max])
                
    odb.close()
    
    with open(csv_path, 'w') as fp:
        writer = csv.writer(fp)
        writer.writerow(['Step', 'Frame_Index', 'Step_Time', 'U1_Top_mm', 'RF1_Bottom_kN', 'd_max'])
        for r in rows:
            writer.writerow(r)
    return len(rows)

def main():
    base_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL"
    sta_file = os.path.join(base_dir, "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.sta")
    msg_file = os.path.join(base_dir, "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.msg")
    odb_file = os.path.join(base_dir, "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.odb")
    csv_file = os.path.join(base_dir, "force_displacement_curve.csv")
    json_file = os.path.join(base_dir, "postprocessing_summary.json")
    
    print("================================================================================")
    print("POST-PROCESSING EXTRACTION: JOB 1390279.mmaster02")
    print("================================================================================")
    
    sta_data = parse_sta_file(sta_file)
    msg_stats = parse_msg_file(msg_file)
    total_frames = extract_curve(odb_file, csv_file)
    
    print("1. General Job Accounting Summary:")
    print("   Total Converged Increments: %d" % len(sta_data))
    print("   Total Extracted Frames:     %d" % total_frames)
    print("   Total CPU Time:            %.2f s (%.2f min)" % (msg_stats['total_cpu_sec'], msg_stats['total_cpu_sec']/60.0))
    print("   Total Wallclock Time:      %.2f s (%.2f min)" % (msg_stats['wallclock_sec'], msg_stats['wallclock_sec']/60.0))
    print("   Cutback Events:            %d" % msg_stats['cutbacks_count'])
    print("   Error Messages:            %d" % msg_stats['error_messages'])
    print("   Analysis Warnings:         %d" % msg_stats['warning_messages'])
    
    step_counts = {}
    for inc in sta_data:
        s = inc['step']
        step_counts[s] = step_counts.get(s, 0) + 1
        
    step_names = {1: 'STATE_INSTALL', 2: 'MECH_EQUILIBRATION', 3: 'PHASE_RELEASE', 4: 'CONTINUATION'}
    print("\n2. Increments by Step:")
    for s, cnt in sorted(step_counts.items()):
        print("   Step %d (%-20s): %3d increments" % (s, step_names.get(s, 'UNKNOWN'), cnt))

    summary = {
        'job_id': '1390279.mmaster02',
        'job_name': 'M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL',
        'accounting': msg_stats,
        'step_increments': step_counts,
        'total_increments': len(sta_data),
        'total_frames': total_frames
    }
    
    with open(json_file, 'w') as fp:
        json.dump(summary, fp, indent=2)
    print("\n3. Saved post-processing summary to %s" % json_file)
    print("4. Saved force-displacement curve to %s" % csv_file)

if __name__ == "__main__":
    main()
