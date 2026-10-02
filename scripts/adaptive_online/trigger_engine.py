#!/usr/bin/env python3
"""
Adaptive Remeshing Trigger Engine.
Evaluates multi-criteria triggers (TR-01, TR-02, TR-03, TR-04) with rigorous
scientific classifications, conservative element-size metrics, and reconciled
Pandey & Kumar (2025) recovery-error indicators.

Scientific Governance Classifications:
- Resolution limit h <= l0/2 is the ADOPTED_PHASE_FIELD_RESOLUTION_SIZING_RULE,
  not an unconditional mathematical convergence guarantee.
- TR-01 (d_invade = 0.05) is classified as PROVISIONAL_AUTOMATION_TRIGGER_REQUIRING_CALIBRATION.
- TR-02 (buffer = 2.0*l0, d_crack_core = 0.30) is classified as PROVISIONAL_AUTOMATION_TRIGGER_REQUIRING_CALIBRATION.
  Note: d_crack_core = 0.30 is the pre-peak non-linear process-zone threshold where proximity checks
  fire before full crack bifurcation (d >= 0.50).
- TR-03 (MISESERI / max(MISESERI) > 0.05) is the RECONCILED_PANDEY_KUMAR_2025_RECOVERY_INDICATOR.
- TR-04 is DIMENSIONLESS_LOCAL_PHASE_GRADIENT_INDICATOR (disabled by default).
"""

import math
from typing import Dict, List, Tuple, Optional, Any, NamedTuple


class TriggerResult(NamedTuple):
    remesh_required: bool
    fired_triggers: List[str]
    metrics: Dict[str, Any]
    refined_zone: Dict[str, float]
    rationale: str
    classifications: Dict[str, str]


def compute_signed_polygon_area(coords: List[Tuple[float, float]]) -> float:
    """Computes signed 2D area using shoelace formula."""
    n = len(coords)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1] - coords[j][0] * coords[i][1]
    return 0.5 * area


def compute_element_metrics(
    nodes: Dict[int, Tuple[float, float]],
    elements: Dict[int, Tuple[int, ...]]
) -> Dict[int, Dict[str, float]]:
    """
    Computes conservative geometric element metrics:
      - h_mean: mean edge length
      - h_max: maximum edge length (conservative characteristic size for anisotropic elements)
      - h_min: minimum edge length
      - h_area: sqrt(abs(Area))
      - area: signed element area
    """
    metrics: Dict[int, Dict[str, float]] = {}
    for eid, conn in elements.items():
        coords = [nodes[n] for n in conn if n in nodes]
        n_pts = len(coords)
        if n_pts < 3:
            metrics[eid] = {
                "h_mean": 0.025,
                "h_max": 0.025,
                "h_min": 0.025,
                "h_area": 0.025,
                "area": 0.000625
            }
            continue

        edges = []
        for i in range(n_pts):
            p0 = coords[i]
            p1 = coords[(i + 1) % n_pts]
            edges.append(math.hypot(p1[0] - p0[0], p1[1] - p0[1]))

        area = compute_signed_polygon_area(coords)
        h_area = math.sqrt(abs(area)) if abs(area) > 1e-14 else 0.0
        h_mean = sum(edges) / float(n_pts)
        h_max = max(edges)
        h_min = min(edges)

        metrics[eid] = {
            "h_mean": h_mean,
            "h_max": h_max,
            "h_min": h_min,
            "h_area": h_area,
            "area": area
        }
    return metrics


