"""
Authoritative Mode-I Spatial Convergence Post-Processing Pipeline
Protocol Version: 2
Governing Directive: "We need to have understood everything related to the first model before we increase complexity."

This module implements the frozen methodology for evaluating multi-quantity spatial convergence
across discretizations S1 -> S2 -> S3 -> S4 -> S5 before S2/S3 results exist:

1. Matched-Displacement Checkpoints:
   u in {0.0010, 0.0050, 0.005857, 0.0060, 0.0062, 0.0065, 0.0070, 0.0100} mm.
2. Interpolation and Permissible Bracketing:
   Linear interpolation between adjacent bracketing frames.
   Explicit error / CENSORED status when u_target exceeds the final converged frame (NEVER extrapolate).
3. Common-Domain L2 Curve Discrepancy:
   Evaluated strictly over the common converged displacement interval [0, min(u_max1, u_max2)].
   Normalized L2 norm for F-u, E_elas(u), E_frac(u), E_model(u), W_ext(u), and Delta_book(u).
4. Spatial Damage Profile d(x, y=0.5):
   Interpolation onto uniform reproducible ligament grid x in [0.500, 1.000] mm.
   Normalized L2 profile difference over common ligament domain.
5. Crack Path Extraction:
   Location of dominant damage ridge y_ridge(x) = argmax_y d(x, y) and deviation from symmetry plane y=0.5 mm.
6. Mechanical Anchors:
   K0 (linear regression on u <= 0.0010 mm, canonical K0 = 137.945520 kN/mm), F_max, u_peak.
7. Successive-Resolution Relative Differences:
   delta_n(phi) = |phi(S_n) - phi(S_{n-1})| / max(|phi(S_{n-1})|, 1e-12) under TREND_ONLY governance.
8. Explicit Energy Units:
   Simultaneous kN*mm (= J) and mJ reporting (1 kN*mm = 1000.0 mJ).
"""

import math
import numpy as np

# Canonical matched-displacement evaluation points [mm]
CANONICAL_MATCHED_DISPLACEMENTS_MM = [
    0.0010,
    0.0050,
    0.005857,
    0.0060,
    0.0062,
    0.0065,
    0.0070,
    0.0100
]

CANONICAL_REFERENCE_K0_KN_PER_MM = 137.945520
CANONICAL_REFERENCE_FMAX_KN = 0.757778
CANONICAL_REFERENCE_UPEAK_MM = 0.005857

class CensoredTrajectoryError(Exception):
    """Raised when a requested checkpoint lies beyond the final converged solver frame."""
    pass

class MissingFieldOutputError(Exception):
    """Raised when an expected field output (e.g. SDV17, SDV18) is completely absent from the data."""
    pass

class ZeroDomainOverlapError(Exception):
    """Raised when two comparison trajectories have zero common displacement overlap."""
    pass


def _trapezoid(y, x=None, dx=1.0):
    """NumPy 1.x and 2.x compatible trapezoidal integration."""
    if hasattr(np, 'trapezoid'):
        if x is not None:
            return np.trapezoid(y, x=x)
        return np.trapezoid(y, dx=dx)
    else:
        if x is not None:
            return np.trapz(y, x=x)
        return np.trapz(y, dx=dx)


