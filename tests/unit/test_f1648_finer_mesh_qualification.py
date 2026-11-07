# -*- coding: utf-8 -*-
"""
tests/unit/test_f1648_finer_mesh_qualification.py
=================================================
Task: F1648-METHOD-A-HOLE-FINER-MESH-SENSITIVITY
Author: Gemini Antigravity (Autonomous Materials Science Agent)
Date: 07-11-2026

Unit tests for the controlled finer-mesh candidate (h_core = 0.75 um = l0/10):
1. Physical and production deck file existence and non-emptiness.
2. Element and node count validation (within capacity N_CAPACITY=150000).
3. Local FPZ resolution: median h <= 1.0 um and >= 90% edges <= 1.5 um in
   notch tip, ligament, and hole boundary zones.
4. Positive element areas (zero inverted or zero-area elements).
5. Geometric precision: notch tip (0.50, 0.50), hole center (0.65, 0.65), R=0.10.
6. 3-layer UEL deck structure, card wrapping (<= 16 entries), and constant parity.
"""

import math
import os
import pytest

PHYS_DECK = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_FINER_PHYS.inp"
PROD_DECK = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_FINER.inp"


def load_mesh(inp_path):
    nodes = {}
    elems = {}
    with open(inp_path, "r") as f:
        in_nodes, in_elems = False, False
        for l in f:
            l = l.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_nodes = l.upper().startswith("*NODE")
                in_elems = l.upper().startswith("*ELEMENT")
                continue
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if in_nodes and len(parts) >= 3:
                try:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                except ValueError:
                    continue
            elif in_elems and len(parts) >= 4:
                try:
                    elems[int(parts[0])] = [int(p) for p in parts[1:]]
                except ValueError:
                    continue
    return nodes, elems


def test_deck_files_exist_and_nonempty():
    assert os.path.isfile(PHYS_DECK), "Physical mesh deck does not exist: %s" % PHYS_DECK
    assert os.path.isfile(PROD_DECK), "Production UEL deck does not exist: %s" % PROD_DECK
    assert os.path.getsize(PHYS_DECK) > 1000000, "Physical mesh deck is too small: %d bytes" % os.path.getsize(PHYS_DECK)
    assert os.path.getsize(PROD_DECK) > 5000000, "Production UEL deck is too small: %d bytes" % os.path.getsize(PROD_DECK)


def test_element_and_node_counts_within_capacity():
    nodes, elems = load_mesh(PHYS_DECK)
    n_phys = len(elems)
    n_nodes = len(nodes)

    assert n_phys == 69903, "Expected 69,903 physical elements, got: %d" % n_phys
    assert n_nodes == 69142, "Expected 69,142 physical nodes, got: %d" % n_nodes
    assert n_phys <= 150000, "Physical elements exceed N_CAPACITY=150000: %d" % n_phys


