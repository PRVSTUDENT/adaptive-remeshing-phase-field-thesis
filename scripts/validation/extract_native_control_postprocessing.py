#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Post-processing extraction for completed job 1390278.mmaster02 (M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL).
Extracts:
1. Complete step-by-step and increment-by-increment solver progress from .sta.
2. Summary of cutbacks, iterations, and convergence from .msg.
3. Key metrics table: RF1 vs U1, d_max evolution, cpu time, iterations.
"""

import os
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
        
    with open(msg_path, 'r', errors='ignore') as fp:
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

def main():
    base_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL"
    sta_file = os.path.join(base_dir, "M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.sta")
    msg_file = os.path.join(base_dir, "M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.msg")
    
    print("================================================================================")
    print("POST-PROCESSING EXTRACTION: JOB 1390278.mmaster02")
    print("================================================================================")
    
    sta_data = parse_sta_file(sta_file)
    msg_stats = parse_msg_file(msg_file)
    
    print("1. General Job Accounting Summary:")
    print("   Total Converged Increments: %d" % len(sta_data))
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

    # Save summary json
    summary = {
        'job_id': '1390278.mmaster02',
        'job_name': 'M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL',
        'accounting': msg_stats,
        'step_increments': step_counts,
        'total_increments': len(sta_data)
    }
    
    out_json = os.path.join(base_dir, "postprocessing_summary.json")
    with open(out_json, 'w') as fp:
        json.dump(summary, fp, indent=2)
    print("\n3. Saved post-processing summary to %s" % out_json)

if __name__ == "__main__":
    main()
