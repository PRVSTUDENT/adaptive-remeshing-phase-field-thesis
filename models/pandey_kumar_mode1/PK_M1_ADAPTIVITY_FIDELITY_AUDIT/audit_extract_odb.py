# -*- coding: utf-8 -*-
"""
Audit script for Pass-1 MISESERI extraction and mesh metrics.
Executed via: abaqus python audit_extract_odb.py <path_to_odb>
"""
import sys
import os
import json
import math
from odbAccess import openOdb

def analyze_preanalysis_odb(odb_path):
    print("Opening ODB: " + str(odb_path))
    if not os.path.exists(odb_path):
        print("ERROR: ODB file not found: " + str(odb_path))
        return None

    odb = openOdb(path=odb_path, readOnly=True)
    step_names = list(odb.steps.keys())
    print("Steps in ODB: " + str(step_names))
    
    step = odb.steps[step_names[0]]
    last_frame = step.frames[-1]
    print("Frame: %s (time=%f)" % (last_frame.description, last_frame.frameValue))

    field_keys = list(last_frame.fieldOutputs.keys())
    print("Field outputs available: " + str(field_keys))

    miseseri_field = None
    if 'MISESERI' in last_frame.fieldOutputs:
        miseseri_field = last_frame.fieldOutputs['MISESERI']
    else:
        print("WARNING: MISESERI not in fieldOutputs directly.")
        for k in field_keys:
            if 'MISESERI' in k.upper():
                miseseri_field = last_frame.fieldOutputs[k]
                print("Found match: " + k)
                break

    root_inst = odb.rootAssembly.instances['PLATE-1'] if 'PLATE-1' in odb.rootAssembly.instances else odb.rootAssembly.instances.values()[0]
    num_elems = len(root_inst.elements)
    num_nodes = len(root_inst.nodes)
    print("Instance %s: %d elements, %d nodes" % (root_inst.name, num_elems, num_nodes))

    # Node coordinates map
    node_coords = {}
    for n in root_inst.nodes:
        node_coords[n.label] = n.coordinates

    # Element data
    elem_centroids = {}
    elem_areas = {}
    elem_h = {}
    for el in root_inst.elements:
        conn = el.connectivity
        pts = [node_coords[nl] for nl in conn]
        cx = sum([p[0] for p in pts]) / float(len(pts))
        cy = sum([p[1] for p in pts]) / float(len(pts))
        elem_centroids[el.label] = (cx, cy)
        
        # Area via shoelace
        if len(pts) == 4:
            area = 0.5 * abs((pts[0][0]*pts[1][1] - pts[1][0]*pts[0][1]) +
                             (pts[1][0]*pts[2][1] - pts[2][0]*pts[1][1]) +
                             (pts[2][0]*pts[3][1] - pts[3][0]*pts[2][1]) +
                             (pts[3][0]*pts[0][1] - pts[0][0]*pts[3][1]))
        elif len(pts) == 3:
            area = 0.5 * abs((pts[0][0]*(pts[1][1] - pts[2][1])) +
                             (pts[1][0]*(pts[2][1] - pts[0][1])) +
                             (pts[2][0]*(pts[0][1] - pts[1][1])))
        else:
            area = 0.0
        elem_areas[el.label] = area
        elem_h[el.label] = math.sqrt(area) if area > 0 else 0.0

    # Extract MISESERI per element
    elem_miseseri = {}
    if miseseri_field is not None:
        for val in miseseri_field.values:
            el_id = val.elementLabel
            # If multiple integration points, take max or average
            m_val = float(val.data) if hasattr(val, 'data') and isinstance(val.data, (int, float)) else float(val.dataDouble) if hasattr(val, 'dataDouble') else float(val.magnitude) if hasattr(val, 'magnitude') else 0.0
            if el_id not in elem_miseseri:
                elem_miseseri[el_id] = []
            elem_miseseri[el_id].append(m_val)

    # Summarize per element (take max across IP)
    elem_miseseri_max = {el_id: max(vals) for el_id, vals in elem_miseseri.items()}
    values_list = sorted(elem_miseseri_max.values()) if elem_miseseri_max else []

    stats = {}
    if values_list:
        n_vals = len(values_list)
        stats['count'] = n_vals
        stats['min'] = values_list[0]
        stats['max'] = values_list[-1]
        stats['mean'] = sum(values_list) / float(n_vals)
        stats['p25'] = values_list[int(0.25 * n_vals)]
        stats['p50'] = values_list[int(0.50 * n_vals)]
        stats['p75'] = values_list[int(0.75 * n_vals)]
        stats['p90'] = values_list[int(0.90 * n_vals)]
        stats['p95'] = values_list[int(0.95 * n_vals)]
        stats['p99'] = values_list[int(0.99 * n_vals)]
        print("MISESERI Stats: min=%f, max=%f, mean=%f, p50=%f, p90=%f, p95=%f, p99=%f" %
              (stats['min'], stats['max'], stats['mean'], stats['p50'], stats['p90'], stats['p95'], stats['p99']))

    # Analyze elements marked under different relative error thresholds
    # In literature: relative error = MISESERI_i / max(MISESERI)
    max_m = stats.get('max', 1.0) if stats.get('max', 0.0) > 0 else 1.0
    thresholds = [0.01, 0.02, 0.05, 0.10, 0.20, 0.50]
    marking_stats = {}
    for th in thresholds:
        marked = [el_id for el_id, m_val in elem_miseseri_max.items() if (m_val / max_m) >= th]
        marking_stats[str(th*100) + "%"] = {
            "marked_elements": len(marked),
            "total_elements": num_elems,
            "fraction": len(marked) / float(num_elems) if num_elems > 0 else 0.0
        }
        print("Threshold >= %.1f%% of max: %d / %d elements (%.2f%%)" % 
              (th*100, len(marked), num_elems, 100.0 * len(marked) / float(num_elems)))

    # Spatial correlation: distance from crack tip (0.5, 0.5)
    tip_x, tip_y = 0.5, 0.5
    distance_bins = [0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50, 1.00]
    dist_stats = {str(d): {"count": 0, "miseseri_avg": 0.0, "miseseri_max": 0.0, "vals": []} for d in distance_bins}
    
    # Slit flanks vs tip: x in [0.0, 0.5], y near 0.5
    slit_flank_elems = []
    tip_vicinity_elems = []
    far_field_elems = []
    
    for el_id, (cx, cy) in elem_centroids.items():
        m_val = elem_miseseri_max.get(el_id, 0.0)
        dist_tip = math.sqrt((cx - tip_x)**2 + (cy - tip_y)**2)
        dist_slit_y = abs(cy - 0.5)
        
        for d in distance_bins:
            if dist_tip <= d:
                dist_stats[str(d)]["vals"].append(m_val)
                break
                
        if cx < 0.45 and dist_slit_y < 0.05:
            slit_flank_elems.append((el_id, cx, cy, m_val))
        elif dist_tip <= 0.05:
            tip_vicinity_elems.append((el_id, cx, cy, m_val))
        else:
            far_field_elems.append((el_id, cx, cy, m_val))

    for d, d_data in dist_stats.items():
        v = d_data["vals"]
        d_data["count"] = len(v)
        d_data["miseseri_avg"] = sum(v)/float(len(v)) if v else 0.0
        d_data["miseseri_max"] = max(v) if v else 0.0
        del d_data["vals"]

    flank_m = [v[3] for v in slit_flank_elems]
    tip_m = [v[3] for v in tip_vicinity_elems]
    far_m = [v[3] for v in far_field_elems]

    spatial_zones = {
        "slit_flank_x_lt_045": {
            "count": len(slit_flank_elems),
            "miseseri_max": max(flank_m) if flank_m else 0.0,
            "miseseri_mean": sum(flank_m)/float(len(flank_m)) if flank_m else 0.0,
            "relative_to_max": (max(flank_m)/max_m) if flank_m and max_m > 0 else 0.0
        },
        "tip_vicinity_r_le_005": {
            "count": len(tip_vicinity_elems),
            "miseseri_max": max(tip_m) if tip_m else 0.0,
            "miseseri_mean": sum(tip_m)/float(len(tip_m)) if tip_m else 0.0,
            "relative_to_max": (max(tip_m)/max_m) if tip_m and max_m > 0 else 0.0
        },
        "far_field": {
            "count": len(far_field_elems),
            "miseseri_max": max(far_m) if far_m else 0.0,
            "miseseri_mean": sum(far_m)/float(len(far_m)) if far_m else 0.0,
            "relative_to_max": (max(far_m)/max_m) if far_m and max_m > 0 else 0.0
        }
    }

    result = {
        "num_elements": num_elems,
        "num_nodes": num_nodes,
        "miseseri_stats": stats,
        "marking_stats": marking_stats,
        "spatial_zones": spatial_zones,
        "distance_bins": dist_stats
    }
    
    odb.close()
    return result

if __name__ == '__main__':
    odb_p = sys.argv[1] if len(sys.argv) > 1 else '/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/02_proposed_adaptive_refined/PK_PREANALYSIS_COARSE.odb'
    res = analyze_preanalysis_odb(odb_p)
    out_json = sys.argv[2] if len(sys.argv) > 2 else 'odb_analysis_results.json'
    with open(out_json, 'w') as f:
        json.dump(res, f, indent=2)
    print("SUCCESS: Wrote results to " + out_json)
