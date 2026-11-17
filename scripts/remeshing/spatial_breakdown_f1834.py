# -*- coding: utf-8 -*-
"""
scripts/remeshing/spatial_breakdown_f1834.py
===========================================
Maps element dominance by region:
- Case 1: Ligament (x >= 0.5, |y-0.5| <= 0.02) vs Far Field
- Case 2: Notch (x <= 0.55, |y-0.5| <= 0.02), Hole perimeter, Distal (x >= 0.75, y in [0.55, 0.75]), Far field
- Case 3: Primary corridor, Secondary corridor, Hole perimeters, Far field
"""
from __future__ import print_function
import os
import sys
import json
import math

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import odbAccess

def inspect_spatial_case1():
    c1_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case1")
    states = [
        "PK_C1_STATE1_INITIATION.odb",
        "PK_C1_STATE2_EARLY_PROPAGATION.odb",
        "PK_C1_STATE3_MID_PROPAGATION.odb",
        "PK_C1_STATE4_OUTER_PROPAGATION.odb",
        "PK_C1_STATE5_TERMINAL_SEVERANCE.odb"
    ]
    odbs = [os.path.join(c1_dir, s) for s in states]
    
    # Read mesh coordinates
    o0 = odbAccess.openOdb(odbs[0], readOnly=True)
    inst = list(o0.rootAssembly.instances.values())[0]
    node_coords = {n.label: n.coordinates for n in inst.nodes}
    elem_nodes = {e.label: e.connectivity for e in inst.elements}
    o0.close()
    
    # Calculate element centroids
    elem_centroids = {}
    for el, conn in elem_nodes.items():
        pts = [node_coords[nid] for nid in conn if nid in node_coords]
        cx = sum(p[0] for p in pts) / float(len(pts))
        cy = sum(p[1] for p in pts) / float(len(pts))
        elem_centroids[el] = (cx, cy)
        
    # Read eta values across states
    state_etas = []
    for p in odbs:
        o = odbAccess.openOdb(p, readOnly=True)
        f = o.steps["RECOVERY_STEP"].frames[-1]
        eri = {v.elementLabel: float(v.data) for v in f.fieldOutputs["MISESERI"].values}
        avg = {v.elementLabel: float(v.data) for v in f.fieldOutputs["MISESAVG"].values}
        o.close()
        etas = {el: (eri[el]/avg[el]) if avg[el] > 0 else 0.0 for el in elem_nodes}
        state_etas.append(etas)
        
    # Classify dominance
    breakdown = {i: {"ligament": 0, "far_field": 0, "total": 0} for i in range(5)}
    for el in elem_nodes:
        best_k = max(range(5), key=lambda k: state_etas[k][el])
        cx, cy = elem_centroids[el]
        is_lig = (0.50 <= cx <= 1.00 and 0.48 <= cy <= 0.52)
        breakdown[best_k]["total"] += 1
        if is_lig:
            breakdown[best_k]["ligament"] += 1
        else:
            breakdown[best_k]["far_field"] += 1
            
    print("\nCase 1 Spatial Dominance Breakdown:")
    for k in range(5):
        d = breakdown[k]
        print("  State %d (%s): Total %4d | Ligament: %4d | Far-Field: %4d" % (
            k, states[k][:18], d["total"], d["ligament"], d["far_field"]
        ))
    return breakdown


