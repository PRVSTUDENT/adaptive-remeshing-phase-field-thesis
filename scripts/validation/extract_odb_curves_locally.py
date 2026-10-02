#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Local ODB extraction for M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL (1390278.mmaster02).
Extracts RF1 vs U1, d_max, and step transitions to CSV.
"""

from odbAccess import openOdb
import os
import csv

def extract_curve():
    base_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL"
    odb_path = os.path.join(base_dir, "M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.odb")
    csv_path = os.path.join(base_dir, "force_displacement_curve.csv")
    
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
            
    print("Extracted %d frames to %s" % (len(rows), csv_path))

if __name__ == "__main__":
    extract_curve()
