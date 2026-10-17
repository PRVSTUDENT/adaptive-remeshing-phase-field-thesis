"""
Experimental Bilinear Gauss-Point History Transfer Operator for Mode-I Phase-Field Remeshing.

Audited against published state-transfer frameworks:
- Tao Jin et al. (deal.II / L-BFGS, DOI: 10.1002/nme.7572): L2-projection of quadrature history
  onto local polynomial Discontinuous Galerkin (FE_DGQ) space.
- Aarosh Dahal et al. (FEniCSx AMR/C, arXiv:2609.21201): Variational inequality nodal bound transfer.

This module provides an isolated, drop-in alternative to the 0th-order HOST_NEAREST_GP operator
without modifying production code or the frozen UEL Fortran source.
"""

from __future__ import annotations
import math
from typing import List, Tuple, Dict, Optional, Any

SQRT3 = math.sqrt(3.0)
GAUSS_XI_QUAD = [-1.0 / SQRT3, 1.0 / SQRT3, 1.0 / SQRT3, -1.0 / SQRT3]
GAUSS_ETA_QUAD = [-1.0 / SQRT3, -1.0 / SQRT3, 1.0 / SQRT3, 1.0 / SQRT3]

def evaluate_bilinear_quad_history(
    H_donor_gps: List[float],
    xi: float,
    eta: float,
    bounded: bool = False
) -> float:
    """
    Evaluates smooth bilinear interpolation of history variable H at parent coordinates (xi, eta)
    from the 4 donor Gauss point values.
    
    The interpolation polynomials phi_k(xi, eta) are the unique bilinear functions satisfying
    phi_k(xi_j, eta_j) = delta_{kj} at the 2x2 Gauss points:
        phi_k(xi, eta) = 0.25 * (1 + 3.0 * xi_k * xi) * (1 + 3.0 * eta_k * eta)
    """
    if len(H_donor_gps) != 4:
        raise ValueError(f"Expected 4 Gauss point values for quad, got {len(H_donor_gps)}")
    
    # Evaluate bilinear polynomial through 2x2 Gauss points
    H_val = 0.0
    for k in range(4):
        phi_k = 0.25 * (1.0 + 3.0 * GAUSS_XI_QUAD[k] * xi) * (1.0 + 3.0 * GAUSS_ETA_QUAD[k] * eta)
        H_val += phi_k * H_donor_gps[k]
        
    # Thermodynamic non-negativity constraint: H >= 0
    H_val = max(0.0, float(H_val))
    
    # Optional slope-limiting bounds: min(H_k) <= H <= max(H_k)
    if bounded:
        min_h = min(H_donor_gps)
        max_h = max(H_donor_gps)
        H_val = max(min_h, min(max_h, H_val))
        
    return H_val

def evaluate_nearest_gp_history(
    H_donor_gps: List[float],
    donor_gp_coords: List[Tuple[float, float, float]],
    target_x: float,
    target_y: float
) -> float:
    """
    Standard production 0th-order nearest-neighbor Gauss point assignment.
    """
    best_k = 0
    min_dist2 = 1e9
    for k, (dgx, dgy, _) in enumerate(donor_gp_coords):
        dist2 = (dgx - target_x)**2 + (dgy - target_y)**2
        if dist2 < min_dist2:
            min_dist2 = dist2
            best_k = k
    return max(0.0, float(H_donor_gps[best_k]))

class BilinearHistoryTransferOperator:
    """
    Isolated experimental state-transfer operator implementing smooth bilinear
    quadrature history interpolation alongside standard nearest-neighbor transfer.
    """
    def __init__(self, mode: str = "BILINEAR_GP_BOUNDED"):
        """
        mode options:
        - "NEAREST_GP": standard production 0th-order baseline
        - "BILINEAR_GP": unbounded smooth bilinear interpolation (clamped H >= 0)
        - "BILINEAR_GP_BOUNDED": slope-limited bilinear interpolation (preserves local bounds)
        """
        if mode not in ("NEAREST_GP", "BILINEAR_GP", "BILINEAR_GP_BOUNDED"):
            raise ValueError(f"Unknown transfer mode: {mode}")
        self.mode = mode

    def transfer_element_history(
        self,
        donor_conn_len: int,
        H_donor_gps: List[float],
        donor_gp_coords: List[Tuple[float, float, float]],
        target_x: float,
        target_y: float,
        host_xi: float,
        host_eta: float
    ) -> float:
        """
        Transfers history variable to a recipient quadrature point (target_x, target_y)
        with parent coordinates (host_xi, host_eta) in the donor element.
        """
        # For triangular donor elements (1 Gauss point), constant transfer is exact
        if donor_conn_len == 3 or len(H_donor_gps) == 1:
            return max(0.0, float(H_donor_gps[0]))
        
        if self.mode == "NEAREST_GP":
            return evaluate_nearest_gp_history(H_donor_gps, donor_gp_coords, target_x, target_y)
        elif self.mode == "BILINEAR_GP":
            return evaluate_bilinear_quad_history(H_donor_gps, host_xi, host_eta, bounded=False)
        elif self.mode == "BILINEAR_GP_BOUNDED":
            return evaluate_bilinear_quad_history(H_donor_gps, host_xi, host_eta, bounded=True)
        else:
            raise ValueError(f"Unhandled mode: {self.mode}")
