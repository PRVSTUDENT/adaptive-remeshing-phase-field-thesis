#!/usr/bin/env python3
"""
Deep Phase, Mesh, Tangent, and Field Analyzer for M2STATE_FRACFIX_RESTART2R6.
"""
import os
import sys
import re
import json
import math

def mean(lst):
    return sum(lst) / float(len(lst)) if lst else 0.0

def analyze():
    inp_path = "M2STATE_FRACFIX_RESTART2R6.inp"
    
    # 1. Parse Nodes
    nodes = {}
    with open(inp_path, "r") as f:
        in_nodes = False
        for line in f:
            line_s = line.strip()
            if line_s.startswith("*NODE"):
                in_nodes = True
                continue
            if line_s.startswith("*") and in_nodes:
                in_nodes = False
                break
            if in_nodes and line_s:
                parts = [p.strip() for p in line_s.split(",")]
                if len(parts) >= 3:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    
    print("Parsed %d physical nodes" % len(nodes))
    
    # 2. Parse Step 1 Prescribed Phase Boundary Conditions (Mapped Initial Phase)
    phase_bc = {} # nid -> prescribed d
    with open(inp_path, "r") as f:
        in_s1_bc = False
        for line in f:
            line_s = line.strip()
            if "*STEP, NAME=Step-1-PhaseInit" in line_s:
                in_s1_bc = True
                continue
            if in_s1_bc:
                if line_s.startswith("*OUTPUT") or line_s.startswith("*END STEP"):
                    in_s1_bc = False
                    break
                if line_s.startswith("*BOUNDARY"):
                    continue
                # Line format: nid, 3, 3, val
                parts = [p.strip() for p in line_s.split(",")]
                if len(parts) >= 4 and parts[1] == "3" and parts[2] == "3":
                    nid = int(parts[0])
                    val = float(parts[3])
                    phase_bc[nid] = val
                    
    print("Parsed %d Step-1 prescribed nodal phase values" % len(phase_bc))
    
    d_vals = list(phase_bc.values())
    d_min = min(d_vals)
    d_max = max(d_vals)
    d_mean = mean(d_vals)
    d_gt_0p1 = sum(1 for v in d_vals if v > 0.1)
    d_gt_0p5 = sum(1 for v in d_vals if v > 0.5)
    d_gt_0p9 = sum(1 for v in d_vals if v > 0.9)
    
    max_d_nid = [nid for nid, v in phase_bc.items() if v == d_max][0]
    max_d_coords = nodes[max_d_nid]
    
    print("\n--- PHASE FIELD IN INITIAL STATE (Step 1 Prescribed / Mapped Target) ---")
    print("d_min: %.6f, d_max: %.6f, d_mean: %.6f" % (d_min, d_max, d_mean))
    print("d > 0.1 count: %d, d > 0.5 count: %d, d > 0.9 count: %d" % (d_gt_0p1, d_gt_0p5, d_gt_0p9))
    print("d_max node: %d at coords (X=%.6f, Y=%.6f)" % (max_d_nid, max_d_coords[0], max_d_coords[1]))
    
    # 3. Parse Initial Conditions (History H)
    # 18-SDVs per element
    elem_H = {} # eid -> H
    with open(inp_path, "r") as f:
        in_ic = False
        current_eid = None
        sdv_buffer = []
        for line in f:
            line_s = line.strip()
            if line_s.startswith("*INITIAL CONDITIONS, TYPE=SOLUTION"):
                in_ic = True
                continue
            if in_ic:
                if line_s.startswith("*"):
                    in_ic = False
                    break
                parts = [p.strip() for p in line_s.split(",") if p.strip()]
                if not parts: continue
                # First line of an element starts with eid
                if not sdv_buffer:
                    current_eid = int(parts[0])
                    sdv_buffer.extend([float(x) for x in parts[1:]])
                else:
                    sdv_buffer.extend([float(x) for x in parts])
                    
                if len(sdv_buffer) >= 18:
                    # In 18-SDV layout:
                    # SDV1..12: strains/stresses, SDV13: unused/time, SDV14: carried_phase, SDV15: solved_phase, SDV16: history_H
                    sdv14 = sdv_buffer[13]
                    sdv15 = sdv_buffer[14]
                    sdv16 = sdv_buffer[15]
                    elem_H[current_eid] = {
                        "sdv14": sdv14,
                        "sdv15": sdv15,
                        "sdv16": sdv16
                    }
                    sdv_buffer = []
                    current_eid = None
                    
    print("\nParsed Initial Conditions for %d elements" % len(elem_H))
    h_vals = [v["sdv16"] for v in elem_H.values()]
    print("History H (SDV16): min=%.6e, max=%.6e, mean=%.6e" % (
        min(h_vals), max(h_vals), mean(h_vals)
    ))
    sdv14_vals = [v["sdv14"] for v in elem_H.values()]
    print("Carried Phase (SDV14): min=%.6e, max=%.6e, mean=%.6e" % (
        min(sdv14_vals), max(sdv14_vals), mean(sdv14_vals)
    ))
    sdv15_vals = [v["sdv15"] for v in elem_H.values()]
    print("Solved Phase (SDV15): min=%.6e, max=%.6e, mean=%.6e" % (
        min(sdv15_vals), max(sdv15_vals), mean(sdv15_vals)
    ))

    # 4. Parse Physical Elements Connectivity (U1 quads and U3 triangles)
    quads = {} # eid -> [n1, n2, n3, n4]
    tris = {} # eid -> [n1, n2, n3]
    with open(inp_path, "r") as f:
        current_eltype = None
        for line in f:
            line_s = line.strip()
            if line_s.startswith("*ELEMENT"):
                if "TYPE=U1" in line_s: current_eltype = "U1"
                elif "TYPE=U3" in line_s: current_eltype = "U3"
                else: current_eltype = None
                continue
            if line_s.startswith("*"):
                current_eltype = None
                continue
            if current_eltype == "U1" and line_s:
                parts = [int(p.strip()) for p in line_s.split(",") if p.strip()]
                quads[parts[0]] = parts[1:]
            elif current_eltype == "U3" and line_s:
                parts = [int(p.strip()) for p in line_s.split(",") if p.strip()]
                tris[parts[0]] = parts[1:]
                
    print("\nParsed %d U1 quads and %d U3 triangles" % (len(quads), len(tris)))
    
    # 5. Check Triangle Coordinates and Distance to Active Damage Zone
    tri_nids = set()
    for conn in tris.values():
        tri_nids.update(conn)
    tri_coords = [nodes[nid] for nid in tri_nids]
    tri_x = [c[0] for c in tri_coords]
    tri_y = [c[1] for c in tri_coords]
    print("Triangles bounding box: X=[%.6f, %.6f], Y=[%.6f, %.6f]" % (
        min(tri_x), max(tri_x), min(tri_y), max(tri_y)
    ))
    
    # Active damage zone: nodes where d > 0.05
    dmg_nids = [nid for nid, d in phase_bc.items() if d > 0.05]
    dmg_coords = [nodes[nid] for nid in dmg_nids]
    dmg_x = [c[0] for c in dmg_coords]
    dmg_y = [c[1] for c in dmg_coords]
    print("Active damage zone (d > 0.05, %d nodes): X=[%.6f, %.6f], Y=[%.6f, %.6f]" % (
        len(dmg_nids), min(dmg_x), max(dmg_x), min(dmg_y), max(dmg_y)
    ))
    
    # Check if any triangle node is in damage zone
    tri_dmg_overlap = set(tri_nids).intersection(set(dmg_nids))
    print("Triangle nodes in active damage zone: %d" % len(tri_dmg_overlap))
    
    # Min distance between active damage zone and triangle boundary
    min_dist_to_tri = min(
        math.hypot(c[0]-tc[0], c[1]-tc[1]) for c in dmg_coords for tc in tri_coords
    )
    print("Minimum distance between active damage zone (d>0.05) and triangle mesh region: %.6f mm" % min_dist_to_tri)
    
    # 6. Element Quality in Active Damage Zone
    dmg_quads = [eid for eid, conn in quads.items() if any(nid in dmg_nids for nid in conn)]
    print("\nTotal quads in active damage zone: %d" % len(dmg_quads))
    
    detJ_mins = []
    detJ_maxs = []
    aspect_ratios = []
    min_angles = []
    
    from audit_r2r6_forensics import calc_quad_geom
    for eid in dmg_quads:
        conn = quads[eid]
        c = [nodes[nid] for nid in conn]
        geom = calc_quad_geom(c)
        detJ_mins.append(geom["detJ_min"])
        detJ_maxs.append(geom["detJ_max"])
        aspect_ratios.append(geom["aspect_ratio"])
        min_angles.append(geom["min_angle_deg"])
        
    print("Damage zone element quality metrics:")
    print("  detJ_min: %.6e" % min(detJ_mins))
    print("  detJ_max: %.6e" % max(detJ_maxs))
    print("  aspect_ratio: max=%.3f, mean=%.3f" % (max(aspect_ratios), mean(aspect_ratios)))
    print("  minimum_angle: min=%.2f deg, mean=%.2f deg" % (min(min_angles), mean(min_angles)))
    
    # 7. Check Node 481, Connected Elements, and Quality
    print("\n--- NODE 481 DEEP GEOMETRY & FIELD AUDIT ---")
    c_481 = nodes[481]
    print("Node 481 coordinates: X=%.6f, Y=%.6f" % (c_481[0], c_481[1]))
    print("Node 481 prescribed Phase d in Step 1: %.6f" % phase_bc.get(481, 0.0))
    
    quads_481 = [eid for eid, conn in quads.items() if 481 in conn]
    print("Physical Quads containing Node 481: %s" % str(quads_481))
    for eid in quads_481:
        conn = quads[eid]
        c = [nodes[nid] for nid in conn]
        geom = calc_quad_geom(c)
        h_info = elem_H.get(eid, {})
        print("  Quad %d: conn=%s, detJ_min=%.4e, aspect=%.2f, min_ang=%.1f deg, SDV16(H)=%.4e" % (
            eid, str(conn), geom["detJ_min"], geom["aspect_ratio"], geom["min_angle_deg"], h_info.get("sdv16", 0.0)
        ))

    # 8. Check Node 362 (Force Residual Node)
    print("\n--- NODE 362 DEEP GEOMETRY & FIELD AUDIT ---")
    c_362 = nodes[362]
    print("Node 362 coordinates: X=%.6f, Y=%.6f" % (c_362[0], c_362[1]))
    print("Node 362 prescribed Phase d in Step 1: %.6f" % phase_bc.get(362, 0.0))
    quads_362 = [eid for eid, conn in quads.items() if 362 in conn]
    print("Physical Quads containing Node 362: %s" % str(quads_362))
    for eid in quads_362:
        conn = quads[eid]
        c = [nodes[nid] for nid in conn]
        geom = calc_quad_geom(c)
        h_info = elem_H.get(eid, {})
        print("  Quad %d: conn=%s, detJ_min=%.4e, aspect=%.2f, min_ang=%.1f deg, SDV16(H)=%.4e" % (
            eid, str(conn), geom["detJ_min"], geom["aspect_ratio"], geom["min_angle_deg"], h_info.get("sdv16", 0.0)
        ))
        
    # 9. Output complete data to JSON
    out_dict = {
        "d_min": d_min,
        "d_max": d_max,
        "d_mean": d_mean,
        "number_d_gt_0p1": d_gt_0p1,
        "number_d_gt_0p5": d_gt_0p5,
        "number_d_gt_0p9": d_gt_0p9,
        "location_of_dmax": {
            "node_label": max_d_nid,
            "coordinates": list(max_d_coords)
        },
        "sdv14_range": [min(sdv14_vals), max(sdv14_vals)],
        "sdv15_range": [min(sdv15_vals), max(sdv15_vals)],
        "sdv16_range": [min(h_vals), max(h_vals)],
        "damage_zone_quality": {
            "detJ_min": min(detJ_mins),
            "detJ_max": max(detJ_maxs),
            "aspect_ratio_max": max(aspect_ratios),
            "minimum_angle_min": min(min_angles)
        },
        "triangle_interface_distance_mm": min_dist_to_tri,
        "node_481": {
            "coordinates": list(c_481),
            "d_initial": phase_bc.get(481, 0.0),
            "connected_quads": quads_481
        },
        "node_362": {
            "coordinates": list(c_362),
            "d_initial": phase_bc.get(362, 0.0),
            "connected_quads": quads_362
        }
    }
    
    with open("PHASE_AND_ELEMENTS_FORENSIC.json", "w") as f_out:
        json.dump(out_dict, f_out, indent=2)
    print("\nSaved PHASE_AND_ELEMENTS_FORENSIC.json")

if __name__ == "__main__":
    analyze()
