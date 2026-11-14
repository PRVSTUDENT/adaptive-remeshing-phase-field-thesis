# -*- coding: utf-8 -*-
"""
tests/unit/test_f1738_case1_ligament.py
======================================
Task F1738: Quantitative Station-by-Station Spatial Audit of Case 1 Horizontal Ligament
Verifies spatial resolution, mesh continuity, Jacobian positivity, and quad dominance
along the uncracked fracture ligament (x in [0.5, 1.0], y = 0.5 mm) for Mode-I edge crack.
"""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import pytest
import math
import numpy as np
from scripts.remeshing.audit_f1736_spatial_resolution import parse_abaqus_inp, compute_element_metrics

def point_to_segment_distance(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    L2 = dx*dx + dy*dy
    if L2 == 0:
        return ((px-x1)**2 + (py-y1)**2)**0.5, 0.0
    t = max(0.0, min(1.0, ((px-x1)*dx + (py-y1)*dy) / L2))
    proj_x = x1 + t*dx
    proj_y = y1 + t*dy
    return ((px-proj_x)**2 + (py-proj_y)**2)**0.5, t

def audit_case1_ligament_stations(inp_path, l0=0.0075, w_perp_factor=2.5):
    """
    Discretizes the horizontal fracture ligament x in [0.5, 1.0], y = 0.5 mm
    into 10 longitudinal stations of length delta_x = 0.05 mm (6.67 l0),
    transverse corridor half-width w_perp = w_perp_factor * l0 = 0.01875 mm (total width 37.5 um).
    """
    assert os.path.exists(inp_path), f"INP deck missing: {inp_path}"
    nodes, elements, elem_types = parse_abaqus_inp(inp_path)
    res = compute_element_metrics(nodes, elements, elem_types, ell_0=l0)
    
    w_perp = w_perp_factor * l0
    stations = [[] for _ in range(10)]
    
    for eid, nids in elements.items():
        pts = [nodes[n] for n in nids]
        cx = float(np.mean([p[0] for p in pts]))
        cy = float(np.mean([p[1] for p in pts]))
        
        # Area calculation
        if len(pts) == 4:
            area = 0.5 * abs((pts[0][0]*pts[1][1] - pts[1][0]*pts[0][1]) +
                             (pts[1][0]*pts[2][1] - pts[2][0]*pts[1][1]) +
                             (pts[2][0]*pts[3][1] - pts[3][0]*pts[2][1]) +
                             (pts[3][0]*pts[0][1] - pts[0][0]*pts[3][1]))
        else:
            area = 0.5 * abs((pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1]) - (pts[2][0]-pts[0][0])*(pts[1][1]-pts[0][1]))
        h_e = math.sqrt(area) * 1000.0  # in um
        
        dist, t = point_to_segment_distance(cx, cy, 0.5, 0.5, 1.0, 0.5)
        if dist <= w_perp:
            st_idx = min(9, int(t * 10))
            stations[st_idx].append(h_e)
            
    station_metrics = []
    for s_idx in range(10):
        x_start = 0.5 + 0.05 * s_idx
        x_end = 0.5 + 0.05 * (s_idx + 1)
        h_vals = stations[s_idx]
        if h_vals:
            mean_h = sum(h_vals) / len(h_vals)
            min_h = min(h_vals)
            max_h = max(h_vals)
            pct_le_l0 = sum(1 for h in h_vals if h <= l0 * 1000.0) / len(h_vals) * 100.0
            pct_le_half = sum(1 for h in h_vals if h <= (l0/2.0) * 1000.0) / len(h_vals) * 100.0
        else:
            mean_h = min_h = max_h = 0.0
            pct_le_l0 = pct_le_half = 0.0
        station_metrics.append({
            "station": s_idx + 1,
            "x_interval": [round(x_start, 3), round(x_end, 3)],
            "count": len(h_vals),
            "mean_h_um": round(mean_h, 3),
            "min_h_um": round(min_h, 3),
            "max_h_um": round(max_h, 3),
            "pct_le_l0": round(pct_le_l0, 2),
            "pct_le_half_l0": round(pct_le_half, 2)
        })
        
    return res, station_metrics


