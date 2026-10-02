#!/usr/bin/env python3
"""
Primary Nodal Field Transfer Engine (Repaired for Clean Physical vs RP Separation):
Interpolates continuous primary fields (Displacements U1, U2 and Phase Damage U3)
from source mesh onto target mesh via C0-consistent finite element isoparametric mapping.
Strictly excludes auxiliary/Reference Point (RP) nodes from spatial FE interpolation.
Enforces topology-aware slit barrier candidate filtering for duplicated crack-flank nodes.
"""

import math
import csv
from typing import Dict, List, Tuple, Optional, Any, Set
from pathlib import Path

try:
    from .geometric_search import SpatialGridIndex, MappingResult
except ImportError:
    from geometric_search import SpatialGridIndex, MappingResult


def classify_target_node_flanks(
    target_nodes: Dict[int, Tuple[float, float]],
    target_elements: Dict[int, Tuple[int, ...]]
) -> Dict[int, int]:
    """
    Computes topological flank for all target nodes based on connected element centroids:
      -1: LOWER flank (connected strictly to elements with cy < 0)
      +1: UPPER flank (connected strictly to elements with cy > 0)
       0: CONTINUUM / BOTH (connected to elements spanning both sides or cy ~ 0)
    """
    node_to_elems: Dict[int, List[int]] = {}
    for eid, conn in target_elements.items():
        for nid in conn:
            if nid not in node_to_elems:
                node_to_elems[nid] = []
            node_to_elems[nid].append(eid)

    elem_centroids: Dict[int, float] = {}
    for eid, conn in target_elements.items():
        pts = [target_nodes[nid] for nid in conn if nid in target_nodes]
        if pts:
            elem_centroids[eid] = sum(p[1] for p in pts) / len(pts)

    node_flanks: Dict[int, int] = {}
    for nid in target_nodes:
        connected = node_to_elems.get(nid, [])
        if not connected:
            node_flanks[nid] = 0
            continue
        cys = [elem_centroids[eid] for eid in connected if eid in elem_centroids]
        has_lower = any(cy < -1e-7 for cy in cys)
        has_upper = any(cy > 1e-7 for cy in cys)
        if has_lower and not has_upper:
            node_flanks[nid] = -1  # LOWER
        elif has_upper and not has_lower:
            node_flanks[nid] = 1   # UPPER
        else:
            node_flanks[nid] = 0   # CONTINUUM / BOTH
    return node_flanks


