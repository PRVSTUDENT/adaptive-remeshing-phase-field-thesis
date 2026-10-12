"""
test_mode1_method_b_propagation_resolution.py
---------------------------------------------
Unit tests verifying the Method B crack-propagation spatial resolution audit,
directional element sizing along the forward ligament (0.5 < x <= 1.0 mm),
phase-field resolution thresholds (l0/h), upper/lower symmetry,
correlation with simulated crack tip progression, and figure artifacts.

Task: F1428-MODE1-METHOD-B-PROPAGATION-AUDIT-AND-METHOD-C-V2-READINESS
"""

import os
import sys
import math
import csv
import pytest

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.visualization.plot_mode1_method_b_propagation_resolution import (
    parse_abaqus_mesh,
    build_element_records,
    INP_PATH,
    STATES_PATH,
    OUT_DIR,
    L0
)


@pytest.fixture(scope="module")
def mesh_records():
    assert os.path.exists(INP_PATH), f"Input deck not found: {INP_PATH}"
    nodes, quads, tris = parse_abaqus_mesh(INP_PATH)
    elements = build_element_records(nodes, quads, tris)
    return elements


def test_independent_preliminary_measurements_reproduction(mesh_records):
    """
    Independently verifies the researcher's preliminary measurements:
    0-25 um: ~1.97 um
    25-50 um: ~1.93 um
    50-100 um: ~3.06 um
    100-200 um: ~6.83 um
    Far-field UR: ~15.64 um
    """
    # 0-25 um ahead of tip in tight corridor |y-0.5| <= 0.010 mm
    sub_0_25 = [el['h_um'] for el in mesh_records if 0.500 <= el['cx'] <= 0.525 and abs(el['cy'] - 0.5) <= 0.010]
    med_0_25 = sorted(sub_0_25)[len(sub_0_25)//2]
    assert med_0_25 == pytest.approx(1.97, abs=0.05), f"Expected ~1.97 um, got {med_0_25:.2f}"

    # 25-50 um ahead of tip in tight corridor |y-0.5| <= 0.010 mm
    sub_25_50 = [el['h_um'] for el in mesh_records if 0.525 < el['cx'] <= 0.550 and abs(el['cy'] - 0.5) <= 0.010]
    med_25_50 = sorted(sub_25_50)[len(sub_25_50)//2]
    assert med_25_50 == pytest.approx(1.93, abs=0.05), f"Expected ~1.93 um, got {med_25_50:.2f}"

    # 50-100 um ahead of tip in tight corridor
    sub_50_100 = [el['h_um'] for el in mesh_records if 0.550 < el['cx'] <= 0.600 and abs(el['cy'] - 0.5) <= 0.010]
    med_50_100 = sorted(sub_50_100)[len(sub_50_100)//2]
    assert med_50_100 == pytest.approx(3.06, abs=0.10), f"Expected ~3.06 um, got {med_50_100:.2f}"

    # 100-200 um ahead of tip in standard corridor |y-0.5| <= 0.025 mm
    sub_100_200 = [el['h_um'] for el in mesh_records if 0.600 < el['cx'] <= 0.700 and abs(el['cy'] - 0.5) <= 0.025]
    med_100_200 = sorted(sub_100_200)[len(sub_100_200)//2]
    assert 6.5 <= med_100_200 <= 7.5, f"Expected ~6.83 um, got {med_100_200:.2f}"

    # Far-field upper-right region (x >= 0.8, y >= 0.8)
    sub_ur = [el['h_um'] for el in mesh_records if el['cx'] >= 0.8 and el['cy'] >= 0.8]
    med_ur = sorted(sub_ur)[len(sub_ur)//2]
    assert 14.5 <= med_ur <= 16.0, f"Expected ~15.1-15.6 um, got {med_ur:.2f}"


def test_monotonic_coarsening_along_ligament(mesh_records):
    """
    Verifies that element size coarsens monotonically from the crack tip
    to the far boundary along the ligament corridor (|y - 0.5| <= 0.025 mm).
    """
    bins = [
        (0.500, 0.525),
        (0.525, 0.550),
        (0.550, 0.600),
        (0.600, 0.650),
        (0.650, 0.700),
        (0.700, 0.800),
        (0.800, 0.900),
        (0.900, 1.000)
    ]
    medians = []
    for x_lo, x_hi in bins:
        sub = [el['h_um'] for el in mesh_records if x_lo < el['cx'] <= x_hi and abs(el['cy'] - 0.5) <= 0.025]
        assert len(sub) > 0
        med = sorted(sub)[len(sub)//2]
        medians.append(med)
        
    for i in range(1, len(medians)):
        assert medians[i] >= medians[i-1] * 0.95, f"Expected non-decreasing size: {medians}"

    assert medians[0] < 2.1  # ~1.99 um at tip
    assert medians[-1] > 14.0  # ~14.8 um at far edge
    assert medians[-1] / medians[0] > 7.0  # >7x coarsening contrast


def test_phase_field_resolution_thresholds(mesh_records):
    """
    Verifies the crucial phase-field resolution thresholds:
    1. Tip zone (x <= 0.55 mm): l0 / h >= 3.5 (well-resolved)
    2. Mid-ligament (x >= 0.65 mm): l0 / h < 1.0 (under-resolved / pinning)
    3. Far edge (x >= 0.80 mm): l0 / h < 0.6 (less than 1 element per 1.5 l0)
    """
    l0_um = L0 * 1000.0  # 7.5 um

    # Tip zone
    sub_tip = [el['h_um'] for el in mesh_records if 0.500 <= el['cx'] <= 0.550 and abs(el['cy'] - 0.5) <= 0.025]
    med_tip_h = sorted(sub_tip)[len(sub_tip)//2]
    assert l0_um / med_tip_h >= 3.5

    # Mid-ligament (150-200 um ahead)
    sub_mid = [el['h_um'] for el in mesh_records if 0.650 < el['cx'] <= 0.700 and abs(el['cy'] - 0.5) <= 0.025]
    med_mid_h = sorted(sub_mid)[len(sub_mid)//2]
    assert l0_um / med_mid_h < 1.0, f"Expected under-resolved l0/h < 1.0, got {l0_um / med_mid_h:.2f}"

    # Far ligament
    sub_far = [el['h_um'] for el in mesh_records if 0.800 < el['cx'] <= 1.000 and abs(el['cy'] - 0.5) <= 0.025]
    med_far_h = sorted(sub_far)[len(sub_far)//2]
    assert l0_um / med_far_h < 0.6, f"Expected l0/h < 0.6, got {l0_um / med_far_h:.2f}"


def test_upper_lower_flank_symmetry(mesh_records):
    """
    Verifies that the adaptive mesh maintains reasonable symmetry
    between upper (y > 0.5) and lower (y < 0.5) flanks along the ligament.
    """
    sectors = [(0.50, 0.55), (0.55, 0.65), (0.65, 0.80), (0.80, 1.00)]
    for x_lo, x_hi in sectors:
        upper = [el['h_um'] for el in mesh_records if x_lo < el['cx'] <= x_hi and 0.5 < el['cy'] <= 0.525]
        lower = [el['h_um'] for el in mesh_records if x_lo < el['cx'] <= x_hi and 0.475 <= el['cy'] < 0.5]
        u_med = sorted(upper)[len(upper)//2]
        l_med = sorted(lower)[len(lower)//2]
        diff_pct = abs(u_med - l_med) / max(l_med, 1e-6) * 100.0
        assert diff_pct < 12.0, f"Symmetry asymmetry exceeded 12%: {diff_pct:.2f}%"


def test_crack_tip_advancement_into_coarse_zone():
    """
    Verifies that the simulation evidence shows the crack propagating
    out of the well-resolved zone into the coarse under-resolved zone.
    """
    assert os.path.exists(STATES_PATH), f"Matched states summary missing: {STATES_PATH}"
    states = []
    with open(STATES_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for r in reader:
            states.append(r)
            
    # Peak load state: u = 0.005727 mm
    peak_state = next(r for r in states if abs(float(r['u_actual_mm']) - 0.005727) < 1e-5)
    assert float(peak_state['crack_tip_x_d90_mm']) == pytest.approx(0.500, abs=1e-3)

    # Post-peak softening states: crack propagates forward
    step2_states = [r for r in states if r['step_name'] == 'Step-2']
    assert len(step2_states) > 0
    
    # At u = 0.0070 mm, crack has reached x ~ 0.708 mm
    state_0070 = next(r for r in step2_states if abs(float(r['u_actual_mm']) - 0.0070) < 1e-4)
    x_tip_0070 = float(state_0070['crack_tip_x_d90_mm'])
    assert x_tip_0070 > 0.65, f"Expected crack past 0.65 mm, got {x_tip_0070:.4f}"


def test_propagation_figure_artifacts_exist():
    """Verifies that both generated publication figures exist and are non-empty."""
    fig1_png = os.path.join(OUT_DIR, "fig_mode1_method_b_propagation_resolution.png")
    fig1_pdf = os.path.join(OUT_DIR, "fig_mode1_method_b_propagation_resolution.pdf")
    fig2_png = os.path.join(OUT_DIR, "fig_mode1_method_b_propagation_ligament_zoom.png")
    fig2_pdf = os.path.join(OUT_DIR, "fig_mode1_method_b_propagation_ligament_zoom.pdf")
    
    assert os.path.exists(fig1_png) and os.path.getsize(fig1_png) > 100000
    assert os.path.exists(fig1_pdf) and os.path.getsize(fig1_pdf) > 50000
    assert os.path.exists(fig2_png) and os.path.getsize(fig2_png) > 100000
    assert os.path.exists(fig2_pdf) and os.path.getsize(fig2_pdf) > 50000
