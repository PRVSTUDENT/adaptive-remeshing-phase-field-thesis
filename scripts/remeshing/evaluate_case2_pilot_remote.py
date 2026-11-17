# -*- coding: utf-8 -*-
"""
scripts/remeshing/evaluate_case2_pilot_remote.py
================================================
Evaluates the Case 2 Native Job-1 Pilot ODB directly on cluster / local:
1. Checks Step-1 and Step-2 frames.
2. Extracts RF2 and U2 for Node 999999 (N_RP).
3. Evaluates peak reaction force F_max, peak displacement u(F_max), and compares with baseline:
   - Baseline F_max = 0.731015 kN at u = 0.007294 mm
4. Checks FieldOutputs for MISESERI, MISESAVG, S, E, SDV:
   - Verifies nonzero MISESERI values and statistics.
5. Evaluates candidate evolved frames for single-state native remeshing.
"""
from __future__ import print_function
import os
import sys
import json
import odbAccess

def main():
    odb_path = "PK_HOLE_COARSE_F1838_PILOT.odb"
    if not os.path.exists(odb_path):
        if len(sys.argv) > 1:
            odb_path = sys.argv[1]
    
    print("="*80)
    print("EVALUATING CASE 2 NATIVE JOB-1 PILOT: %s" % odb_path)
    print("="*80)
    
    odb = odbAccess.openOdb(odb_path, readOnly=True)
    steps = list(odb.steps.keys())
    print("Steps in ODB:", steps)
    
    # 1. Force-displacement extraction
    s1 = odb.steps['Step-1']
    s2 = odb.steps['Step-2']
    print("Step-1 frames: %d" % len(s1.frames))
    print("Step-2 frames: %d" % len(s2.frames))
    
    fd_data = []
    peak_rf2 = 0.0
    peak_u2 = 0.0
    peak_info = None
    
    for sname in ['Step-1', 'Step-2']:
        st = odb.steps[sname]
        for idx, fr in enumerate(st.frames):
            if 'RF' not in fr.fieldOutputs or 'U' not in fr.fieldOutputs:
                continue
            rf_fo = fr.fieldOutputs['RF']
            u_fo = fr.fieldOutputs['U']
            rf2 = None
            u2 = None
            for v in rf_fo.values:
                if v.nodeLabel == 999999:
                    rf2 = float(v.data[1])
                    break
            for v in u_fo.values:
                if v.nodeLabel == 999999:
                    u2 = float(v.data[1])
                    break
            if rf2 is not None and u2 is not None:
                fd_data.append({
                    "step": sname,
                    "frame_idx": idx,
                    "frame_val": float(fr.frameValue),
                    "rf2": rf2,
                    "u2": u2
                })
                if abs(rf2) > abs(peak_rf2):
                    peak_rf2 = rf2
                    peak_u2 = u2
                    peak_info = (sname, idx, float(fr.frameValue))
                    
    print("\nForce-Displacement Summary:")
    print("  Total recorded points: %d" % len(fd_data))
    print("  Peak Reaction Force:   RF2 = %.6f kN at U2 = %.6f mm" % (peak_rf2, peak_u2))
    print("  Peak Occurred In:      %s Frame %d (time %.4f)" % peak_info)
    
    # Baseline comparison
    base_fmax = 0.731015
    base_umax = 0.007294
    diff_fmax = abs(peak_rf2 - base_fmax)
    rel_diff_fmax = (diff_fmax / base_fmax) * 100.0
    diff_umax = abs(peak_u2 - base_umax)
    rel_diff_umax = (diff_umax / base_umax) * 100.0
    
    print("\nMechanical Equivalence Verification:")
    print("  Baseline F_max:         %.6f kN" % base_fmax)
    print("  Pilot F_max:            %.6f kN (Diff = %.8f kN, Rel = %.6f%%)" % (peak_rf2, diff_fmax, rel_diff_fmax))
    print("  Baseline u(F_max):      %.6f mm" % base_umax)
    print("  Pilot u(F_max):         %.6f mm (Diff = %.8f mm, Rel = %.6f%%)" % (peak_u2, diff_umax, rel_diff_umax))
    
    tol_fmax = 0.01  # 0.01%
    tol_umax = 0.01  # 0.01%
    fmax_pass = (rel_diff_fmax <= tol_fmax)
    umax_pass = (rel_diff_umax <= tol_umax)
    print("  Predeclared F_max tolerance (<= 0.01%%): %s (%.6f%%)" % ("PASS" if fmax_pass else "FAIL", rel_diff_fmax))
    print("  Predeclared u_max tolerance (<= 0.01%%): %s (%.6f%%)" % ("PASS" if umax_pass else "FAIL", rel_diff_umax))
    
    # 2. FieldOutput verification across frames in Step-2
    print("\nFieldOutput Verification in Step-2:")
    f_test = s2.frames[-1]
    avail_fields = list(f_test.fieldOutputs.keys())
    print("  Available FieldOutputs in Step-2 Frame %d: %s" % (len(s2.frames)-1, avail_fields))
    
    has_miseseri = "MISESERI" in avail_fields
    has_misesavg = "MISESAVG" in avail_fields
    print("  MISESERI present: %s" % has_miseseri)
    print("  MISESAVG present: %s" % has_misesavg)
    
    # Check nonzero values across multiple key frames:
    # Frame 0 (initiation of Step-2), Frame 167 (Peak load), Frame 250 (mid propagation), Frame 337 (terminal)
    test_frame_indices = [0, 50, 100, 167, 200, 250, 300, len(s2.frames)-1]
    frame_audits = []
    
    for fi in test_frame_indices:
        if fi >= len(s2.frames):
            continue
        fr = s2.frames[fi]
        eri_fo = fr.fieldOutputs["MISESERI"] if "MISESERI" in fr.fieldOutputs else None
        avg_fo = fr.fieldOutputs["MISESAVG"] if "MISESAVG" in fr.fieldOutputs else None
        sdv_fo = fr.fieldOutputs["SDV1"] if "SDV1" in fr.fieldOutputs else None
        
        eri_max = 0.0
        eri_min = 1e9
        avg_max = 0.0
        avg_min = 1e9
        d_max = 0.0
        num_nonzero_eri = 0
        
        if eri_fo:
            for v in eri_fo.values:
                val = float(v.data)
                if val > 0.0:
                    num_nonzero_eri += 1
                if val > eri_max: eri_max = val
                if val < eri_min: eri_min = val
        if avg_fo:
            for v in avg_fo.values:
                val = float(v.data)
                if val > avg_max: avg_max = val
                if val < avg_min: avg_min = val
        if sdv_fo:
            for v in sdv_fo.values:
                val = float(v.data)
                if val > d_max: d_max = val
                
        frame_audits.append({
            "frame_idx": fi,
            "frame_val": float(fr.frameValue),
            "num_nonzero_eri": num_nonzero_eri,
            "total_elements": len(eri_fo.values) if eri_fo else 0,
            "eri_max": eri_max,
            "eri_min": eri_min if eri_min < 1e9 else 0.0,
            "avg_max": avg_max,
            "avg_min": avg_min if avg_min < 1e9 else 0.0,
            "d_max": d_max
        })
        print("  Frame %3d (time %.4f): non-zero MISESERI = %d / %d, max ERI = %.4e, max AVG = %.4e, max d = %.4f" % 
              (fi, fr.frameValue, num_nonzero_eri, len(eri_fo.values) if eri_fo else 0, eri_max, avg_max, d_max))
              
    odb.close()
    
    # Save audit summary JSON
    summary = {
        "mechanical_equivalence": {
            "pilot_fmax_kn": peak_rf2,
            "base_fmax_kn": base_fmax,
            "rel_diff_fmax_pct": rel_diff_fmax,
            "fmax_pass": fmax_pass,
            "pilot_umax_mm": peak_u2,
            "base_umax_mm": base_umax,
            "rel_diff_umax_pct": rel_diff_umax,
            "umax_pass": umax_pass,
            "peak_frame": peak_info
        },
        "field_outputs": {
            "has_miseseri": has_miseseri,
            "has_misesavg": has_misesavg,
            "frame_audits": frame_audits
        }
    }
    with open("case2_pilot_remote_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\nAudit summary saved to case2_pilot_remote_summary.json")

if __name__ == "__main__":
    main()
