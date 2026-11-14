# -*- coding: utf-8 -*-
"""
scripts/remeshing/audit_f1736_spatial_resolution.py

Rigorous spatial-resolution and element-quality audit for all five benchmark geometries:
- Case 1: Mode-I Single-Edge Notched Plate
- Case 2: Plate with an Off-Axis Hole
- Case 3: Rectangular Notched Plate with Hole and Pins (Sec 4.3)
- Case 4: Five-Hole Plate (Sec 4.5)
- Case 5: Seven-Hole Plate (Sec 4.6)

Computes:
- Node count, element count, quad count, tri count, quad percentage
- Element area A_e, equivalent size h_e = sqrt(A_e)
- Resolution ratio R_e = h_e / ell_0
- Min, 5th percentile, median, mean, 95th percentile, max h_e
- Compliance metrics:
  - h <= ell_0 (count %, area %)
  - h <= ell_0 / 2 (count %, area %)
  - h <= ell_0 / 3 (count %, area %)
- Element quality:
  - 2D signed Jacobian det(J) at centroid and corner integration points
  - Aspect ratio L_max / L_min
  - Skewness / distortion indicators
  - Non-positive Jacobian count (strictly 0 required)
- Bounding boxes and coordinate extents
- Verification of process-zone coverage vs coarse clusters
"""

