# -*- coding: utf-8 -*-
"""
Abaqus Python ODB Field & History Extractor for Mode-II Validation Jobs:
Extracts reaction force (RF), displacement (U), and phase damage (SDV / U3) from .odb files.
Executable with: abaqus python extract_validation_odb.py --odb <path> --output-csv <path>
"""

import sys
import os
import csv

def extract_odb(odb_path, out_csv_path, total_disp=0.050):
    if not os.path.exists(odb_path):
        sys.stderr.write("Error: ODB file not found: %s\n" % odb_path)
        sys.exit(1)
        
    try:
        from odbAccess import openOdb
    except ImportError:
        sys.stderr.write("Error: odbAccess module not available. Run with 'abaqus python'.\n")
        sys.exit(1)

    odb = openOdb(path=odb_path, readOnly=True)
    rows = []
    
    for step_name in odb.steps.keys():
        step = odb.steps[step_name]
        for frame_idx, frame in enumerate(step.frames):
            t = float(frame.frameValue)
            u1 = total_disp * t
            
            # Reaction force RF1 extraction
            rf1_pos = 0.0
            rf1_neg = 0.0
            if 'RF' in frame.fieldOutputs:
                rf_field = frame.fieldOutputs['RF']
                for val in rf_field.values:
                    if val.data[0] is not None:
                        if val.data[0] > 0.0:
                            rf1_pos += float(val.data[0])
                        else:
                            rf1_neg += abs(float(val.data[0]))
            rf1_val = max(rf1_pos, rf1_neg)
            
            # Max Phase Damage d_max extraction (U3 or SDV)
            d_max = 0.0
            if 'U' in frame.fieldOutputs:
                u_field = frame.fieldOutputs['U']
                for val in u_field.values:
                    if len(val.data) >= 3 and val.data[2] is not None:
                        v = float(val.data[2])
                        if v > d_max:
                            d_max = v
                            
            rows.append({
                'step_name': step_name,
                'frame_idx': frame_idx,
                'step_time': t,
                'u1_mm': u1,
                'rf1_kN': rf1_val,
                'd_max': d_max
            })
            
    odb.close()
    
    # Write to CSV
    with open(out_csv_path, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['step_name', 'frame_idx', 'step_time', 'u1_mm', 'rf1_kN', 'd_max'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
            
    sys.stdout.write("Extracted %d frames to %s\n" % (len(rows), out_csv_path))

if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.stderr.write("Usage: abaqus python extract_validation_odb.py <odb_path> <out_csv_path>\n")
        sys.exit(1)
    odb_path = sys.argv[1]
    out_csv = sys.argv[2]
    extract_odb(odb_path, out_csv)
