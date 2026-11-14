# -*- coding: utf-8 -*-
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.generate_f1728_five_case_figure import generate_five_case_figure

def test_generate_five_case_figure():
    out_png = "results/figures/fig_f1728_five_case_mesh_comparison.png"
    out_pdf = "results/figures/fig_f1728_five_case_mesh_comparison.pdf"
    
    generate_five_case_figure(out_png, out_pdf)
    
    assert os.path.exists(out_png), "PNG not generated"
    assert os.path.getsize(out_png) > 10000, "PNG too small"
    assert os.path.exists(out_pdf), "PDF not generated"
    assert os.path.getsize(out_pdf) > 10000, "PDF too small"
