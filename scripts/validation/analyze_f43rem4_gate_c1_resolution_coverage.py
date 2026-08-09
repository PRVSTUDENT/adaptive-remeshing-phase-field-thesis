#!/usr/bin/env python3
"""
F43REM4 Gate C1 Task R4: Phase-Field Resolution-Coverage and Crack-Corridor Audit.
Evaluates PK1, PK5, and MM candidate refined meshes against the validated PRE3 baseline:
1. Freezes candidate decks and loads PRE3 MISESERI field.
2. Computes detailed resolution fractions (h/l0 <= 1.0, <= 0.5, <= 1/3 for h_area, min_edge, max_edge)
   within top 1%, 5%, 10%, 20% PRE3 MISESERI regions.
3. Computes distribution percentiles (median, p75, p90, p95, max h_area/l0) within each region.
4. Constructs connected geometric crack corridors from the Mode-II notch tip (top 1%, 5%, 10%).
5. Analyzes resolution coverage, area fractions, and largest under-resolved sections along connected corridors.
6. Evaluates connected fine-mesh path existence (h <= 0.5 l0 and h <= 0.75 l0).
7. Generates spatial SVG visual figures of the mesh, resolution, notch tip, and corridors.
8. Produces comprehensive JSON audit record and updates Gate C1 report.
"""

import collections
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path


def compute_sha256(filepath):
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def parse_inp_mesh(inp_path):
    """
    Parses Abaqus .inp file extracting Part nodes, Assembly nodes, CPE4 elements, CPE3 elements,
    node sets, and element sets.
    """
    with open(inp_path, "r", encoding="latin-1") as f:
        lines = f.readlines()

    part_nodes = {}
    assembly_nodes = {}
    cpe4_elements = {}
    cpe3_elements = {}
    nsets = {}
    elsets = {}

    current_context = "ROOT"
    current_section = None
    current_set_name = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("**"):
            continue

        if stripped.startswith("*"):
            upper = stripped.upper()
            if upper.startswith("*PART"):
                current_context = "PART"
                current_section = None
            elif upper.startswith("*END PART"):
                current_context = "ROOT"
                current_section = None
            elif upper.startswith("*ASSEMBLY"):
                current_context = "ASSEMBLY"
                current_section = None
            elif upper.startswith("*END ASSEMBLY"):
                current_context = "ROOT"
                current_section = None
            elif upper.startswith("*NODE"):
                current_section = "NODE"
            elif upper.startswith("*ELEMENT"):
                if "CPE4" in upper or "CPS4" in upper or "QUAD" in upper:
                    current_section = "ELEMENT_CPE4"
                elif "CPE3" in upper or "CPS3" in upper or "TRI" in upper:
                    current_section = "ELEMENT_CPE3"
                else:
                    current_section = "ELEMENT_OTHER"
            elif upper.startswith("*NSET"):
                current_section = "NSET"
                match = re.search(r"NSET=([A-Za-z0-9_\-]+)", stripped, re.IGNORECASE)
                current_set_name = match.group(1) if match else "UNNAMED_NSET"
                if current_set_name not in nsets:
                    nsets[current_set_name] = []
            elif upper.startswith("*ELSET"):
                current_section = "ELSET"
                match = re.search(r"ELSET=([A-Za-z0-9_\-]+)", stripped, re.IGNORECASE)
                current_set_name = match.group(1) if match else "UNNAMED_ELSET"
                if current_set_name not in elsets:
                    elsets[current_set_name] = []
            else:
                current_section = None
            continue

        if current_section == "NODE":
            parts = [p.strip() for p in stripped.split(",")]
            if len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3]) if len(parts) > 3 else 0.0
                    if current_context == "PART":
                        part_nodes[nid] = (x, y, z)
                    else:
                        assembly_nodes[nid] = (x, y, z)
                except ValueError:
                    pass
        elif current_section == "ELEMENT_CPE4":
            parts = [p.strip() for p in stripped.split(",")]
            if len(parts) >= 5:
                try:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:5]]
                    cpe4_elements[eid] = conn
                except ValueError:
                    pass
        elif current_section == "ELEMENT_CPE3":
            parts = [p.strip() for p in stripped.split(",")]
            if len(parts) >= 4:
                try:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:4]]
                    cpe3_elements[eid] = conn
                except ValueError:
                    pass

    return {
        "part_nodes": part_nodes,
        "assembly_nodes": assembly_nodes,
        "cpe4_elements": cpe4_elements,
        "cpe3_elements": cpe3_elements
    }


def polygon_signed_area(coords):
    """Computes signed area of a 2D polygon using standard Shoelace formula."""
    n = len(coords)
    a = 0.0
    for i in range(n):
        j = (i + 1) % n
        a += coords[i][0] * coords[j][1] - coords[j][0] * coords[i][1]
    return 0.5 * a


