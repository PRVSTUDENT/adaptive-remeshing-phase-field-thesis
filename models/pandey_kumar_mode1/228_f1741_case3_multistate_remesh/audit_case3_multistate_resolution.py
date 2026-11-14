# -*- coding: utf-8 -*-
"""
audit_case3_multistate_resolution.py

Rigorous spatial resolution and FE quality audit for Case 3 (Section 4.3):
  - Primary Corridor (Notch tip to central hole left flank)
  - Secondary Corridor (Central hole right flank to right boundary)
  - 10-station longitudinal discretization along both corridor centerlines
  - Count-weighted and area-weighted compliance with h <= l0/2 (0.1425 mm)
  - Contiguous coarse cluster and transverse coarse barrier analysis
  - Circumferential hole-boundary annular resolution
  - Gaussian Jacobian determinant and aspect ratio audits
"""
from __future__ import print_function
import os
import sys
import math
import json
from collections import defaultdict, deque

L0_MM = 0.285
L0_HALF_MM = L0_MM / 2.0  # 0.1425 mm
L0_THIRD_MM = L0_MM / 3.0  # 0.0950 mm

# Case 3 Geometry (mm)
PLATE_W = 65.0
PLATE_H = 120.0
NOTCH_X = 10.0
NOTCH_Y = 70.0
HOLE_C_X = 36.5
HOLE_C_Y = 51.0
HOLE_R = 10.0
HOLE_LEFT_X = 26.5
HOLE_LEFT_Y = 51.0
HOLE_RIGHT_X = 46.5
HOLE_RIGHT_Y = 51.0
RIGHT_EDGE_X = 65.0
RIGHT_EDGE_Y = 51.0

def parse_inp_mesh(inp_path):
    nodes = {}
    elements = {}

    current_section = None
    with open(inp_path, 'r') as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.startswith('*'):
                line_upper = line_str.upper()
                if line_upper.startswith('*NODE'):
                    current_section = 'NODE'
                elif line_upper.startswith('*ELEMENT'):
                    current_section = 'ELEMENT'
                else:
                    current_section = None
                continue

            if current_section == 'NODE':
                parts = [p.strip() for p in line_str.split(',')]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        pass
            elif current_section == 'ELEMENT':
                parts = [p.strip() for p in line_str.split(',') if p.strip()]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        conn = [int(p) for p in parts[1:]]
                        elements[eid] = conn
                    except ValueError:
                        pass
    return nodes, elements

def compute_element_metrics(nodes, elements):
    metrics = {}
    for eid, conn in elements.items():
        coords = [nodes[nid] for nid in conn if nid in nodes]
        n_pts = len(coords)
        if n_pts < 3:
            continue
        xs = [pt[0] for pt in coords]
        ys = [pt[1] for pt in coords]
        area = 0.5 * abs(sum(xs[i]*ys[(i+1)%n_pts] - ys[i]*xs[(i+1)%n_pts] for i in range(n_pts)))
        h_eq = math.sqrt(area)
        cx = sum(xs) / float(n_pts)
        cy = sum(ys) / float(n_pts)

        # Approximate element Jacobian det(J) for quads
        if n_pts == 4:
            x1, y1 = coords[0]; x2, y2 = coords[1]; x3, y3 = coords[2]; x4, y4 = coords[3]
            # sub-triangle cross products
            j1 = (x2 - x1)*(y4 - y1) - (x4 - x1)*(y2 - y1)
            j2 = (x3 - x2)*(y1 - y2) - (x1 - x2)*(y3 - y2)
            j3 = (x4 - x3)*(y2 - y3) - (x2 - x3)*(y4 - y3)
            j4 = (x1 - x4)*(y3 - y4) - (x3 - x4)*(y1 - y4)
            min_j = min(j1, j2, j3, j4)
        else:
            x1, y1 = coords[0]; x2, y2 = coords[1]; x3, y3 = coords[2]
            min_j = (x2 - x1)*(y3 - y1) - (x3 - x1)*(y2 - y1)

        # Aspect ratio
        edge_lens = [math.hypot(xs[(i+1)%n_pts] - xs[i], ys[(i+1)%n_pts] - ys[i]) for i in range(n_pts)]
        ar = max(edge_lens) / min(edge_lens) if min(edge_lens) > 0 else 1.0

        metrics[eid] = {
            'conn': conn,
            'coords': coords,
            'n_pts': n_pts,
            'area': area,
            'h_eq': h_eq,
            'cx': cx,
            'cy': cy,
            'min_det_j': min_j,
            'aspect_ratio': ar
        }
    return metrics