def inspect_spatial_case2():
    c2_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case2")
    states = [
        "PK_C2_STATE1_PREANALYSIS.odb",
        "PK_C2_STATE2_HOLE_ARREST.odb",
        "PK_C2_STATE3_DISTAL_NUCLEATION.odb",
        "PK_C2_STATE4_OUTER_PROPAGATION.odb"
    ]
    odbs = [os.path.join(c2_dir, s) for s in states]
    
    o0 = odbAccess.openOdb(odbs[0], readOnly=True)
    inst = list(o0.rootAssembly.instances.values())[0]
    node_coords = {n.label: n.coordinates for n in inst.nodes}
    elem_nodes = {e.label: e.connectivity for e in inst.elements}
    o0.close()
    
    elem_centroids = {}
    for el, conn in elem_nodes.items():
        pts = [node_coords[nid] for nid in conn if nid in node_coords]
        cx = sum(p[0] for p in pts) / float(len(pts))
        cy = sum(p[1] for p in pts) / float(len(pts))
        elem_centroids[el] = (cx, cy)
        
    state_etas = []
    for p in odbs:
        o = odbAccess.openOdb(p, readOnly=True)
        f = o.steps["RECOVERY_STEP"].frames[-1]
        eri = {v.elementLabel: float(v.data) for v in f.fieldOutputs["MISESERI"].values}
        avg = {v.elementLabel: float(v.data) for v in f.fieldOutputs["MISESAVG"].values}
        o.close()
        etas = {el: (eri[el]/avg[el]) if avg[el] > 0 else 0.0 for el in elem_nodes}
        state_etas.append(etas)
        
    breakdown = {i: {"notch": 0, "hole_perim": 0, "distal": 0, "far_field": 0, "total": 0} for i in range(4)}
    # Hole center is at (0.65, 0.60), radius 0.10
    hx, hy, hr = 0.65, 0.60, 0.10
    for el in elem_nodes:
        best_k = max(range(4), key=lambda k: state_etas[k][el])
        cx, cy = elem_centroids[el]
        dist_hole = math.hypot(cx - hx, cy - hy)
        
        breakdown[best_k]["total"] += 1
        if 0.0 <= cx <= 0.55 and 0.48 <= cy <= 0.52:
            breakdown[best_k]["notch"] += 1
        elif dist_hole <= hr * 1.5:
            breakdown[best_k]["hole_perim"] += 1
        elif 0.75 <= cx <= 1.00 and 0.55 <= cy <= 0.75:
            breakdown[best_k]["distal"] += 1
        else:
            breakdown[best_k]["far_field"] += 1
            
    print("\nCase 2 Spatial Dominance Breakdown:")
    for k in range(4):
        d = breakdown[k]
        print("  State %d (%s): Total %4d | Notch: %4d | Hole: %4d | Distal: %4d | Far-Field: %4d" % (
            k, states[k][:18], d["total"], d["notch"], d["hole_perim"], d["distal"], d["far_field"]
        ))
    return breakdown


def inspect_spatial_case3():
    c3_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case3")
    states = [
        "SEC43_C3_STATE1_INITIATION.odb",
        "SEC43_C3_STATE2_HOLE_ARREST.odb",
        "SEC43_C3_STATE3_PROPAGATION.odb"
    ]
    odbs = [os.path.join(c3_dir, s) for s in states]
    
    o0 = odbAccess.openOdb(odbs[0], readOnly=True)
    inst = list(o0.rootAssembly.instances.values())[0]
    node_coords = {n.label: n.coordinates for n in inst.nodes}
    elem_nodes = {e.label: e.connectivity for e in inst.elements}
    o0.close()
    
    elem_centroids = {}
    for el, conn in elem_nodes.items():
        pts = [node_coords[nid] for nid in conn if nid in node_coords]
        cx = sum(p[0] for p in pts) / float(len(pts))
        cy = sum(p[1] for p in pts) / float(len(pts))
        elem_centroids[el] = (cx, cy)
        
    state_etas = []
    for p in odbs:
        o = odbAccess.openOdb(p, readOnly=True)
        f = o.steps["RECOVERY_STEP"].frames[-1]
        eri = {v.elementLabel: float(v.data) for v in f.fieldOutputs["MISESERI"].values}
        avg = {v.elementLabel: float(v.data) for v in f.fieldOutputs["MISESAVG"].values}
        o.close()
        etas = {el: (eri[el]/avg[el]) if avg[el] > 0 else 0.0 for el in elem_nodes}
        state_etas.append(etas)
        
    breakdown = {i: {"primary": 0, "secondary": 0, "holes_pins": 0, "far_field": 0, "total": 0} for i in range(3)}
    for el in elem_nodes:
        best_k = max(range(3), key=lambda k: state_etas[k][el])
        cx, cy = elem_centroids[el]
        
        breakdown[best_k]["total"] += 1
        if 10.0 <= cx <= 36.5 and 45.0 <= cy <= 75.0:
            breakdown[best_k]["primary"] += 1
        elif 36.5 <= cx <= 65.0 and 45.0 <= cy <= 65.0:
            breakdown[best_k]["secondary"] += 1
        elif (math.hypot(cx - 20.0, cy - 100.0) <= 6.0 or 
              math.hypot(cx - 20.0, cy - 20.0) <= 6.0 or 
              math.hypot(cx - 35.0, cy - 50.0) <= 7.0):
            breakdown[best_k]["holes_pins"] += 1
        else:
            breakdown[best_k]["far_field"] += 1
            
    print("\nCase 3 Spatial Dominance Breakdown:")
    for k in range(3):
        d = breakdown[k]
        print("  State %d (%s): Total %4d | Primary: %4d | Secondary: %4d | Holes/Pins: %4d | Far-Field: %4d" % (
            k, states[k][:18], d["total"], d["primary"], d["secondary"], d["holes_pins"], d["far_field"]
        ))
    return breakdown


if __name__ == "__main__":
    inspect_case1 = inspect_spatial_case1()
    inspect_case2 = inspect_spatial_case2()
    inspect_case3 = inspect_spatial_case3()
