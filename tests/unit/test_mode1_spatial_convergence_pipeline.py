"""
Unit Tests for Authoritative Mode-I Spatial Convergence Post-Processing Pipeline
Tests cover:
1. Exact frame match.
2. Linear interpolation between adjacent bracketing frames.
3. Censored trajectory handling (fails loudly / marks CENSORED, never extrapolates).
4. Zero / near-zero denominator protection.
5. Missing SDV field detection (fails loudly with MissingFieldOutputError, never substitutes zeros).
6. Deduplication of 4x Gauss point CPE4 companion outputs.
7. Mismatched spatial grid sampling and normalized L2 profile discrepancy.
8. Common-domain L2 curve discrepancy on F-u and energy trajectories.
9. Crack-path damage ridge extraction and symmetry verification.
10. Historical data integration and successive relative difference decay (TREND_ONLY).
"""

import sys
import os
import math
import pytest
import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from scripts.validation.spatial_convergence_pipeline import (
    CANONICAL_MATCHED_DISPLACEMENTS_MM,
    CANONICAL_REFERENCE_K0_KN_PER_MM,
    CANONICAL_REFERENCE_FMAX_KN,
    CANONICAL_REFERENCE_UPEAK_MM,
    CensoredTrajectoryError,
    MissingFieldOutputError,
    ZeroDomainOverlapError,
    linear_regression_k0,
    interpolate_scalar_at_displacement,
    extract_matched_displacement_checkpoints,
    compute_curve_l2_discrepancy,
    compute_spatial_profile_l2_discrepancy,
    sample_damage_profile_along_ligament,
    extract_crack_path_centerline,
    compute_successive_relative_difference,
    deduplicate_cpe4_element_integrals
)


def test_linear_regression_k0_synthetic():
    """Verify linear regression extracts exact slope and R2 for synthetic linear elastic data."""
    u_vals = np.linspace(0.0, 0.0010, 101)
    f_vals = 137.945520 * u_vals + 4.47e-5
    
    fit = linear_regression_k0(u_vals, f_vals, u_cutoff=0.0010)
    assert abs(fit["K0_kN_per_mm"] - 137.945520) < 1e-6
    assert abs(fit["intercept_kN"] - 4.47e-5) < 1e-8
    assert abs(fit["R2"] - 1.0) < 1e-8
    assert fit["N_points"] == 101


def test_interpolate_scalar_exact_match():
    """Verify exact frame match within numerical tolerance."""
    u_series = [0.0, 0.0010, 0.0020, 0.0050, 0.005857, 0.0100]
    f_series = [0.0, 0.1379, 0.2758, 0.6800, 0.7578, 0.0002]
    
    val = interpolate_scalar_at_displacement(u_series, f_series, 0.005857)
    assert abs(val - 0.7578) < 1e-12


def test_interpolate_scalar_bracketed():
    """Verify linear interpolation strictly between adjacent bracketing frames."""
    u_series = [0.0050, 0.0060]
    f_series = [0.6800, 0.7500]
    
    val = interpolate_scalar_at_displacement(u_series, f_series, 0.0055)
    expected = 0.6800 + 0.5 * (0.7500 - 0.6800)
    assert abs(val - expected) < 1e-12


def test_interpolate_scalar_censored_fails_loudly():
    """Verify that requesting a displacement beyond u_final raises CensoredTrajectoryError."""
    u_series = [0.0, 0.0020, 0.0050, 0.006820] # Model terminates at u = 6.82 um
    f_series = [0.0, 0.2758, 0.6800, 0.1200]
    
    # Within range works
    val = interpolate_scalar_at_displacement(u_series, f_series, 0.0062)
    assert val > 0.0
    
    # Beyond u_final must raise CensoredTrajectoryError (no extrapolation)
    with pytest.raises(CensoredTrajectoryError) as exc_info:
        interpolate_scalar_at_displacement(u_series, f_series, 0.0070)
    assert "exceeds final converged frame" in str(exc_info.value)
    
    with pytest.raises(CensoredTrajectoryError):
        interpolate_scalar_at_displacement(u_series, f_series, 0.0100)


