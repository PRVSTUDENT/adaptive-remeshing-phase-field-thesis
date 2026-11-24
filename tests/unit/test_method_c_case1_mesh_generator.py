# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case1_mesh_generator.py
================================================
Tests for Case 1 adaptive corridor mesh generator:
- Narrow corridor geometry & sizing
- Seam edge duplication along notch
- Quality gates: quad fraction >= 85%, href <= l0/2, bounded element count < 35000
"""

import os
import math
import pytest
from collections import defaultdict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PHYS_MESH_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "291_method_c_case1", "PK_METHOD_C_CASE1_ADAPTIVE_PHYS.inp")


def test_case1_corridor_spec_geometry():
    import importlib.util
    spec_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "291_method_c_case1", "generate_case1_adaptive_corridor_mesh.py")
    spec_mod = importlib.util.spec_from_file_location("generate_case1_adaptive_corridor_mesh", spec_path)
    mod = importlib.util.module_from_spec(spec_mod)
    spec_mod.loader.exec_module(mod)
    compute_narrow_band_spec = mod.compute_narrow_band_spec
    L0 = mod.L0
    L0_HALF = mod.L0_HALF
    H_REF = mod.H_REF

    spec = compute_narrow_band_spec(tip_x=0.5000, tip_y=0.5000)
    assert spec["band_type"] == "NARROW_DAMAGE_FOLLOWING_BAND"
    assert spec["h_ref_mm"] == 0.0035
    assert spec["h_ref_mm"] <= L0_HALF
    assert spec["l0_mm"] == 0.0075
    assert spec["notch_x"] == 0.5000
    assert spec["notch_y"] == 0.5000
    assert spec["half_width_mm"] == 0.0250
    assert spec["band_height_mm"] == 0.0500
    assert spec["x_min"] <= 0.4500
    assert spec["x_max"] >= 0.6000
    assert spec["y_min"] == pytest.approx(0.4750, 1e-4)
    assert spec["y_max"] == pytest.approx(0.5250, 1e-4)


def test_case1_physical_mesh_metrics_and_gates():
    assert os.path.isfile(PHYS_MESH_PATH), "Physical mesh file does not exist: %s" % PHYS_MESH_PATH

    nodes = {}
    quads = {}
    tris = {}
    in_nodes = False
    in_elements = False
    elem_type = None

    with open(PHYS_MESH_PATH, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_nodes = False
                in_elements = False
                u = l.upper()
                if u.startswith("*NODE"):
                    in_nodes = True
                elif u.startswith("*ELEMENT"):
                    in_elements = True
                    if "CPE4" in u or "QUAD" in u:
                        elem_type = "QUAD"
                    elif "CPE3" in u or "TRI" in u:
                        elem_type = "TRI"
                continue
            if in_nodes:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 3:
                    nid = int(parts[0])
                    nodes[nid] = (float(parts[1]), float(parts[2]))
            elif in_elements:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 4:
                    eid = int(parts[0])
                    nids = [int(p) for p in parts[1:]]
                    if elem_type == "QUAD" or len(nids) == 4:
                        quads[eid] = nids
                    else:
                        tris[eid] = nids

    total_elems = len(quads) + len(tris)
    quad_pct = (len(quads) / total_elems) * 100.0

    # Gate 02: Quad fraction >= 85.0%
    assert quad_pct >= 85.0, "Quad percentage %.2f%% below 85.0%%" % quad_pct
    assert quad_pct >= 95.0, "Expected quad fraction >= 95.0%%, got %.2f%%" % quad_pct

    # Bounded mesh: strictly < 35,000 elements
    assert total_elems < 35000, "Element count %d exceeds 35,000" % total_elems
    assert total_elems >= 2000, "Element count %d too low" % total_elems

    # Gate 04: Refined element size in corridor <= l0 / 2 = 0.00375 mm
    corridor_h = []
    for eid, conn in quads.items():
        coords = [nodes[n] for n in conn if n in nodes]
        cx = sum(c[0] for c in coords) / 4.0
        cy = sum(c[1] for c in coords) / 4.0
        if 0.48 <= cx <= 0.58 and 0.48 <= cy <= 0.52:
            x0, y0 = coords[0]
            x1, y1 = coords[1]
            x2, y2 = coords[2]
            x3, y3 = coords[3]
            area = 0.5 * abs((x0*y1 - y0*x1) + (x1*y2 - y1*x2) + (x2*y3 - y2*x3) + (x3*y0 - y3*x0))
            corridor_h.append(math.sqrt(area))

    assert len(corridor_h) > 50, "Insufficient elements found in refinement corridor"
    median_h = sorted(corridor_h)[len(corridor_h) // 2]
    assert median_h <= 0.00375, "Median corridor h = %.5f mm exceeds l0/2 = 0.00375 mm" % median_h


def test_case1_seam_flank_duplication():
    """Verify that the initial notch x in [0.0, 0.5], y = 0.5 has duplicate nodes for upper and lower flanks."""
    nodes = {}
    in_nodes = False
    with open(PHYS_MESH_PATH, "r") as f:
        for line in f:
            l = line.strip()
            if l.startswith("*"):
                in_nodes = l.upper().startswith("*NODE")
                continue
            if in_nodes:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 3:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))

    coord_counts = defaultdict(list)
    for nid, (x, y) in nodes.items():
        key = (round(x, 4), round(y, 4))
        coord_counts[key].append(nid)

    # Check notch seam coordinates: should have duplicate nodes
    seam_dups = {k: v for k, v in coord_counts.items() if abs(k[1] - 0.5000) < 1e-4 and 0.0 <= k[0] < 0.5000 and len(v) >= 2}
    print("Found %d duplicate coordinate positions along notch seam" % len(seam_dups))

    # The uncracked ligament x > 0.5000 should have single unique nodes (no duplication)
    ligament_dups = {k: v for k, v in coord_counts.items() if abs(k[1] - 0.5000) < 1e-4 and k[0] > 0.5000 and len(v) >= 2}
    assert len(ligament_dups) == 0, "Uncracked ligament should not have duplicate nodes: %s" % ligament_dups
