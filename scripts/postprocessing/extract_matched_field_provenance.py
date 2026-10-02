#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract comprehensive matched-displacement field provenance for H1, H2, PK10R2, and PK10R3.
"""

import sys
import os
import json
import numpy as np

ROOT = "/home/pr21vyci/projects/adaptive-remeshing"
if not os.path.exists(ROOT):
    ROOT = "D:/Master thesis/Adaptive remeshing"

from odbAccess import openOdb

def parse_mesh_structure(inp_path):
    nodes = {}
    phase_elems = {} # 1..N_phys
    mech_elems = {}  # N_phys+1..2*N_phys
    
    with open(inp_path, 'r') as f:
        reading_nodes = False
        reading_elems = False
        elem_type = None
        
        for line in f:
            line_s = line.strip()
            if "*NODE" in line_s.upper() and "*OUTPUT" not in line_s.upper():
                reading_nodes = True
                reading_elems = False
                continue
            elif "*ELEMENT" in line_s.upper():
                reading_nodes = False
                reading_elems = True
                if "TYPE=U1" in line_s.upper():
                    elem_type = "PHASE"
                elif "TYPE=U2" in line_s.upper():
                    elem_type = "MECH"
                else:
                    elem_type = "VIS"
                continue
            elif line_s.startswith("*"):
                reading_nodes = False
                reading_elems = False
                continue
                
            if reading_nodes:
                parts = line_s.split(",")
                if len(parts) >= 3:
                    try:
                        nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    except: pass
            elif reading_elems:
                parts = line_s.split(",")
                if len(parts) >= 5:
                    try:
                        eid = int(parts[0])
                        conn = [int(parts[i]) for i in range(1, 5)]
                        if elem_type == "PHASE":
                            phase_elems[eid] = conn
                        elif elem_type == "MECH":
                            mech_elems[eid] = conn
                    except: pass
                    
    return nodes, phase_elems, mech_elems

def analyze_model_fields(odb_path, inp_path, model_id, n_phys, is_uel=True):
    print("================================================================================")
    print("FIELD PROVENANCE EXTRACTION: %s" % model_id)
    print("ODB: %s" % odb_path)
    print("INP: %s" % inp_path)
    print("================================================================================")
    
    nodes, phase_elems, mech_elems = parse_mesh_structure(inp_path)
    print("Parsed %d nodes, %d phase quads, %d mech quads" % (len(nodes), len(phase_elems), len(mech_elems)))
    
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps[odb.steps.keys()[0]]
    
    target_disps = [0.005, 0.010, 0.0125, 0.020, 0.035, 0.050]
    matched_data = []
    
    for td in target_disps:
        best_f_idx = 0
        min_diff = 1e9
        for i, f in enumerate(step.frames):
            diff = abs(float(f.frameValue) - td)
            if diff < min_diff:
                min_diff = diff
                best_f_idx = i
                
        best_frame = step.frames[best_f_idx]
        t_val = float(best_frame.frameValue)
        
        # Extract max U3 / d
        max_d = 0.0
        max_d_node = None
        max_d_elem = None
        
        if 'U' in best_frame.fieldOutputs:
            for val in best_frame.fieldOutputs['U'].values:
                if len(val.data) >= 3:
                    d_val = float(val.data[2])
                    if d_val > max_d:
                        max_d = d_val
                        max_d_node = val.nodeLabel
                        
        max_h = 0.0
        max_h_elem = None
        max_h_pt = None
        
        # Check SDVs
        if 'SDV' in best_frame.fieldOutputs:
            for val in best_frame.fieldOutputs['SDV'].values:
                data = val.data
                eid = val.elementLabel
                if isinstance(data, (list, tuple, np.ndarray)):
                    if len(data) >= 9:
                        d_v = float(data[8])
                        if d_v > max_d:
                            max_d = d_v
                            max_d_elem = eid
                    if len(data) >= 13:
                        h_v = float(data[12])
                        if h_v > max_h:
                            max_h = h_v
                            max_h_elem = eid
                            max_h_pt = getattr(val, 'integrationPoint', 1)
                            
        node_coord = nodes.get(max_d_node, (0.0, 0.0)) if max_d_node else None
        
        elem_coord = None
        if max_h_elem:
            phys_id = max_h_elem - n_phys if max_h_elem > n_phys else max_h_elem
            if phys_id in mech_elems:
                conn = mech_elems[phys_id]
                coords = [nodes[n] for n in conn if n in nodes]
                elem_coord = (sum([c[0] for c in coords])/4.0, sum([c[1] for c in coords])/4.0)
            elif phys_id in phase_elems:
                conn = phase_elems[phys_id]
                coords = [nodes[n] for n in conn if n in nodes]
                elem_coord = (sum([c[0] for c in coords])/4.0, sum([c[1] for c in coords])/4.0)
                
        rec = {
            "target_u1_mm": td,
            "matched_frame": best_f_idx,
            "matched_u1_mm": t_val,
            "max_d": max_d,
            "max_d_node": max_d_node,
            "max_d_node_coords": node_coord,
            "max_d_elem": max_d_elem,
            "max_H_kN_mm2": max_h,
            "max_H_elem": max_h_elem,
            "max_H_elem_coords": elem_coord,
            "max_H_int_pt": max_h_pt
        }
        matched_data.append(rec)
        print("U1 = %.4f mm (Frame %3d, t = %.6f) | max(d) = %.6f (node %s, elem %s) | max(H) = %.6f kN/mm^2 (elem %s, pt %s, centroid %s)" % (
            td, best_f_idx, t_val, max_d, str(max_d_node), str(max_d_elem), max_h, str(max_h_elem), str(max_h_pt), str(elem_coord)))
            
    odb.close()
    return matched_data

if __name__ == "__main__":
    p_h1_odb = os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb")
    p_h1_inp = os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.inp")
    
    p_h2_odb = os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H2_FREEU2_FULL_U050/M2CORR_H2_FREEU2_FULL_U050.odb")
    p_h2_inp = os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H2_FREEU2_FULL_U050/M2CORR_H2_FREEU2_FULL_U050.inp")
    
    p_r2_odb = os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.odb")
    p_r2_inp = os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp")
    
    p_r3_odb = os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.odb")
    p_r3_inp = os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.inp")
    
    h1_prov = analyze_model_fields(p_h1_odb, p_h1_inp, "H1_UNIFORM_FINE", 12064, is_uel=False)
    h2_prov = analyze_model_fields(p_h2_odb, p_h2_inp, "H2_UNIFORM_ULTRAFINE", 33852, is_uel=False)
    r2_prov = analyze_model_fields(p_r2_odb, p_r2_inp, "PK10R2_TOPOLOGY_CORRECTED", 6048, is_uel=True)
    r3_prov = analyze_model_fields(p_r3_odb, p_r3_inp, "PK10R3_REFINED_TIP", 17732, is_uel=True)
    
    full_prov = {
        "H1_UNIFORM_FINE": h1_prov,
        "H2_UNIFORM_ULTRAFINE": h2_prov,
        "PK10R2_TOPOLOGY_CORRECTED": r2_prov,
        "PK10R3_REFINED_TIP": r3_prov
    }
    
    out_json = os.path.join(ROOT, "docs/studies/matched_field_provenance.json")
    with open(out_json, "w") as fp:
        json.dump(full_prov, fp, indent=2)
    print("\nSaved matched field provenance to %s" % out_json)
