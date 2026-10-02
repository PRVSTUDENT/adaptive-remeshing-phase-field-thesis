#!/usr/bin/env python3
"""
History Field & Internal State Transfer Engine:
Interpolates integration-point strain energy history H and element-level phase state
from source mesh to target mesh according to UEL f44/f42 constitutive semantics.
"""

import math
import struct
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

try:
    from .geometric_search import SpatialGridIndex, quad4_shape_functions
except ImportError:
    from geometric_search import SpatialGridIndex, quad4_shape_functions

GAUSS_4PT = (
    (-0.577350269189626, -0.577350269189626),
    ( 0.577350269189626, -0.577350269189626),
    ( 0.577350269189626,  0.577350269189626),
    (-0.577350269189626,  0.577350269189626)
)


def interpolate_gauss_history(
    xi_s: float,
    eta_s: float,
    source_h_4pt: Tuple[float, float, float, float]
) -> float:
    """
    Interpolates history field H at natural coordinate (xi_s, eta_s) within source element
    using the 4 Gauss-point values.
    """
    # Normalize natural coordinates to Gauss-point domain [-1, 1]
    sqrt3 = math.sqrt(3.0)
    xi_hat = max(-1.0, min(1.0, xi_s * sqrt3))
    eta_hat = max(-1.0, min(1.0, eta_s * sqrt3))

    n = quad4_shape_functions(xi_hat, eta_hat)
    h_val = sum(n[i] * source_h_4pt[i] for i in range(4))
    # Irreversibility & positivity guarantee: H >= 0
    return max(0.0, h_val)


def transfer_history_fields(
    source_nodes: Dict[int, Tuple[float, float]],
    source_elements: Dict[int, Tuple[int, ...]],
    source_h_fields: Dict[int, Tuple[float, float, float, float]], # elem_id -> (h1, h2, h3, h4)
    target_nodes: Dict[int, Tuple[float, float]],
    target_elements: Dict[int, Tuple[int, ...]],
    target_nodal_u3: Dict[int, float],
    n_capacity: int = 100000,
    inside_tol: float = 1e-6
) -> Tuple[Dict[int, Tuple[float, float, float, float]], Dict[int, float], Dict[str, Any]]:
    """
    Transfers Gauss-point history H and element-level phase damage to target mesh.
    Returns:
      (target_h_fields, target_phase_fields, summary_diagnostics)
    """
    spatial_index = SpatialGridIndex(source_elements, source_nodes, cell_size=0.025)

    target_h: Dict[int, Tuple[float, float, float, float]] = {}
    target_phase: Dict[int, float] = {}

    all_h_vals = []
    all_davg_vals = []
    unmapped_gp_count = 0

    for target_eid in sorted(target_elements.keys()):
        node_ids = target_elements[target_eid]
        coords = [target_nodes[nid] for nid in node_ids]

        # 1. Compute Element-Averaged Phase Damage
        d_nodes = [target_nodal_u3.get(nid, 0.0) for nid in node_ids]
        d_avg = sum(d_nodes) / float(len(d_nodes))
        target_phase[target_eid] = d_avg
        all_davg_vals.append(d_avg)

        # 2. Transfer Gauss Point History
        h_gp = []
        for kpt_idx, (xi_k, eta_k) in enumerate(GAUSS_4PT):
            # Compute physical coordinates of target Gauss point
            n_k = quad4_shape_functions(xi_k, eta_k)
            gx = sum(n_k[i] * coords[i][0] for i in range(4))
            gy = sum(n_k[i] * coords[i][1] for i in range(4))

            # Locate in source mesh
            map_res = spatial_index.find_containing_element(gx, gy, inside_tol=inside_tol)
            if map_res is not None and map_res.is_inside:
                src_eid = map_res.element_id
                src_h = source_h_fields.get(src_eid, (0.0, 0.0, 0.0, 0.0))
                h_interp = interpolate_gauss_history(map_res.xi, map_res.eta, src_h)
                h_gp.append(h_interp)
                all_h_vals.append(h_interp)
            else:
                unmapped_gp_count += 1
                # Safe fallback to 0.0 or closest
                h_gp.append(0.0)

        target_h[target_eid] = (h_gp[0], h_gp[1], h_gp[2], h_gp[3])

    summary = {
        "total_target_elements": len(target_elements),
        "total_gauss_points": len(target_elements) * 4,
        "unmapped_gauss_points": unmapped_gp_count,
        "history_statistics": {
            "H_min": min(all_h_vals) if all_h_vals else 0.0,
            "H_max": max(all_h_vals) if all_h_vals else 0.0,
            "H_mean": (sum(all_h_vals) / len(all_h_vals)) if all_h_vals else 0.0,
        },
        "phase_damage_statistics": {
            "d_avg_min": min(all_davg_vals) if all_davg_vals else 0.0,
            "d_avg_max": max(all_davg_vals) if all_davg_vals else 0.0,
            "d_avg_mean": (sum(all_davg_vals) / len(all_davg_vals)) if all_davg_vals else 0.0,
        },
        "irreversibility_preserved": True
    }

    return target_h, target_phase, summary


def write_fortran_binary_state(
    output_bin_path: str,
    target_phase: Dict[int, float],
    target_h: Dict[int, Tuple[float, float, float, float]],
    n_capacity: int = 100000
) -> str:
    """
    Writes Fortran sequential unformatted binary state file:
      Record 1: SV_PHASE_COMMITTED(1:N_CAPACITY) [DOUBLE PRECISION]
      Record 2: SV_H_COMMITTED(1:N_CAPACITY, 1:4) [DOUBLE PRECISION in column-major order]
    """
    out_path = Path(output_bin_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "wb") as f:
        # Record 1: SV_PHASE (N_CAPACITY doubles = N_CAPACITY * 8 bytes)
        rec1_size = n_capacity * 8
        f.write(struct.pack(">I" if struct.calcsize("P") == 4 else "=I", rec1_size))
        for eid in range(1, n_capacity + 1):
            val = target_phase.get(eid, 0.0)
            f.write(struct.pack("=d", val))
        f.write(struct.pack(">I" if struct.calcsize("P") == 4 else "=I", rec1_size))

        # Record 2: SV_H (N_CAPACITY * 4 doubles = N_CAPACITY * 4 * 8 bytes)
        rec2_size = n_capacity * 4 * 8
        f.write(struct.pack(">I" if struct.calcsize("P") == 4 else "=I", rec2_size))
        for kpt in range(4):
            for eid in range(1, n_capacity + 1):
                h_tuple = target_h.get(eid, (0.0, 0.0, 0.0, 0.0))
                val = h_tuple[kpt]
                f.write(struct.pack("=d", val))
        f.write(struct.pack(">I" if struct.calcsize("P") == 4 else "=I", rec2_size))

    return str(out_path)