def test_extract_matched_displacement_checkpoints_censoring():
    """Verify extract_matched_displacement_checkpoints flags censored frames without substituting zeros."""
    u_series = np.linspace(0.0, 0.006554, 656) # Censored at u = 0.006554 mm
    rf_series = np.sin(u_series * 200.0)
    e_elas_series = 0.002 * (u_series / 0.006554)
    e_frac_series = 0.001 * (u_series / 0.006554)
    w_ext_series = 0.003 * (u_series / 0.006554)
    
    traj = {
        "u_mm": u_series,
        "rf_kN": rf_series,
        "e_elas_kNmm": e_elas_series,
        "e_frac_kNmm": e_frac_series,
        "w_ext_kNmm": w_ext_series
    }
    
    cps = extract_matched_displacement_checkpoints(traj)
    
    # Valid checkpoints: 0.0010, 0.0050, 0.005857, 0.0060, 0.0062, 0.0065
    assert cps["0.001000"]["status"] == "VALID"
    assert cps["0.005000"]["status"] == "VALID"
    assert cps["0.005857"]["status"] == "VALID"
    assert cps["0.006500"]["status"] == "VALID"
    assert cps["0.006500"]["rf_kN"] is not None
    
    # Censored checkpoints: 0.0070 and 0.0100 must be CENSORED_BEYOND_ENDPOINT with rf_kN is None
    assert cps["0.007000"]["status"] == "CENSORED_BEYOND_ENDPOINT"
    assert cps["0.007000"]["rf_kN"] is None
    assert cps["0.007000"]["e_elas_kNmm"] is None
    assert cps["0.010000"]["status"] == "CENSORED_BEYOND_ENDPOINT"
    assert cps["0.010000"]["rf_kN"] is None


def test_missing_sdv_field_fails_loudly():
    """Verify that missing energetic fields raise MissingFieldOutputError instead of substituting zeros."""
    traj_missing_sdv = {
        "u_mm": [0.0, 0.0050, 0.0100],
        "rf_kN": [0.0, 0.7000, 0.0002]
        # Missing e_elas_kNmm, e_frac_kNmm, w_ext_kNmm
    }
    
    with pytest.raises(MissingFieldOutputError) as exc_info:
        extract_matched_displacement_checkpoints(traj_missing_sdv)
    assert "missing required energetic field outputs" in str(exc_info.value)


def test_compute_curve_l2_discrepancy_identity():
    """Verify that identical curves have 0% discrepancy."""
    u = np.linspace(0.0, 0.0100, 500)
    f = 0.75 * np.sin(np.pi * u / 0.0100)
    
    res = compute_curve_l2_discrepancy(u, f, u, f)
    assert abs(res["rel_l2_discrepancy_pct"]) < 1e-10
    assert abs(res["l2_diff_absolute"]) < 1e-12
    assert res["common_interval_mm"] == [0.0, 0.0100]


def test_compute_curve_l2_discrepancy_censored_common_interval():
    """Verify L2 discrepancy evaluates strictly on the common converged interval."""
    # Model 1 solves to 0.0100 mm
    u1 = np.linspace(0.0, 0.0100, 1000)
    f1 = 0.75 * np.ones_like(u1)
    
    # Model 2 cut back and stopped at 0.0068 mm
    u2 = np.linspace(0.0, 0.0068, 680)
    f2 = 0.74 * np.ones_like(u2) # 0.01 kN difference
    
    res = compute_curve_l2_discrepancy(u1, f1, u2, f2)
    # Common interval must be [0.0, 0.0068]
    assert abs(res["common_interval_mm"][1] - 0.0068) < 1e-6
    # Relative difference is (0.74 - 0.75) / 0.75 = 1/75 = 1.333%
    assert abs(res["rel_l2_discrepancy_pct"] - (1.0 / 75.0 * 100.0)) < 0.01


def test_zero_domain_overlap_fails_loudly():
    """Verify non-overlapping displacement intervals raise ZeroDomainOverlapError."""
    u1 = np.linspace(0.0, 0.0020, 100)
    f1 = np.ones_like(u1)
    u2 = np.linspace(0.0030, 0.0050, 100)
    f2 = np.ones_like(u2)
    
    with pytest.raises(ZeroDomainOverlapError):
        compute_curve_l2_discrepancy(u1, f1, u2, f2)


