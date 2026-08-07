#!/usr/bin/env python3
"""
F41 Crack Topology Extractor

Parses original 2D cracked mesh decks, identifies coincident crack-face node pairs
BEFORE any merging, extracts the crack trace and endpoints, and generates the
F41_TOPOLOGY_MAP structure.
"""

import json
import math
import os
import sys

TOLERANCE = 1e-4

def parse_nodes_and_elements(deck_path):
    if not os.path.exists(deck_path):
        raise IOError("Source deck path does not exist: {0}".format(deck_path))

    nodes = {}
    elements = {}
    in_node_section = False
    in_element_section = False

    with open(deck_path, 'r') as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith('*'):
                line_upper = stripped.upper()
                if line_upper.startswith('*NODE'):
                    in_node_section = True
                    in_element_section = False
                    continue
                elif line_upper.startswith('*ELEMENT'):
                    in_node_section = False
                    in_element_section = True
                    continue
                elif line_upper.startswith('**'):
                    continue
                else:
                    in_node_section = False
                    in_element_section = False
                    continue

            if in_node_section:
                parts = [p.strip() for p in stripped.split(',')]
                if len(parts) >= 3:
                    try:
                        node_id = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[node_id] = (x, y)
                    except ValueError:
                        pass

            elif in_element_section:
                parts = [p.strip() for p in stripped.split(',')]
                if len(parts) >= 2:
                    try:
                        elem_id = int(parts[0])
                        node_ids = [int(p) for p in parts[1:] if p]
                        elements[elem_id] = node_ids
                    except ValueError:
                        pass

    if not nodes:
        raise ValueError("No nodes parsed from deck: {0}".format(deck_path))

    # Compute bounding box
    xs = [coord[0] for coord in nodes.values()]
    ys = [coord[1] for coord in nodes.values()]
    bounding_box = {
        "x_min": min(xs),
        "x_max": max(xs),
        "y_min": min(ys),
        "y_max": max(ys)
    }

    return nodes, elements, bounding_box


def identify_crack_topology(nodes, elements, tol=TOLERANCE):
    # Candidate nodes along x in [-0.5 - tol, 0.0 + tol], |y| <= tol
    candidate_nodes = {}
    for node_id, (x, y) in nodes.items():
        if -0.5 - tol <= x <= 0.0 + tol and abs(y) <= tol:
            candidate_nodes[node_id] = (x, y)

    # Separate into lower (y < 0) and upper (y > 0) or exact y=0
    # In Mode-II deck, lower nodes have small negative y or duplicate coordinates
    # Group by coordinate x
    coord_groups = {}
    for n_id, (x, y) in candidate_nodes.items():
        x_key = round(x, 5)
        if x_key not in coord_groups:
            coord_groups[x_key] = []
        coord_groups[x_key].append((n_id, x, y))

    coincident_pairs = []
    singletons = []

    for x_key in sorted(coord_groups.keys()):
        group = coord_groups[x_key]
        if len(group) == 2:
            n1, n2 = group[0], group[1]
            # Order lower, upper by node ID or y coordinate
            if n1[2] < n2[2] or (n1[2] == n2[2] and n1[0] < n2[0]):
                lower_id, upper_id = n1[0], n2[0]
            else:
                lower_id, upper_id = n2[0], n1[0]
            coincident_pairs.append({
                "lower_node_id": lower_id,
                "upper_node_id": upper_id,
                "x": (n1[1] + n2[1]) / 2.0,
                "y": (n1[2] + n2[2]) / 2.0
            })
        else:
            singletons.extend(group)

    # Order coincident pairs from x = -0.5 to x = 0.0
    coincident_pairs.sort(key=lambda p: p["x"])

    crack_start = [-0.5, 0.0]
    crack_tip = [0.0, 0.0]
    if coincident_pairs:
        crack_start = [coincident_pairs[0]["x"], coincident_pairs[0]["y"]]
        # Find if a tip node exists at x=0.0, y=0.0 among candidate nodes
        tip_candidates = [coord for n_id, coord in candidate_nodes.items() if abs(coord[0] - 0.0) <= tol and abs(coord[1] - 0.0) <= tol]
        if tip_candidates:
            crack_tip = [tip_candidates[0][0], tip_candidates[0][1]]
        else:
            crack_tip = [coincident_pairs[-1]["x"], coincident_pairs[-1]["y"]]

    dx = crack_tip[0] - crack_start[0]
    dy = crack_tip[1] - crack_start[1]
    crack_length = math.sqrt(dx * dx + dy * dy)


    # Find elements touching crack nodes
    crack_node_set = set()
    for p in coincident_pairs:
        crack_node_set.add(p["lower_node_id"])
        crack_node_set.add(p["upper_node_id"])

    crack_elements = []
    for elem_id, n_ids in elements.items():
        if any(n in crack_node_set for n in n_ids):
            crack_elements.append(elem_id)

    return {
        "source_node_count": len(nodes),
        "duplicate_pairs_before": len(coincident_pairs),
        "coincident_pairs": coincident_pairs,
        "crack_start": crack_start,
        "crack_tip": crack_tip,
        "crack_length": crack_length,
        "crack_elements_count": len(crack_elements),
        "tolerance_used": tol
    }


def generate_topology_map_dict(crack_info):
    pairs_map = []
    for p in crack_info["coincident_pairs"]:
        pairs_map.append({
            "original_pair_ids": [p["lower_node_id"], p["upper_node_id"]],
            "original_coordinates": [p["x"], p["y"]],
            "temporary_merged_node_identity": p["lower_node_id"],
            "reconstructed_crack_edge_id": "CRACK_EDGE_X_{0:.3f}".format(p["x"])
        })

    return {
        "protocol_version": 1,
        "tolerance": crack_info["tolerance_used"],
        "duplicate_pairs_count": crack_info["duplicate_pairs_before"],
        "crack_start": crack_info["crack_start"],
        "crack_tip": crack_info["crack_tip"],
        "crack_length": crack_info["crack_length"],
        "node_pairs_mapping": pairs_map
    }


if __name__ == "__main__":
    deck_p = sys.argv[1] if len(sys.argv) > 1 else "source_deck.inp"
    nodes, elements, bbox = parse_nodes_and_elements(deck_p)
    info = identify_crack_topology(nodes, elements)
    t_map = generate_topology_map_dict(info)
    print("Parsed node count: {0}".format(info["source_node_count"]))
    print("Detected crack pairs: {0}".format(info["duplicate_pairs_before"]))
    print("Crack start: {0}, crack tip: {1}, length: {2:.4f}".format(info["crack_start"], info["crack_tip"], info["crack_length"]))
    print("Bounding box: {0}".format(bbox))
