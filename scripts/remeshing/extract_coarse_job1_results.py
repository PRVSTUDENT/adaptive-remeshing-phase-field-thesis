# -*- coding: utf-8 -*-
"""
scripts/remeshing/extract_coarse_job1_results.py
===============================================
Extracts reaction force, displacement, damage (SDV1), history (SDV2),
von Mises stress (S), and native MISESERI error indicator from PK_HOLE_COARSE_JOB1.odb.
"""

from __future__ import print_function
import os
import sys
import json
import csv

try:
    import odbAccess
    from abaqusConstants import *
    ABAQUS_AVAILABLE = True
except ImportError:
    ABAQUS_AVAILABLE = False


def extract_results(odb_path, output_json, output_csv, output_fields_json):
    if not os.path.exists(odb_path):
        raise FileNotFoundError("ODB not found: %s" % odb_path)
        
    print("Opening ODB: %s" % odb_path)
    odb = odbAccess.openOdb(odb_path, readOnly=True)
    ra = odb.rootAssembly
    inst = list(ra.instances.values())[0] if ra.instances else None
    
    # 1. Extract RF2 and U2 at RP (node 999999)
    rp_nid = 999999
    rf_u_history = []
    
    steps = odb.steps
    print("Available steps: %s" % list(steps.keys()))
    
    total_frames = 0
    max_rf2 = -1e9
    peak_record = None
    
    for sname in steps.keys():
        st = steps[sname]
        print("Step %s has %d frames" % (sname, len(st.frames)))
        total_frames += len(st.frames)
        
        for fidx, frame in enumerate(st.frames):
            t_total = frame.frameValue
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
                
    # Write RF-U history to CSV
    with open(output_csv, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["step", "frame", "time", "u2", "rf2"])
        for r in rf_u_history:
            writer.writerow([r["step"], r["frame"], r["time"], r["u2"], r["rf2"]])
    print("Wrote RF-U history to: %s (%d records)" % (output_csv, len(rf_u_history)))
    print("Peak Reaction Force: F_max = %.6f kN at u2 = %.6f mm (Step %s, frame %d)" % (
        peak_record["rf2"], peak_record["u2"], peak_record["step"], peak_record["frame"]
    ))
    
    # 2. Detailed field audit across key frames:
    # (a) Last frame of Step 1
    # (b) Peak frame
    # (c) Last frame of Step 2
    key_frames = {
        "step1_end": (steps['Step-1'].frames[-1], "Step-1 end (u2=0.0050 mm)"),
        "step2_peak": (steps[peak_record['step']].frames[peak_record['frame']], "Step-2 peak load"),
        "step2_end": (steps['Step-2'].frames[-1], "Step-2 end / last converged")
    }
    
    fields_data = {}
    audit_summary = {
        "odb_path": odb_path,
        "total_frames": total_frames,
        "peak_force_kN": peak_record["rf2"],
        "peak_disp_mm": peak_record["u2"],
        "last_disp_mm": rf_u_history[-1]["u2"],
        "last_rf2_kN": rf_u_history[-1]["rf2"],
        "key_frames": {}
    }
    
    for kf_name, (frame, desc) in key_frames.items():
        print("\n--- Extracting %s: %s (time=%.6f) ---" % (kf_name, desc, frame.frameValue))
        
        # Damage d (SDV1)
        d_dict = {}
        if 'SDV1' in frame.fieldOutputs:
            for v in frame.fieldOutputs['SDV1'].values:
                # v.elementLabel is companion label (5813..8718)
                # Map to physical element (1..2906)
                phys_eid = v.elementLabel - 2 * 2906 if v.elementLabel > 2 * 2906 else v.elementLabel
                d_dict[phys_eid] = float(v.data)
                
        # History H (SDV2)
        h_dict = {}
        if 'SDV2' in frame.fieldOutputs:
            for v in frame.fieldOutputs['SDV2'].values:
                phys_eid = v.elementLabel - 2 * 2906 if v.elementLabel > 2 * 2906 else v.elementLabel
                h_dict[phys_eid] = float(v.data)
                
        # Stress S
        s_dict = {}
        if 'S' in frame.fieldOutputs:
            for v in frame.fieldOutputs['S'].values:
                phys_eid = v.elementLabel - 2 * 2906 if v.elementLabel > 2 * 2906 else v.elementLabel
                s_dict[phys_eid] = float(v.mises) if v.mises is not None else 0.0
                
        # MISESERI
        meri_dict = {}
        if 'MISESERI' in frame.fieldOutputs:
            for v in frame.fieldOutputs['MISESERI'].values:
                phys_eid = v.elementLabel - 2 * 2906 if v.elementLabel > 2 * 2906 else v.elementLabel
                meri_dict[phys_eid] = float(v.data) if v.data is not None else 0.0
                
        d_vals = list(d_dict.values())
        h_vals = list(h_dict.values())
        s_vals = list(s_dict.values())
        meri_vals = list(meri_dict.values())
        
        kf_summary = {
            "description": desc,
            "time": frame.frameValue,
            "d_max": max(d_vals) if d_vals else 0.0,
            "d_min": min(d_vals) if d_vals else 0.0,
            "h_max": max(h_vals) if h_vals else 0.0,
            "s_mises_max": max(s_vals) if s_vals else 0.0,
            "miseseri_max": max(meri_vals) if meri_vals else 0.0,
            "miseseri_min": min(meri_vals) if meri_vals else 0.0,
            "miseseri_count": len(meri_vals),
            "broken_elements_d09": sum(1 for d in d_vals if d >= 0.90),
            "softened_elements_d05": sum(1 for d in d_vals if d >= 0.50),
            "damaged_elements_d01": sum(1 for d in d_vals if d >= 0.10)
        }
        audit_summary["key_frames"][kf_name] = kf_summary
        
        print("  d_max: %.6f, d >= 0.90: %d elements, d >= 0.50: %d elements" % (
            kf_summary["d_max"], kf_summary["broken_elements_d09"], kf_summary["softened_elements_d05"]
        ))
        print("  H_max: %.6e, S_mises_max: %.6e" % (kf_summary["h_max"], kf_summary["s_mises_max"]))
        print("  MISESERI: max=%.6e, min=%.6e, count=%d" % (
            kf_summary["miseseri_max"], kf_summary["miseseri_min"], kf_summary["miseseri_count"]
        ))
        
        # Store full element arrays for visualization
        fields_data[kf_name] = {
            "d": d_dict,
            "H": h_dict,
            "S_mises": s_dict,
            "MISESERI": meri_dict
        }
        
    with open(output_json, 'w') as f:
        json.dump(audit_summary, f, indent=2)
    print("Wrote audit summary to: %s" % output_json)
    
    with open(output_fields_json, 'w') as f:
        json.dump(fields_data, f)
    print("Wrote full fields data to: %s" % output_fields_json)
    
    odb.close()

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Usage: abaqus python extract_coarse_job1_results.py <odb_path> <output_json> <output_csv> <output_fields_json>")
        sys.exit(1)
    extract_results(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