def linear_regression_k0(u_vals, f_vals, u_cutoff=0.0010):
    """
    Computes initial structural stiffness K0, intercept, and R^2 on the elastic range u <= u_cutoff.
    Matches the exact reference extraction procedure.
    """
    u_fit = []
    f_fit = []
    for u, f in zip(u_vals, f_vals):
        if u <= u_cutoff + 1e-8:
            u_fit.append(float(u))
            f_fit.append(float(f))
            
    n = len(u_fit)
    if n < 2:
        raise ValueError("Insufficient points (n < 2) in elastic range u <= %g mm" % u_cutoff)
        
    sum_x = sum(u_fit)
    sum_y = sum(f_fit)
    sum_xx = sum(x * x for x in u_fit)
    sum_yy = sum(y * y for y in f_fit)
    sum_xy = sum(x * y for x, y in zip(u_fit, f_fit))
    
    denom = n * sum_xx - sum_x * sum_x
    if abs(denom) < 1e-24:
        raise ValueError("Degenerate displacement variance in elastic range.")
        
    k0 = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - k0 * sum_x) / n
    
    ss_tot = sum((y - (sum_y / n)) ** 2 for y in f_fit)
    ss_res = sum((y - (k0 * x + intercept)) ** 2 for x, y in zip(u_fit, f_fit))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-24 else 1.0
    
    return {
        "K0_kN_per_mm": k0,
        "intercept_kN": intercept,
        "R2": r2,
        "N_points": n,
        "u_cutoff_mm": u_cutoff
    }


def interpolate_scalar_at_displacement(u_series, val_series, u_target, tol=1e-7):
    """
    Linearly interpolates a scalar variable at u_target from discrete (u, val) series.
    Strictly forbids extrapolation beyond the final converged frame (raises CensoredTrajectoryError).
    """
    if len(u_series) != len(val_series):
        raise ValueError("Length mismatch between u_series (%d) and val_series (%d)" % (len(u_series), len(val_series)))
    if len(u_series) == 0:
        raise ValueError("Empty trajectory provided.")
        
    u_arr = np.asarray(u_series, dtype=float)
    val_arr = np.asarray(val_series, dtype=float)
    
    u_min = u_arr[0]
    u_max = u_arr[-1]
    
    # Exact frame match within numerical tolerance
    exact_idx = np.where(np.abs(u_arr - u_target) <= tol)[0]
    if len(exact_idx) > 0:
        return float(val_arr[exact_idx[0]])
        
    # Check bounds
    if u_target < u_min - tol:
        raise ValueError("Requested u_target=%g mm is below initial displacement u_min=%g mm" % (u_target, u_min))
        
    if u_target > u_max + tol:
        raise CensoredTrajectoryError(
            "CENSORED: Requested displacement u=%g mm exceeds final converged frame u_final=%g mm. Extrapolation forbidden."
            % (u_target, u_max)
        )
        
    # Find bracketing interval [u_k, u_{k+1}]
    idx = np.searchsorted(u_arr, u_target)
    if idx == 0:
        return float(val_arr[0])
    if idx >= len(u_arr):
        return float(val_arr[-1])
        
    u0 = u_arr[idx - 1]
    u1 = u_arr[idx]
    v0 = val_arr[idx - 1]
    v1 = val_arr[idx]
    
    if abs(u1 - u0) < 1e-20:
        return float(v0)
        
    # Linear interpolation
    frac = (u_target - u0) / (u1 - u0)
    return float(v0 + frac * (v1 - v0))