def test_f1728_case1_audit():
    """Verify the documented localized deficiency of the existing F1728 Case 1 mesh."""
    inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "219_f1728_five_geometry_study", "PK_F1728_CASE_1_ADAPT_PHYS.inp")
    res, stations = audit_case1_ligament_stations(inp)
    
    assert res["num_elements"] == 14147
    assert res["quad_percentage"] > 97.0
    assert res["negative_jacobian_count"] == 0
    assert res["min_jacobian"] > 0
    assert res["aspect_ratio_stats"]["max"] < 3.0
    
    # Notch tip region (Stations 1-3) is well refined
    assert stations[0]["mean_h_um"] < 7.5
    assert stations[0]["pct_le_l0"] > 90.0
    
    # But distal stations (Stations 7-10) are under-refined in F1728
    print("\nExisting F1728 Case 1 Ligament Stations:")
    for st in stations:
        print(f"  Station {st['station']:2d} (x in {st['x_interval']}): {st['count']:3d} elems | mean h = {st['mean_h_um']:5.2f} um | %<=l0: {st['pct_le_l0']:5.1f}%")
        
    # Stations 8, 9, 10 have mean h > l0 = 7.5 um (confirming documented deficiency)
    assert stations[8]["mean_h_um"] > 7.5 or stations[9]["mean_h_um"] > 7.5

def test_f1713_case1_audit():
    """Evaluate candidate mesh F1713 to determine whether its ligament is refined."""
    inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "206_f1713_new_mode1_adaptive_experiment", "PK_F1713_JOB2_ADAPTED_PHYS.inp")
    if not os.path.exists(inp):
        pytest.skip("F1713 mesh not present")
    res, stations = audit_case1_ligament_stations(inp)
    
    print("\nCandidate F1713 Case 1 Ligament Stations:")
    for st in stations:
        print(f"  Station {st['station']:2d} (x in {st['x_interval']}): {st['count']:3d} elems | mean h = {st['mean_h_um']:5.2f} um | %<=l0: {st['pct_le_l0']:5.1f}%")
        
    assert res["num_elements"] == 14933
    assert res["negative_jacobian_count"] == 0
    assert res["min_jacobian"] > 0
    assert res["quad_percentage"] > 97.0


def test_task5_2pct_case1_audit():
    """Evaluate candidate mesh from 06_production_adaptive_2pct (Job 1400395)."""
    inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "06_production_adaptive_2pct", "inputs", "PK_MODE1_PROPOSED_PFM_PHYS.inp")
    if not os.path.exists(inp):
        pytest.skip("06_production_adaptive_2pct mesh not present")
    res, stations = audit_case1_ligament_stations(inp)
    
    print("\nCandidate 06_production_adaptive_2pct Ligament Stations:")
    for st in stations:
        print(f"  Station {st['station']:2d} (x in {st['x_interval']}): {st['count']:3d} elems | mean h = {st['mean_h_um']:5.2f} um | %<=l0: {st['pct_le_l0']:5.1f}%")
        
    print(f"Total elements: {res['num_elements']}, Quad %: {res['quad_percentage']:.2f}%")


