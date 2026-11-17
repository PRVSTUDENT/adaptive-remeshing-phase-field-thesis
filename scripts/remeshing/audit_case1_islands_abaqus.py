# -*- coding: utf-8 -*-
"""
scripts/remeshing/audit_case1_islands_abaqus.py
===============================================
Abaqus Python script to deeply inspect Case 1 donor ODBs and trace
the origin of the isolated refinement islands (diagonal band, top edge, bottom edge).
"""
from __future__ import print_function
import os
import sys

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
import odbAccess

def main():
    envelope_odb_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "275_f1835_scale_invariant", "case1", "PK_CASE1_MULTISTATE_RECOVERY.odb")
    print("Opening envelope ODB: %s" % envelope_odb_path)
    odb = odbAccess.openOdb(envelope_odb_path, readOnly=True)
    
    # Check steps and frames
    print("Steps in envelope ODB:", list(odb.steps.keys()))
    step = odb.steps[list(odb.steps.keys())[0]]
    print("Num frames in step:", len(step.frames))
    for i, f in enumerate(step.frames):
        print("  Frame %d: desc='%s', value=%.4f" % (i, f.description, f.frameValue))
    
    last_frame = step.frames[-1]
    eri_field = last_frame.fieldOutputs["MISESERI"]
    avg_field = last_frame.fieldOutputs["MISESAVG"]
    evol_field = last_frame.fieldOutputs["EVOL"] if "EVOL" in last_frame.fieldOutputs else None
    
    # Get mesh coordinates for elements
    inst = list(odb.rootAssembly.instances.values())[0]
    elem_coords = {}
    node_coords = {n.label: n.coordinates for n in inst.nodes}
    for e in inst.elements:
        conn = e.connectivity
        xs = [node_coords[nl][0] for nl in conn]
        ys = [node_coords[nl][1] for nl in conn]
        elem_coords[e.label] = (sum(xs)/len(xs), sum(ys)/len(ys))
        
    print("Total elements in donor instance: %d" % len(inst.elements))
    
    eri_vals = {v.elementLabel: float(v.data) for v in eri_field.values}
    avg_vals = {v.elementLabel: float(v.data) for v in avg_field.values}
    
    # Compute eta
    eta_vals = {}
    for el in eri_vals:
        avg_val = avg_vals.get(el, 1.0)
        eta_vals[el] = (eri_vals[el] / avg_val) if avg_val > 0 else 0.0
        
    odb.close()
    
    # Sort elements by eta descending
    sorted_by_eta = sorted(eta_vals.items(), key=lambda x: x[1], reverse=True)
    print("\nTop 20 elements by eta in envelope frame:")
    print("  ElemID | (Centroid X, Y) | MISESERI | MISESAVG | eta (%)")
    for el, eta in sorted_by_eta[:20]:
        cx, cy = elem_coords.get(el, (0,0))
        print("  %6d | (%7.4f, %7.4f) | %10.4e | %10.4e | %8.2f%%" % 
              (el, cx, cy, eri_vals[el], avg_vals[el], eta*100.0))
              
    # Specifically check the diagonal band ~(0.2, 0.0) to ~(0.45, 0.65)
    print("\nChecking elements in the diagonal band ~(0.2, 0.0) to ~(0.45, 0.65):")
    diag_elements = []
    for el, (cx, cy) in elem_coords.items():
        if cx < 0.50 and cy < 0.70:
            dist_diag = abs(2.6*cx - cy - 0.52) / (2.6**2 + 1)**0.5
            if dist_diag < 0.05:
                diag_elements.append((el, cx, cy, eta_vals[el], eri_vals[el], avg_vals[el]))
                
    diag_elements.sort(key=lambda x: x[3], reverse=True)
    print("Found %d elements along the diagonal corridor. Top 10 by eta:" % len(diag_elements))
    for el, cx, cy, eta, eri, avg in diag_elements[:10]:
        print("  %6d | (%7.4f, %7.4f) | ERI=%10.4e | AVG=%10.4e | eta=%8.2f%%" % 
              (el, cx, cy, eri, avg, eta*100.0))
              
    # Check top edge elements (cy >= 0.90)
    print("\nChecking elements at top edge (cy >= 0.90):")
    top_elements = [(el, cx, cy, eta_vals[el], eri_vals[el], avg_vals[el]) 
                    for el, (cx, cy) in elem_coords.items() if cy >= 0.90]
    top_elements.sort(key=lambda x: x[3], reverse=True)
    print("Found %d elements at top edge. Top 10 by eta:" % len(top_elements))
    for el, cx, cy, eta, eri, avg in top_elements[:10]:
        print("  %6d | (%7.4f, %7.4f) | ERI=%10.4e | AVG=%10.4e | eta=%8.2f%%" % 
              (el, cx, cy, eri, avg, eta*100.0))
              
    # Check bottom edge elements (cy <= 0.10)
    print("\nChecking elements at bottom edge (cy <= 0.10):")
    bot_elements = [(el, cx, cy, eta_vals[el], eri_vals[el], avg_vals[el]) 
                    for el, (cx, cy) in elem_coords.items() if cy <= 0.10]
    bot_elements.sort(key=lambda x: x[3], reverse=True)
    print("Found %d elements at bottom edge. Top 10 by eta:" % len(bot_elements))
    for el, cx, cy, eta, eri, avg in bot_elements[:10]:
        print("  %6d | (%7.4f, %7.4f) | ERI=%10.4e | AVG=%10.4e | eta=%8.2f%%" % 
              (el, cx, cy, eri, avg, eta*100.0))

    # Now let's trace which of the 5 states produced the peak eta for these elements!
    print("\n" + "="*80)
    print("TRACING STATE-BY-STATE FOR DIAGONAL AND EDGE ELEMENTS")
    print("="*80)
    c1_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case1")
    state_names = [
        "PK_C1_STATE1_INITIATION.odb",
        "PK_C1_STATE2_EARLY_PROPAGATION.odb",
        "PK_C1_STATE3_MID_PROPAGATION.odb",
        "PK_C1_STATE4_OUTER_PROPAGATION.odb",
        "PK_C1_STATE5_TERMINAL_SEVERANCE.odb"
    ]
    state_data = {}
    for sname in state_names:
        spath = os.path.join(c1_dir, sname)
        so = odbAccess.openOdb(spath, readOnly=True)
        sf = so.steps["RECOVERY_STEP"].frames[-1]
        s_eri = {v.elementLabel: float(v.data) for v in sf.fieldOutputs["MISESERI"].values}
        s_avg = {v.elementLabel: float(v.data) for v in sf.fieldOutputs["MISESAVG"].values}
        so.close()
        state_data[sname] = (s_eri, s_avg)
        
    # For the top 5 diagonal elements, inspect all 5 states
    print("\nDetailed state breakdown for top diagonal elements:")
    for el, cx, cy, env_eta, _, _ in diag_elements[:5]:
        print("\nElement %d at (%.4f, %.4f), Envelope eta = %.2f%%:" % (el, cx, cy, env_eta*100.0))
        for sname in state_names:
            s_eri, s_avg = state_data[sname]
            e_val = s_eri.get(el, 0.0)
            a_val = s_avg.get(el, 0.0)
            r = (e_val / a_val * 100.0) if a_val > 0 else 0.0
            print("  %32s: ERI = %10.4e, AVG = %10.4e, eta = %8.2f%%" % (sname, e_val, a_val, r))

    # For the top 5 bottom-edge elements, inspect all 5 states
    print("\nDetailed state breakdown for bottom edge elements:")
    for el, cx, cy, env_eta, _, _ in bot_elements[:5]:
        print("\nElement %d at (%.4f, %.4f), Envelope eta = %.2f%%:" % (el, cx, cy, env_eta*100.0))
        for sname in state_names:
            s_eri, s_avg = state_data[sname]
            e_val = s_eri.get(el, 0.0)
            a_val = s_avg.get(el, 0.0)
            r = (e_val / a_val * 100.0) if a_val > 0 else 0.0
            print("  %32s: ERI = %10.4e, AVG = %10.4e, eta = %8.2f%%" % (sname, e_val, a_val, r))

    # Also check what coarse elements look like in the donor mesh!
    # Are there any element label mismatch or mesh distortion?
    print("\n" + "="*80)
    print("CHECKING DONOR TOPOLOGY AND ELEMENT LABEL INTEGRITY")
    print("="*80)
    # Check if elements are structured or unstructured
    print("Total donor elements: %d" % len(elem_coords))
    # Count elements with eta >= 4.5% (the remeshing threshold for Case 1)
    over_threshold = [el for el, eta in eta_vals.items() if eta >= 0.045]
    print("Elements in donor with eta >= 4.5%%: %d / %d (%.2f%%)" % 
          (len(over_threshold), len(eta_vals), len(over_threshold)*100.0/len(eta_vals)))

if __name__ == "__main__":
    main()