def extract_matched_displacement_checkpoints(trajectory_dict, u_checkpoints=None):
    """
    Extracts canonical mechanical and energetic variables at discrete matched displacement checkpoints.
    Trajectory dict must supply arrays:
      - 'u_mm': displacement history
      - 'rf_kN': reaction force history
      - 'e_elas_kNmm': stored elastic strain energy
      - 'e_frac_kNmm': regularized surface energy
      - 'w_ext_kNmm': external work
    Returns a dictionary keyed by checkpoint displacement with status and values.
    """
    if u_checkpoints is None:
        u_checkpoints = CANONICAL_MATCHED_DISPLACEMENTS_MM
        
    u_series = trajectory_dict.get('u_mm')
    if u_series is None or len(u_series) == 0:
        raise ValueError("Trajectory missing required 'u_mm' array.")
        
    rf_series = trajectory_dict.get('rf_kN')
    if rf_series is None:
        raise ValueError("Trajectory missing required 'rf_kN' array.")
        
    e_elas_series = trajectory_dict.get('e_elas_kNmm')
    e_frac_series = trajectory_dict.get('e_frac_kNmm')
    w_ext_series = trajectory_dict.get('w_ext_kNmm')
    
    if e_elas_series is None or e_frac_series is None or w_ext_series is None:
        raise MissingFieldOutputError("Trajectory missing required energetic field outputs ('e_elas_kNmm', 'e_frac_kNmm', or 'w_ext_kNmm').")
        
    results = {}
    u_final = float(u_series[-1])
    
    for u_cp in u_checkpoints:
        cp_key = "%.6f" % u_cp
        if u_cp > u_final + 1e-7:
            results[cp_key] = {
                "u_target_mm": u_cp,
                "status": "CENSORED_BEYOND_ENDPOINT",
                "u_final_mm": u_final,
                "rf_kN": None,
                "e_elas_kNmm": None,
                "e_elas_mJ": None,
                "e_frac_kNmm": None,
                "e_frac_mJ": None,
                "e_model_kNmm": None,
                "e_model_mJ": None,
                "w_ext_kNmm": None,
                "w_ext_mJ": None,
                "delta_book_kNmm": None,
                "delta_book_mJ": None,
                "reldiff_signed_pct": None,
                "eps_book_pct": None
            }
            continue
            
        try:
            rf = interpolate_scalar_at_displacement(u_series, rf_series, u_cp)
            e_elas = interpolate_scalar_at_displacement(u_series, e_elas_series, u_cp)
            e_frac = interpolate_scalar_at_displacement(u_series, e_frac_series, u_cp)
            w_ext = interpolate_scalar_at_displacement(u_series, w_ext_series, u_cp)
            
            e_model = e_elas + e_frac
            delta_book = e_model - w_ext
            denom_signed = max(abs(w_ext), 1e-12)
            reldiff_signed = (delta_book / denom_signed) * 100.0
            
            denom_norm = max(abs(w_ext), abs(e_model), 1e-12)
            eps_book = (abs(delta_book) / denom_norm) * 100.0
            
            results[cp_key] = {
                "u_target_mm": u_cp,
                "status": "VALID",
                "u_final_mm": u_final,
                "rf_kN": rf,
                "e_elas_kNmm": e_elas,
                "e_elas_mJ": e_elas * 1000.0,
                "e_frac_kNmm": e_frac,
                "e_frac_mJ": e_frac * 1000.0,
                "e_model_kNmm": e_model,
                "e_model_mJ": e_model * 1000.0,
                "w_ext_kNmm": w_ext,
                "w_ext_mJ": w_ext * 1000.0,
                "delta_book_kNmm": delta_book,
                "delta_book_mJ": delta_book * 1000.0,
                "reldiff_signed_pct": reldiff_signed,
                "eps_book_pct": eps_book
            }
        except CensoredTrajectoryError:
            results[cp_key] = {
                "u_target_mm": u_cp,
                "status": "CENSORED_BEYOND_ENDPOINT",
                "u_final_mm": u_final,
                "rf_kN": None
            }
            
    return results