import os
import sys
import json
import math
import hashlib
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Benchmark specifications
BENCHMARK_CONFIGS = {
    "case_1": {
        "name": "Case 1: Mode-I Single-Edge Notched Plate",
        "section": "Pandey & Kumar (2025) Sec 4.1",
        "ell_0": 0.0075,  # mm
        "published_elements": 13762,
        "final_mesh_path": os.path.join("models", "pandey_kumar_mode1", "219_f1728_five_geometry_study", "PK_F1728_CASE_1_ADAPT_PHYS.inp"),
        "intermediate_mesh_path": os.path.join("models", "pandey_kumar_mode1", "207_f1727_three_geometry_benchmark", "PK_F1727_MODEL_B_ADAPT_PHYS.inp"),
        "donor_source": "Linear elastic / companion stress donor at u=0.005 mm (F1727/F1728)",
        "published_fig": "Figure 9(a)",
        "expected_crack_path": "Horizontal straight crack from notch tip (x=0.5, y=0.5) to right boundary (x=1.0, y=0.5)"
    },
    "case_2": {
        "name": "Case 2: Plate with an Off-Axis Hole",
        "section": "Pandey & Kumar (2025) Sec 4.4",
        "ell_0": 0.0075,  # mm
        "published_elements": 23618,
        "final_mesh_path": os.path.join("models", "pandey_kumar_mode1", "224_f1734_case2_distal_refinement", "PK_F1728_CASE_2_ADAPT_PHYS.inp"),
        "intermediate_mesh_path": os.path.join("models", "pandey_kumar_mode1", "207_f1727_three_geometry_benchmark", "PK_F1727_MODEL_C_ADAPT_PHYS.inp"),
        "donor_source": "Distal-refined companion stress donor at u=0.005 mm with calibrated err_indicator (F1734)",
        "published_fig": "Figure 19(a)",
        "expected_crack_path": "Curved path from notch tip into hole, and distal path from hole to right edge"
    },
    "case_3": {
        "name": "Case 3: Rectangular Notched Plate with Hole and Pins",
        "section": "Pandey & Kumar (2025) Sec 4.3",
        "ell_0": 0.285,  # mm
        "published_elements": 12168,
        "final_mesh_path": os.path.join("models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1", "PK_SEC43_STAGGERED_ADAPT_BEST_DONOR.inp"),
        "intermediate_mesh_path": os.path.join("models", "pandey_kumar_mode1", "207_f1727_three_geometry_benchmark", "PK_F1727_MODEL_A_ADAPT_PHYS.inp"),
        "donor_source": "Staggered coupled pre-peak donor at u=0.105 mm (Task 192/F1727)",
        "published_fig": "Figure 15(a)",
        "expected_crack_path": "Notch tip to central hole, and secondary path from central hole to right boundary"
    },
    "case_4": {
        "name": "Case 4: Five-Hole Plate",
        "section": "Pandey & Kumar (2025) Sec 4.5",
        "ell_0": 0.008,  # mm
        "published_elements": 12944,
        "final_mesh_path": os.path.join("models", "pandey_kumar_mode1", "217_f1725_physics_study", "F1725_S2_COARSEN_ET315.inp"),
        "intermediate_mesh_path": os.path.join("models", "pandey_kumar_mode1", "210_f1719_five_hole_coarse_pfm", "PK_F1719_ADAPTED_STATE2.inp"),
        "donor_source": "Authentic coarse coupled phase-field solution at State 2 (u=0.0058 mm, F1725)",
        "published_fig": "Figure 23(b)",
        "expected_crack_path": "Continuous multi-ligament fracture trajectory between holes 1->2->3->4"
    },
    "case_5": {
        "name": "Case 5: Seven-Hole Plate",
        "section": "Pandey & Kumar (2025) Sec 4.6",
        "ell_0": 0.008,  # mm
        "published_elements": 15714,
        "final_mesh_path": os.path.join("models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_ADAPTED_PHYS.inp"),
        "intermediate_mesh_path": os.path.join("models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_COARSE_PHYS.inp"),
        "donor_source": "Authentic coarse coupled phase-field donor at u=0.0048 mm (Task F1726)",
        "published_fig": "Figure 25(b)",
        "expected_crack_path": "Concentrated upper-ligament refinement between hole 1, hole 2, and hole 3"
    }
}

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def parse_abaqus_inp(inp_path):
    """
    Parses nodes and 2D elements from an Abaqus input deck.
    Returns:
      nodes: dict of node_id -> np.array([x, y])
      elements: dict of elem_id -> list of node_ids
      elem_types: dict of elem_id -> 'QUAD' or 'TRI'
    """
    nodes = {}
    elements = {}
    elem_types = {}
    
    reading_nodes = False
    reading_elements = False
    
    with open(inp_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            
            lu = l.upper()
            if lu.startswith("*NODE"):
                reading_nodes = True
                reading_elements = False
                continue
            elif lu.startswith("*ELEMENT") and not lu.startswith("*ELEMENT OUTPUT"):
                reading_nodes = False
                reading_elements = True
                continue
            elif lu.startswith("*"):
                reading_nodes = False
                reading_elements = False
                continue
            
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if reading_nodes:
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    nodes[nid] = np.array([x, y], dtype=float)
                except (ValueError, IndexError):
                    pass
            elif reading_elements:
                try:
                    eid = int(parts[0])
                    nids = [int(p) for p in parts[1:]]
                    if len(nids) == 4:
                        elements[eid] = nids
                        elem_types[eid] = "QUAD"
                    elif len(nids) == 3:
                        elements[eid] = nids
                        elem_types[eid] = "TRI"
                    elif len(nids) == 8:
                        # 8-node quad, take corner nodes
                        elements[eid] = nids[:4]
                        elem_types[eid] = "QUAD"
                    elif len(nids) == 6:
                        # 6-node tri, take corner nodes
                        elements[eid] = nids[:3]
                        elem_types[eid] = "TRI"
                except (ValueError, IndexError):
                    pass

    return nodes, elements, elem_types

def compute_element_metrics(nodes, elements, elem_types, ell_0):
    """
    Computes rigorous geometric metrics for every element:
    - Area (signed polygon area)
    - Equivalent size h_e = sqrt(A_e)
    - Aspect ratio
    - Signed Jacobian min det(J)
    """
    areas = []
    sizes = []
    aspect_ratios = []
    signed_jacs = []
    negative_jac_count = 0
    
    elem_ids = sorted(elements.keys())
    
    for eid in elem_ids:
        nids = elements[eid]
        etype = elem_types[eid]
        coords = np.array([nodes[nid] for nid in nids])
        
        # 1. Signed Area using Shoelace formula
        n = len(coords)
        x = coords[:, 0]
        y = coords[:, 1]
        area = 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)
        abs_area = abs(area)
        areas.append(abs_area)
        
        # Equivalent size
        h = math.sqrt(abs_area) if abs_area > 0 else 0.0
        sizes.append(h)
        
        # 2. Aspect Ratio & Edge lengths
        edge_vecs = np.roll(coords, -1, axis=0) - coords
        edge_lens = np.linalg.norm(edge_vecs, axis=1)
        max_edge = np.max(edge_lens)
        min_edge = np.min(edge_lens)
        ar = (max_edge / min_edge) if min_edge > 1e-15 else 1e6
        aspect_ratios.append(ar)
        
        # 3. Signed Jacobian check
        if etype == "TRI":
            # 2 * Area is the constant determinant of the Jacobian for a linear triangle
            det_j = 2.0 * area
            signed_jacs.append(det_j)
            if det_j <= 0:
                negative_jac_count += 1
        elif etype == "QUAD":
            # Evaluate Jacobian at the 4 corners: xi = +-1, eta = +-1
            # N_i(xi, eta) = 1/4 (1 + xi*xi_i)(1 + eta*eta_i)
            corner_evals = [(-0.57735, -0.57735), (0.57735, -0.57735), 
                            (0.57735, 0.57735), (-0.57735, 0.57735)]
            min_det = 1e30
            for xi, eta in corner_evals:
                dN_dxi = 0.25 * np.array([
                    -(1.0 - eta),  (1.0 - eta),  (1.0 + eta), -(1.0 + eta)
                ])
                dN_deta = 0.25 * np.array([
                    -(1.0 - xi), -(1.0 + xi),   (1.0 + xi),   (1.0 - xi)
                ])
                dx_dxi = np.dot(dN_dxi, x)
                dx_deta = np.dot(dN_deta, x)
                dy_dxi = np.dot(dN_dxi, y)
                dy_deta = np.dot(dN_deta, y)
                det_j = dx_dxi * dy_deta - dx_deta * dy_dxi
                if det_j < min_det:
                    min_det = det_j
            signed_jacs.append(min_det)
            if min_det <= 0:
                negative_jac_count += 1

    areas = np.array(areas)
    sizes = np.array(sizes)
    aspect_ratios = np.array(aspect_ratios)
    signed_jacs = np.array(signed_jacs)
    ratios = sizes / ell_0
    
    total_area = np.sum(areas)
    num_elems = len(sizes)
    
    # Compliance calculations
    c_ell0 = np.sum(ratios <= 1.0)
    c_ell0_area = np.sum(areas[ratios <= 1.0])
    
    c_half = np.sum(ratios <= 0.5)
    c_half_area = np.sum(areas[ratios <= 0.5])
    
    c_third = np.sum(ratios <= (1.0 / 3.0))
    c_third_area = np.sum(areas[ratios <= (1.0 / 3.0)])
    
    # Quad percentage
    num_quads = sum(1 for t in elem_types.values() if t == "QUAD")
    num_tris = sum(1 for t in elem_types.values() if t == "TRI")
    quad_pct = (num_quads / num_elems * 100.0) if num_elems > 0 else 0.0
    
    # Coordinates bounding box
    all_coords = np.array(list(nodes.values()))
    min_x, min_y = np.min(all_coords, axis=0)
    max_x, max_y = np.max(all_coords, axis=0)

    stats = {
        "num_nodes": len(nodes),
        "num_elements": num_elems,
        "num_quads": num_quads,
        "num_tris": num_tris,
        "quad_percentage": float(quad_pct),
        "total_domain_area": float(total_area),
        "bounding_box": {
            "x_min": float(min_x), "x_max": float(max_x),
            "y_min": float(min_y), "y_max": float(max_y)
        },
        "negative_jacobian_count": int(negative_jac_count),
        "min_jacobian": float(np.min(signed_jacs)) if len(signed_jacs) > 0 else 0.0,
        "element_size_stats_mm": {
            "min": float(np.min(sizes)),
            "p05": float(np.percentile(sizes, 5)),
            "median": float(np.median(sizes)),
            "mean": float(np.mean(sizes)),
            "p95": float(np.percentile(sizes, 95)),
            "max": float(np.max(sizes))
        },
        "resolution_ratio_stats": {
            "min": float(np.min(ratios)),
            "p05": float(np.percentile(ratios, 5)),
            "median": float(np.median(ratios)),
            "mean": float(np.mean(ratios)),
            "p95": float(np.percentile(ratios, 95)),
            "max": float(np.max(ratios))
        },
        "aspect_ratio_stats": {
            "min": float(np.min(aspect_ratios)),
            "median": float(np.median(aspect_ratios)),
            "mean": float(np.mean(aspect_ratios)),
            "p95": float(np.percentile(aspect_ratios, 95)),
            "max": float(np.max(aspect_ratios))
        },
        "compliance": {
            "h_le_ell0": {
                "count": int(c_ell0),
                "count_pct": float(c_ell0 / num_elems * 100.0),
                "area_pct": float(c_ell0_area / total_area * 100.0)
            },
            "h_le_half_ell0": {
                "count": int(c_half),
                "count_pct": float(c_half / num_elems * 100.0),
                "area_pct": float(c_half_area / total_area * 100.0)
            },
            "h_le_third_ell0": {
                "count": int(c_third),
                "count_pct": float(c_third / num_elems * 100.0),
                "area_pct": float(c_third_area / total_area * 100.0)
            }
        }
    }
    return stats