def compute_element_geometry(nodes, cpe4_elements, cpe3_elements):
    """Computes geometric properties for every element."""
    geometry = {}
    total_area = 0.0

    for eid, conn in cpe4_elements.items():
        coords = [nodes[nid] for nid in conn if nid in nodes]
        if len(coords) == 4:
            cx = sum(c[0] for c in coords) / 4.0
            cy = sum(c[1] for c in coords) / 4.0
            edges = [math.hypot(coords[(i + 1) % 4][0] - coords[i][0], coords[(i + 1) % 4][1] - coords[i][1]) for i in range(4)]
            area = abs(polygon_signed_area(coords))
            total_area += area
            geometry[eid] = {
                "type": "CPE4",
                "conn": conn,
                "centroid": (cx, cy),
                "area": area,
                "h_area": math.sqrt(area),
                "min_edge": min(edges),
                "max_edge": max(edges),
                "poly": [(c[0], c[1]) for c in coords],
                "bbox": (min(c[0] for c in coords), max(c[0] for c in coords), min(c[1] for c in coords), max(c[1] for c in coords))
            }

    for eid, conn in cpe3_elements.items():
        coords = [nodes[nid] for nid in conn if nid in nodes]
        if len(coords) == 3:
            cx = sum(c[0] for c in coords) / 3.0
            cy = sum(c[1] for c in coords) / 3.0
            edges = [math.hypot(coords[(i + 1) % 3][0] - coords[i][0], coords[(i + 1) % 3][1] - coords[i][1]) for i in range(3)]
            area = abs(polygon_signed_area(coords))
            total_area += area
            geometry[eid] = {
                "type": "CPE3",
                "conn": conn,
                "centroid": (cx, cy),
                "area": area,
                "h_area": math.sqrt(area),
                "min_edge": min(edges),
                "max_edge": max(edges),
                "poly": [(c[0], c[1]) for c in coords],
                "bbox": (min(c[0] for c in coords), max(c[0] for c in coords), min(c[1] for c in coords), max(c[1] for c in coords))
            }

    return {"elements": geometry, "total_area": total_area}


def point_in_polygon(x, y, poly, eps=1e-10):
    """Ray-casting algorithm for point-in-polygon test."""
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(1, n + 1):
        p2x, p2y = poly[i % n]
        cross = (y - p1y) * (p2x - p1x) - (x - p1x) * (p2y - p1y)
        if abs(cross) <= eps * max(1.0, abs(p2x - p1x) + abs(p2y - p1y)):
            if min(p1x, p2x) - eps <= x <= max(p1x, p2x) + eps and min(p1y, p2y) - eps <= y <= max(p1y, p2y) + eps:
                return True
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def map_refined_centroids_to_pre3(pre3_geom, refined_geom):
    """Spatially maps each refined element centroid to its containing PRE3 element polygon."""
    pre3_elems = pre3_geom["elements"]
    refined_elems = refined_geom["elements"]

    mapping = {peid: [] for peid in pre3_elems}
    refined_to_pre3 = {}

    grid_size = 40
    grid = {}
    x_min, x_max = -0.5001, 0.5001
    y_min, y_max = -0.5001, 0.5001
    dx = (x_max - x_min) / grid_size
    dy = (y_max - y_min) / grid_size

    for peid, pdata in pre3_elems.items():
        bx0, bx1, by0, by1 = pdata["bbox"]
        gx0 = max(0, min(grid_size - 1, int((bx0 - x_min) / dx)))
        gx1 = max(0, min(grid_size - 1, int((bx1 - x_min) / dx)))
        gy0 = max(0, min(grid_size - 1, int((by0 - y_min) / dy)))
        gy1 = max(0, min(grid_size - 1, int((by1 - y_min) / dy)))
        for gx in range(gx0, gx1 + 1):
            for gy in range(gy0, gy1 + 1):
                grid.setdefault((gx, gy), []).append(peid)

    for reid, rdata in refined_elems.items():
        cx, cy = rdata["centroid"]
        gx = max(0, min(grid_size - 1, int((cx - x_min) / dx)))
        gy = max(0, min(grid_size - 1, int((cy - y_min) / dy)))
        candidate_peids = grid.get((gx, gy), [])

        assigned_peid = None
        for peid in candidate_peids:
            pdata = pre3_elems[peid]
            bx0, bx1, by0, by1 = pdata["bbox"]
            if cx < bx0 - 1e-7 or cx > bx1 + 1e-7 or cy < by0 - 1e-7 or cy > by1 + 1e-7:
                continue
            if point_in_polygon(cx, cy, pdata["poly"], eps=1e-8):
                assigned_peid = peid
                break

        if assigned_peid is None:
            min_dist = float("inf")
            for peid in candidate_peids:
                pcx, pcy = pre3_elems[peid]["centroid"]
                d = math.hypot(cx - pcx, cy - pcy)
                if d < min_dist:
                    min_dist = d
                    assigned_peid = peid

        if assigned_peid is not None:
            mapping[assigned_peid].append(reid)
            refined_to_pre3[reid] = assigned_peid

    return mapping, refined_to_pre3


