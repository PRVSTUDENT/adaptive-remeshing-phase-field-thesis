# -*- coding: utf-8 -*-
"""Correlate physical mesh geometry with pilot damage and history fields.

Zero external dependencies: uses Python standard library.
"""
from __future__ import print_function
import os
import sys
import json
import csv
from collections import defaultdict

def run_correlation(inp_path, damage_csv_path, out_json_path, out_csv_path):
    print("Reading physical mesh from: %s" % inp_path)
    nodes = {}
    elements = {}

    in_nodes = False
    in_elements = False

    with open(inp_path, 'r') as f:
        for line in f:
            line_str = line.strip()
            if line_str.startswith('*'):
                in_nodes = False
                in_elements = False
                upper = line_str.upper()
                if upper.startswith('*NODE'):
                    in_nodes = True
                elif upper.startswith('*ELEMENT'):
                    in_elements = True
                continue

            if in_nodes:
                parts = line_str.split(',')
                if len(parts) >= 3:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    nodes[nid] = (x, y)
            elif in_elements:
                parts = line_str.split(',')
                if len(parts) >= 4:
                    eid = int(parts[0])
                    if eid > 46747:
                        # Physical elements are 1..46747; stop collecting companion layers
                        continue
                    conn = [int(p) for p in parts[1:]]
                    elements[eid] = conn

    print("Loaded %d nodes and %d elements." % (len(nodes), len(elements)))

    # Compute element centroids
    centroids = {}
    for eid, conn in elements.items():
        coords = [nodes[nid] for nid in conn if nid in nodes]
        if coords:
            cx = sum(c[0] for c in coords) / float(len(coords))
            cy = sum(c[1] for c in coords) / float(len(coords))
            centroids[eid] = (cx, cy)

    # Read damage CSV
    print("Reading localized damage from: %s" % damage_csv_path)
    elem_damage = defaultdict(float)
    elem_history = defaultdict(float)

    with open(damage_csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            eid = int(row['phys_elem_id'])
            d = float(row['damage'])
            h = float(row['history'])
            if d > elem_damage[eid]:
                elem_damage[eid] = d
            if h > elem_history[eid]:
                elem_history[eid] = h

    print("Found damage records for %d physical elements." % len(elem_damage))

    # Analyze spatial extent of damage zones
    # Slit tip is at (0.50, 0.50); Hole is at (0.65, 0.65), R=0.10
    zones = {
        'all': {'count': 0, 'x_min': 1.0, 'x_max': 0.0, 'y_min': 1.0, 'y_max': 0.0},
        'd_ge_0.01': {'count': 0, 'x_min': 1.0, 'x_max': 0.0, 'y_min': 1.0, 'y_max': 0.0},
        'd_ge_0.05': {'count': 0, 'x_min': 1.0, 'x_max': 0.0, 'y_min': 1.0, 'y_max': 0.0},
        'd_ge_0.10': {'count': 0, 'x_min': 1.0, 'x_max': 0.0, 'y_min': 1.0, 'y_max': 0.0},
        'd_ge_0.20': {'count': 0, 'x_min': 1.0, 'x_max': 0.0, 'y_min': 1.0, 'y_max': 0.0},
        'd_ge_0.30': {'count': 0, 'x_min': 1.0, 'x_max': 0.0, 'y_min': 1.0, 'y_max': 0.0},
        'd_ge_0.40': {'count': 0, 'x_min': 1.0, 'x_max': 0.0, 'y_min': 1.0, 'y_max': 0.0}
    }

    high_damage_elements = []

    for eid, d in elem_damage.items():
        if eid not in centroids:
            continue
        cx, cy = centroids[eid]
        h = elem_history[eid]

        if d >= 0.05:
            high_damage_elements.append({
                'element_id': eid,
                'x': round(cx, 6),
                'y': round(cy, 6),
                'damage': round(d, 6),
                'history': round(h, 6)
            })

        for threshold_key, threshold_val in [
            ('d_ge_0.01', 0.01),
            ('d_ge_0.05', 0.05),
            ('d_ge_0.10', 0.10),
            ('d_ge_0.20', 0.20),
            ('d_ge_0.30', 0.30),
            ('d_ge_0.40', 0.40)
        ]:
            if d >= threshold_val:
                z = zones[threshold_key]
                z['count'] += 1
                if cx < z['x_min']: z['x_min'] = cx
                if cx > z['x_max']: z['x_max'] = cx
                if cy < z['y_min']: z['y_min'] = cy
                if cy > z['y_max']: z['y_max'] = cy

    # Sort high damage elements descending by damage
    high_damage_elements.sort(key=lambda item: item['damage'], reverse=True)

    summary = {
        'total_mesh_elements': len(elements),
        'total_mesh_nodes': len(nodes),
        'elements_with_damage': len(elem_damage),
        'max_damage_element': high_damage_elements[0] if high_damage_elements else None,
        'damage_zones': zones,
        'slit_tip_reference': {'x': 0.50, 'y': 0.50},
        'hole_reference': {'center_x': 0.65, 'center_y': 0.65, 'radius': 0.10}
    }

    with open(out_json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print("Spatial damage correlation written to: %s" % out_json_path)

    # Write top damage elements CSV
    with open(out_csv_path, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['element_id', 'x', 'y', 'damage', 'history'])
        writer.writeheader()
        for row in high_damage_elements[:2000]:  # Top 2000 localized elements
            writer.writerow(row)
    print("Top localized damage elements written to: %s" % out_csv_path)

if __name__ == '__main__':
    inp = sys.argv[1] if len(sys.argv) > 1 else 'PK_HOLE_METHOD_A_PROD_PHYS.inp'
    dmg_csv = sys.argv[2] if len(sys.argv) > 2 else 'f1642_pilot_localized_damage.csv'
    out_j = sys.argv[3] if len(sys.argv) > 3 else 'f1642_pilot_damage_distribution.json'
    out_c = sys.argv[4] if len(sys.argv) > 4 else 'f1642_pilot_top_damage_elements.csv'
    run_correlation(inp, dmg_csv, out_j, out_c)
