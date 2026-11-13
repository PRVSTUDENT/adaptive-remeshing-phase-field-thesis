# -*- coding: utf-8 -*-
"""
scripts/remeshing/audit_case2_damage_connectivity.py
===================================================
Audits the element adjacency, spatial graph connectivity, and distance to hole
for the 48 softening elements (d >= 0.10) in Case 2 coarse phase-field donor
at Step-2 peak load (uy = 0.00729 mm).
"""

from __future__ import print_function
import os
import math
import json
from collections import defaultdict, deque

def parse_inp_mesh(inp_path):
    nodes = {}
    elements = {}
    current_section = None
    
    with open(inp_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('**'):
                continue
            if line.startswith('*'):
                upline = line.upper()
                if upline.startswith('*NODE'):
                    current_section = 'NODE'
                elif upline.startswith('*ELEMENT'):
                    current_section = 'ELEMENT'
                else:
                    current_section = None
                continue
                
            if current_section == 'NODE':
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    nodes[nid] = (x, y)
            elif current_section == 'ELEMENT':
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 4:
                    eid = int(parts[0])
                    nids = [int(p) for p in parts[1:] if p]
                    elements[eid] = nids
                    
    return nodes, elements

def compute_centroids(nodes, elements):
    centroids = {}
    for eid, nids in elements.items():
        coords = [nodes[n] for n in nids if n in nodes]
        cx = sum(c[0] for c in coords) / len(coords)
        cy = sum(c[1] for c in coords) / len(coords)
        centroids[eid] = (cx, cy)
    return centroids

def analyze_connectivity():
    inp_path = 'models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_PHYS.inp'
    fields_path = 'results/validation/f1728_case2_coarse_job1_fields.json'
    out_json = 'results/validation/f1728_case2_damage_connectivity.json'
    out_txt = 'results/validation/f1728_case2_damage_connectivity.txt'
    
    nodes, elements = parse_inp_mesh(inp_path)
    centroids = compute_centroids(nodes, elements)
    
    with open(fields_path, 'r') as f:
        fields = json.load(f)
        
    step2_peak_d = fields['step2_peak']['d']
    step2_peak_h = fields['step2_peak']['H']
    
    # 48 elements with d >= 0.10
    damaged_eids = set(int(k) for k, v in step2_peak_d.items() if v >= 0.10)
    
    # Build node-to-element mapping for damaged elements
    node_to_damaged_elems = defaultdict(set)
    for eid in damaged_eids:
        for nid in elements[eid]:
            node_to_damaged_elems[nid].add(eid)
            
    # Build element adjacency graph (sharing at least one edge: 2 nodes for quad/tri)
    # Also check node-sharing (sharing at least 1 node)
    edge_adj = defaultdict(set)
    node_adj = defaultdict(set)
    
    for nid, e_set in node_to_damaged_elems.items():
        for e1 in e_set:
            for e2 in e_set:
                if e1 != e2:
                    node_adj[e1].add(e2)
                    # Check if they share at least 2 nodes (an edge)
                    shared_nodes = set(elements[e1]).intersection(elements[e2])
                    if len(shared_nodes) >= 2:
                        edge_adj[e1].add(e2)
                        
    # Find connected components under edge-sharing
    def get_components(adj_graph, all_nodes):
        visited = set()
        components = []
        for start_node in sorted(all_nodes):
            if start_node not in visited:
                comp = []
                queue = deque([start_node])
                visited.add(start_node)
                while queue:
                    curr = queue.popleft()
                    comp.append(curr)
                    for neighbor in adj_graph[curr]:
                        if neighbor not in visited and neighbor in all_nodes:
                            visited.add(neighbor)
                            queue.append(neighbor)
                components.append(sorted(comp))
        return sorted(components, key=lambda c: len(c), reverse=True)

    edge_components = get_components(edge_adj, damaged_eids)
    node_components = get_components(node_adj, damaged_eids)
    
    # Analyze distance to notch tip (0.50, 0.50) and hole (0.65, 0.65), R=0.10
    notch_tip = (0.50, 0.50)
    hole_center = (0.65, 0.65)
    hole_radius = 0.10
    
    comp_details = []
    for c_idx, comp in enumerate(edge_components):
        comp_centroids = [centroids[eid] for eid in comp]
        comp_d_vals = [step2_peak_d[str(eid)] for eid in comp]
        
        # Min distance to notch tip
        dist_to_tip = min(math.hypot(c[0] - notch_tip[0], c[1] - notch_tip[1]) for c in comp_centroids)
        # Min distance to hole center and hole perimeter
        dist_to_hole_center = min(math.hypot(c[0] - hole_center[0], c[1] - hole_center[1]) for c in comp_centroids)
        dist_to_hole_perimeter = dist_to_hole_center - hole_radius
        
        # Bounding box of component
        min_x = min(c[0] for c in comp_centroids)
        max_x = max(c[0] for c in comp_centroids)
        min_y = min(c[1] for c in comp_centroids)
        max_y = max(c[1] for c in comp_centroids)
        
        comp_details.append({
            "component_id": c_idx + 1,
            "element_count": len(comp),
            "elements": comp,
            "d_max": max(comp_d_vals),
            "d_mean": sum(comp_d_vals) / len(comp_d_vals),
            "min_dist_to_notch_tip_mm": dist_to_tip,
            "min_dist_to_hole_center_mm": dist_to_hole_center,
            "min_dist_to_hole_perimeter_mm": dist_to_hole_perimeter,
            "bbox_mm": {
                "x_min": min_x, "x_max": max_x,
                "y_min": min_y, "y_max": max_y
            }
        })
        
    # Element-by-element table for the 48 damaged elements
    element_table = []
    for eid in sorted(damaged_eids):
        cx, cy = centroids[eid]
        d_val = step2_peak_d[str(eid)]
        h_val = step2_peak_h[str(eid)]
        dtip = math.hypot(cx - notch_tip[0], cy - notch_tip[1])
        dhole_c = math.hypot(cx - hole_center[0], cy - hole_center[1])
        dhole_p = dhole_c - hole_radius
        element_table.append({
            "element_id": eid,
            "centroid_mm": [cx, cy],
            "d": d_val,
            "H": h_val,
            "dist_to_notch_tip_mm": dtip,
            "dist_to_hole_center_mm": dhole_c,
            "dist_to_hole_perimeter_mm": dhole_p
        })
        
    result = {
        "benchmark": "Case 2 (Single Off-Axis Hole Plate)",
        "step": "Step-2",
        "checkpoint": "step2_peak",
        "displacement_mm": fields.get("peak_disp_mm", 0.0072938),
        "total_damaged_elements_d_ge_010": len(damaged_eids),
        "edge_sharing_components_count": len(edge_components),
        "node_sharing_components_count": len(node_components),
        "largest_component_element_count": len(edge_components[0]) if edge_components else 0,
        "is_single_connected_chain": len(edge_components) == 1,
        "edge_components": comp_details,
        "elements_summary": element_table
    }
    
    with open(out_json, 'w') as f:
        json.dump(result, f, indent=2)
        
    lines = [
        "================================================================================",
        "CASE 2 COARSE PHASE-FIELD DONOR: STEP-2 PEAK DAMAGE CONNECTIVITY AUDIT",
        "================================================================================",
        "Checkpoint: Step-2 Peak (uy = 0.007294 mm, F = 0.7310 kN)",
        "Total Damaged Elements (d >= 0.10): %d" % len(damaged_eids),
        "Edge-Sharing Connected Components: %d" % len(edge_components),
        "Node-Sharing Connected Components: %d" % len(node_components),
        ""
    ]
    for c in comp_details:
        lines.append("Component %d: %d elements, d_max=%.4f, d_mean=%.4f" % (
            c["component_id"], c["element_count"], c["d_max"], c["d_mean"]
        ))
        lines.append("  Bounding box: x in [%.4f, %.4f], y in [%.4f, %.4f]" % (
            c["bbox_mm"]["x_min"], c["bbox_mm"]["x_max"], c["bbox_mm"]["y_min"], c["bbox_mm"]["y_max"]
        ))
        lines.append("  Distance to notch tip: %.4f mm (%.2f um)" % (
            c["min_dist_to_notch_tip_mm"], c["min_dist_to_notch_tip_mm"] * 1000
        ))
        lines.append("  Distance to hole perimeter: %.4f mm (%.2f um)" % (
            c["min_dist_to_hole_perimeter_mm"], c["min_dist_to_hole_perimeter_mm"] * 1000
        ))
        lines.append("  Elements: %s" % str(c["elements"]))
        lines.append("")
        
    with open(out_txt, 'w') as f:
        f.write("\n".join(lines))
        
    print("Connectivity audit complete.")

if __name__ == '__main__':
    analyze_connectivity()