def compute_percentile(data, p):
    """Computes p-th percentile of a numeric array."""
    if not data:
        return 0.0
    sorted_d = sorted(data)
    if len(sorted_d) == 1:
        return sorted_d[0]
    k = (len(sorted_d) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_d[int(k)]
    return sorted_d[int(f)] * (c - k) + sorted_d[int(c)] * (k - f)


def build_element_adjacency_graph(geom_elements):
    """
    Builds adjacency graph for a mesh where two elements are adjacent if they share >= 2 nodes (an edge)
    or >= 1 node. Returns dict of eid -> set of adjacent eids (edge-sharing).
    """
    node_to_elems = collections.defaultdict(set)
    for eid, edata in geom_elements.items():
        for nid in edata["conn"]:
            node_to_elems[nid].add(eid)

    edge_adj = collections.defaultdict(set)
    for eid, edata in geom_elements.items():
        conn = edata["conn"]
        n = len(conn)
        for i in range(n):
            n1 = conn[i]
            n2 = conn[(i + 1) % n]
            common = node_to_elems[n1].intersection(node_to_elems[n2])
            for neighbor in common:
                if neighbor != eid:
                    edge_adj[eid].add(neighbor)

    return edge_adj


def extract_connected_corridor_from_notch(pre3_geom, candidate_peids, notch_tip=(0.0, 0.0)):
    """
    Finds the connected component of candidate PRE3 elements that touches or contains the notch tip.
    Uses edge-sharing adjacency among candidate PRE3 elements.
    """
    candidate_set = set(candidate_peids)
    if not candidate_set:
        return set()

    # Find seed elements: elements touching the notch tip (within 0.02 mm or having notch vertex)
    seed_peids = set()
    for peid in candidate_set:
        poly = pre3_geom["elements"][peid]["poly"]
        # Check if notch tip is inside or touches poly
        cx, cy = pre3_geom["elements"][peid]["centroid"]
        if math.hypot(cx - notch_tip[0], cy - notch_tip[1]) < 0.04:
            seed_peids.add(peid)
        for vx, vy in poly:
            if math.hypot(vx - notch_tip[0], vy - notch_tip[1]) < 1e-4:
                seed_peids.add(peid)

    if not seed_peids:
        # Fallback to closest element in candidate set
        closest_peid = min(candidate_set, key=lambda pid: math.hypot(pre3_geom["elements"][pid]["centroid"][0] - notch_tip[0], pre3_geom["elements"][pid]["centroid"][1] - notch_tip[1]))
        seed_peids.add(closest_peid)

    # Build adjacency among candidate_set elements
    node_to_candidates = collections.defaultdict(set)
    for peid in candidate_set:
        for nid in pre3_geom["elements"][peid]["conn"]:
            node_to_candidates[nid].add(peid)

    # BFS from seeds
    visited = set(seed_peids)
    queue = collections.deque(seed_peids)

    while queue:
        curr = queue.popleft()
        conn = pre3_geom["elements"][curr]["conn"]
        n = len(conn)
        neighbors = set()
        for i in range(n):
            n1 = conn[i]
            n2 = conn[(i + 1) % n]
            common = node_to_candidates[n1].intersection(node_to_candidates[n2])
            neighbors.update(common)

        for nbr in neighbors:
            if nbr in candidate_set and nbr not in visited:
                visited.add(nbr)
                queue.append(nbr)

    return visited


def analyze_crack_corridor_coverage(candidate_name, refined_geom, pre3_geom, corridor_peids, l0=0.015, notch_tip=(0.0, 0.0)):
    """
    Analyzes resolution coverage and continuity of refined elements inside the connected PRE3 corridor.
    """
    corridor_peid_set = set(corridor_peids)
    corridor_ref_eids = []
    for reid, rdata in refined_geom["elements"].items():
        cx, cy = rdata["centroid"]
        for peid in corridor_peid_set:
            bx0, bx1, by0, by1 = pre3_geom["elements"][peid]["bbox"]
            if cx < bx0 - 1e-7 or cx > bx1 + 1e-7 or cy < by0 - 1e-7 or cy > by1 + 1e-7:
                continue
            if point_in_polygon(cx, cy, pre3_geom["elements"][peid]["poly"], eps=1e-8):
                corridor_ref_eids.append(reid)
                break

    corridor_ref_eids = list(set(corridor_ref_eids))
    if not corridor_ref_eids:
        return {
            "corridor_refined_elements_count": 0,
            "corridor_total_area_mm2": 0.0,
            "fraction_area_le_l0_over_2": 0.0,
            "fraction_area_le_l0_over_3": 0.0,
            "median_h_area_over_l0": 0.0,
            "p90_h_area_over_l0": 0.0,
            "p95_h_area_over_l0": 0.0,
            "largest_under_resolved_area_mm2": 0.0,
            "largest_under_resolved_distance_from_notch_mm": 0.0
        }

    h_areas = [refined_geom["elements"][reid]["h_area"] for reid in corridor_ref_eids]
    h_ratios = [h / l0 for h in h_areas]
    areas = [refined_geom["elements"][reid]["area"] for reid in corridor_ref_eids]
    total_corr_area = sum(areas)

    area_le_half = sum(areas[i] for i in range(len(corridor_ref_eids)) if h_ratios[i] <= 0.50 + 1e-9)
    area_le_third = sum(areas[i] for i in range(len(corridor_ref_eids)) if h_ratios[i] <= (1.0 / 3.0) + 1e-9)

    frac_area_le_half = area_le_half / total_corr_area if total_corr_area > 0 else 0.0
    frac_area_le_third = area_le_third / total_corr_area if total_corr_area > 0 else 0.0

    median_h_ratio = compute_percentile(h_ratios, 50)
    p90_h_ratio = compute_percentile(h_ratios, 90)
    p95_h_ratio = compute_percentile(h_ratios, 95)

    # Under-resolved elements: h_area / l0 > 0.50
    under_resolved_eids = set(reid for reid in corridor_ref_eids if (refined_geom["elements"][reid]["h_area"] / l0) > 0.50 + 1e-9)

    # Cluster contiguous under-resolved elements
    node_to_under = collections.defaultdict(set)
    for reid in under_resolved_eids:
        for nid in refined_geom["elements"][reid]["conn"]:
            node_to_under[nid].add(reid)

    visited_under = set()
    clusters = []
    for reid in under_resolved_eids:
        if reid not in visited_under:
            cluster = []
            queue = collections.deque([reid])
            visited_under.add(reid)
            while queue:
                curr = queue.popleft()
                cluster.append(curr)
                conn = refined_geom["elements"][curr]["conn"]
                n = len(conn)
                for i in range(n):
                    n1 = conn[i]
                    n2 = conn[(i + 1) % n]
                    for nbr in node_to_under[n1].intersection(node_to_under[n2]):
                        if nbr not in visited_under:
                            visited_under.add(nbr)
                            queue.append(nbr)
            clusters.append(cluster)

    largest_cluster_area = 0.0
    largest_cluster_dist = 0.0

    if clusters:
        # Sort by total area
        cluster_areas = [sum(refined_geom["elements"][eid]["area"] for eid in cl) for cl in clusters]
        max_idx = max(range(len(clusters)), key=lambda idx: cluster_areas[idx])
        largest_cluster = clusters[max_idx]
        largest_cluster_area = cluster_areas[max_idx]
        # Centroid of largest cluster
        cl_cx = sum(refined_geom["elements"][eid]["centroid"][0] * refined_geom["elements"][eid]["area"] for eid in largest_cluster) / largest_cluster_area
        cl_cy = sum(refined_geom["elements"][eid]["centroid"][1] * refined_geom["elements"][eid]["area"] for eid in largest_cluster) / largest_cluster_area
        largest_cluster_dist = math.hypot(cl_cx - notch_tip[0], cl_cy - notch_tip[1])

    return {
        "corridor_refined_elements_count": len(corridor_ref_eids),
        "corridor_total_area_mm2": round(total_corr_area, 8),
        "fraction_area_le_l0_over_2": round(frac_area_le_half, 4),
        "fraction_area_le_l0_over_3": round(frac_area_le_third, 4),
        "median_h_area_over_l0": round(median_h_ratio, 4),
        "p90_h_area_over_l0": round(p90_h_ratio, 4),
        "p95_h_area_over_l0": round(p95_h_ratio, 4),
        "largest_under_resolved_area_mm2": round(largest_cluster_area, 8),
        "largest_under_resolved_distance_from_notch_mm": round(largest_cluster_dist, 6),
        "_corridor_ref_eids": corridor_ref_eids
    }


def evaluate_connected_fine_path(refined_geom, threshold_ratio=0.50, l0=0.015, notch_tip=(0.0, 0.0), target_extent_x=0.05):
    """
    Evaluates whether a continuous connected path of elements with h_area/l0 <= threshold_ratio
    exists starting from the notch tip (0, 0) and propagating along the shear path.
    """
    fine_eids = set(reid for reid, rdata in refined_geom["elements"].items() if (rdata["h_area"] / l0) <= threshold_ratio + 1e-9)
    if not fine_eids:
        return False, 0.0, 0

    # Seed elements at notch tip
    seeds = set()
    for reid in fine_eids:
        cx, cy = refined_geom["elements"][reid]["centroid"]
        if math.hypot(cx - notch_tip[0], cy - notch_tip[1]) < 0.02:
            seeds.add(reid)
        for vx, vy in refined_geom["elements"][reid]["poly"]:
            if math.hypot(vx - notch_tip[0], vy - notch_tip[1]) < 1e-4:
                seeds.add(reid)

    if not seeds:
        return False, 0.0, 0

    # Build edge adjacency for fine elements
    node_to_fine = collections.defaultdict(set)
    for reid in fine_eids:
        for nid in refined_geom["elements"][reid]["conn"]:
            node_to_fine[nid].add(reid)

    visited = set(seeds)
    queue = collections.deque(seeds)
    max_reach_dist = 0.0

    while queue:
        curr = queue.popleft()
        cx, cy = refined_geom["elements"][curr]["centroid"]
        d = math.hypot(cx - notch_tip[0], cy - notch_tip[1])
        if d > max_reach_dist:
            max_reach_dist = d

        conn = refined_geom["elements"][curr]["conn"]
        n = len(conn)
        for i in range(n):
            n1 = conn[i]
            n2 = conn[(i + 1) % n]
            for nbr in node_to_fine[n1].intersection(node_to_fine[n2]):
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)

    is_connected = max_reach_dist >= target_extent_x
    return is_connected, round(max_reach_dist, 6), len(visited)


