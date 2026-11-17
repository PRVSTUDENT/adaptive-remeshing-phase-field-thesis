# -*- coding: utf-8 -*-
"""
scripts/remeshing/extract_case2_pilot_donor.py
=============================================
Inspects candidate evolved frames (e.g. Frames 200, 250, 300, 330)
in PK_HOLE_COARSE_F1838_PILOT.odb, evaluates their untouched native error distribution,
and extracts the chosen single evolved frame into a compact donor ODB for native remeshing.
"""
from __future__ import print_function
import os
import sys
import json
import odbAccess
from abaqusConstants import SCALAR, WHOLE_ELEMENT

def main():
    odb_path = "PK_HOLE_COARSE_F1838_PILOT.odb"
    if not os.path.exists(odb_path):
        if len(sys.argv) > 1:
            odb_path = sys.argv[1]
            
    print("="*80)
    print("INSPECTING CANDIDATE EVOLVED FRAMES IN: %s" % odb_path)
    print("="*80)
    
    odb = odbAccess.openOdb(odb_path, readOnly=True)
    inst = list(odb.rootAssembly.instances.values())[0]
    node_coords = {n.label: n.coordinates for n in inst.nodes}
    elem_centroids = {}
    for e in inst.elements:
        conn = e.connectivity
        xs = [node_coords[nl][0] for nl in conn]
        ys = [node_coords[nl][1] for nl in conn]
        elem_centroids[e.label] = (sum(xs)/len(xs), sum(ys)/len(ys))
        
    s2 = odb.steps['Step-2']
    
    # Define Case 2 regions:
    # Primary ligament: x in [0.0, 0.45], y in [0.45, 0.55]
    # Hole center is at (0.45, 0.65), radius = 0.10 -> hole extends x in [0.35, 0.55], y in [0.55, 0.75]
    # Outermost distal ligament: x in [0.55, 1.0], y in [0.55, 0.75]
    # Far-field: everywhere else
    
    candidate_frames = [167, 200, 250, 300, 330]
    results = {}
    
    for fi in candidate_frames:
        if fi >= len(s2.frames):
            continue
        fr = s2.frames[fi]
        eri_fo = fr.fieldOutputs["MISESERI"]
        avg_fo = fr.fieldOutputs["MISESAVG"]
        sdv_fo = fr.fieldOutputs["SDV1"]
        
        eri_dict = {v.elementLabel: float(v.data) for v in eri_fo.values}
        avg_dict = {v.elementLabel: float(v.data) for v in avg_fo.values}
        d_dict   = {v.elementLabel: float(v.data) for v in sdv_fo.values}
        
        # Relative error
        eta_dict = {}
        for el in eri_dict:
            a = avg_dict.get(el, 1.0)
            eta_dict[el] = (eri_dict[el] / a) if a > 0 else 0.0
            
        # Count elements over 4.0% error target in different regions
        target_eta = 0.040
        over_target = [el for el, eta in eta_dict.items() if eta >= target_eta]
        
        distal_over = []
        primary_over = []
        farfield_over = []
        
        for el in over_target:
            cx, cy = elem_centroids[el]
            if cx >= 0.55 and 0.50 <= cy <= 0.80:
                distal_over.append(el)
            elif cx <= 0.55 and 0.40 <= cy <= 0.70:
                primary_over.append(el)
            else:
                farfield_over.append(el)
                
        d_max = max(d_dict.values())
        print("Frame %3d (t=%.4f): d_max=%.4f | Over 4.0%%: %d total (Primary: %d, Distal: %d, Far-field: %d)" % 
              (fi, fr.frameValue, d_max, len(over_target), len(primary_over), len(distal_over), len(farfield_over)))
              
        results[fi] = {
            "time": float(fr.frameValue),
            "d_max": float(d_max),
            "total_over_target": len(over_target),
            "primary_over_target": len(primary_over),
            "distal_over_target": len(distal_over),
            "farfield_over_target": len(farfield_over)
        }
        
    odb.close()
    
    # Let's save this audit
    with open("case2_candidate_frames_audit.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Candidate frames audit saved to case2_candidate_frames_audit.json")

if __name__ == "__main__":
    main()