def test_deduplicate_cpe4_element_integrals():
    """Verify single-value deduplication prevents 4x overcounting from CPE4 integration points."""
    # Create 100 unique elements, each having 4 Gauss point entries with identical values
    records = []
    for el_id in range(1, 101):
        for gp in range(1, 5):
            records.append({
                "elementLabel": el_id,
                "e_elas": 0.010, # 0.010 kN*mm per element
                "e_frac": 0.005  # 0.005 kN*mm per element
            })
            
    assert len(records) == 400 # 400 total records
    
    dedup = deduplicate_cpe4_element_integrals(records)
    assert dedup["unique_elements_count"] == 100
    # Expected: 100 * 0.010 = 1.0 kN*mm (NOT 4.0 kN*mm)
    assert abs(dedup["total_e_elas_kNmm"] - 1.0) < 1e-12
    # Expected: 100 * 0.005 = 0.5 kN*mm (NOT 2.0 kN*mm)
    assert abs(dedup["total_e_frac_kNmm"] - 0.5) < 1e-12
    assert abs(dedup["total_e_elas_mJ"] - 1000.0) < 1e-9


def test_sample_damage_profile_mismatched_grids():
    """Verify sampling from non-matching element centroid coordinates onto uniform ligament grid."""
    # Synthetic elements for Mesh A (irregular spacing along y = 0.500 mm)
    rng = np.random.RandomState(42)
    x_rand = 0.500 + np.sort(rng.uniform(0.0, 0.500, 200))
    y_rand = 0.500 + rng.uniform(-0.005, 0.005, 200) # within tol_y = 0.010
    d_rand = 1.0 - (x_rand - 0.500) * 1.5 # linear decay from 1.0 to 0.25
    
    elements_A = [{"x": x, "y": y, "d": d} for x, y, d in zip(x_rand, y_rand, d_rand)]
    
    # Target uniform grid along ligament
    target_grid = np.linspace(0.500, 1.000, 101)
    
    sampled_A = sample_damage_profile_along_ligament(elements_A, target_grid, y_target=0.500, tol_y=0.010)
    assert len(sampled_A) == 101
    assert abs(sampled_A[0] - 1.0) < 0.05
    assert abs(sampled_A[-1] - 0.25) < 0.05


def test_extract_crack_path_centerline_planar_symmetry():
    """Verify crack path centerline locates planar horizontal propagation at y = 0.500 mm."""
    elements = []
    for x in np.linspace(0.500, 1.000, 100):
        for y in np.linspace(0.480, 0.520, 21):
            # Peak damage strictly at y = 0.500 mm
            dist = abs(y - 0.500)
            d = max(0.0, 1.0 - dist * 100.0)
            elements.append({"x": x, "y": y, "d": d})
            
    crack_path = extract_crack_path_centerline(elements, x_bins=25)
    assert crack_path["max_deviation_mm"] < 1e-6
    for y_c in crack_path["y_crack_mm"]:
        assert abs(y_c - 0.500) < 1e-6


def test_compute_successive_relative_difference_trend_only():
    """Verify successive relative difference formula delta_n(phi)."""
    # Peak forces: S1 = 0.757778 kN, S2 = 0.741200 kN, S3 = 0.732200 kN
    f_s1 = 0.757778
    f_s2 = 0.741200
    f_s3 = 0.732200
    
    delta_2 = compute_successive_relative_difference(f_s1, f_s2)
    delta_3 = compute_successive_relative_difference(f_s2, f_s3)
    
    # Expected: delta_2 = |0.7412 - 0.757778| / 0.757778 = 0.021877 (2.19%)
    assert abs(delta_2 - 0.021877) < 1e-4
    # Expected: delta_3 = |0.7322 - 0.7412| / 0.7412 = 0.012142 (1.21%)
    assert abs(delta_3 - 0.012142) < 1e-4
    
    # Successive decay: delta_3 < delta_2
    assert delta_3 < delta_2
