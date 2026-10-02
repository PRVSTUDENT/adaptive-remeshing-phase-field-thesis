#!/usr/bin/env python3
"""
Geometric Search and Inverse Isoparametric Mapping Engine:
Provides spatial indexing, bounding boxes, point-in-element testing, and
Newton-Raphson inverse isoparametric mapping for 2D 4-node quadrilaterals (QUAD4)
and 3-node triangles (TRI3).
Enhanced with topology-aware slit barrier candidate filtering.
"""

import math
from typing import List, Tuple, Dict, Optional, NamedTuple


class MappingResult(NamedTuple):
    element_id: int
    element_type: str
    node_ids: Tuple[int, ...]
    xi: float
    eta: float
    weights: Tuple[float, ...]
    residual: float
    is_inside: bool
    is_boundary: bool


def quad4_shape_functions(xi: float, eta: float) -> Tuple[float, float, float, float]:
    """Evaluates standard 4-node bilinear quad shape functions in [-1, 1] x [-1, 1]."""
    n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
    n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
    n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
    n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
    return (n1, n2, n3, n4)


def quad4_shape_derivatives(xi: float, eta: float) -> Tuple[Tuple[float, float, float, float], Tuple[float, float, float, float]]:
    """Evaluates derivatives of shape functions w.r.t. (xi, eta)."""
    # dN/dxi
    dn_dxi = (
        -0.25 * (1.0 - eta),
         0.25 * (1.0 - eta),
         0.25 * (1.0 + eta),
        -0.25 * (1.0 + eta)
    )
    # dN/deta
    dn_deta = (
        -0.25 * (1.0 - xi),
        -0.25 * (1.0 + xi),
         0.25 * (1.0 + xi),
         0.25 * (1.0 - xi)
    )
    return (dn_dxi, dn_deta)


def inverse_isoparametric_quad4(
    target_x: float,
    target_y: float,
    node_coords: List[Tuple[float, float]],
    tol: float = 1e-10,
    max_iter: int = 25
) -> Optional[Tuple[float, float, float]]:
    """
    Computes natural coordinates (xi, eta) within a 4-node quadrilateral using
    a 2x2 Newton-Raphson iteration.
    Returns: (xi, eta, residual_norm) or None if non-convergent.
    """
    if len(node_coords) != 4:
        raise ValueError("QUAD4 requires exactly 4 node coordinates")

    # Initial guess: centroid (0, 0)
    xi, eta = 0.0, 0.0

    for iteration in range(max_iter):
        n = quad4_shape_functions(xi, eta)
        # Current physical coordinate estimate
        x_est = sum(n[i] * node_coords[i][0] for i in range(4))
        y_est = sum(n[i] * node_coords[i][1] for i in range(4))

        # Residual vector
        rx = x_est - target_x
        ry = y_est - target_y
        res_norm = math.hypot(rx, ry)

        if res_norm < tol:
            return (xi, eta, res_norm)

        # Jacobian matrix: J = d(x,y)/d(xi,eta)
        dn_dxi, dn_deta = quad4_shape_derivatives(xi, eta)
        j11 = sum(dn_dxi[i] * node_coords[i][0] for i in range(4))
        j12 = sum(dn_deta[i] * node_coords[i][0] for i in range(4))
        j21 = sum(dn_dxi[i] * node_coords[i][1] for i in range(4))
        j22 = sum(dn_deta[i] * node_coords[i][1] for i in range(4))

        det_j = j11 * j22 - j12 * j21
        if abs(det_j) < 1e-15:
            # Degenerate element
            break

        # Solve J * [dxi, deta]^T = -[rx, ry]^T
        inv_j11 =  j22 / det_j
        inv_j12 = -j12 / det_j
        inv_j21 = -j21 / det_j
        inv_j22 =  j11 / det_j

        dxi = -(inv_j11 * rx + inv_j12 * ry)
        deta = -(inv_j21 * rx + inv_j22 * ry)

        xi += dxi
        eta += deta

        if math.hypot(dxi, deta) < tol:
            # Compute final residual
            n_final = quad4_shape_functions(xi, eta)
            xf = sum(n_final[i] * node_coords[i][0] for i in range(4))
            yf = sum(n_final[i] * node_coords[i][1] for i in range(4))
            return (xi, eta, math.hypot(xf - target_x, yf - target_y))

    # Return best estimate with residual
    n_final = quad4_shape_functions(xi, eta)
    xf = sum(n_final[i] * node_coords[i][0] for i in range(4))
    yf = sum(n_final[i] * node_coords[i][1] for i in range(4))
    return (xi, eta, math.hypot(xf - target_x, yf - target_y))


def barycentric_triangle(
    target_x: float,
    target_y: float,
    node_coords: List[Tuple[float, float]]
) -> Tuple[float, float, float, float]:
    """
    Computes barycentric coordinates (lambda1, lambda2, lambda3) for a 3-node triangle.
    Returns: (l1, l2, l3, residual)
    """
    (x1, y1), (x2, y2), (x3, y3) = node_coords
    det_t = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
    if abs(det_t) < 1e-15:
        return (0.0, 0.0, 0.0, 999.0)

    l1 = ((y2 - y3) * (target_x - x3) + (x3 - x2) * (target_y - y3)) / det_t
    l2 = ((y3 - y1) * (target_x - x3) + (x1 - x3) * (target_y - y3)) / det_t
    l3 = 1.0 - l1 - l2

    # Residual
    x_rec = l1 * x1 + l2 * x2 + l3 * x3
    y_rec = l1 * y1 + l2 * y2 + l3 * y3
    residual = math.hypot(x_rec - target_x, y_rec - target_y)
    return (l1, l2, l3, residual)


