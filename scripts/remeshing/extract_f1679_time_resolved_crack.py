# -*- coding: utf-8 -*-
"""
scripts/remeshing/extract_f1679_time_resolved_crack.py
=====================================================
Extracts time-resolved phase-field damage fields, crack connectivity,
primary crack trajectory, hole interaction/arrest, secondary crack initiation,
and damage bound overshoot at 7 key simulation states from M1_HOLE_F1664_METHOD_A_PROD.odb.

Targeted Key States:
  State 0: Step-1, frame 57  (u = 0.00500 mm, elastic pre-loading)
  State 1: Step-2, frame 50  (u = 0.00570 mm, peak reaction force P_max = 0.5934 kN)
  State 2: Step-2, frame 180 (u = 0.00752 mm, primary crack entering hole)
  State 3: Step-2, frame 198 (u = 0.00776 mm, secondary crack initiation onset)
  State 4: Step-2, frame 220 (u = 0.00776 mm, snap-through load drop P = 0.045 kN)
  State 5: Step-2, frame 248 (u = 0.00780 mm, right-ligament severance P = 0.0009 kN)
  State 6: Step-2, frame 557 (u = 0.01200 mm, final displacement endpoint)
"""
from __future__ import print_function
import os
import sys
import json
import csv
import math
import time

try:
    import odbAccess
    from abaqusConstants import *
    ABAQUS_AVAILABLE = True
except ImportError:
    ABAQUS_AVAILABLE = False


def build_element_topology(inp_path, n_phys):
    """
    Parses node coordinates and element connectivity from INP to build:
    1. element centroids: dict {eid: (cx, cy)}
    2. element nodes: dict {eid: [n1, n2, n3, ...]}
    3. element adjacency: dict {eid: set(neighbor_eids)}
    """
    nodes = {}
    elem_nodes = {}
    elem_centroids = {}
    node_to_elems = {}

    print("[%s] Parsing mesh topology from %s..." % (time.strftime('%H:%M:%S'), inp_path))
    with open(inp_path, 'r') as f:
        section = None
        for line in f:
            line = line.strip()
            if not line or line.startswith('**'):
                continue
            if line.startswith('*'):
                upper = line.upper()
                if upper.startswith('*NODE'):
                    section = 'NODE'
                elif upper.startswith('*ELEMENT') and ('TYPE=U' in upper or 'TYPE=CPE' in upper):
                    section = 'ELEMENT'
                else:
                    section = None
                continue
            
            if section == 'NODE':
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        nodes[nid] = (float(parts[1]), float(parts[2]))
                    except ValueError:
                        pass
            elif section == 'ELEMENT':
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        if 1 <= eid <= n_phys:
                            conn = [int(p) for p in parts[1:]]
                            elem_nodes[eid] = conn
                            pts = [nodes[n] for n in conn if n in nodes]
                            if pts:
                                cx = sum(p[0] for p in pts) / float(len(pts))
                                cy = sum(p[1] for p in pts) / float(len(pts))
                                elem_centroids[eid] = (cx, cy)
                            for n in conn:
                                if n not in node_to_elems:
                                    node_to_elems[n] = []
                                node_to_elems[n].append(eid)
                    except ValueError:
                        pass

    # Build adjacency: two elements are adjacent if they share at least 2 nodes (share an edge)
    elem_adj = {}
    for eid, conn in elem_nodes.items():
        candidates = {}
        for n in conn:
            for neighbor in node_to_elems.get(n, []):
                if neighbor != eid:
                    candidates[neighbor] = candidates.get(neighbor, 0) + 1
        # Share an edge (>= 2 nodes) or corner (>= 1 node)
        # In 2D FEM, sharing >= 2 nodes ensures continuous line connectivity
        neighbors = set(nbr for nbr, shared_count in candidates.items() if shared_count >= 2)
        elem_adj[eid] = neighbors

    print("[%s] Topology built: %d physical elements, %d nodes." % (
        time.strftime('%H:%M:%S'), len(elem_centroids), len(nodes)
    ))
    return elem_centroids, elem_nodes, elem_adj


