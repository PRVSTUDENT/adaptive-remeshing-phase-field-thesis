"""
Unit Test Suite: Task F1712 - Pandey-Kumar Mode-I Figures 5, 6 & 7 Reproduction
and Reusable 2D Adaptive Framework Generalization

Verifies:
1. All generated figure artifacts exist, are non-empty, and valid images/PDFs.
2. Authentic coarse mesh topology (2,906 physical elements: 2,818 CPE4, 88 CPE3).
3. Authentic adapted mesh topology (14,483 physical elements: 14,082 CPE4, 401 CPE3).
4. S1 audited reference load-displacement dataset matches standard PFM benchmark.
5. Adapted load-displacement dataset matches proposed PFM benchmark within expected tolerance.
6. Reusable adaptive framework module imports and passes basic parameter validation.
"""

import os
import sys
sys.path.insert(0, os.path.abspath("."))
import pytest
import pandas as pd
from PIL import Image

OUT_DIR = "MA_AdaptiveRemeshing_Report_2026/figures/pandey_kumar_fig5_7_reproduction"

FIGURE_BASENAMES = [
    "fig_f1712_figure6a_reproduced",
    "fig_f1712_figure5b_reproduced",
    "fig_f1712_mode1_adapted_mesh_only",
    "fig_f1712_mode1_primary_mesh_zoom",
    "fig_f1712_figure7_reproduced",
    "fig_f1712_comparison_figures5_6",
]


def test_all_f1712_figures_exist_and_non_empty():
    """Verify all 6 PNG and 6 PDF figures exist and have non-zero size."""
    for base in FIGURE_BASENAMES:
        png_path = os.path.join(OUT_DIR, f"{base}.png")
        pdf_path = os.path.join(OUT_DIR, f"{base}.pdf")
        
        assert os.path.exists(png_path), f"Missing PNG: {png_path}"
        assert os.path.getsize(png_path) > 10000, f"PNG unexpectedly small: {png_path}"
        
        assert os.path.exists(pdf_path), f"Missing PDF: {pdf_path}"
        assert os.path.getsize(pdf_path) > 10000, f"PDF unexpectedly small: {pdf_path}"


def test_png_dimensions_and_validity():
    """Verify all PNG figures open cleanly and have high resolution."""
    for base in FIGURE_BASENAMES:
        png_path = os.path.join(OUT_DIR, f"{base}.png")
        with Image.open(png_path) as img:
            assert img.width >= 1000, f"Image width too low for {base}: {img.width}"
            assert img.height >= 800, f"Image height too low for {base}: {img.height}"


def test_coarse_mesh_elements_count():
    """Verify coarse mesh contains exactly 2,906 elements (2,818 quads, 88 triangles)."""
    coarse_inp = "models/pandey_kumar_mode1/02_proposed_adaptive_refined/PK_PREANALYSIS_COARSE.inp"
    assert os.path.exists(coarse_inp), f"Missing {coarse_inp}"
    
    quad_count = 0
    tri_count = 0
    current_type = None
    with open(coarse_inp, 'r') as f:
        for line in f:
            line_s = line.strip()
            if line_s.upper().startswith('*ELEMENT'):
                if 'CPE4' in line_s.upper():
                    current_type = 'quad'
                elif 'CPE3' in line_s.upper():
                    current_type = 'tri'
                else:
                    current_type = None
            elif line_s.startswith('*'):
                current_type = None
            elif current_type:
                tokens = [t.strip() for t in line_s.split(',') if t.strip()]
                if current_type == 'quad' and len(tokens) == 5:
                    quad_count += 1
                elif current_type == 'tri' and len(tokens) == 4:
                    tri_count += 1
                    
    assert quad_count == 2818, f"Expected 2,818 quads, found {quad_count}"
    assert tri_count == 88, f"Expected 88 tris, found {tri_count}"
    assert (quad_count + tri_count) == 2906, f"Expected 2,906 elements, found {quad_count + tri_count}"