class SpatialGridIndex:
    """
    High-performance 2D spatial binning index for candidate element pre-filtering.
    Supports both 4-node quadrilaterals (QUAD4) and 3-node triangles (TRI3).
    Includes topology-aware slit barrier candidate filtering.
    """

    def __init__(self, elements: Dict[int, Tuple[int, ...]], nodes: Dict[int, Tuple[float, float]], cell_size: float = 0.05):
        self.elements = elements
        self.nodes = nodes
        self.cell_size = cell_size
        self.grid: Dict[Tuple[int, int], List[int]] = {}
        self.elem_bboxes: Dict[int, Tuple[float, float, float, float]] = {}
        self.elem_flanks: Dict[int, int] = {}
        self._build_index()

    def _build_index(self):
        for elem_id, node_ids in self.elements.items():
            pts = [self.nodes[nid] for nid in node_ids]
            min_x = min(p[0] for p in pts)
            max_x = max(p[0] for p in pts)
            min_y = min(p[1] for p in pts)
            max_y = max(p[1] for p in pts)
            self.elem_bboxes[elem_id] = (min_x, max_x, min_y, max_y)

            # Determine donor element topological flank based on centroid
            cy = sum(p[1] for p in pts) / len(pts)
            if cy < -1e-7:
                self.elem_flanks[elem_id] = -1 # LOWER FLANK
            elif cy > 1e-7:
                self.elem_flanks[elem_id] = 1  # UPPER FLANK
            else:
                self.elem_flanks[elem_id] = 0  # CONTINUUM / STRADDLE

            # Binning
            i_min = int(math.floor(min_x / self.cell_size))
            i_max = int(math.floor(max_x / self.cell_size))
            j_min = int(math.floor(min_y / self.cell_size))
            j_max = int(math.floor(max_y / self.cell_size))

            for i in range(i_min, i_max + 1):
                for j in range(j_min, j_max + 1):
                    cell = (i, j)
                    if cell not in self.grid:
                        self.grid[cell] = []
                    self.grid[cell].append(elem_id)

    def query_point(self, x: float, y: float, target_flank: Optional[int] = None) -> List[int]:
        """Returns candidate element IDs whose bounding boxes cover (x, y), filtered by topological flank."""
        i = int(math.floor(x / self.cell_size))
        j = int(math.floor(y / self.cell_size))
        candidates = self.grid.get((i, j), [])
        
        # Bounding box and flank filter
        matched = []
        for eid in candidates:
            min_x, max_x, min_y, max_y = self.elem_bboxes[eid]
            if (min_x - 1e-7) <= x <= (max_x + 1e-7) and (min_y - 1e-7) <= y <= (max_y + 1e-7):
                if target_flank is not None and target_flank != 0:
                    eflank = self.elem_flanks.get(eid, 0)
                    if eflank != 0 and eflank != target_flank:
                        continue # Skip donor element from opposite flank
                matched.append(eid)
        return matched

    def find_containing_element(
        self,
        x: float,
        y: float,
        inside_tol: float = 1e-6,
        target_flank: Optional[int] = None
    ) -> Optional[MappingResult]:
        """
        Finds the unique containing element for point (x, y), solves inverse
        isoparametric coordinates, and applies deterministic tie-breaking for boundaries.
        Enforces topological flank filtering across slit boundaries.
        """
        candidates = self.query_point(x, y, target_flank=target_flank)
        best_result = None

        # Deterministic sort of candidates by element ID
        candidates.sort()

        for eid in candidates:
            node_ids = self.elements[eid]
            coords = [self.nodes[nid] for nid in node_ids]
            
            if len(node_ids) == 4:
                res = inverse_isoparametric_quad4(x, y, coords)
                if res is not None:
                    xi, eta, residual = res
                    is_inside = (-1.0 - inside_tol <= xi <= 1.0 + inside_tol) and (-1.0 - inside_tol <= eta <= 1.0 + inside_tol)
                    is_boundary = (abs(abs(xi) - 1.0) < inside_tol) or (abs(abs(eta) - 1.0) < inside_tol)
                    
                    if is_inside:
                        xi_c = max(-1.0, min(1.0, xi))
                        eta_c = max(-1.0, min(1.0, eta))
                        weights = quad4_shape_functions(xi_c, eta_c)
                        return MappingResult(
                            element_id=eid,
                            element_type="QUAD4",
                            node_ids=node_ids,
                            xi=xi_c,
                            eta=eta_c,
                            weights=weights,
                            residual=residual,
                            is_inside=True,
                            is_boundary=is_boundary
                        )
            elif len(node_ids) == 3:
                l1, l2, l3, residual = barycentric_triangle(x, y, coords)
                is_inside = (l1 >= -inside_tol and l2 >= -inside_tol and l3 >= -inside_tol)
                is_boundary = (abs(l1) < inside_tol or abs(l2) < inside_tol or abs(l3) < inside_tol)
                if is_inside:
                    l1_c = max(0.0, min(1.0, l1))
                    l2_c = max(0.0, min(1.0, l2))
                    l3_c = max(0.0, min(1.0, l3))
                    s = l1_c + l2_c + l3_c
                    weights = (l1_c/s, l2_c/s, l3_c/s)
                    return MappingResult(
                        element_id=eid,
                        element_type="TRI3",
                        node_ids=node_ids,
                        xi=l1_c,
                        eta=l2_c,
                        weights=weights,
                        residual=residual,
                        is_inside=True,
                        is_boundary=is_boundary
                    )

        return best_result