def transfer_primary_fields(
    source_nodes: Dict[int, Tuple[float, float]],
    source_elements: Dict[int, Tuple[int, ...]],
    source_nodal_fields: Dict[int, Dict[str, float]],
    target_nodes: Dict[int, Tuple[float, float]],
    target_elements: Optional[Dict[int, Tuple[int, ...]]] = None,
    target_node_flanks: Optional[Dict[int, int]] = None,
    auxiliary_node_ids: Optional[Set[int]] = None,
    handoff_rp_u1: Optional[float] = 0.010143300518393517,
    inside_tol: float = 1e-6
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Interpolates primary fields (U1, U2, U3) from source mesh to target mesh.
    Strictly separates physical nodes from auxiliary/RP control nodes.
    Enforces topological slit-flank isolation for split nodes.
    Returns:
      (node_records, summary_diagnostics)
    """
    if auxiliary_node_ids is None:
        auxiliary_node_ids = set()

    # Precompute topological flanks for target nodes if target_elements provided
    if target_node_flanks is None:
        if target_elements is not None:
            target_node_flanks = classify_target_node_flanks(target_nodes, target_elements)
        else:
            target_node_flanks = {}

    spatial_index = SpatialGridIndex(source_elements, source_nodes, cell_size=0.025)

    node_records: List[Dict[str, Any]] = []
    
    physical_total = 0
    physical_inside_count = 0
    physical_boundary_count = 0
    physical_outside_count = 0
    max_residual = 0.0
    sum_residual = 0.0
    
    u1_vals = []
    u2_vals = []
    u3_vals = []

    for target_nid in sorted(target_nodes.keys()):
        tx, ty = target_nodes[target_nid]
        
        # 1. Handle Auxiliary / RP Nodes (NO FE Interpolation)
        if target_nid in auxiliary_node_ids:
            node_records.append({
                "target_node_id": target_nid,
                "node_type": "AUXILIARY_RP",
                "x": tx,
                "y": ty,
                "source_element_id": None,
                "source_element_type": None,
                "source_node_ids": [],
                "xi": None,
                "eta": None,
                "weights": [],
                "residual": None,
                "is_inside": False,
                "is_boundary": False,
                "fallback_used": False,
                "U1": handoff_rp_u1,
                "U2": None,  # Preserves top U2 FREE
                "U3": None   # RP has no phase DOF
            })
            continue

        # 2. Handle Physical Mesh Nodes (C0 FE Isoparametric Interpolation with Slit Barrier)
        physical_total += 1
        flank = target_node_flanks.get(target_nid, 0)
        map_res = spatial_index.find_containing_element(tx, ty, inside_tol=inside_tol, target_flank=flank)
        
        if map_res is not None and map_res.is_inside:
            physical_inside_count += 1
            if map_res.is_boundary:
                physical_boundary_count += 1
            
            res_val = map_res.residual
            max_residual = max(max_residual, res_val)
            sum_residual += res_val
            
            u1_interp = 0.0
            u2_interp = 0.0
            u3_interp = 0.0
            
            for i, src_nid in enumerate(map_res.node_ids):
                w = map_res.weights[i]
                src_f = source_nodal_fields.get(src_nid, {"U1": 0.0, "U2": 0.0, "U3": 0.0})
                u1_interp += w * src_f.get("U1", 0.0)
                u2_interp += w * src_f.get("U2", 0.0)
                u3_interp += w * src_f.get("U3", 0.0)

            u1_vals.append(u1_interp)
            u2_vals.append(u2_interp)
            u3_vals.append(u3_interp)

            node_records.append({
                "target_node_id": target_nid,
                "node_type": "PHYSICAL_MESH",
                "x": tx,
                "y": ty,
                "source_element_id": map_res.element_id,
                "source_element_type": map_res.element_type,
                "source_node_ids": list(map_res.node_ids),
                "xi": map_res.xi,
                "eta": map_res.eta,
                "weights": list(map_res.weights),
                "residual": res_val,
                "is_inside": True,
                "is_boundary": map_res.is_boundary,
                "fallback_used": False,
                "U1": u1_interp,
                "U2": u2_interp,
                "U3": u3_interp
            })
        else:
            physical_outside_count += 1
            node_records.append({
                "target_node_id": target_nid,
                "node_type": "PHYSICAL_MESH",
                "x": tx,
                "y": ty,
                "source_element_id": map_res.element_id if map_res else None,
                "source_element_type": map_res.element_type if map_res else None,
                "source_node_ids": list(map_res.node_ids) if map_res else [],
                "xi": map_res.xi if map_res else None,
                "eta": map_res.eta if map_res else None,
                "weights": list(map_res.weights) if map_res else [],
                "residual": map_res.residual if map_res else None,
                "is_inside": False,
                "is_boundary": False,
                "fallback_used": False,
                "U1": None,
                "U2": None,
                "U3": None
            })

    mean_residual = (sum_residual / physical_inside_count) if physical_inside_count > 0 else 0.0

    summary = {
        "target_physical_nodes": physical_total,
        "target_auxiliary_nodes": len(auxiliary_node_ids),
        "physical_nodes_mapped": physical_inside_count,
        "auxiliary_nodes_FE_interpolated": 0,
        "unmapped_physical_nodes": physical_outside_count,
        "fallback_physical_nodes": 0,
        "boundary_physical_nodes": physical_boundary_count,
        "max_mapping_residual": max_residual,
        "mean_mapping_residual": mean_residual,
        "field_statistics": {
            "U1_min": min(u1_vals) if u1_vals else None,
            "U1_max": max(u1_vals) if u1_vals else None,
            "U1_mean": (sum(u1_vals) / len(u1_vals)) if u1_vals else None,
            "U2_min": min(u2_vals) if u2_vals else None,
            "U2_max": max(u2_vals) if u2_vals else None,
            "U2_mean": (sum(u2_vals) / len(u2_vals)) if u2_vals else None,
            "U3_min": min(u3_vals) if u3_vals else None,
            "U3_max": max(u3_vals) if u3_vals else None,
            "U3_mean": (sum(u3_vals) / len(u3_vals)) if u3_vals else None,
        },
        "all_physical_nodes_mapped": (physical_outside_count == 0)
    }

    return node_records, summary


def load_nodal_csv(csv_path: str) -> Dict[int, Dict[str, float]]:
    """Loads nodal fields (U1, U2, U3) from CSV file."""
    nodal_data: Dict[int, Dict[str, float]] = {}
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                nid_str = r.get("node_label") or r.get("node_id") or r.get("node") or r.get("NODE") or "0"
                nid = int(nid_str)
                u1 = float(r.get("U1_solver") or r.get("U1") or r.get("u1") or 0.0)
                u2 = float(r.get("U2_solver") or r.get("U2") or r.get("u2") or 0.0)
                u3 = float(r.get("U3_phase_solver") or r.get("U3") or r.get("u3") or r.get("d") or r.get("phase") or 0.0)
                nodal_data[nid] = {"U1": u1, "U2": u2, "U3": u3}
            except (ValueError, TypeError):
                continue
    return nodal_data