def test_adapted_mesh_elements_count():
    """Verify adapted physical mesh contains 14,483 elements (14,082 quads, 401 triangles) and dual UEL layers."""
    adapt_inp = "models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp"
    assert os.path.exists(adapt_inp), f"Missing {adapt_inp}"
    
    physical_count = 0
    phase_uel_count = 0
    mech_uel_count = 0
    current_layer = None
    with open(adapt_inp, 'r') as f:
        for line in f:
            line_s = line.strip()
            if line_s.upper().startswith('*ELEMENT'):
                if 'ELSET=PHASE' in line_s.upper():
                    current_layer = 'phase'
                elif 'ELSET=MECH' in line_s.upper():
                    current_layer = 'mech'
                elif 'ELSET=UMAT' in line_s.upper() or 'TYPE=CPE' in line_s.upper():
                    current_layer = 'physical'
                else:
                    current_layer = None
            elif line_s.startswith('*'):
                current_layer = None
            elif current_layer:
                tokens = [t.strip() for t in line_s.split(',') if t.strip()]
                if current_layer == 'physical' and len(tokens) in (4, 5):
                    physical_count += 1
                elif current_layer == 'phase' and len(tokens) in (4, 5):
                    phase_uel_count += 1
                elif current_layer == 'mech' and len(tokens) in (4, 5):
                    mech_uel_count += 1
                    
    assert physical_count == 14483, f"Expected 14,483 physical companion elements, found {physical_count}"
    assert phase_uel_count == 14483, f"Expected 14,483 phase UEL elements, found {phase_uel_count}"
    assert mech_uel_count == 14483, f"Expected 14,483 mech UEL elements, found {mech_uel_count}"
    assert (phase_uel_count + mech_uel_count) == 28966, f"Expected 28,966 total UEL elements, found {phase_uel_count + mech_uel_count}"


def test_reaction_force_metrics():
    """Verify peak load and displacement metrics against Pandey & Kumar (2025)."""
    adapt_fu = "models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/PK_MODE1_STAGE14_ADAPT_14K_FRACTURE_fu.csv"
    assert os.path.exists(adapt_fu)
    df_adapt = pd.read_csv(adapt_fu)
    f_peak_adapt = df_adapt['reaction_force_kN'].max()
    u_peak_adapt = df_adapt.loc[df_adapt['reaction_force_kN'].idxmax(), 'displacement_mm']
    
    # Check that peak force is within 2% of the published peak ~0.74 kN
    assert 0.72 <= f_peak_adapt <= 0.76, f"Adapted peak force {f_peak_adapt:.4f} kN out of expected [0.72, 0.76]"
    assert 0.0050 <= u_peak_adapt <= 0.0062, f"Adapted peak displacement {u_peak_adapt:.6f} mm out of expected range"

    ref_fu = "models/pandey_kumar_mode1/batch_mode1_energy_convergence/S1_h0030_15k_MECHANICAL_FU_AUDITED.csv"
    assert os.path.exists(ref_fu)
    df_ref = pd.read_csv(ref_fu)
    f_peak_ref = df_ref['rf2_kN'].max()
    u_peak_ref = df_ref.loc[df_ref['rf2_kN'].idxmax(), 'u2_mm']
    
    # Check that standard reference peak force is ~0.758 kN
    assert 0.74 <= f_peak_ref <= 0.78, f"Standard reference peak force {f_peak_ref:.4f} kN out of expected [0.74, 0.78]"
    assert 0.0052 <= u_peak_ref <= 0.0065, f"Standard reference peak displacement {u_peak_ref:.6f} mm out of expected range"


def test_reusable_adaptive_framework_module():
    """Verify reusable adaptive framework script imports and instantiates properly."""
    from scripts.remeshing.reusable_2d_adaptive_framework import (
        AdaptiveConfig,
        StraightNotchMode1Adapter,
        get_geometry_adapter,
        ProductionDeckBuilder,
        MeshQualityAuditEngine,
    )
    raw_cfg = {
        "benchmark_name": "Mode1_Benchmark",
        "geometry_type": "STRAIGHT_NOTCH",
        "geometry": {
            "plate_width": 1.0,
            "plate_height": 1.0,
            "notch_length": 0.5,
        },
        "material": {
            "youngs_modulus": 210.0,
            "poissons_ratio": 0.30,
            "fracture_energy": 2.7e-3,
            "length_scale": 0.0075,
        },
        "remeshing": {
            "h_coarse": 0.02,
            "h_fine": 0.001,
            "target_element_count": 13941,
        }
    }
    cfg = AdaptiveConfig(raw_cfg)
    assert cfg.benchmark_name == "Mode1_Benchmark"
    assert cfg.plate_w == 1.0
    adapter = get_geometry_adapter(cfg)
    assert isinstance(adapter, StraightNotchMode1Adapter)