def audit_trajectory(metrics, x1, y1, x2, y2, corridor_w, n_stations=10):
    dx = x2 - x1
    dy = y2 - y1
    L = math.hypot(dx, dy)
    ux = dx / L
    uy = dy / L

    corridor_elems = {}
    stations = [[] for _ in range(n_stations)]

    for eid, data in metrics.items():
        cx, cy = data['cx'], data['cy']
        vx = cx - x1
        vy = cy - y1
        proj = vx * ux + vy * uy
        perp = abs(-ux * vy + uy * vx)

        if 0.0 <= proj <= L and perp <= corridor_w:
            corridor_elems[eid] = data
            s_frac = proj / L
            idx = int(s_frac * n_stations)
            if idx >= n_stations:
                idx = n_stations - 1
            stations[idx].append(data)

    # Station stats
    station_stats = []
    for i, s_elems in enumerate(stations):
        n = len(s_elems)
        if n == 0:
            station_stats.append({'station': i+1, 'count': 0, 'mean_h': 0.0, 'pct_le_l0_half': 0.0})
            continue
        hs = [e['h_eq'] for e in s_elems]
        c_half = sum(1 for h in hs if h <= L0_HALF_MM)
        station_stats.append({
            'station': i+1,
            'count': n,
            'min_h_mm': min(hs),
            'max_h_mm': max(hs),
            'mean_h_mm': sum(hs) / float(n),
            'count_le_l0_half': c_half,
            'pct_count_le_l0_half': 100.0 * c_half / float(n)
        })

    # Overall corridor stats
    tot_n = len(corridor_elems)
    tot_area = sum(e['area'] for e in corridor_elems.values()) if tot_n > 0 else 0.0
    c_half = sum(1 for e in corridor_elems.values() if e['h_eq'] <= L0_HALF_MM)
    a_half = sum(e['area'] for e in corridor_elems.values() if e['h_eq'] <= L0_HALF_MM)
    c_l0 = sum(1 for e in corridor_elems.values() if e['h_eq'] <= L0_MM)
    a_l0 = sum(e['area'] for e in corridor_elems.values() if e['h_eq'] <= L0_MM)
    hs_all = [e['h_eq'] for e in corridor_elems.values()] if tot_n > 0 else [0.0]

    # Cluster / coarse barrier check
    noncompliant_ids = set([eid for eid, e in corridor_elems.items() if e['h_eq'] > L0_HALF_MM])
    # Build adjacency
    node_to_elems = defaultdict(set)
    for eid in noncompliant_ids:
        for nid in corridor_elems[eid]['conn']:
            node_to_elems[nid].add(eid)

    adj = defaultdict(set)
    for eid in noncompliant_ids:
        for nid in corridor_elems[eid]['conn']:
            for other_eid in node_to_elems[nid]:
                if other_eid != eid:
                    adj[eid].add(other_eid)

    visited = set()
    clusters = []
    has_transverse_barrier = False

    for eid in noncompliant_ids:
        if eid not in visited:
            cluster = []
            q = deque([eid])
            visited.add(eid)
            while q:
                curr = q.popleft()
                cluster.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        q.append(neighbor)
            clusters.append(cluster)

            # Check transverse span of this coarse cluster
            perp_dists = []
            for ceid in cluster:
                ccx = corridor_elems[ceid]['cx']
                ccy = corridor_elems[ceid]['cy']
                p_dist = -ux * (ccy - y1) + uy * (ccx - x1)
                perp_dists.append(p_dist)
            span_perp = max(perp_dists) - min(perp_dists) if perp_dists else 0.0
            # If a coarse cluster spans >= 50% of total corridor width (2 * corridor_w), it is a transverse barrier
            if span_perp >= 0.50 * (2.0 * corridor_w):
                has_transverse_barrier = True

    return {
        'trajectory_length_mm': L,
        'corridor_width_mm': 2.0 * corridor_w,
        'element_count': tot_n,
        'total_area_mm2': tot_area,
        'min_h_mm': min(hs_all),
        'max_h_mm': max(hs_all),
        'mean_h_mm': sum(hs_all) / float(tot_n) if tot_n > 0 else 0.0,
        'count_le_l0_half': c_half,
        'pct_count_le_l0_half': 100.0 * c_half / float(tot_n) if tot_n > 0 else 0.0,
        'area_le_l0_half_mm2': a_half,
        'pct_area_le_l0_half': 100.0 * a_half / tot_area if tot_area > 0 else 0.0,
        'count_le_l0': c_l0,
        'pct_count_le_l0': 100.0 * c_l0 / float(tot_n) if tot_n > 0 else 0.0,
        'pct_area_le_l0': 100.0 * a_l0 / tot_area if tot_area > 0 else 0.0,
        'has_transverse_coarse_barrier': has_transverse_barrier,
        'coarse_cluster_count': len(clusters),
        'stations': station_stats
    }