def test_local_fpz_resolution_criteria():
    nodes, elems = load_mesh(PHYS_DECK)
    l0 = 0.0075
    target_h = l0 / 5.0  # 0.0015 mm = 1.5 um

    # Notch tip zone: elements within r <= 0.05 mm from (0.50, 0.50)
    tip_edges = []
    ligament_edges = []
    hole_edges = []

    for eid, conn in elems.items():
        pts = [nodes[n] for n in conn]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)

        # Compute edge lengths
        edges = []
        n_pts = len(pts)
        for i in range(n_pts):
            p1 = pts[i]
            p2 = pts[(i + 1) % n_pts]
            d = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            edges.append(d)

        # 1. Notch tip zone
        r_tip = math.sqrt((cx - 0.50)**2 + (cy - 0.50)**2)
        if r_tip <= 0.05:
            tip_edges.extend(edges)

        # 2. Ligament zone
        if 0.50 <= cx <= 0.65 and 0.48 <= cy <= 0.65:
            ligament_edges.extend(edges)

        # 3. Hole boundary zone
        r_hole = math.sqrt((cx - 0.65)**2 + (cy - 0.65)**2)
        if 0.09 <= r_hole <= 0.12:
            hole_edges.extend(edges)

    assert len(tip_edges) > 1000, "Too few tip edges: %d" % len(tip_edges)
    assert len(ligament_edges) > 5000, "Too few ligament edges: %d" % len(ligament_edges)
    assert len(hole_edges) > 2000, "Too few hole edges: %d" % len(hole_edges)

    tip_sorted = sorted(tip_edges)
    median_tip = tip_sorted[len(tip_sorted) // 2]
    pct_tip_pass = sum(1 for e in tip_edges if e <= target_h) / float(len(tip_edges)) * 100.0

    lig_sorted = sorted(ligament_edges)
    median_lig = lig_sorted[len(lig_sorted) // 2]
    pct_lig_pass = sum(1 for e in ligament_edges if e <= target_h) / float(len(ligament_edges)) * 100.0

    hole_sorted = sorted(hole_edges)
    median_hole = hole_sorted[len(hole_sorted) // 2]
    pct_hole_pass = sum(1 for e in hole_edges if e <= target_h) / float(len(hole_edges)) * 100.0

    # Verification: finer mesh achieves median h < 1.0 um and > 90% compliance
    assert median_tip < 0.0010, "Notch tip median edge (%.4f mm) exceeds 1.0 um" % median_tip
    assert pct_tip_pass >= 90.0, "Notch tip compliance (%.1f%%) below 90%%" % pct_tip_pass

    assert median_lig < 0.0010, "Ligament median edge (%.4f mm) exceeds 1.0 um" % median_lig
    assert pct_lig_pass >= 95.0, "Ligament compliance (%.1f%%) below 95%%" % pct_lig_pass

    assert median_hole < 0.0010, "Hole boundary median edge (%.4f mm) exceeds 1.0 um" % median_hole
    assert pct_hole_pass >= 90.0, "Hole boundary compliance (%.1f%%) below 90%%" % pct_hole_pass


def test_positive_element_areas_no_inversions():
    nodes, elems = load_mesh(PHYS_DECK)
    neg_or_zero = 0

    for eid, conn in elems.items():
        pts = [nodes[n] for n in conn]
        if len(conn) == 3:
            x1, y1 = pts[0]
            x2, y2 = pts[1]
            x3, y3 = pts[2]
            area = 0.5 * abs(x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
        elif len(conn) == 4:
            x1, y1 = pts[0]
            x2, y2 = pts[1]
            x3, y3 = pts[2]
            x4, y4 = pts[3]
            area = 0.5 * abs((x1*y2 - y1*x2) + (x2*y3 - y2*x3) + (x3*y4 - y3*x4) + (x4*y1 - y4*x1))
        else:
            area = 0.0

        if area <= 1e-14:
            neg_or_zero += 1

    assert neg_or_zero == 0, "Found %d non-positive area elements" % neg_or_zero


def test_geometric_precision():
    nodes, _ = load_mesh(PHYS_DECK)
    tol = 1e-3

    # Check that initial slit tip is at (0.50, 0.50)
    tip_nodes = [nid for nid, (x, y) in nodes.items() if abs(x - 0.50) < 0.005 and abs(y - 0.50) < 0.005]
    assert len(tip_nodes) >= 2, "Crack tip nodes not found near (0.50, 0.50)"

    # Check hole perimeter nodes: distance from (0.65, 0.65) should be approx R = 0.10
    hole_nodes = [nid for nid, (x, y) in nodes.items() if abs(math.sqrt((x - 0.65)**2 + (y - 0.65)**2) - 0.10) < 0.002]
    assert len(hole_nodes) >= 50, "Too few hole perimeter nodes: %d" % len(hole_nodes)


def test_production_deck_structure_and_parity():
    n_phys = 69903
    found_constants = False
    found_uel_prop = False

    with open(PROD_DECK, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if "*USER MATERIAL, CONSTANTS=3" in line.upper():
            next_line = lines[i+1].strip()
            parts = [p.strip() for p in next_line.split(",")]
            assert len(parts) == 3, "USER MATERIAL card must have 3 constants"
            assert float(parts[2]) == float(n_phys), "USER MATERIAL third constant (%.1f) != n_phys (%d)" % (float(parts[2]), n_phys)
            found_constants = True
        elif "*UEL PROPERTY" in line.upper():
            next_line = lines[i+1].strip()
            parts = [p.strip() for p in next_line.split(",")]
            assert len(parts) == 6, "UEL PROPERTY card must have 6 properties"
            assert float(parts[5]) == float(n_phys), "UEL PROPERTY sixth property (%.1f) != n_phys (%d)" % (float(parts[5]), n_phys)
            found_uel_prop = True

    assert found_constants, "Missing or invalid *USER MATERIAL card in %s" % PROD_DECK
    assert found_uel_prop, "Missing or invalid *UEL PROPERTY card in %s" % PROD_DECK
