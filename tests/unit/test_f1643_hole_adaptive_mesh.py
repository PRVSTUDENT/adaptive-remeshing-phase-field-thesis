# -*- coding: utf-8 -*-
"""
tests/unit/test_f1643_hole_adaptive_mesh.py
===========================================
Task: F1643-METHOD-A-HOLE-ADAPTIVE-REFINEMENT-CRITERIA
Author: Gemini Antigravity (Autonomous Materials Science Agent)
Date: 06-11-2026

Unit tests for the indicator-driven adaptive mesh and production deck:
1. Physical and production deck file existence and non-emptiness.
2. Element and node count validation (within capacity N_CAPACITY=150000).
3. Local FPZ resolution: median h <= 1.5 um and >= 80% edges <= 1.5 um in
   notch tip, ligament, and hole boundary zones.
4. Positive element areas (zero inverted or zero-area elements).
5. Geometric precision: notch tip (0.50, 0.50), hole center (0.65, 0.65), R=0.10.
6. 3-layer UEL deck structure, card wrapping (<= 16 entries), and constant parity.
"""

import math
import os
import pytest

PHYS_DECK = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_ADAPT_PHYS.inp"
PROD_DECK = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_ADAPT.inp"


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
    assert os.path.getsize(PHYS_DECK) > 100000, "Physical mesh deck is too small: %d bytes" % os.path.getsize(PHYS_DECK)
    assert os.path.getsize(PROD_DECK) > 500000, "Production UEL deck is too small: %d bytes" % os.path.getsize(PROD_DECK)


def test_element_and_node_counts_within_capacity():
    nodes, elems = load_mesh(PHYS_DECK)
    n_elems = len(elems)
    n_nodes = len(nodes)

    assert 40000 <= n_elems <= 70000, "Unexpected element count: %d" % n_elems
    assert 40000 <= n_nodes <= 70000, "Unexpected node count: %d" % n_nodes
    # Strict capacity bound from f42_mixed_uel.for
    assert n_elems <= 150000, "Element count %d exceeds N_CAPACITY=150000" % n_elems

    # Verify quad vs tri breakdown
    quads = sum(1 for conn in elems.values() if len(conn) == 4)
    tris = sum(1 for conn in elems.values() if len(conn) == 3)
    assert quads + tris == n_elems, "Elements contain unsupported topologies"
    assert quads > 0.90 * n_elems, "Mesh is not quad-dominated: %d quads out of %d" % (quads, n_elems)


def test_local_fpz_resolution_criteria():
    nodes, elems = load_mesh(PHYS_DECK)
    l0 = 0.0075
    target_h = l0 / 5.0  # 0.0015 mm = 1.5 um

    zones = {"notch_tip": [], "ligament": [], "hole_boundary": []}
    hx, hy, hr = 0.65, 0.65, 0.10

    for eid, conn in elems.items():
        pts = [nodes[n] for n in conn]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)

        dist_tip = math.sqrt((cx - 0.50)**2 + (cy - 0.50)**2)
        dist_hole_center = math.sqrt((cx - hx)**2 + (cy - hy)**2)
        dist_hole_surface = abs(dist_hole_center - hr)

        n_pts = len(pts)
        edges = [math.sqrt((pts[i][0] - pts[(i+1)%n_pts][0])**2 + (pts[i][1] - pts[(i+1)%n_pts][1])**2) for i in range(n_pts)]

        if dist_tip <= 0.025:
            zones["notch_tip"].extend(edges)
        elif dist_hole_surface <= 0.015:
            zones["hole_boundary"].extend(edges)
        elif 0.50 <= cx <= hx and 0.48 <= cy <= (hy + 0.05) and dist_hole_center > hr:
            zones["ligament"].extend(edges)

    for zname in ["notch_tip", "ligament", "hole_boundary"]:
        edges = sorted(zones[zname])
        n = len(edges)
        assert n > 0, "No edges found in zone: %s" % zname
        median_h = edges[int(n * 0.50)]
        frac_pass = sum(1 for e in edges if e <= target_h) / float(n) * 100.0

        print("Zone %s: Median h = %.4f um (h/l0 = %.3f), Pass fraction = %.1f%%" % (
            zname, median_h * 1e3, median_h / l0, frac_pass
        ))

        # Scientific criteria: median h <= 1.5 um (l0/5) and pass fraction >= 80%
        assert median_h <= target_h, "Zone %s median edge %.4f um exceeds target %.4f um" % (zname, median_h * 1e3, target_h * 1e3)
        assert frac_pass >= 80.0, "Zone %s pass fraction %.1f%% below 80%% requirement" % (zname, frac_pass)


