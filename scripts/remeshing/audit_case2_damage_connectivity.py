# -*- coding: utf-8 -*-
"""
scripts/remeshing/audit_case2_damage_connectivity.py
===================================================
Audits element adjacency, spatial graph connectivity, and physical hole-boundary
contact for the 48 softening elements (d >= 0.10) in Case 2 coarse phase-field donor
at Step-2 peak load (uy = 0.00729 mm).

Resolves Independent Review Finding F1728-R20:
- Tests physical hole-boundary contact from actual polygon vertices and boundary nodes.
- Distinguishes physical polygon boundary contact (0.0 um, touching) from element centroid
  clearance (7.69 um).
- Distinguishes diffuse softening damage contact (d in [0.10, 0.58]) from full crack
  rupture/penetration (d >= 0.90).
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
            if not line or line.startswith('**'):
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
    
    notch_tip = (0.50, 0.50)
    hole_center = (0.65, 0.65)
    hole_radius = 0.10
    
    # Identify all nodes lying on circular hole boundary: |r - R| < 1e-4 mm
    hole_boundary_nodes = {}
    for nid, (nx, ny) in nodes.items():
        r = math.hypot(nx - hole_center[0], ny - hole_center[1])
        radial_residual = abs(r - hole_radius)
        if radial_residual < 1e-4:
            hole_boundary_nodes[nid] = {
                "coords": (nx, ny),
                "radial_residual_mm": radial_residual
            }
            
    with open(fields_path, 'r') as f:
        fields = json.load(f)
        
    step2_peak_d = fields['step2_peak']['d']
    step2_peak_h = fields['step2_peak']['H']
    
    # 48 elements with d >= 0.10
    damaged_eids = set(int(k) for k, v in step2_peak_d.items() if v >= 0.10)
    
    # Node-to-damaged-element mapping
    node_to_damaged_elems = defaultdict(set)
    for eid in damaged_eids:
        for nid in elements[eid]:
            node_to_damaged_elems[nid].add(eid)
            
    # Adjacency graphs: edge-sharing (>=2 nodes) and node-sharing (>=1 node)
    edge_adj = defaultdict(set)
    node_adj = defaultdict(set)
    
    for nid, e_set in node_to_damaged_elems.items():
        for e1 in e_set:
            for e2 in e_set:
                if e1 != e2:
                    node_adj[e1].add(e2)
                    shared_nodes = set(elements[e1]).intersection(elements[e2])
                    if len(shared_nodes) >= 2:
                        edge_adj[e1].add(e2)
                        
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
    
    comp_details = []
    for c_idx, comp in enumerate(edge_components):
        comp_centroids = [centroids[eid] for eid in comp]
        comp_d_vals = [step2_peak_d[str(eid)] for eid in comp]
        
        # Min distance from element centroids to notch tip and hole center/perimeter
        dist_to_tip_centroids = min(math.hypot(c[0] - notch_tip[0], c[1] - notch_tip[1]) for c in comp_centroids)
        centroid_dist_to_hole_center = min(math.hypot(c[0] - hole_center[0], c[1] - hole_center[1]) for c in comp_centroids)
        centroid_clearance_to_hole_perimeter = centroid_dist_to_hole_center - hole_radius

        # Identify which element achieves the nearest centroid clearance to the hole perimeter
        min_c_clearance = 1e9
        nearest_centroid_eid = None
        for eid in comp:
            cx, cy = centroids[eid]
            c_dist = math.hypot(cx - hole_center[0], cy - hole_center[1]) - hole_radius
            if c_dist < min_c_clearance:
                min_c_clearance = c_dist
                nearest_centroid_eid = eid
        
        # True polygon-level vertex distance to hole boundary
        comp_nodes = set()
        for eid in comp:
            comp_nodes.update(elements[eid])
            
        boundary_nodes_in_comp = [nid for nid in comp_nodes if nid in hole_boundary_nodes]
        touches_boundary = len(boundary_nodes_in_comp) > 0
        
        # Elements in this component directly possessing boundary nodes
        touching_elements = [
            eid for eid in comp if any(nid in hole_boundary_nodes for nid in elements[eid])
        ]
        
        # If any node is on boundary, polygon clearance is 0.0; otherwise min distance of polygon vertices to boundary
        if touches_boundary:
            polygon_clearance_to_hole_mm = 0.0
        else:
            vertex_dists = [abs(math.hypot(nodes[n][0] - hole_center[0], nodes[n][1] - hole_center[1]) - hole_radius) for n in comp_nodes]
            polygon_clearance_to_hole_mm = min(vertex_dists)
            
        min_x = min(c[0] for c in comp_centroids)
        max_x = max(c[0] for c in comp_centroids)
        min_y = min(c[1] for c in comp_centroids)
        max_y = max(c[1] for c in comp_centroids)
        
        # Check fully broken elements (d >= 0.90) in this component
        broken_count = sum(1 for d in comp_d_vals if d >= 0.90)
        
        comp_details.append({
            "component_id": c_idx + 1,
            "element_count": len(comp),
            "elements": comp,
            "d_max": max(comp_d_vals),
            "d_mean": sum(comp_d_vals) / len(comp_d_vals),
            "fully_broken_elements_d_ge_090": broken_count,
            "physical_boundary_contact": touches_boundary,
            "polygon_clearance_to_hole_perimeter_mm": polygon_clearance_to_hole_mm,
            "boundary_touching_elements": touching_elements,
            "boundary_touching_elements_details": [
                {
                    "element_id": eid,
                    "d": step2_peak_d[str(eid)],
                    "H": step2_peak_h[str(eid)],
                    "nodes": elements[eid],
                    "centroid_mm": list(centroids[eid]),
                    "boundary_nodes": [nid for nid in elements[eid] if nid in hole_boundary_nodes]
                }
                for eid in touching_elements
            ],
            "boundary_nodes_count": len(boundary_nodes_in_comp),
            "boundary_nodes": sorted(boundary_nodes_in_comp),
            "min_dist_to_notch_tip_mm": dist_to_tip_centroids,
            "nearest_centroid_element_id": nearest_centroid_eid,
            "nearest_centroid_dist_to_hole_center_mm": centroid_dist_to_hole_center,
            "nearest_centroid_clearance_to_hole_perimeter_mm": centroid_clearance_to_hole_perimeter,
            "bbox_mm": {
                "x_min": min_x, "x_max": max_x,
                "y_min": min_y, "y_max": max_y
            }
        })
        
    element_table = []
    for eid in sorted(damaged_eids):
        cx, cy = centroids[eid]
        d_val = step2_peak_d[str(eid)]
        h_val = step2_peak_h[str(eid)]
        dtip = math.hypot(cx - notch_tip[0], cy - notch_tip[1])
        dhole_c = math.hypot(cx - hole_center[0], cy - hole_center[1])
        dhole_p = dhole_c - hole_radius
        elem_b_nodes = [nid for nid in elements[eid] if nid in hole_boundary_nodes]
        element_table.append({
            "element_id": eid,
            "centroid_mm": [cx, cy],
            "d": d_val,
            "H": h_val,
            "dist_to_notch_tip_mm": dtip,
            "dist_to_hole_center_mm": dhole_c,
            "centroid_clearance_to_hole_perimeter_mm": dhole_p,
            "touches_hole_boundary": len(elem_b_nodes) > 0,
            "boundary_nodes": elem_b_nodes
        })
        
    result = {
        "benchmark": "Case 2 (Single Off-Axis Hole Plate)",
        "step": "Step-2",
        "checkpoint": "step2_peak",
        "displacement_mm": fields.get("peak_disp_mm", 0.0072938),
        "total_damaged_elements_d_ge_010": len(damaged_eids),
        "total_broken_elements_d_ge_090": sum(1 for eid in damaged_eids if step2_peak_d[str(eid)] >= 0.90),
        "edge_sharing_components_count": len(edge_components),
        "node_sharing_components_count": len(node_components),
        "largest_component_element_count": len(edge_components[0]) if edge_components else 0,
        "is_single_connected_chain": len(edge_components) == 1,
        "primary_component_touches_hole_boundary": comp_details[0]["physical_boundary_contact"] if comp_details else False,
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
        "Total Broken Elements (d >= 0.90): %d" % result["total_broken_elements_d_ge_090"],
        "Edge-Sharing Connected Components: %d" % len(edge_components),
        "Node-Sharing Connected Components: %d" % len(node_components),
        "Primary Component Boundary Contact: %s" % ("YES (Physical Contact at Element Level)" if result["primary_component_touches_hole_boundary"] else "NO"),
        ""
    ]
    for c in comp_details:
        lines.append("Component %d: %d elements, d_max=%.4f, d_mean=%.4f" % (
            c["component_id"], c["element_count"], c["d_max"], c["d_mean"]
        ))
        lines.append("  Bounding box: x in [%.4f, %.4f], y in [%.4f, %.4f]" % (
            c["bbox_mm"]["x_min"], c["bbox_mm"]["x_max"], c["bbox_mm"]["y_min"], c["bbox_mm"]["y_max"]
        ))
        lines.append("  Physical Hole Boundary Contact: %s (Polygon clearance: %.4f mm)" % (
            "YES" if c["physical_boundary_contact"] else "NO", c["polygon_clearance_to_hole_perimeter_mm"]
        ))
        if c["physical_boundary_contact"]:
            lines.append("  Boundary-touching elements (%d): %s" % (
                len(c["boundary_touching_elements"]), str(c["boundary_touching_elements"])
            ))
            lines.append("  Boundary nodes (%d): %s" % (
                len(c["boundary_nodes"]), str(c["boundary_nodes"])
            ))
        lines.append("  Nearest centroid distance to notch tip: %.4f mm (%.2f um)" % (
            c["min_dist_to_notch_tip_mm"], c["min_dist_to_notch_tip_mm"] * 1000
        ))
        lines.append("  Nearest centroid clearance to hole perimeter: %.4f mm (%.2f um) [NOTE: Centroid metric, not physical gap]" % (
            c["nearest_centroid_clearance_to_hole_perimeter_mm"], c["nearest_centroid_clearance_to_hole_perimeter_mm"] * 1000
        ))
        lines.append("  Fully broken elements (d >= 0.90): %d" % c["fully_broken_elements_d_ge_090"])
        lines.append("  Elements: %s" % str(c["elements"]))
        lines.append("")
        
    with open(out_txt, 'w') as f:
        f.write("\n".join(lines))
        
    print("Connectivity audit complete: Primary component boundary contact = %s" % result["primary_component_touches_hole_boundary"])

if __name__ == '__main__':
    analyze_connectivity()