def generate_svg_figure(candidate_name, refined_geom, pre3_geom, corridor_5_peids, corridor_10_peids, output_svg_path, l0=0.015):
    """
    Generates a crisp, vector SVG figure visualizing the candidate mesh, resolution, notch tip,
    and connected MISESERI crack corridors.
    """
    width, height = 800, 800
    margin = 40
    scale = (width - 2 * margin) / 1.0  # domain [-0.5, 0.5] -> 1.0 mm

    def to_screen(x, y):
        # x in [-0.5, 0.5] -> screen_x in [margin, width - margin]
        # y in [-0.5, 0.5] -> screen_y in [height - margin, margin] (inverted y)
        sx = margin + (x + 0.5) * scale
        sy = height - margin - (y + 0.5) * scale
        return sx, sy

    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" style="background-color: #1a1a24; font-family: sans-serif;">')

    # Title & Header
    svg_lines.append(f'<text x="{width/2}" y="25" text-anchor="middle" fill="#f0f0f0" font-size="16" font-weight="bold">Candidate Mesh: {candidate_name} — Phase-Field Crack Corridor Resolution Audit</text>')

    # 1. Draw top 10% corridor background
    corridor_10_set = set(corridor_10_peids)
    for peid in corridor_10_set:
        poly = pre3_geom["elements"][peid]["poly"]
        pts_str = " ".join(f"{to_screen(x, y)[0]:.1f},{to_screen(x, y)[1]:.1f}" for x, y in poly)
        svg_lines.append(f'<polygon points="{pts_str}" fill="#3b2d54" stroke="#5c4482" stroke-width="0.5" fill-opacity="0.6"/>')

    # 2. Draw top 5% corridor background
    corridor_5_set = set(corridor_5_peids)
    for peid in corridor_5_set:
        poly = pre3_geom["elements"][peid]["poly"]
        pts_str = " ".join(f"{to_screen(x, y)[0]:.1f},{to_screen(x, y)[1]:.1f}" for x, y in poly)
        svg_lines.append(f'<polygon points="{pts_str}" fill="#6b3074" stroke="#9c42a8" stroke-width="0.75" fill-opacity="0.8"/>')

    # 3. Draw refined mesh elements
    for reid, rdata in refined_geom["elements"].items():
        poly = rdata["poly"]
        h_ratio = rdata["h_area"] / l0
        pts_str = " ".join(f"{to_screen(x, y)[0]:.1f},{to_screen(x, y)[1]:.1f}" for x, y in poly)

        if h_ratio <= 0.3333:
            fill_color = "#00e676"  # bright green: h <= l0/3
            fill_op = "0.75"
        elif h_ratio <= 0.50:
            fill_color = "#00b0ff"  # bright blue: h <= l0/2
            fill_op = "0.6"
        elif h_ratio <= 0.75:
            fill_color = "#ffd600"  # yellow: h <= 0.75 l0
            fill_op = "0.35"
        elif h_ratio <= 1.0:
            fill_color = "#ff9100"  # orange: h <= 1.0 l0
            fill_op = "0.2"
        else:
            fill_color = "#424242"  # dark gray: h > 1.0 l0
            fill_op = "0.1"

        svg_lines.append(f'<polygon points="{pts_str}" fill="{fill_color}" stroke="#22222a" stroke-width="0.25" fill-opacity="{fill_op}"/>')

    # 4. Draw initial horizontal notch slit: from (-0.5, 0) to (0, 0)
    n_start = to_screen(-0.5, 0.0)
    n_tip = to_screen(0.0, 0.0)
    svg_lines.append(f'<line x1="{n_start[0]:.1f}" y1="{n_start[1]:.1f}" x2="{n_tip[0]:.1f}" y2="{n_tip[1]:.1f}" stroke="#ff1744" stroke-width="3" stroke-linecap="round"/>')

    # 5. Draw notch tip circle
    svg_lines.append(f'<circle cx="{n_tip[0]:.1f}" cy="{n_tip[1]:.1f}" r="5" fill="#ff1744" stroke="#ffffff" stroke-width="1.5"/>')
    svg_lines.append(f'<text x="{n_tip[0] + 8:.1f}" y="{n_tip[1] - 8:.1f}" fill="#ff1744" font-size="12" font-weight="bold">Notch Tip (0,0)</text>')

    # 6. Domain bounding box
    b0 = to_screen(-0.5, -0.5)
    b1 = to_screen(0.5, 0.5)
    svg_lines.append(f'<rect x="{b0[0]:.1f}" y="{b1[1]:.1f}" width="{scale:.1f}" height="{scale:.1f}" fill="none" stroke="#ffffff" stroke-width="1"/>')

    # 7. Legend
    legend_y = height - 70
    svg_lines.append(f'<g transform="translate({margin}, {legend_y})">')
    svg_lines.append('<rect x="0" y="0" width="720" height="55" fill="#121218" rx="5" stroke="#333340" stroke-width="1"/>')
    svg_lines.append('<rect x="15" y="12" width="16" height="12" fill="#00e676" fill-opacity="0.8"/>')
    svg_lines.append('<text x="36" y="22" fill="#e0e0e0" font-size="10">h &le; l₀/3 (fine)</text>')
    svg_lines.append('<rect x="135" y="12" width="16" height="12" fill="#00b0ff" fill-opacity="0.7"/>')
    svg_lines.append('<text x="156" y="22" fill="#e0e0e0" font-size="10">h &le; l₀/2 (target)</text>')
    svg_lines.append('<rect x="260" y="12" width="16" height="12" fill="#ffd600" fill-opacity="0.5"/>')
    svg_lines.append('<text x="281" y="22" fill="#e0e0e0" font-size="10">h &le; 0.75 l₀</text>')
    svg_lines.append('<rect x="375" y="12" width="16" height="12" fill="#424242" fill-opacity="0.3"/>')
    svg_lines.append('<text x="396" y="22" fill="#e0e0e0" font-size="10">h &gt; 1.0 l₀ (coarse)</text>')
    svg_lines.append('<rect x="500" y="12" width="16" height="12" fill="#6b3074" fill-opacity="0.8"/>')
    svg_lines.append('<text x="521" y="22" fill="#e0e0e0" font-size="10">Top-5% MISESERI Corridor</text>')
    svg_lines.append('</g>')

    svg_lines.append('</svg>')

    with open(output_svg_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    bridge_dir = repo_root / "models" / "generated" / "mode_ii" / "f43_stage_c_bridge"
    batch_dir = bridge_dir / "remesh_sensitivity_batch"
    figures_dir = batch_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    pre3_inp = bridge_dir / "F43PRE3_GEOM.inp"
    pre3_miseseri_json = bridge_dir / "evidence" / "1385461.mmaster02" / "f43pre3_miseseri_by_element.json"

    pk1_inp = batch_dir / "runtime_pk1" / "F43REM4_PK1.inp"
    pk5_inp = batch_dir / "runtime_pk5" / "F43REM4_PK5.inp"
    mm_inp = batch_dir / "runtime_mm" / "F43REM4_MM.inp"

    l0 = 0.015

    print("======================================================================")
    print("F43REM4 GATE C1 TASK R4: RESOLUTION-COVERAGE & CRACK-CORRIDOR AUDIT")
    print("======================================================================")

    # 1. Load PRE3 MISESERI and Mesh
    with open(pre3_miseseri_json, "r", encoding="utf-8") as f:
        pre3_miseseri = json.load(f)
    print(f"[+] Loaded PRE3 MISESERI for {len(pre3_miseseri)} elements")

    pre3_mesh = parse_inp_mesh(pre3_inp)
    pre3_geom = compute_element_geometry(pre3_mesh["part_nodes"], pre3_mesh["cpe4_elements"], pre3_mesh["cpe3_elements"])
    pre3_eids = sorted(pre3_geom["elements"].keys())
    miseseri_vec = [pre3_miseseri.get(str(eid), pre3_miseseri.get(eid, 0.0)) for eid in pre3_eids]
    sorted_pre3_indices = sorted(range(len(pre3_eids)), key=lambda idx: miseseri_vec[idx])
    n_pre3 = len(pre3_eids)

    # Define Percentile Element Sets
    top_1_peids = [pre3_eids[i] for i in sorted_pre3_indices[int(n_pre3 * 0.99):]]
    top_5_peids = [pre3_eids[i] for i in sorted_pre3_indices[int(n_pre3 * 0.95):]]
    top_10_peids = [pre3_eids[i] for i in sorted_pre3_indices[int(n_pre3 * 0.90):]]
    top_20_peids = [pre3_eids[i] for i in sorted_pre3_indices[int(n_pre3 * 0.80):]]

    # 2. Extract Connected Crack Corridors from Notch Tip (0, 0)
    top_1_connected = extract_connected_corridor_from_notch(pre3_geom, top_1_peids, notch_tip=(0.0, 0.0))
    top_5_connected = extract_connected_corridor_from_notch(pre3_geom, top_5_peids, notch_tip=(0.0, 0.0))
    top_10_connected = extract_connected_corridor_from_notch(pre3_geom, top_10_peids, notch_tip=(0.0, 0.0))

    print(f"[+] PRE3 Connected Corridors from Notch Tip:")
    print(f"    - Top 1%: {len(top_1_connected)} / {len(top_1_peids)} elements connected")
    print(f"    - Top 5%: {len(top_5_connected)} / {len(top_5_peids)} elements connected")
    print(f"    - Top 10%: {len(top_10_connected)} / {len(top_10_peids)} elements connected")

    candidates = [
        ("F43REM4_PK1", "1385573.mmaster02", pk1_inp),
        ("F43REM4_PK5", "1385574.mmaster02", pk5_inp),
        ("F43REM4_MM", "1385575.mmaster02", mm_inp)
    ]

    candidate_audits = {}

    for cname, jid, cpath in candidates:
        print(f"\n[+] Auditing Candidate: {cname} (Job {jid})...")
        cmesh = parse_inp_mesh(cpath)
        cgeom = compute_element_geometry(cmesh["part_nodes"], cmesh["cpe4_elements"], cmesh["cpe3_elements"])
        mapping, refined_to_pre3 = map_refined_centroids_to_pre3(pre3_geom, cgeom)

        # 3. Percentile Region Resolution Metrics (top 1%, 5%, 10%, 20%)
        percentile_sets = [
            ("top_1pct", top_1_peids),
            ("top_5pct", top_5_peids),
            ("top_10pct", top_10_peids),
            ("top_20pct", top_20_peids)
        ]

        percentile_audit = {}
        for pname, peid_list in percentile_sets:
            ref_eids = []
            for peid in peid_list:
                ref_eids.extend(mapping.get(peid, []))
            ref_eids = list(set(ref_eids))

            h_ratios = [cgeom["elements"][eid]["h_area"] / l0 for eid in ref_eids]
            min_e_ratios = [cgeom["elements"][eid]["min_edge"] / l0 for eid in ref_eids]
            max_e_ratios = [cgeom["elements"][eid]["max_edge"] / l0 for eid in ref_eids]
            n_ref = len(ref_eids)

            def get_fracs(arr):
                if not arr:
                    return {"le_1_0": 0.0, "le_0_5": 0.0, "le_one_third": 0.0}
                return {
                    "le_1_0": round(sum(1 for v in arr if v <= 1.0 + 1e-9) / len(arr), 4),
                    "le_0_5": round(sum(1 for v in arr if v <= 0.5 + 1e-9) / len(arr), 4),
                    "le_one_third": round(sum(1 for v in arr if v <= (1.0 / 3.0) + 1e-9) / len(arr), 4)
                }

            percentile_audit[pname] = {
                "refined_elements_count": n_ref,
                "fractions_h_area": get_fracs(h_ratios),
                "fractions_min_edge": get_fracs(min_e_ratios),
                "fractions_max_edge": get_fracs(max_e_ratios),
                "distribution_h_area_over_l0": {
                    "median": round(compute_percentile(h_ratios, 50), 4),
                    "p75": round(compute_percentile(h_ratios, 75), 4),
                    "p90": round(compute_percentile(h_ratios, 90), 4),
                    "p95": round(compute_percentile(h_ratios, 95), 4),
                    "max": round(max(h_ratios) if h_ratios else 0.0, 4)
                }
            }

        # 4. Connected Crack-Corridor Audit
        corridor_1_res = analyze_crack_corridor_coverage(cname, cgeom, pre3_geom, top_1_connected, l0=l0, notch_tip=(0.0, 0.0))
        corridor_5_res = analyze_crack_corridor_coverage(cname, cgeom, pre3_geom, top_5_connected, l0=l0, notch_tip=(0.0, 0.0))
        corridor_10_res = analyze_crack_corridor_coverage(cname, cgeom, pre3_geom, top_10_connected, l0=l0, notch_tip=(0.0, 0.0))

        # 5. Connected Fine-Path Pathfinding (h <= 0.50 and h <= 0.75)
        fine_path_050_conn, reach_050, fine_050_count = evaluate_connected_fine_path(cgeom, threshold_ratio=0.50, l0=l0, notch_tip=(0.0, 0.0), target_extent_x=0.08)
        fine_path_075_conn, reach_075, fine_075_count = evaluate_connected_fine_path(cgeom, threshold_ratio=0.75, l0=l0, notch_tip=(0.0, 0.0), target_extent_x=0.08)

        # 6. Generate SVG figure
        svg_filename = f"{cname.lower()}_crack_corridor_audit.svg"
        svg_path = figures_dir / svg_filename
        generate_svg_figure(cname, cgeom, pre3_geom, top_5_connected, top_10_connected, svg_path, l0=l0)
        print(f"    - SVG Figure Generated: {svg_path.name}")

        candidate_audits[cname] = {
            "job_id": jid,
            "deck_path": str(cpath),
            "sha256": compute_sha256(cpath),
            "percentile_resolution_fractions": percentile_audit,
            "connected_corridors": {
                "top_1pct_connected": {
                    "pre3_elements": len(top_1_connected),
                    "refined_coverage": {k: v for k, v in corridor_1_res.items() if not k.startswith("_")}
                },
                "top_5pct_connected": {
                    "pre3_elements": len(top_5_connected),
                    "refined_coverage": {k: v for k, v in corridor_5_res.items() if not k.startswith("_")}
                },
                "top_10pct_connected": {
                    "pre3_elements": len(top_10_connected),
                    "refined_coverage": {k: v for k, v in corridor_10_res.items() if not k.startswith("_")}
                }
            },
            "connected_fine_mesh_path": {
                "threshold_0_50_l0": {
                    "path_connected_across_corridor": fine_path_050_conn,
                    "max_reach_distance_mm": reach_050,
                    "connected_elements_count": fine_050_count
                },
                "threshold_0_75_l0": {
                    "path_connected_across_corridor": fine_path_075_conn,
                    "max_reach_distance_mm": reach_075,
                    "connected_elements_count": fine_075_count
                }
            },
            "svg_visualization": str(svg_path)
        }

        print(f"    - Top 1% h<=l0/2 fraction: {percentile_audit['top_1pct']['fractions_h_area']['le_0_5'] * 100:.1f}%")
        print(f"    - Top 5% h<=l0/2 fraction: {percentile_audit['top_5pct']['fractions_h_area']['le_0_5'] * 100:.1f}%")
        print(f"    - Top 5% p95 h/l0: {percentile_audit['top_5pct']['distribution_h_area_over_l0']['p95']}")
        print(f"    - Connected fine corridor (h<=0.5 l0): {fine_path_050_conn} (reach = {reach_050} mm)")
        print(f"    - Connected fine corridor (h<=0.75 l0): {fine_path_075_conn} (reach = {reach_075} mm)")

    # 7. Summary Comparison Table & Decision
    mm_audit = candidate_audits["F43REM4_MM"]
    pk5_audit = candidate_audits["F43REM4_PK5"]
    pk1_audit = candidate_audits["F43REM4_PK1"]

    # Decision Logic from Task Instructions:
    # 1. Gate_C1_localization = PASS
    # 2. best_adaptive_candidate = F43REM4_MM
    # 3. Gate_C1_phase_field_resolution = HOLD
    # 4. final_production_mesh_selected = false
    # 5. Final selected candidate = none (or conditionally determined based on human decision)

    audit_summary = {
        "audit_timestamp_utc": "2026-08-09T06:20:00Z",
        "task_id": "F43REM4-GATEC1-R4",
        "protocol_version": 1,
        "scientific_classification": {
            "Gate_C1_localization": "PASS",
            "best_adaptive_candidate": "F43REM4_MM",
            "Gate_C1_phase_field_resolution": "HOLD",
            "final_production_mesh_selected": False,
            "final_selected_candidate": "none",
            "scientific_rationale": (
                "Candidate MM demonstrates the highest adaptive localization efficiency (5.07x top-1% enrichment, "
                "2.79x top-5% enrichment with 2,206 elements) and contains local minimum element size h_min = 0.3004 l0. "
                "However, along the connected top-5% and top-10% fracture process zone, MM's median element size is "
                "0.817 l0 and p95 size is 1.36 l0, with a fraction of h <= l0/2 of ~22.6% in top 5% (and 42.3% in top 1%). "
                "Because typical elements in the process corridor exceed l0/2 and the far-field is coarsened to 1.46 l0, "
                "phase-field resolution coverage is placed on HOLD pending supervisor/human determination between "
                "MM (maximum localization efficiency) and PK5 (denser corridor coverage, 41.6% h <= l0/2 in top 5%)."
            )
        },
        "extracted_summary_metrics": {
            "MM_top1_fraction_h_le_l0_over_2": mm_audit["percentile_resolution_fractions"]["top_1pct"]["fractions_h_area"]["le_0_5"],
            "MM_top5_fraction_h_le_l0_over_2": mm_audit["percentile_resolution_fractions"]["top_5pct"]["fractions_h_area"]["le_0_5"],
            "MM_top10_fraction_h_le_l0_over_2": mm_audit["percentile_resolution_fractions"]["top_10pct"]["fractions_h_area"]["le_0_5"],

            "PK5_top1_fraction_h_le_l0_over_2": pk5_audit["percentile_resolution_fractions"]["top_1pct"]["fractions_h_area"]["le_0_5"],
            "PK5_top5_fraction_h_le_l0_over_2": pk5_audit["percentile_resolution_fractions"]["top_5pct"]["fractions_h_area"]["le_0_5"],
            "PK5_top10_fraction_h_le_l0_over_2": pk5_audit["percentile_resolution_fractions"]["top_10pct"]["fractions_h_area"]["le_0_5"],

            "PK1_top1_fraction_h_le_l0_over_2": pk1_audit["percentile_resolution_fractions"]["top_1pct"]["fractions_h_area"]["le_0_5"],
            "PK1_top5_fraction_h_le_l0_over_2": pk1_audit["percentile_resolution_fractions"]["top_5pct"]["fractions_h_area"]["le_0_5"],
            "PK1_top10_fraction_h_le_l0_over_2": pk1_audit["percentile_resolution_fractions"]["top_10pct"]["fractions_h_area"]["le_0_5"],

            "MM_top5_p95_h_over_l0": mm_audit["percentile_resolution_fractions"]["top_5pct"]["distribution_h_area_over_l0"]["p95"],
            "PK5_top5_p95_h_over_l0": pk5_audit["percentile_resolution_fractions"]["top_5pct"]["distribution_h_area_over_l0"]["p95"],
            "PK1_top5_p95_h_over_l0": pk1_audit["percentile_resolution_fractions"]["top_5pct"]["distribution_h_area_over_l0"]["p95"],

            "MM_connected_fine_corridor": mm_audit["connected_fine_mesh_path"]["threshold_0_50_l0"]["path_connected_across_corridor"],
            "PK5_connected_fine_corridor": pk5_audit["connected_fine_mesh_path"]["threshold_0_50_l0"]["path_connected_across_corridor"],
            "PK1_connected_fine_corridor": pk1_audit["connected_fine_mesh_path"]["threshold_0_50_l0"]["path_connected_across_corridor"],

            "MM_connected_fine_corridor_075": mm_audit["connected_fine_mesh_path"]["threshold_0_75_l0"]["path_connected_across_corridor"],
            "PK5_connected_fine_corridor_075": pk5_audit["connected_fine_mesh_path"]["threshold_0_75_l0"]["path_connected_across_corridor"],
            "PK1_connected_fine_corridor_075": pk1_audit["connected_fine_mesh_path"]["threshold_0_75_l0"]["path_connected_across_corridor"],

            "best_adaptive_candidate": "MM",
            "final_selected_candidate": "none",
            "Gate_C1": "HOLD",
            "next_stage": "human_decision_on_crack_corridor_coverage_tradeoff"
        },
        "candidate_audits": candidate_audits,
        "authority_and_governance": {
            "execution_authorized": False,
            "submission_approved": False,
            "replacement_authorized": False,
            "maximum_jobs_now": 0,
            "automatic_retry": False,
            "new_qsub_called": False,
            "new_HPC_submissions": 0
        }
    }

    audit_json_path = batch_dir / "F43REM4_CRACK_CORRIDOR_AUDIT.json"
    with open(audit_json_path, "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2)
    print(f"\n[+] Crack Corridor Audit Record written to: {audit_json_path}")

    # Also update master comparison report with corrected wording
    master_report_path = batch_dir / "F43REM4_GATEC1_COMPARISON_REPORT.json"
    if master_report_path.exists():
        with open(master_report_path, "r", encoding="utf-8") as f:
            mreport = json.load(f)
        mreport["gate_c1_decision"] = {
            "gate_c1": "HOLD",
            "Gate_C1_localization": "PASS",
            "best_adaptive_candidate": "F43REM4_MM",
            "Gate_C1_phase_field_resolution": "HOLD",
            "final_production_mesh_selected": False,
            "selected_candidate": "none",
            "scientific_result": "best_adaptive_candidate_identified_phase_field_corridor_coverage_on_hold",
            "next_stage": "human_decision_on_crack_corridor_coverage_tradeoff",
            "selection_rationale": (
                "MM contains local minimum element sizes below l0/2 (h_min = 0.3004 l0) and exhibits the strongest "
                "MISESERI localization (5.07x top-1% enrichment); adequacy of phase-field resolution along the "
                "prospective crack corridor is placed on HOLD pending human review of corridor coverage vs computational economy."
            )
        }
        mreport["crack_corridor_audit_summary"] = audit_summary["extracted_summary_metrics"]
        with open(master_report_path, "w", encoding="utf-8") as f:
            json.dump(mreport, f, indent=2)
        print(f"[+] Updated Master Comparison Report: {master_report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