def audit_case3_mesh(inp_path, out_json_path=None):
    print("Auditing Case 3 mesh: %s" % inp_path)
    nodes, elements = parse_inp_mesh(inp_path)
    metrics = compute_element_metrics(nodes, elements)

    tot_elems = len(metrics)
    quad_count = sum(1 for m in metrics.values() if m['n_pts'] == 4)
    tri_count = sum(1 for m in metrics.values() if m['n_pts'] == 3)
    min_det_j = min(m['min_det_j'] for m in metrics.values())
    max_ar = max(m['aspect_ratio'] for m in metrics.values())

    w_half = 2.0 * L0_MM  # 0.570 mm

    # Primary Corridor: Notch tip (10.0, 70.0) to Central Hole left flank (26.5, 51.0)
    primary_audit = audit_trajectory(metrics, NOTCH_X, NOTCH_Y, HOLE_LEFT_X, HOLE_LEFT_Y, w_half, n_stations=10)

    # Secondary Corridor: Central Hole right flank (46.5, 51.0) to Right Edge (65.0, 51.0)
    secondary_audit = audit_trajectory(metrics, HOLE_RIGHT_X, HOLE_RIGHT_Y, RIGHT_EDGE_X, RIGHT_EDGE_Y, w_half, n_stations=10)

    # Hole boundary annular resolution (R in [10.0, 10.5] mm)
    hole_elems = [m for m in metrics.values() if 10.0 <= math.hypot(m['cx'] - HOLE_C_X, m['cy'] - HOLE_C_Y) <= 10.5]
    hole_hs = [m['h_eq'] for m in hole_elems] if hole_elems else [0.0]
    hole_mean_h = sum(hole_hs) / float(len(hole_hs)) if hole_elems else 0.0

    report = {
        'mesh_file': os.path.basename(inp_path),
        'total_physical_elements': tot_elems,
        'quad_elements': quad_count,
        'tri_elements': tri_count,
        'quad_percentage': 100.0 * quad_count / float(tot_elems),
        'min_jacobian_det': min_det_j,
        'zero_negative_jacobians': (min_det_j > 0),
        'max_aspect_ratio': max_ar,
        'hole_boundary_mean_h_mm': hole_mean_h,
        'hole_boundary_le_l0_half': (hole_mean_h <= L0_HALF_MM),
        'primary_corridor': primary_audit,
        'secondary_corridor': secondary_audit
    }

    if out_json_path:
        with open(out_json_path, 'w') as f:
            json.dump(report, f, indent=2)
        print("Audit report saved to: %s" % out_json_path)

    return report

if __name__ == '__main__':
    inp = sys.argv[1] if len(sys.argv) > 1 else "PK_F1741_CASE_3_ADAPT_PHYS.inp"
    out = sys.argv[2] if len(sys.argv) > 2 else "f1741_case3_spatial_audit.json"
    audit_case3_mesh(inp, out)
