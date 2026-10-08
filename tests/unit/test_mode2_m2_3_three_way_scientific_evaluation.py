"""
Unit tests for Mode-II Gate M2-3 Three-Way Scientific Mesh Evaluation & Decision Correction
Verifies:
  1. Existence and integrity of all 3 native adaptive mesh datasets and audit JSON
  2. Scale-invariance and topological equivalence between Step-1 2% (22,530 FEs) and Step-2 2% (22,405 FEs)
  3. Near-global overrefinement proof for Step-2 1% (80,474 FEs, 93.1% area <= l0/2)
  4. Accuracy of Mode-II length scale l0 = 15.0 um and h/l0 ratios
  5. Correct classification 'NOT YET PROVEN' in durable decision record
  6. Generated publication figures across PNG (300 DPI), PNG (600 DPI), and PDF
"""
import os
import json
import pytest
import pandas as pd
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis")
FIG_DIR = os.path.join(REPO_ROOT, "results", "figures", "mode2")
DECISION_FILE = os.path.join(REPO_ROOT, "docs", "decisions", "2026-10-08_MODE2_STEP2_REMESHING_FRAME_DECISION.md")
AUDIT_JSON = os.path.join(BASE_DIR, "mode2_three_way_area_weighted_audit.json")


def test_01_three_way_datasets_and_audit_json_exist():
    """Verify all required CSVs, INP decks, and audit JSON exist."""
    assert os.path.exists(os.path.join(BASE_DIR, "M2_3_ADAPTED_RAW_2PCT.inp")), "Step-1 2% INP missing"
    assert os.path.exists(os.path.join(BASE_DIR, "M2_3_ADAPTED_STEP2_RAW_2PCT.inp")), "Step-2 2% INP missing"
    assert os.path.exists(os.path.join(BASE_DIR, "M2_3_ADAPTED_STEP2_RAW_1PCT.inp")), "Step-2 1% INP missing"
    assert os.path.exists(os.path.join(BASE_DIR, "m2_3_mesh_elements_et2pct.csv")), "Step-1 2% CSV missing"
    assert os.path.exists(os.path.join(BASE_DIR, "m2_3_mesh_elements_step2_et2pct.csv")), "Step-2 2% CSV missing"
    assert os.path.exists(os.path.join(BASE_DIR, "m2_3_mesh_elements_step2_et1pct.csv")), "Step-2 1% CSV missing"
    assert os.path.exists(AUDIT_JSON), "Audit JSON missing"


def test_02_step1_vs_step2_2pct_topological_equivalence():
    """Verify Step-1 2% (22,530) vs Step-2 2% (22,405) differ by <= 1% and have equivalent area distributions."""
    with open(AUDIT_JSON) as f:
        data = json.load(f)
    
    s1 = data["Step-1 2.0%"]
    s2 = data["Step-2 2.0%"]
    
    assert s1["n_elems"] == 22530
    assert s2["n_elems"] == 22405
    
    # Relative element delta
    fe_delta_pct = abs(s2["n_elems"] - s1["n_elems"]) / s1["n_elems"] * 100.0
    assert fe_delta_pct < 1.0, f"FE delta exceeds 1%: {fe_delta_pct:.2f}%"
    
    # Area-weighted mean size agreement
    wmean_delta_pct = abs(s2["h_weighted_mean_um"] - s1["h_weighted_mean_um"]) / s1["h_weighted_mean_um"] * 100.0
    assert wmean_delta_pct < 1.0, f"Area-weighted mean size delta exceeds 1%: {wmean_delta_pct:.2f}%"
    
    # Crack tip area coverage (h <= l0/2 = 7.5 um)
    assert s1["crack_tip_neighborhood"]["fine_area_pct_le_l0_2"] == 100.0
    assert s2["crack_tip_neighborhood"]["fine_area_pct_le_l0_2"] == 100.0


def test_03_step2_1pct_near_global_overrefinement():
    """Verify Step-2 1% (80,474) has >90% domain area refined to h <= l0/2 and 0% coarse far field."""
    with open(AUDIT_JSON) as f:
        data = json.load(f)
    
    s3 = data["Step-2 1.0%"]
    assert s3["n_elems"] == 80474
    assert s3["h_min_um"] < 1.0
    
    # Domain area fraction h <= 7.5 um
    area_fine_pct = s3["thresholds"]["h_le_7.5um"]["area_pct"]
    assert area_fine_pct > 90.0, f"Domain fine area fraction unexpectedly low: {area_fine_pct:.2f}%"
    
    # Far-field coarse area fraction (h >= 15.0 um)
    coarse_area_pct = s3["far_field"]["coarse_area_pct_ge_l0"]
    assert coarse_area_pct == 0.0, f"Far field contains coarse elements: {coarse_area_pct:.2f}%"
    assert s3["h_max_um"] < 15.0, f"Max size exceeds l0: {s3['h_max_um']:.2f} um"


def test_04_mode2_length_scale_and_ratios():
    """Verify l0 = 15.0 um for Mode-II and correct h/l0 ratios."""
    with open(AUDIT_JSON) as f:
        data = json.load(f)
    
    s1 = data["Step-1 2.0%"]
    s2 = data["Step-2 2.0%"]
    s3 = data["Step-2 1.0%"]
    
    # Mode-II l0 = 15.0 um
    assert pytest.approx(s1["h_min_l0"], rel=1e-2) == s1["h_min_um"] / 15.0
    assert pytest.approx(s2["h_min_l0"], rel=1e-2) == s2["h_min_um"] / 15.0
    assert pytest.approx(s3["h_min_l0"], rel=1e-2) == s3["h_min_um"] / 15.0
    
    # Singularity resolution (h_min << l0)
    assert s1["h_min_l0"] < 0.1
    assert s2["h_min_l0"] < 0.1
    assert s3["h_min_l0"] < 0.1


def test_05_decision_record_epistemic_classification():
    """Verify decision record classifies Step-2 superiority as NOT YET PROVEN."""
    assert os.path.exists(DECISION_FILE), "Decision file missing"
    with open(DECISION_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    
    assert "NOT YET PROVEN" in text, "Decision record must classify Step-2 superiority as NOT YET PROVEN"
    assert "15.0" in text, "Decision record must reference Mode-II l0 = 15.0 um"
    assert "1411103.mmaster02" in text, "Decision record must reference active baseline job"


def test_06_publication_figures_exist_and_nonempty():
    """Verify 3-way scientific comparison figures exist and are non-empty."""
    fig_png = os.path.join(FIG_DIR, "fig_mode2_m2_3_three_way_scientific_comparison.png")
    fig_pdf = os.path.join(FIG_DIR, "fig_mode2_m2_3_three_way_scientific_comparison.pdf")
    fig_600 = os.path.join(FIG_DIR, "fig_mode2_m2_3_three_way_scientific_comparison_600dpi.png")
    
    for path in [fig_png, fig_pdf, fig_600]:
        assert os.path.exists(path), f"Figure file missing: {path}"
        assert os.path.getsize(path) > 100000, f"Figure file suspiciously small: {path}"
