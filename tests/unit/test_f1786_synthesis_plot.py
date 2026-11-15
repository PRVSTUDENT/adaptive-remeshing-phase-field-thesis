# -*- coding: utf-8 -*-
"""
test_f1786_synthesis_plot.py
Verifies generation of Task F1786 four-benchmark scientific synthesis figures
and validates that physical parameters, dimensions, and baseline counts match
the committed configuration JSON files exactly.
"""

import os
import sys
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(REPO_ROOT, "scripts", "remeshing"))

from plot_f1786_scientific_synthesis import generate_synthesis_figure

def test_generate_synthesis_figures():
    output_dir = 'results/figures'
    generate_synthesis_figure(output_dir)
    
    png_path = os.path.join(output_dir, 'fig_f1786_four_benchmark_scientific_synthesis.png')
    pdf_path = os.path.join(output_dir, 'fig_f1786_four_benchmark_scientific_synthesis.pdf')
    
    assert os.path.exists(png_path), f"Expected PNG file missing: {png_path}"
    assert os.path.exists(pdf_path), f"Expected PDF file missing: {pdf_path}"
    assert os.path.getsize(png_path) > 10000, "PNG file too small"
    assert os.path.getsize(pdf_path) > 5000, "PDF file too small"

def test_source_grounded_config_parameters():
    """Verify that all parameters match the committed configuration JSON files."""
    # Case 1
    with open('configs/remeshing/f1728_case1_mode1_edge_crack.json', 'r') as f:
        c1 = json.load(f)
    assert c1['geometry']['plate_width'] == 1.0
    assert c1['geometry']['plate_height'] == 1.0
    assert c1['material']['length_scale_l0_mm'] == 0.0075
    assert c1['published_benchmark']['target_elements'] == 13941

    # Case 2
    with open('configs/remeshing/f1728_case2_off_axis_hole.json', 'r') as f:
        c2 = json.load(f)
    assert c2['geometry']['plate_width'] == 1.0
    assert c2['geometry']['plate_height'] == 1.0
    assert c2['geometry']['hole_center_x'] == 0.65
    assert c2['geometry']['hole_center_y'] == 0.65
    assert c2['geometry']['hole_radius'] == 0.10
    assert c2['material']['length_scale_l0_mm'] == 0.0075

    # Case 3
    with open('configs/remeshing/f1728_case3_notched_plate_pins.json', 'r') as f:
        c3 = json.load(f)
    assert c3['geometry']['plate_width'] == 65.0
    assert c3['geometry']['plate_height'] == 120.0
    assert c3['geometry']['notch_length'] == 10.0
    assert c3['geometry']['notch_slit_opening'] == 0.2
    assert c3['material']['length_scale_l0_mm'] == 0.285
    assert c3['published_benchmark']['target_elements'] == 12168

    # Case 5
    with open('configs/remeshing/f1728_case5_seven_hole.json', 'r') as f:
        c5 = json.load(f)
    assert c5['geometry']['plate_width'] == 1.0
    assert c5['geometry']['plate_height'] == 1.0
    assert c5['material']['length_scale_l0_mm'] == 0.008
    assert len(c5['geometry']['voids']) == 7
    assert c5['published_benchmark']['target_elements'] == 15714
