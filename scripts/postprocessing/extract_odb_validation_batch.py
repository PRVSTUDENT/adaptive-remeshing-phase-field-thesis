#!/usr/bin/env python
"""
Abaqus Python ODB Extractor for Mode-II Dual Validation Batch:
Extracts exact step, frame, time, RP displacement, RP reaction forces, and phase field damage.
"""

import sys
import os
import csv
import json

from odbAccess import openOdb

def extract_job_odb(odb_path, csv_out_path):
    print("Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)
    
    # Identify RP Node (Node 99999 or RP set)
    root_assembly = odb.rootAssembly
    
    records = []
    
    for step_name in odb.steps.keys():
        step = odb.steps[step_name]
        print("Processing Step: %s (Total Frames: %d)" % (step_name, len(step.frames)))
        
        for f_idx, frame in enumerate(step.frames):
            t = frame.frameValue
            
            # Extract RP displacement and reaction
            u_field = frame.fieldOutputs['U'] if 'U' in frame.fieldOutputs.keys() else None
            rf_field = frame.fieldOutputs['RF'] if 'RF' in frame.fieldOutputs.keys() else None
            sdv_field = frame.fieldOutputs['SDV15'] if 'SDV15' in frame.fieldOutputs.keys() else None
            
            u1, u2, u3 = 0.0, 0.0, 0.0
            rf1, rf2, rf3 = 0.0, 0.0, 0.0
            
            if u_field is not None:
                for val in u_field.values:
                    if val.nodeLabel == 99999:
                        u1 = val.data[0]
                        u2 = val.data[1]
                        u3 = val.data[2] if len(val.data) > 2 else 0.0
                        break
                        
            if rf_field is not None:
                for val in rf_field.values:
                    if val.nodeLabel == 99999:
                        rf1 = val.data[0]
                        rf2 = val.data[1]
                        rf3 = val.data[2] if len(val.data) > 2 else 0.0
                        break
                        
            max_d = 0.0
            if sdv_field is not None:
                for val in sdv_field.values:
                    if val.data > max_d:
                        max_d = val.data
                        
            records.append({
                'step_name': step_name,
                'frame_idx': f_idx,
                'step_time': t,
                'u1_mm': u1,
                'u2_mm': u2,
                'u3_mm': u3,
                'rf1_kN': rf1,
                'rf2_kN': rf2,
                'rf3_kN': rf3,
                'd_max': max_d
            })
            
    odb.close()
    
    print("Writing %d records to %s" % (len(records), csv_out_path))
    with open(csv_out_path, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['step_name', 'frame_idx', 'step_time', 'u1_mm', 'u2_mm', 'u3_mm', 'rf1_kN', 'rf2_kN', 'rf3_kN', 'd_max'])
        writer.writeheader()
        for r in records:
            writer.writerow(r)
            
    return records

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: abaqus python extract_odb_validation_batch.py <odb_path> <csv_out_path>")
        sys.exit(1)
        
    extract_job_odb(sys.argv[1], sys.argv[2])