def cluster_damaged_elements(damaged_eids, elem_adj):
    """
    Finds connected components of damaged elements based on edge adjacency.
    Returns list of clusters (each cluster is a set of eids).
    """
    damaged_set = set(damaged_eids)
    visited = set()
    clusters = []

    for eid in damaged_eids:
        if eid in visited:
            continue
        cluster = []
        queue = [eid]
        visited.add(eid)
        while queue:
            curr = queue.pop(0)
            cluster.append(curr)
            for nbr in elem_adj.get(curr, set()):
                if nbr in damaged_set and nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)
        clusters.append(cluster)

    # Sort clusters by size descending
    clusters.sort(key=lambda c: len(c), reverse=True)
    return clusters


def run_time_resolved_extraction(odb_path, inp_path, n_phys, out_summary_path, out_csv_path):
    if not os.path.exists(odb_path):
        raise RuntimeError("ODB not found: %s" % odb_path)

    t0 = time.time()
    elem_centroids, elem_nodes, elem_adj = build_element_topology(inp_path, n_phys)

    print("[%s] Opening ODB: %s..." % (time.strftime('%H:%M:%S'), odb_path))
    odb = odbAccess.openOdb(odb_path, readOnly=True)
    steps = odb.steps
    umat_offset = 2 * n_phys

    # Key state targets
    targets = [
        {"state_id": 0, "name": "step1_final", "step": "Step-1", "frame_idx": 57, "desc": "Step 1 endpoint (u = 0.0050 mm)"},
        {"state_id": 1, "name": "step2_peak", "step": "Step-2", "frame_idx": 50, "desc": "Step 2 peak force (u = 0.00570 mm, P_max = 0.5934 kN)"},
        {"state_id": 2, "name": "step2_inc180", "step": "Step-2", "frame_idx": 180, "desc": "Step 2 increment 180 (u = 0.00752 mm, primary crack near hole)"},
        {"state_id": 3, "name": "step2_inc198", "step": "Step-2", "frame_idx": 198, "desc": "Step 2 increment 198 (u = 0.00776 mm, secondary crack initiation onset)"},
        {"state_id": 4, "name": "step2_inc220", "step": "Step-2", "frame_idx": 220, "desc": "Step 2 increment 220 (u = 0.00776 mm, secondary snap-through)"},
        {"state_id": 5, "name": "step2_inc248", "step": "Step-2", "frame_idx": 248, "desc": "Step 2 increment 248 (u = 0.00780 mm, right-ligament severance)"},
        {"state_id": 6, "name": "step2_final", "step": "Step-2", "frame_idx": 557, "desc": "Step 2 final endpoint (u = 0.01200 mm)"}
    ]

    hole_center = (0.65, 0.65)
    hole_radius = 0.10
    notch_tip = (0.50, 0.50)

    all_state_summaries = []
    csv_rows = []

    for tgt in targets:
        sname = tgt["step"]
        fidx = tgt["frame_idx"]
        st = steps[sname] if sname in steps else None
        if st is None or fidx >= len(st.frames):
            print("Warning: Target %s (%s, frame %d) not found in ODB!" % (tgt["name"], sname, fidx))
            continue

        frame = st.frames[fidx]
        frame_time = float(frame.frameValue)
        print("[%s] Processing State %d: %s (%s, frame %d)..." % (
            time.strftime('%H:%M:%S'), tgt["state_id"], tgt["name"], sname, fidx
        ))

        # Extract U and RF at Reference Node 999999
        u2_top = 0.0
        rf2_top = 0.0
        if 'U' in frame.fieldOutputs:
            for v in frame.fieldOutputs['U'].values:
                if v.nodeLabel == 999999:
                    u2_top = float(v.data[1])
                    break
        if 'RF' in frame.fieldOutputs:
            for v in frame.fieldOutputs['RF'].values:
                if v.nodeLabel == 999999:
                    rf2_top = float(v.data[1])
                    break

        # Extract Damage field SDV1
        dmg_field = 'SDV1' if 'SDV1' in frame.fieldOutputs else ('SDV14' if 'SDV14' in frame.fieldOutputs else None)
        if dmg_field is None:
            raise RuntimeError("Damage field SDV1 not found in frame!")

        d_map = {}
        for val in frame.fieldOutputs[dmg_field].values:
            eid = val.elementLabel
            if eid > umat_offset and eid <= umat_offset + n_phys:
                phys_id = eid - umat_offset
                d_val = float(val.dataDouble if hasattr(val, 'dataDouble') else val.data)
                d_map[phys_id] = d_val

        # Statistics and Bounds
        d_vals = list(d_map.values())
        d_min = min(d_vals) if d_vals else 0.0
        d_max = max(d_vals) if d_vals else 0.0

        # Overshoot quantification
        overshoot_eids = [eid for eid, d in d_map.items() if d > 1.0]
        undershoot_eids = [eid for eid, d in d_map.items() if d < 0.0]
        max_overshoot = (d_max - 1.0) if d_max > 1.0 else 0.0

        count_ge_02 = sum(1 for d in d_vals if d >= 0.20)
        count_ge_05 = sum(1 for d in d_vals if d >= 0.50)
        count_ge_08 = sum(1 for d in d_vals if d >= 0.80)
        count_ge_095 = sum(1 for d in d_vals if d >= 0.95)

        # Connected Component Analysis for FPZ Core (d >= 0.50)
        core_eids = [eid for eid, d in d_map.items() if d >= 0.50]
        clusters = cluster_damaged_elements(core_eids, elem_adj)

        # Classify clusters:
        # Cluster 1: Primary crack emanating from notch tip (starts near x=0.50, y=0.50)
        # Cluster 2: Secondary crack on right ligament (starts near hole boundary x >= 0.70, propagates to x=1.0)
        primary_cluster = None
        secondary_cluster = None
        other_clusters = []

        for c in clusters:
            xs = [elem_centroids[eid][0] for eid in c if eid in elem_centroids]
            ys = [elem_centroids[eid][1] for eid in c if eid in elem_centroids]
            min_x = min(xs)
            max_x = max(xs)
            avg_y = sum(ys) / float(len(ys))

            # Primary crack starts near notch tip (min_x <= 0.53, y ~ 0.50)
            if min_x <= 0.53 and primary_cluster is None:
                primary_cluster = {
                    "num_elements": len(c),
                    "min_x": min_x,
                    "max_x": max_x,
                    "avg_y": avg_y,
                    "eids": c
                }
            # Secondary crack initiates near hole right flank (min_x >= 0.70, max_x > min_x)
            elif min_x >= 0.70 and secondary_cluster is None:
                secondary_cluster = {
                    "num_elements": len(c),
                    "min_x": min_x,
                    "max_x": max_x,
                    "avg_y": avg_y,
                    "eids": c
                }
            else:
                other_clusters.append({
                    "num_elements": len(c),
                    "min_x": min_x,
                    "max_x": max_x,
                    "avg_y": avg_y
                })

        # Calculate distances to hole and right boundary for primary and secondary cracks
        primary_dist_to_hole = None
        primary_reached_hole = False
        if primary_cluster is not None:
            # Distance from each element in primary crack to hole perimeter
            dists = []
            for eid in primary_cluster["eids"]:
                cx, cy = elem_centroids[eid]
                dist_to_center = math.sqrt((cx - hole_center[0])**2 + (cy - hole_center[1])**2)
                dist_to_perim = dist_to_center - hole_radius
                dists.append(dist_to_perim)
            min_dist = min(dists)
            primary_dist_to_hole = min_dist
            primary_reached_hole = (min_dist <= 0.005) # Within 5 microns of hole perimeter

        secondary_reached_boundary = False
        secondary_dist_to_boundary = None
        if secondary_cluster is not None:
            secondary_dist_to_boundary = 1.0 - secondary_cluster["max_x"]
            secondary_reached_boundary = (secondary_cluster["max_x"] >= 0.995)

        state_summary = {
            "state_id": tgt["state_id"],
            "name": tgt["name"],
            "description": tgt["desc"],
            "step": sname,
            "frame_idx": fidx,
            "step_time": frame_time,
            "u2_top_mm": u2_top,
            "rf2_top_kN": rf2_top,
            "damage_bounds": {
                "d_min": d_min,
                "d_max": d_max,
                "num_undershoot_elements": len(undershoot_eids),
                "num_overshoot_elements": len(overshoot_eids),
                "max_overshoot": max_overshoot,
                "overshoot_pct": (max_overshoot / 1.0) * 100.0 if max_overshoot > 0 else 0.0
            },
            "damage_counts": {
                "d_ge_0.20": count_ge_02,
                "d_ge_0.50": count_ge_05,
                "d_ge_0.80": count_ge_08,
                "d_ge_0.95": count_ge_095
            },
            "crack_topology": {
                "total_clusters_d_ge_0.50": len(clusters),
                "primary_crack": {
                    "present": primary_cluster is not None,
                    "num_elements": primary_cluster["num_elements"] if primary_cluster else 0,
                    "tip_x": primary_cluster["max_x"] if primary_cluster else None,
                    "avg_y": primary_cluster["avg_y"] if primary_cluster else None,
                    "dist_to_hole_perimeter_mm": primary_dist_to_hole,
                    "reached_hole": primary_reached_hole
                },
                "secondary_crack": {
                    "present": secondary_cluster is not None,
                    "num_elements": secondary_cluster["num_elements"] if secondary_cluster else 0,
                    "nucleation_x": secondary_cluster["min_x"] if secondary_cluster else None,
                    "tip_x": secondary_cluster["max_x"] if secondary_cluster else None,
                    "avg_y": secondary_cluster["avg_y"] if secondary_cluster else None,
                    "dist_to_right_boundary_mm": secondary_dist_to_boundary,
                    "reached_boundary": secondary_reached_boundary
                },
                "other_isolated_clusters": len(other_clusters)
            }
        }
        all_state_summaries.append(state_summary)

        # Prepare CSV rows for all elements with damage >= 0.10 in this state
        primary_eids_set = set(primary_cluster["eids"]) if primary_cluster else set()
        secondary_eids_set = set(secondary_cluster["eids"]) if secondary_cluster else set()

        for eid, d in d_map.items():
            if d >= 0.10 and eid in elem_centroids:
                cx, cy = elem_centroids[eid]
                cid = "primary" if eid in primary_eids_set else ("secondary" if eid in secondary_eids_set else "diffuse")
                csv_rows.append([
                    tgt["name"], tgt["state_id"], sname, fidx, "%.6e" % u2_top, "%.6e" % rf2_top,
                    eid, "%.6f" % cx, "%.6f" % cy, "%.6f" % d, cid
                ])

    # Write summary JSON
    with open(out_summary_path, 'w') as f:
        json.dump(all_state_summaries, f, indent=4)
    print("[%s] Wrote time-resolved summary to %s" % (time.strftime('%H:%M:%S'), out_summary_path))

    # Write CSV
    with open(out_csv_path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow([
            "state_name", "state_id", "step", "frame_idx", "u2_mm", "rf2_kN",
            "phys_elem_id", "x_mm", "y_mm", "damage", "cluster_type"
        ])
        for r in csv_rows:
            writer.writerow(r)
    print("[%s] Wrote time-resolved damaged elements to %s (%d records)" % (
        time.strftime('%H:%M:%S'), out_csv_path, len(csv_rows)
    ))

    print("[%s] Total extraction time: %.2f seconds." % (time.strftime('%H:%M:%S'), time.time() - t0))


if __name__ == '__main__':
    odb_arg = "M1_HOLE_F1664_METHOD_A_PROD.odb"
    inp_arg = "PK_HOLE_F1664_METHOD_A_PROD.inp"
    n_phys_arg = 20213
    out_summary_arg = "f1679_time_resolved_crack_summary.json"
    out_csv_arg = "f1679_time_resolved_crack_states.csv"

    for i, arg in enumerate(sys.argv):
        if arg == '--odb' and i + 1 < len(sys.argv):
            odb_arg = sys.argv[i + 1]
        elif arg == '--inp' and i + 1 < len(sys.argv):
            inp_arg = sys.argv[i + 1]
        elif arg == '--n-phys' and i + 1 < len(sys.argv):
            n_phys_arg = int(sys.argv[i + 1])
        elif arg == '--out-summary' and i + 1 < len(sys.argv):
            out_summary_arg = sys.argv[i + 1]
        elif arg == '--out-csv' and i + 1 < len(sys.argv):
            out_csv_arg = sys.argv[i + 1]

    run_time_resolved_extraction(odb_arg, inp_arg, n_phys_arg, out_summary_arg, out_csv_arg)