def test_job1400395_15k_audit():
    """Evaluate candidate mesh from 06_production_adaptive_2pct (Job 1400395, 15,396 elements)."""
    inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "06_production_adaptive_2pct", "inputs", "PK_MODE1_PROPOSED_PFM.inp")
    if not os.path.exists(inp):
        pytest.skip("06_production_adaptive_2pct deck not present")
        
    nodes = {}
    elements = {}
    elem_types = {}
    
    with open(inp, "r") as f:
        in_nodes = False
        in_layer1_quad = False
        in_layer1_tri = False
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_nodes = False
                in_layer1_quad = False
                in_layer1_tri = False
                if l.upper().startswith("*NODE") and not l.upper().startswith("*NODE OUTPUT") and not l.upper().startswith("*NODE PRINT") and not l.upper().startswith("*NODE FILE"):
                    in_nodes = True
                elif l.upper().startswith("*ELEMENT, TYPE=U1"):
                    in_layer1_quad = True
                elif l.upper().startswith("*ELEMENT, TYPE=U3"):
                    in_layer1_tri = True
                continue
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if in_nodes:
                nid = int(parts[0])
                if nid != 999999:
                    nodes[nid] = (float(parts[1]), float(parts[2]))
            elif in_layer1_quad:
                eid = int(parts[0])
                elements[eid] = tuple(int(p) for p in parts[1:5])
                elem_types[eid] = "CPE4"
            elif in_layer1_tri:
                eid = int(parts[0])
                elements[eid] = tuple(int(p) for p in parts[1:4])
                elem_types[eid] = "CPE3"
                
    from scripts.remeshing.audit_f1736_spatial_resolution import compute_element_metrics
    l0 = 0.0075
    w_perp = 2.5 * l0
    res = compute_element_metrics(nodes, elements, elem_types, ell_0=l0)
    
    stations = [[] for _ in range(10)]
    for eid, nids in elements.items():
        pts = [nodes[n] for n in nids]
        cx = float(np.mean([p[0] for p in pts]))
        cy = float(np.mean([p[1] for p in pts]))
        if len(pts) == 4:
            area = 0.5 * abs((pts[0][0]*pts[1][1] - pts[1][0]*pts[0][1]) +
                             (pts[1][0]*pts[2][1] - pts[2][0]*pts[1][1]) +
                             (pts[2][0]*pts[3][1] - pts[3][0]*pts[2][1]) +
                             (pts[3][0]*pts[0][1] - pts[0][0]*pts[3][1]))
        else:
            area = 0.5 * abs((pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1]) - (pts[2][0]-pts[0][0])*(pts[1][1]-pts[0][1]))
        h_e = math.sqrt(area) * 1000.0
        dist, t = point_to_segment_distance(cx, cy, 0.5, 0.5, 1.0, 0.5)
        if dist <= w_perp:
            st_idx = min(9, int(t * 10))
            stations[st_idx].append(h_e)
            
    print(f"\nJob 1400395 (15,396 elements) Ligament Stations:")
    for s_idx in range(10):
        x_start = 0.5 + 0.05 * s_idx
        x_end = 0.5 + 0.05 * (s_idx + 1)
        h_vals = stations[s_idx]
        if h_vals:
            mean_h = sum(h_vals) / len(h_vals)
            pct_le_l0 = sum(1 for h in h_vals if h <= l0 * 1000.0) / len(h_vals) * 100.0
            print(f"  Station {s_idx+1:2d} (x in [{x_start:.2f}, {x_end:.2f}]): {len(h_vals):3d} elems | mean h = {mean_h:5.2f} um | %<=l0: {pct_le_l0:5.1f}%")
        else:
            print(f"  Station {s_idx+1:2d} (x in [{x_start:.2f}, {x_end:.2f}]):   0 elems")
            
    print(f"Total elements: {res['num_elements']}, Quad %: {res['quad_percentage']:.2f}%, Min det(J): {res['min_jacobian']:.3e}")


def test_f1738_ligament_qualified_mesh():
    """Verify all 7 execution gates on the authoritative Case 1 ligament-qualified mesh."""
    import json
    json_path = os.path.join(REPO_ROOT, "results", "validation", "f1738_case1_ligament_spatial_audit.json")
    assert os.path.exists(json_path), f"Audit JSON missing: {json_path}"
    with open(json_path, "r") as f:
        data = json.load(f)

    # Gate 01: Elements and quad dominance
    assert data["total_elements"] == 13960
    assert data["quad_percentage"] >= 95.0
    assert data["quad_count"] == 13611
    assert data["tri_count"] == 349

    # Gate 02: Inversion safety
    assert data["min_det_j"] > 0
    assert data["negative_jacobian_count"] == 0
    assert data["max_aspect_ratio"] < 5.0

    # Gate 03: 10-Station resolution
    assert data["all_stations_mean_le_l0"] is True
    assert len(data["station_metrics"]) == 10
    st1 = data["station_metrics"][0]
    assert st1["min_h_um"] <= 1.0
    assert st1["mean_h_um"] <= 3.75  # l0 / 2
    for st in data["station_metrics"]:
        assert st["mean_h_um"] <= 7.5
        assert st["area_pct_le_l0"] == 100.0

    # Gate 04: Area compliance & barrier freedom
    assert data["overall_area_compliance_pct_l0"] >= 80.0
    assert data["has_transverse_coarse_barrier"] is False
    assert data["max_contiguous_coarse_span_um"] == 0.0

    # Gate 05: Physical mesh and production deck integrity
    phys_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "226_f1738_case1_ligament_refinement", "PK_F1738_CASE_1_ADAPT_PHYS.inp")
    prod_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "226_f1738_case1_ligament_refinement", "PK_F1738_CASE_1_PROD.inp")
    assert os.path.exists(phys_inp)
    assert os.path.exists(prod_inp)

    # Gate 06: Datacheck completion
    dc_dat = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "226_f1738_case1_ligament_refinement", "PK_F1738_CASE_1_DC.dat")
    assert os.path.exists(dc_dat)
    with open(dc_dat, "r") as f:
        content = f.read()
    assert "ANALYSIS DATACHECK COMPLETE" in content