def compute_curve_l2_discrepancy(u_arr1, f_arr1, u_arr2, f_arr2, num_eval_points=1000):
    r"""
    Computes the normalized L2 curve discrepancy between two discrete trajectories
    strictly over their common converged displacement interval [u_min, u_max].
    
    eps_F = [ \int (F2 - F1)^2 du ]^(1/2) / [ \int F1^2 du ]^(1/2)
    """
    u1 = np.asarray(u_arr1, dtype=float)
    f1 = np.asarray(f_arr1, dtype=float)
    u2 = np.asarray(u_arr2, dtype=float)
    f2 = np.asarray(f_arr2, dtype=float)
    
    u_start = max(u1[0], u2[0])
    u_end = min(u1[-1], u2[-1])
    
    if u_end <= u_start + 1e-12:
        raise ZeroDomainOverlapError(
            "Common displacement interval is empty: u_start=%g mm, u_end=%g mm." % (u_start, u_end)
        )
        
    common_grid = np.linspace(u_start, u_end, num_eval_points)
    
    # Linear interpolation on common grid
    f1_interp = np.interp(common_grid, u1, f1)
    f2_interp = np.interp(common_grid, u2, f2)
    
    du = (u_end - u_start) / (num_eval_points - 1)
    diff_sq = (f2_interp - f1_interp) ** 2
    f1_sq = f1_interp ** 2
    
    # Trapezoidal quadrature (NumPy 1.x / 2.x compatible)
    l2_diff = math.sqrt(float(_trapezoid(diff_sq, dx=du)))
    l2_base = math.sqrt(float(_trapezoid(f1_sq, dx=du)))
    
    denom = max(l2_base, 1e-12)
    rel_l2_pct = (l2_diff / denom) * 100.0
    
    # Pointwise relative differences along common grid
    pointwise_denom = np.maximum(np.abs(f1_interp), 1e-12)
    pointwise_reldiff_pct = np.abs(f2_interp - f1_interp) / pointwise_denom * 100.0
    
    return {
        "common_interval_mm": [u_start, u_end],
        "common_span_mm": u_end - u_start,
        "l2_diff_absolute": l2_diff,
        "l2_baseline": l2_base,
        "rel_l2_discrepancy_pct": rel_l2_pct,
        "max_pointwise_reldiff_pct": float(np.max(pointwise_reldiff_pct)),
        "mean_pointwise_reldiff_pct": float(np.mean(pointwise_reldiff_pct))
    }


def compute_spatial_profile_l2_discrepancy(x_grid, d1_profile, d2_profile):
    """
    Computes normalized L2 profile discrepancy between two spatial damage profiles evaluated on the same x_grid.
    """
    x = np.asarray(x_grid, dtype=float)
    d1 = np.asarray(d1_profile, dtype=float)
    d2 = np.asarray(d2_profile, dtype=float)
    
    if len(x) != len(d1) or len(x) != len(d2):
        raise ValueError("Length mismatch between x_grid (%d), d1 (%d), and d2 (%d)" % (len(x), len(d1), len(d2)))
    if len(x) < 2:
        raise ValueError("Grid must contain at least 2 points.")
        
    diff_sq = (d2 - d1) ** 2
    d1_sq = d1 ** 2
    
    l2_diff = math.sqrt(float(_trapezoid(diff_sq, x=x)))
    l2_base = math.sqrt(float(_trapezoid(d1_sq, x=x)))
    
    denom = max(l2_base, 1e-12)
    rel_l2_pct = (l2_diff / denom) * 100.0
    
    return {
        "x_range_mm": [float(x[0]), float(x[-1])],
        "l2_diff_absolute": l2_diff,
        "l2_baseline": l2_base,
        "rel_l2_profile_discrepancy_pct": rel_l2_pct,
        "max_pointwise_diff": float(np.max(np.abs(d2 - d1)))
    }

# Alias for backward compatibility
compute_damage_profile_l2_discrepancy = compute_spatial_profile_l2_discrepancy


def sample_damage_profile_along_ligament(elements_data, target_x_grid, y_target=0.500, tol_y=0.010):
    """
    Samples damage field d(x, y=y_target) onto target_x_grid from element centroid data.
    Each element record must contain:
      - 'x': centroid x coordinate [mm]
      - 'y': centroid y coordinate [mm]
      - 'd': damage field value
    Filters elements within |y - y_target| <= tol_y and interpolates onto target_x_grid.
    """
    x_filtered = []
    d_filtered = []
    
    for el in elements_data:
        x_el = float(el['x'])
        y_el = float(el['y'])
        d_el = float(el['d'])
        if abs(y_el - y_target) <= tol_y:
            x_filtered.append(x_el)
            d_filtered.append(d_el)
            
    if len(x_filtered) < 2:
        raise ValueError("Insufficient element centroids found within y = %g +- %g mm (found %d)" % (y_target, tol_y, len(x_filtered)))
        
    # Sort by x
    sort_idx = np.argsort(x_filtered)
    x_sorted = np.asarray(x_filtered)[sort_idx]
    d_sorted = np.asarray(d_filtered)[sort_idx]
    
    # Remove duplicate x coordinates by averaging d
    unique_x, inverse_indices = np.unique(np.round(x_sorted, decimals=7), return_inverse=True)
    averaged_d = np.zeros_like(unique_x)
    counts = np.zeros_like(unique_x)
    for idx, d_val in zip(inverse_indices, d_sorted):
        averaged_d[idx] += d_val
        counts[idx] += 1
    averaged_d /= counts
    
    # Interpolate onto target_x_grid
    target_grid = np.asarray(target_x_grid, dtype=float)
    sampled_d = np.interp(target_grid, unique_x, averaged_d)
    return sampled_d