def test_positive_element_areas():
    nodes, elems = load_mesh(PHYS_DECK)
    neg_area_count = 0
    min_area = 1e9

    for eid, conn in elems.items():
        pts = [nodes[n] for n in conn]
        if len(pts) == 4:
            x1, y1 = pts[0]; x2, y2 = pts[1]; x3, y3 = pts[2]; x4, y4 = pts[3]
            area = 0.5 * ((x1*y2 - y1*x2) + (x2*y3 - y2*x3) + (x3*y4 - y3*x4) + (x4*y1 - y4*x1))
        elif len(pts) == 3:
            x1, y1 = pts[0]; x2, y2 = pts[1]; x3, y3 = pts[2]
            area = 0.5 * (x1*(y2 - y3) + x2*(y3 - y1) + x3*(y1 - y2))
        else:
            area = 0.0

        if area <= 0.0:
            neg_area_count += 1
        min_area = min(min_area, area)

    assert neg_area_count == 0, "Found %d inverted or zero-area elements" % neg_area_count
    assert min_area > 0.0, "Minimum area is non-positive: %.6e" % min_area


def test_geometry_and_boundary_sets():
    nodes, elems = load_mesh(PHYS_DECK)
    xs = [pt[0] for pt in nodes.values()]
    ys = [pt[1] for pt in nodes.values()]

    # Plate boundaries
    assert min(xs) >= -1e-6 and max(xs) <= 1.0 + 1e-6
    assert min(ys) >= -1e-6 and max(ys) <= 1.0 + 1e-6

    # Hole boundary
    hx, hy, hr = 0.65, 0.65, 0.10
    hole_nodes = [pt for pt in nodes.values() if abs(math.sqrt((pt[0]-hx)**2 + (pt[1]-hy)**2) - hr) < 1e-4]
    assert len(hole_nodes) >= 50, "Insufficient nodes along hole perimeter: %d" % len(hole_nodes)

    # Notch tip
    notch_nodes = [pt for pt in nodes.values() if abs(pt[0] - 0.50) < 1e-4 and abs(pt[1] - 0.50) < 0.002]
    assert len(notch_nodes) >= 2, "Missing notch tip boundary nodes"


def test_production_deck_structure_and_constants():
    nodes, elems = load_mesh(PHYS_DECK)
    n_phys = len(elems)

    with open(PROD_DECK, "r") as f:
        content = f.read()

    # Check 3 layers presence
    assert "*USER ELEMENT, TYPE=U1" in content
    assert "*USER ELEMENT, TYPE=U2" in content
    assert "*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD" in content
    assert "*ELEMENT, TYPE=U2, ELSET=DISP_QUAD" in content
    assert "*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS" in content

    # Check companion offset parameter matching n_phys
    expected_uel_prop = "0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.0" % n_phys
    expected_umat_const = "210.0, 0.3, %d.0" % n_phys
    assert expected_uel_prop in content, "Missing or incorrect UEL PROPERTY line: %s" % expected_uel_prop
    assert expected_umat_const in content, "Missing or incorrect USER MATERIAL line: %s" % expected_umat_const

    # Check boundary node sets
    assert "*NSET, NSET=N_BOTTOM" in content
    assert "*NSET, NSET=N_PIN" in content
    assert "*NSET, NSET=N_TOP" in content
    assert "*NSET, NSET=N_RP" in content

    # Check card wrapping: no NSET line should have more than 16 comma-separated items
    with open(PROD_DECK, "r") as f:
        in_nset = False
        for l in f:
            l = l.strip()
            if l.startswith("*NSET"):
                in_nset = True
                continue
            if l.startswith("*"):
                in_nset = False
                continue
            if in_nset:
                items = [p.strip() for p in l.split(",") if p.strip()]
                assert len(items) <= 16, "NSET card line exceeds 16 entries: %d entries" % len(items)

    # Check equation ties
    assert "*EQUATION" in content
    assert "999999, 2, -1.0" in content

    # Check Step 1
    assert "*STEP, NAME=Step-1" in content
    assert "N_RP, 2, 2, 0.0050" in content
    assert "*RESTART, WRITE, FREQUENCY=1" in content
