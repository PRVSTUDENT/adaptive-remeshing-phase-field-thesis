# -*- coding: utf-8 -*-
"""
audit_f1714_mesh_quality.py
Audit finite-element mesh quality, signed isoparametric Jacobians, aspect ratios,
and local resolution near all five holes for PK_F1714_JOB2_ADAPTED_PHYS.inp.
"""
from __future__ import print_function
import os
import sys
import math
import json

def audit_mesh(phys_inp, out_json):
    nodes = {}
    elements = {}
    elem_types = {}
    
    in_nodes = False
    in_elems = False
    cur_type = None
    
    with open(phys_inp, 'r') as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith('**'):
                continue
            if l.startswith('*'):
                in_nodes = False
                in_elems = False
                if l.upper().startswith('*NODE'):
                    in_nodes = True
                elif l.upper().startswith('*ELEMENT'):
                    in_elems = True
                    if 'CPE4' in l.upper() or 'CPS4' in l.upper() or 'QUAD' in l.upper():
                        cur_type = 'QUAD'
                    elif 'CPE3' in l.upper() or 'CPS3' in l.upper() or 'TRI' in l.upper():
                        cur_type = 'TRI'
                    else:
                        cur_type = 'QUAD'
                continue
                
            if in_nodes:
                parts = [p.strip() for p in l.split(',') if p.strip()]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        nodes[nid] = (float(parts[1]), float(parts[2]))
                    except ValueError:
                        pass
            elif in_elems:
                parts = [p.strip() for p in l.split(',') if p.strip()]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        conn = [int(p) for p in parts[1:]]
                        if cur_type == 'QUAD' or len(conn) == 4:
                            elements[eid] = tuple(conn[:4])
                            elem_types[eid] = 'QUAD'
                        else:
                            elements[eid] = tuple(conn[:3])
                            elem_types[eid] = 'TRI'
                    except ValueError:
                        pass
                        
    n_elems = len(elements)
    n_nodes = len(nodes)
    n_quads = sum(1 for t in elem_types.values() if t == 'QUAD')
    n_tris = sum(1 for t in elem_types.values() if t == 'TRI')
    
    # 1. Jacobian and Aspect Ratio Auditing
    jacobians = []
    aspect_ratios = []
    min_angles = []
    elem_sizes = {}
    
    inverted_elements = []
    
    for eid, conn in elements.items():
        coords = [nodes[nid] for nid in conn]
        
        if elem_types[eid] == 'QUAD':
            # 4 Gauss points for 2x2 integration
            # Shape function derivatives
            gps = [-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)]
            min_detj = 1e30
            for xi in gps:
                for eta in gps:
                    dn_dxi = [
                        -0.25 * (1.0 - eta),
                         0.25 * (1.0 - eta),
                         0.25 * (1.0 + eta),
                        -0.25 * (1.0 + eta)
                    ]
                    dn_deta = [
                        -0.25 * (1.0 - xi),
                        -0.25 * (1.0 + xi),
                         0.25 * (1.0 + xi),
                         0.25 * (1.0 - xi)
                    ]
                    j11 = sum(dn_dxi[k] * coords[k][0] for k in range(4))
                    j12 = sum(dn_dxi[k] * coords[k][1] for k in range(4))
                    j21 = sum(dn_deta[k] * coords[k][0] for k in range(4))
                    j22 = sum(dn_deta[k] * coords[k][1] for k in range(4))
                    detj = j11 * j22 - j12 * j21
                    if detj < min_detj:
                        min_detj = detj
            jacobians.append(min_detj)
            if min_detj <= 0.0:
                inverted_elements.append(eid)
                
            # Edge lengths
            edge_lens = [
                math.hypot(coords[1][0] - coords[0][0], coords[1][1] - coords[0][1]),
                math.hypot(coords[2][0] - coords[1][0], coords[2][1] - coords[1][1]),
                math.hypot(coords[3][0] - coords[2][0], coords[3][1] - coords[2][1]),
                math.hypot(coords[0][0] - coords[3][0], coords[0][1] - coords[3][1])
            ]
            ar = max(edge_lens) / max(min(edge_lens), 1e-12)
            aspect_ratios.append(ar)
            h_char = math.sqrt(sum(e**2 for e in edge_lens) / 4.0)
            elem_sizes[eid] = h_char
            
        elif elem_types[eid] == 'TRI':
            x1, y1 = coords[0]
            x2, y2 = coords[1]
            x3, y3 = coords[2]
            detj = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
            jacobians.append(detj)
            if detj <= 0.0:
                inverted_elements.append(eid)
                
            e1 = math.hypot(x2 - x1, y2 - y1)
            e2 = math.hypot(x3 - x2, y3 - y2)
            e3 = math.hypot(x1 - x3, y1 - y3)
            edge_lens = [e1, e2, e3]
            ar = max(edge_lens) / max(min(edge_lens), 1e-12)
            aspect_ratios.append(ar)
            h_char = math.sqrt(sum(e**2 for e in edge_lens) / 3.0)
            elem_sizes[eid] = h_char
            
    # 2. Void Proximity & Ligament Resolution Auditing
    # Table 5 holes:
    holes = {
        "h1": {"center": (0.000, 0.500), "radius": 0.100},
        "h2": {"center": (0.350, 0.450), "radius": 0.100},
        "h3": {"center": (0.600, 0.550), "radius": 0.050},
        "h4": {"center": (0.750, 0.500), "radius": 0.075},
        "h5": {"center": (1.000, 0.450), "radius": 0.075}
    }
    
    l0 = 0.008  # 8 um
    
    hole_resolution = {}
    for hname, hinfo in holes.items():
        xc, yc = hinfo["center"]
        r = hinfo["radius"]
        
        # Elements touching or within 2*l0 of hole boundary
        near_elem_sizes = []
        for eid, conn in elements.items():
            cx = sum(nodes[nid][0] for nid in conn) / len(conn)
            cy = sum(nodes[nid][1] for nid in conn) / len(conn)
            dist_center = math.hypot(cx - xc, cy - yc)
            dist_boundary = abs(dist_center - r)
            if dist_boundary <= 2.5 * l0:
                near_elem_sizes.append(elem_sizes[eid])
                
        min_h_hole = min(near_elem_sizes) if near_elem_sizes else 0.0
        mean_h_hole = sum(near_elem_sizes) / len(near_elem_sizes) if near_elem_sizes else 0.0
        hole_resolution[hname] = {
            "num_elements_near": len(near_elem_sizes),
            "min_h_mm": min_h_hole,
            "min_h_over_l0": min_h_hole / l0,
            "mean_h_mm": mean_h_hole,
            "mean_h_over_l0": mean_h_hole / l0,
            "adequate_refinement": min_h_hole <= 0.5 * l0
        }
        
    audit_report = {
        "task_id": "F1714-FIVE-HOLE-GENERALIZATION-BENCHMARK",
        "mesh_source": phys_inp,
        "topology": {
            "total_physical_elements": n_elems,
            "total_nodes": n_nodes,
            "quad_count": n_quads,
            "tri_count": n_tris,
            "quad_fraction_pct": round(100.0 * n_quads / float(n_elems), 2)
        },
        "quality_metrics": {
            "min_jacobian": min(jacobians) if jacobians else 0.0,
            "max_jacobian": max(jacobians) if jacobians else 0.0,
            "positive_jacobian_rate_pct": round(100.0 * (n_elems - len(inverted_elements)) / float(n_elems), 4),
            "inverted_element_count": len(inverted_elements),
            "min_aspect_ratio": min(aspect_ratios) if aspect_ratios else 0.0,
            "max_aspect_ratio": max(aspect_ratios) if aspect_ratios else 0.0,
            "mean_aspect_ratio": sum(aspect_ratios) / len(aspect_ratios) if aspect_ratios else 0.0
        },
        "resolution_telemetry": {
            "min_global_h_mm": min(elem_sizes.values()) if elem_sizes else 0.0,
            "max_global_h_mm": max(elem_sizes.values()) if elem_sizes else 0.0,
            "mean_global_h_mm": sum(elem_sizes.values()) / len(elem_sizes) if elem_sizes else 0.0,
            "min_global_h_over_l0": (min(elem_sizes.values()) / l0) if elem_sizes else 0.0,
            "hole_neighborhoods": hole_resolution
        },
        "verification_verdict": "PASS" if len(inverted_elements) == 0 else "FAIL"
    }
    
    with open(out_json, 'w') as f:
        json.dump(audit_report, f, indent=2)
        
    print("=================================================================")
    print("MESH QUALITY AUDIT SUMMARY:")
    print("Total Elements: %d (%d quads [%.1f%%], %d tris)" % (
        n_elems, n_quads, 100.0 * n_quads / float(n_elems), n_tris
    ))
    print("Positive Jacobians: %.2f%% (Inverted: %d)" % (
        audit_report["quality_metrics"]["positive_jacobian_rate_pct"], len(inverted_elements)
    ))
    print("Aspect Ratios: min = %.2f, max = %.2f, mean = %.2f" % (
        audit_report["quality_metrics"]["min_aspect_ratio"],
        audit_report["quality_metrics"]["max_aspect_ratio"],
        audit_report["quality_metrics"]["mean_aspect_ratio"]
    ))
    print("Global Resolution: min h = %.4f mm (%.3f * l0), max h = %.4f mm" % (
        audit_report["resolution_telemetry"]["min_global_h_mm"],
        audit_report["resolution_telemetry"]["min_global_h_over_l0"],
        audit_report["resolution_telemetry"]["max_global_h_mm"]
    ))
    for hname, hres in hole_resolution.items():
        print("  Hole %s: min h = %.4f mm (%.2f * l0), mean h = %.4f mm (elements: %d)" % (
            hname, hres["min_h_mm"], hres["min_h_over_l0"], hres["mean_h_mm"], hres["num_elements_near"]
        ))
    print("VERDICT: %s" % audit_report["verification_verdict"])
    print("=================================================================")
    return audit_report

if __name__ == "__main__":
    phys_inp = "models/pandey_kumar_mode1/207_f1714_five_hole_benchmark/PK_F1714_JOB2_ADAPTED_PHYS.inp"
    out_json = "models/pandey_kumar_mode1/207_f1714_five_hole_benchmark/F1714_MESH_QUALITY_REPORT.json"
    audit_mesh(phys_inp, out_json)