def evaluate_adaptive_triggers(
    nodes: Dict[int, Tuple[float, float]],
    elements: Dict[int, Tuple[int, ...]],
    nodal_phase: Dict[int, float],
    miseseri: Optional[Dict[int, float]] = None,
    l0: float = 0.015,
    d_invade_threshold: float = 0.05,
    d_crack_core: float = 0.30,
    buffer_multiplier: float = 2.0,
    min_element_size: float = 0.005,
    global_element_size: float = 0.025,
    current_u1: float = 0.0,
    final_u1: float = 0.050,
    enable_tr04: bool = False
) -> TriggerResult:
    """
    Evaluates multi-criteria adaptive remeshing triggers and calculates refined corridor bounds.
    """
    elem_metrics = compute_element_metrics(nodes, elements)
    # Working phase-field resolution sizing design rule: h <= l0/2
    h_res_limit = l0 / 2.0  # 0.0075 mm for l0=0.015 mm

    fired_triggers: List[str] = []
    
    # --------------------------------------------------------------------------
    # 1. Evaluate TR-01: Coarse-Element Damage Invasion
    # --------------------------------------------------------------------------
    # Uses conservative characteristic size h_max so elongated elements cannot hide under-resolution
    max_d_in_coarse = 0.0
    violating_coarse_elems: List[int] = []
    coarse_elem_count = 0

    for eid, conn in elements.items():
        m = elem_metrics.get(eid, {})
        h_char = m.get("h_max", global_element_size)
        if h_char > h_res_limit + 1e-6:
            coarse_elem_count += 1
            d_vals = [nodal_phase.get(nid, 0.0) for nid in conn]
            if d_vals:
                d_elem_max = max(d_vals)
                if d_elem_max > max_d_in_coarse:
                    max_d_in_coarse = d_elem_max
                if d_elem_max >= d_invade_threshold:
                    violating_coarse_elems.append(eid)

    if max_d_in_coarse >= d_invade_threshold:
        fired_triggers.append("TR-01_COARSE_DAMAGE_INVASION")

    # --------------------------------------------------------------------------
    # 2. Evaluate TR-02: Buffer Zone Proximity
    # --------------------------------------------------------------------------
    # d_crack_core = 0.30 marks the non-linear process zone core nodes
    core_nodes = [nid for nid, d in nodal_phase.items() if d >= d_crack_core and nid in nodes]
    coarse_elem_nodes = set()
    for eid, conn in elements.items():
        m = elem_metrics.get(eid, {})
        if m.get("h_max", global_element_size) > h_res_limit + 1e-6:
            for n in conn:
                coarse_elem_nodes.add(n)

    min_buffer_dist = float("inf")
    if core_nodes and coarse_elem_nodes:
        for cn in core_nodes:
            cx, cy = nodes[cn]
            for csen in coarse_elem_nodes:
                csx, csy = nodes[csen]
                dist = math.hypot(cx - csx, cy - csy)
                if dist < min_buffer_dist:
                    min_buffer_dist = dist

    buffer_threshold = buffer_multiplier * l0
    if min_buffer_dist <= buffer_threshold:
        fired_triggers.append("TR-02_BUFFER_ZONE_BREACH")

    # --------------------------------------------------------------------------
    # 3. Evaluate TR-03: Stress Recovery Error Indicator (Pandey & Kumar 2025)
    # --------------------------------------------------------------------------
    max_miseseri = 0.0
    miseseri_marked_count = 0
    if miseseri:
        m_vals = [v for v in miseseri.values() if v is not None and v > 0]
        if m_vals:
            max_miseseri = max(m_vals)
            for eid, m_val in miseseri.items():
                # Reconciled Stage-C relative error indicator: normalized to peak recovery indicator
                if (m_val / max_miseseri) > 0.05:
                    miseseri_marked_count += 1
                    m = elem_metrics.get(eid, {})
                    if m.get("h_max", global_element_size) > h_res_limit:
                        if "TR-03_STRESS_RECOVERY_INDICATOR" not in fired_triggers:
                            fired_triggers.append("TR-03_STRESS_RECOVERY_INDICATOR")

    # --------------------------------------------------------------------------
    # 4. Evaluate TR-04: Dimensionless Local Phase Gradient (Disabled by default)
    # --------------------------------------------------------------------------
    max_grad_d_norm = 0.0
    if enable_tr04:
        for eid, conn in elements.items():
            coords = [nodes[n] for n in conn if n in nodes]
            d_vals = [nodal_phase.get(n, 0.0) for n in conn if n in nodes]
            if len(coords) >= 4 and len(d_vals) >= 4:
                # Approximate grad d in element
                dx = coords[1][0] - coords[0][0]
                dy = coords[3][1] - coords[0][1]
                if abs(dx) > 1e-7 and abs(dy) > 1e-7:
                    dd_dx = (d_vals[1] - d_vals[0] + d_vals[2] - d_vals[3]) / (2.0 * dx)
                    dd_dy = (d_vals[3] - d_vals[0] + d_vals[2] - d_vals[1]) / (2.0 * dy)
                    grad_mag = math.hypot(dd_dx, dd_dy)
                    h_e = elem_metrics[eid]["h_max"]
                    # Dimensionless jump / local variation metric
                    dimless_var = (h_e * grad_mag) / max(l0, 1e-6)
                    if dimless_var > max_grad_d_norm:
                        max_grad_d_norm = dimless_var
                    if dimless_var > 0.50 and h_e > h_res_limit:
                        if "TR-04_LOCAL_PHASE_GRADIENT" not in fired_triggers:
                            fired_triggers.append("TR-04_LOCAL_PHASE_GRADIENT")

    # --------------------------------------------------------------------------
    # 5. Compute Refined Bounding Box Corridor
    # --------------------------------------------------------------------------
    # Core damaged region (d >= 0.02)
    damaged_pts = [nodes[nid] for nid, d in nodal_phase.items() if d >= 0.02 and nid in nodes]
    
    # Always include initial notch tip region [-0.02, 0.05] x [-0.02, 0.02]
    all_x = [-0.02, 0.05] + [p[0] for p in damaged_pts]
    all_y = [-0.02, 0.02] + [p[1] for p in damaged_pts]

    # Add forward propagation lead padding
    pad_x_back = 2.0 * l0
    pad_x_forward = 4.0 * l0
    pad_y = 3.0 * l0

    x_min_ref = max(-0.5, min(all_x) - pad_x_back)
    x_max_ref = min(0.5, max(all_x) + pad_x_forward)
    y_min_ref = max(-0.5, min(all_y) - pad_y)
    y_max_ref = min(0.5, max(all_y) + pad_y)

    refined_zone = {
        "x_min": x_min_ref,
        "x_max": x_max_ref,
        "y_min": y_min_ref,
        "y_max": y_max_ref,
        "area": (x_max_ref - x_min_ref) * (y_max_ref - y_min_ref),
        "target_h": min_element_size
    }

    remesh_required = len(fired_triggers) > 0

    if remesh_required:
        rationale = (
            f"Remeshing triggered by {fired_triggers}. "
            f"Max d in coarse grid (h_max > {h_res_limit:.4f} mm) = {max_d_in_coarse:.4f} "
            f"(provisional threshold = {d_invade_threshold:.4f}), "
            f"buffer distance to coarse elements = {min_buffer_dist:.4f} mm "
            f"(provisional limit = {buffer_threshold:.4f} mm)."
        )
    else:
        rationale = (
            f"No remeshing required. Phase field is contained within fine elements (h_max <= {h_res_limit:.4f} mm). "
            f"Max d in coarse elements = {max_d_in_coarse:.4f} < {d_invade_threshold:.4f}."
        )

    classifications = {
        "h_res_limit_rule": "ADOPTED_PHASE_FIELD_RESOLUTION_SIZING_RULE",
        "tr01_classification": "PROVISIONAL_AUTOMATION_TRIGGER_REQUIRING_CALIBRATION",
        "tr02_classification": "PROVISIONAL_AUTOMATION_TRIGGER_REQUIRING_CALIBRATION",
        "tr03_classification": "RECONCILED_PANDEY_KUMAR_2025_RECOVERY_INDICATOR",
        "tr04_classification": "DIMENSIONLESS_LOCAL_PHASE_GRADIENT_INDICATOR_DISABLED",
        "characteristic_size_metric": "CONSERVATIVE_H_MAX_AND_H_AREA"
    }

    metrics = {
        "max_d_in_coarse_elements": max_d_in_coarse,
        "d_invade_threshold": d_invade_threshold,
        "d_crack_core_threshold": d_crack_core,
        "coarse_element_count": coarse_elem_count,
        "violating_coarse_element_count": len(violating_coarse_elems),
        "min_buffer_distance_mm": min_buffer_dist if min_buffer_dist != float("inf") else -1.0,
        "buffer_threshold_mm": buffer_threshold,
        "max_miseseri": max_miseseri,
        "miseseri_marked_count": miseseri_marked_count,
        "current_u1_mm": current_u1,
        "final_u1_mm": final_u1,
        "damaged_node_count_gt_002": len(damaged_pts),
        "core_node_count_gt_dcore": len(core_nodes),
        "tr04_enabled": enable_tr04,
        "max_grad_d_norm": max_grad_d_norm
    }

    return TriggerResult(
        remesh_required=remesh_required,
        fired_triggers=fired_triggers,
        metrics=metrics,
        refined_zone=refined_zone,
        rationale=rationale,
        classifications=classifications
    )
