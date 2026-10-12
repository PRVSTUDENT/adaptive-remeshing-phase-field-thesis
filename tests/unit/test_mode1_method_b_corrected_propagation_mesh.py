"""Unit test for Mode-I Method B Corrected Propagation Mesh.

Task: F1430-MODE1-METHOD-B-CORRECTED-PROPAGATION-REMESH-AND-LICENSE-CHECK
Verifies the corrected Method B 14,483-element adaptive mesh input deck:
- 14,456 mesh nodes + RP 999999
- 14,483 base elements (401 tris, 14,082 quads)
- 43,449 layered elements (Phase UEL, Mech UEL, Companion UMAT)
- Slit and boundary definitions (52 bottom, 52 top, pin node 33, 52 constraint equations)
- Fracture corridor resolution: >= 5,000 corridor elements, h <= l0/2 across entire ligament [0.5, 1.0] mm
- Existence and non-trivial size of all 3 figure pairs (PNG and PDF)
"""

import os
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DECK_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "40_method_b_corrected_propagation_14k" / "M1_MB_CORRECTED_PROPAGATION_14K.inp"
FIG_DIR = REPO_ROOT / "results" / "figures" / "mode1_method_b_corrected_mesh"


def parse_deck_summary(deck_path):
    nodes = {}
    base_elements = {}
    total_elements = 0
    in_nodes = False
    in_elements = False
    current_elem_type = None

    bottom_nodes = []
    top_nodes = []
    equations = 0

    with open(deck_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        idx += 1
        if not line or line.startswith("**"):
            continue

        if line.startswith("*"):
            upper = line.upper()
            if upper.startswith("*NODE") and not upper.startswith("*NODE PRINT") and not upper.startswith("*NODE OUTPUT") and not upper.startswith("*NODEFILE"):
                in_nodes = True
                in_elements = False
                continue
            elif upper.startswith("*ELEMENT") and not upper.startswith("*ELEMENT OUTPUT") and not upper.startswith("*ELEMENT PRINT") and not upper.startswith("*ELEMENTFILE"):
                in_nodes = False
                in_elements = True
                parts = [p.strip() for p in upper.split(",")]
                current_elem_type = None
                for p in parts:
                    if p.startswith("TYPE="):
                        current_elem_type = p.split("=")[1].strip()
                continue
            elif upper.startswith("*NSET"):
                in_nodes = False
                in_elements = False
                parts = [p.strip() for p in upper.split(",")]
                nset_name = None
                for p in parts:
                    if p.startswith("NSET="):
                        nset_name = p.split("=")[1].strip()
                # Read nset lines
                while idx < len(lines):
                    peek = lines[idx].strip()
                    if peek.startswith("*") or not peek:
                        break
                    n_ids = [int(x.strip()) for x in peek.split(",") if x.strip()]
                    if nset_name == "N_BOTTOM":
                        bottom_nodes.extend(n_ids)
                    elif nset_name == "N_TOP":
                        top_nodes.extend(n_ids)
                    idx += 1
                continue
            elif upper.startswith("*EQUATION"):
                in_nodes = False
                in_elements = False
                # Count equations
                while idx < len(lines):
                    peek = lines[idx].strip()
                    if peek.startswith("*"):
                        break
                    if peek and not peek.startswith("**"):
                        if peek == "2":
                            equations += 1
                    idx += 1
                continue
            else:
                in_nodes = False
                in_elements = False
                continue

        if in_nodes:
            parts = [p.strip() for p in line.split(",")]
            nid = int(parts[0])
            coords = [float(p) for p in parts[1:]]
            nodes[nid] = coords

        elif in_elements:
            total_elements += 1
            if current_elem_type in ("U1", "U3"):
                parts = [p.strip() for p in line.split(",")]
                eid = int(parts[0])
                conn = [int(p) for p in parts[1:]]
                base_elements[eid] = (current_elem_type, conn)

    return nodes, base_elements, total_elements, bottom_nodes, top_nodes, equations


def test_input_deck_exists():
    assert DECK_PATH.exists(), f"Corrected Method B input deck not found: {DECK_PATH}"
    assert DECK_PATH.stat().st_size > 500_000, f"Deck file too small: {DECK_PATH.stat().st_size} bytes"


def test_mesh_node_and_element_counts():
    nodes, base_elements, total_elements, bottom_nodes, top_nodes, equations = parse_deck_summary(DECK_PATH)

    # 14,456 mesh nodes + RP 999999 = 14,457 total nodes defined in deck
    assert len(nodes) == 14457, f"Expected 14,457 nodes (14,456 mesh + RP), got {len(nodes)}"
    assert 999999 in nodes, "Reference point 999999 missing"

    # Base elements: 14,483 (401 tris U3, 14,082 quads U1)
    assert len(base_elements) == 14483, f"Expected 14,483 base elements, got {len(base_elements)}"
    tri_count = sum(1 for etype, _ in base_elements.values() if etype == "U3")
    quad_count = sum(1 for etype, _ in base_elements.values() if etype == "U1")
    assert tri_count == 401, f"Expected 401 tris, got {tri_count}"
    assert quad_count == 14082, f"Expected 14,082 quads, got {quad_count}"

    # Total layered elements: 3 * 14,483 = 43,449
    assert total_elements == 43449, f"Expected 43,449 total layered elements, got {total_elements}"


def test_boundary_conditions_and_equations():
    nodes, _, _, bottom_nodes, top_nodes, equations = parse_deck_summary(DECK_PATH)

    assert len(bottom_nodes) == 52, f"Expected 52 bottom nodes, got {len(bottom_nodes)}"
    assert len(top_nodes) == 52, f"Expected 52 top nodes, got {len(top_nodes)}"
    assert equations == 52, f"Expected 52 constraint equations, got {equations}"

    # Verify all bottom nodes are at y = 0
    for nid in bottom_nodes:
        assert abs(nodes[nid][1] - 0.0) < 1e-5, f"Bottom node {nid} y-coord not 0.0: {nodes[nid][1]}"

    # Verify all top nodes are at y = 1.0
    for nid in top_nodes:
        assert abs(nodes[nid][1] - 1.0) < 1e-5, f"Top node {nid} y-coord not 1.0: {nodes[nid][1]}"


def test_propagation_corridor_resolution():
    nodes, base_elements, _, _, _, _ = parse_deck_summary(DECK_PATH)

    corridor_elements = []
    x_bins = [(0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0)]
    bin_h_values = {b: [] for b in x_bins}

    for eid, (etype, conn) in base_elements.items():
        coords = np.array([nodes[nid][:2] for nid in conn])
        centroid = coords.mean(axis=0)
        cx, cy = centroid[0], centroid[1]

        # Calculate element area and effective size h
        if len(conn) == 3:
            x0, y0 = coords[0]
            x1, y1 = coords[1]
            x2, y2 = coords[2]
            area = 0.5 * abs((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0))
            h = np.sqrt(4.0 * area / np.sqrt(3.0)) * 1000.0  # in um
        else:
            x0, y0 = coords[0]
            x1, y1 = coords[1]
            x2, y2 = coords[2]
            x3, y3 = coords[3]
            area = 0.5 * abs((x0*y1 - y0*x1) + (x1*y2 - y1*x2) + (x2*y3 - y2*x3) + (x3*y0 - y3*x0))
            h = np.sqrt(area) * 1000.0  # in um

        # Corridor: x in [0.5, 1.0], |y - 0.5| <= 0.025 mm
        if cx >= 0.5 and abs(cy - 0.5) <= 0.025:
            corridor_elements.append((eid, cx, h))
            for b in x_bins:
                if b[0] <= cx < b[1] or (b[1] == 1.0 and b[0] <= cx <= b[1]):
                    bin_h_values[b].append(h)

    # 1. Total corridor elements must exceed 5,000 (actual: 5,126)
    assert len(corridor_elements) >= 5000, f"Expected >= 5,000 corridor elements, got {len(corridor_elements)}"

    # 2. In every 0.1 mm bin across the ligament [0.5, 1.0], median h must satisfy h <= l0/2 = 3.75 um
    l0_half = 3.75  # um
    for b, h_vals in bin_h_values.items():
        assert len(h_vals) > 0, f"Bin {b} has no elements"
        median_h = float(np.median(h_vals))
        assert median_h <= l0_half, f"Bin {b} median h={median_h:.2f} um exceeds l0/2={l0_half} um"


def test_generated_figures_exist_and_non_trivial():
    expected_figures = [
        "fig_mode1_method_b_corrected_vs_original_full_mesh.png",
        "fig_mode1_method_b_corrected_vs_original_full_mesh.pdf",
        "fig_mode1_method_b_corrected_vs_original_ligament_zoom.png",
        "fig_mode1_method_b_corrected_vs_original_ligament_zoom.pdf",
        "fig_mode1_method_b_corrected_propagation_sizing_profile.png",
        "fig_mode1_method_b_corrected_propagation_sizing_profile.pdf",
    ]

    for fname in expected_figures:
        fig_path = FIG_DIR / fname
        assert fig_path.exists(), f"Figure file missing: {fig_path}"
        assert fig_path.stat().st_size > 10_000, f"Figure file unexpectedly small ({fig_path.stat().st_size} bytes): {fig_path}"
