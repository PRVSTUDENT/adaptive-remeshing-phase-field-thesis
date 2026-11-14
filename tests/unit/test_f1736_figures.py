# -*- coding: utf-8 -*-
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import pytest
from scripts.remeshing.plot_f1736_meshes import main as generate_figures

def test_f1736_figures_generation():
    generate_figures()
    
    fig_dir = os.path.join(REPO_ROOT, "results", "figures")
    expected_files = [
        "fig_f1736_case_1_standalone_mesh.png",
        "fig_f1736_case_1_standalone_mesh.pdf",
        "fig_f1736_case_2_standalone_mesh.png",
        "fig_f1736_case_2_standalone_mesh.pdf",
        "fig_f1736_case_3_standalone_mesh.png",
        "fig_f1736_case_3_standalone_mesh.pdf",
        "fig_f1736_case_4_standalone_mesh.png",
        "fig_f1736_case_4_standalone_mesh.pdf",
        "fig_f1736_case_5_standalone_mesh.png",
        "fig_f1736_case_5_standalone_mesh.pdf",
        "fig_f1736_five_case_comparison_corrected.png",
        "fig_f1736_five_case_comparison_corrected.pdf"
    ]
    
    for f in expected_files:
        p = os.path.join(fig_dir, f)
        assert os.path.exists(p), f"Missing expected figure: {f}"
        assert os.path.getsize(p) > 10000, f"Figure {f} is suspiciously small: {os.path.getsize(p)} bytes"
