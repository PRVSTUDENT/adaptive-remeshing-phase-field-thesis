# -*- coding: utf-8 -*-
import sys
import os
import json
from odbAccess import openOdb

def extract_propagation():
    odb_path = "/scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1/PK_SEC43_STAGGERED_JOB1.odb"
    print("Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)

    root_assembly = odb.rootAssembly
    nodes_dict = {}
    for inst_name, inst in root_assembly.instances.items():
        for n in inst.nodes:
            nodes_dict[n.label] = (float(n.coordinates[0]), float(n.coordinates[1]))

    elem_centroids = {}
    for inst_name, inst in root_assembly.instances.items():
        for el in inst.elements:
            conn = list(el.connectivity)
            pts = [nodes_dict[nid] for nid in conn if nid in nodes_dict]
            if len(pts) >= 3:
                cx = sum(p[0] for p in pts) / float(len(pts))
                cy = sum(p[1] for p in pts) / float(len(pts))
                elem_centroids[el.label] = (cx, cy)

    step1 = odb.steps['Step-1']
    target_frames = [40, 50, 60, 70, 80, 90, 100, 120, 150, 200]
    
    results = {}
    
    for f_idx in target_frames:
        f = step1.frames[f_idx]
        frame_val = float(f.frameValue)
        uy = frame_val * 1.0
        
        sdv1_field = None
        for k in f.fieldOutputs.keys():
            if 'SDV1' in k:
                sdv1_field = f.fieldOutputs[k]
                break
        
        elem_d = {}
        for v in sdv1_field.values:
            eid = v.elementLabel
            if eid not in elem_d:
                elem_d[eid] = []
            elem_d[eid].append(float(v.data))
        
        # average per element
        elem_avg_d = {}
        sec_cracked_elements = [] # elements in secondary corridor with d >= 0.5
        
        for eid, vals in elem_d.items():
            d = sum(vals) / float(len(vals))
            elem_avg_d[eid] = d
            if eid in elem_centroids:
                cx, cy = elem_centroids[eid]
                if cx >= 36.5 and 40.0 <= cy <= 60.0 and d >= 0.5:
                    sec_cracked_elements.append({
                        'eid': eid,
                        'cx': cx,
                        'cy': cy,
                        'damage': d
                    })
        
        # sort by cx
        sec_cracked_elements.sort(key=lambda item: item['cx'])
        
        if sec_cracked_elements:
            min_x = sec_cracked_elements[0]['cx']
            max_x = sec_cracked_elements[-1]['cx']
            crack_tip = sec_cracked_elements[-1]
            dist_from_hole = max_x - 46.50
            pct_ligament = (dist_from_hole / 18.50) * 100.0
        else:
            min_x = 46.50
            max_x = 46.50
            crack_tip = None
            dist_from_hole = 0.0
            pct_ligament = 0.0
            
        results[str(f_idx)] = {
            'frame_index': f_idx,
            'time': frame_val,
            'uy_mm': uy,
            'num_sec_cracked_elements_d05': len(sec_cracked_elements),
            'min_x': min_x,
            'max_x': max_x,
            'crack_tip': crack_tip,
            'dist_from_hole_mm': dist_from_hole,
            'pct_ligament': pct_ligament,
            'sec_elements': sec_cracked_elements
        }
        print("Frame %3d (uy = %.3f mm): %2d sec cracked els (d>=0.5), tip at x = %.2f mm (%.1f%% of ligament)" % (
            f_idx, uy, len(sec_cracked_elements), max_x, pct_ligament))
            
    odb.close()
    
    out_path = "/scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1/secondary_crack_propagation_timeline.json"
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print("Saved to %s" % out_path)

if __name__ == '__main__':
    extract_propagation()