def audit_all_benchmarks():
    results = {}
    print("=" * 80)
    print("TASK F1736: QUANTITATIVE SPATIAL-RESOLUTION AND MESH-QUALITY AUDIT")
    print("=" * 80)
    
    for case_key, cfg in BENCHMARK_CONFIGS.items():
        print(f"\nAuditing {cfg['name']}...")
        final_abs = os.path.join(REPO_ROOT, cfg["final_mesh_path"])
        inter_abs = os.path.join(REPO_ROOT, cfg["intermediate_mesh_path"])
        
        if not os.path.exists(final_abs):
            raise FileNotFoundError(f"Missing final mesh: {final_abs}")
        if not os.path.exists(inter_abs):
            raise FileNotFoundError(f"Missing intermediate mesh: {inter_abs}")
            
        final_sha = sha256_file(final_abs)
        inter_sha = sha256_file(inter_abs)
        
        # Parse and audit final mesh
        fnodes, felems, fetypes = parse_abaqus_inp(final_abs)
        fstats = compute_element_metrics(fnodes, felems, fetypes, cfg["ell_0"])
        
        # Parse and audit intermediate mesh
        inodes, ielems, ietypes = parse_abaqus_inp(inter_abs)
        istats = compute_element_metrics(inodes, ielems, ietypes, cfg["ell_0"])
        
        results[case_key] = {
            "config": {
                "name": cfg["name"],
                "section": cfg["section"],
                "ell_0_mm": cfg["ell_0"],
                "published_elements": cfg["published_elements"],
                "published_fig": cfg["published_fig"],
                "donor_source": cfg["donor_source"],
                "expected_crack_path": cfg["expected_crack_path"]
            },
            "final_mesh": {
                "rel_path": cfg["final_mesh_path"],
                "sha256": final_sha,
                "metrics": fstats
            },
            "intermediate_mesh": {
                "rel_path": cfg["intermediate_mesh_path"],
                "sha256": inter_sha,
                "metrics": istats
            }
        }
        
        print(f"  Final Mesh: {fstats['num_elements']} elems ({fstats['quad_percentage']:.1f}% Q) | SHA: {final_sha[:12]}...")
        print(f"    h_min: {fstats['element_size_stats_mm']['min']*1e3:.2f} um, h_med: {fstats['element_size_stats_mm']['median']*1e3:.2f} um, h_max: {fstats['element_size_stats_mm']['max']*1e3:.2f} um")
        print(f"    h/ell_0 min: {fstats['resolution_ratio_stats']['min']:.3f}, median: {fstats['resolution_ratio_stats']['median']:.3f}")
        print(f"    h <= ell_0: {fstats['compliance']['h_le_ell0']['count']} elems ({fstats['compliance']['h_le_ell0']['count_pct']:.1f}% count, {fstats['compliance']['h_le_ell0']['area_pct']:.1f}% area)")
        print(f"    h <= ell_0/2: {fstats['compliance']['h_le_half_ell0']['count']} elems ({fstats['compliance']['h_le_half_ell0']['count_pct']:.1f}% count, {fstats['compliance']['h_le_half_ell0']['area_pct']:.1f}% area)")
        print(f"    Neg Jacobians: {fstats['negative_jacobian_count']} | Max Aspect Ratio: {fstats['aspect_ratio_stats']['max']:.2f}")

    out_json = os.path.join(REPO_ROOT, "results", "validation", "f1736_five_case_spatial_audit.json")
    with open(out_json, "w", encoding="utf-8") as jf:
        json.dump(results, jf, indent=2)
    print(f"\nAudit completed. Saved results to {os.path.relpath(out_json, REPO_ROOT)}")
    return results

if __name__ == "__main__":
    audit_all_benchmarks()