def extract_crack_path_centerline(elements_data, x_bins=50, x_min=0.500, x_max=1.000):
    """
    Extracts the crack centerline y_crack(x) by locating the dominant damage ridge in each x-bin.
    Returns:
      - 'x_mid_mm': bin center coordinates
      - 'y_crack_mm': ridge y-coordinates
      - 'delta_y_mm': deviation from nominal symmetry plane y = 0.500 mm
      - 'max_deviation_mm': maximum absolute deviation along the ligament
    """
    bins = np.linspace(x_min, x_max, x_bins + 1)
    x_mid = 0.5 * (bins[:-1] + bins[1:])
    y_crack = []
    
    for i in range(x_bins):
        bin_x0 = bins[i]
        bin_x1 = bins[i+1]
        
        bin_elements = [
            el for el in elements_data
            if bin_x0 <= float(el['x']) < bin_x1
        ]
        
        if not bin_elements:
            y_crack.append(0.500)
            continue
            
        # Find element with maximum damage in this bin
        best_el = max(bin_elements, key=lambda el: float(el['d']))
        y_crack.append(float(best_el['y']))
        
    y_crack = np.asarray(y_crack)
    delta_y = y_crack - 0.500
    max_dev = float(np.max(np.abs(delta_y)))
    
    return {
        "x_mid_mm": x_mid.tolist(),
        "y_crack_mm": y_crack.tolist(),
        "delta_y_mm": delta_y.tolist(),
        "max_deviation_mm": max_dev
    }


def compute_successive_relative_difference(phi_coarse, phi_fine):
    """
    Computes the outcome-independent successive-resolution relative difference:
    delta_n(phi) = |phi_fine - phi_coarse| / max(|phi_coarse|, 1e-12)
    Kept strictly under TREND_ONLY governance.
    """
    if phi_coarse is None or phi_fine is None:
        return None
    denom = max(abs(float(phi_coarse)), 1e-12)
    diff = abs(float(phi_fine) - float(phi_coarse))
    return float(diff / denom)


def deduplicate_cpe4_element_integrals(element_records):
    """
    Ensures that when CPE4 elements have 4 integration point values logged,
    only ONE unique value per elementLabel is accumulated to prevent 4x overcounting.
    
    Input: list of dicts with 'elementLabel', 'e_elas', 'e_frac'
    Returns: total_e_elas, total_e_frac, unique_element_count
    """
    seen_labels = set()
    total_elas = 0.0
    total_frac = 0.0
    
    for rec in element_records:
        lbl = int(rec['elementLabel'])
        if lbl in seen_labels:
            continue
        seen_labels.add(lbl)
        total_elas += float(rec.get('e_elas', 0.0))
        total_frac += float(rec.get('e_frac', 0.0))
        
    return {
        "total_e_elas_kNmm": total_elas,
        "total_e_elas_mJ": total_elas * 1000.0,
        "total_e_frac_kNmm": total_frac,
        "total_e_frac_mJ": total_frac * 1000.0,
        "unique_elements_count": len(seen_labels)
    }
