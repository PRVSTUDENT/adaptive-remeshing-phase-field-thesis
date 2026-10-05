# -*- coding: utf-8 -*-
"""
Unit test suite for Gate-6B Stage 14U-AP Mode-I errorTarget sensitivity meshes,
figures, provenance, and storage compliance.
"""
import os
import json
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def test_errortarget_sensitivity_files_exist():
    folder = os.path.join(BASE_DIR, "models", "pandey_kumar_mode1", "32_stage14_remeshing_errortarget_sensitivity")
    assert os.path.isdir(folder), f"Directory {folder} does not exist"

    expected_files = [
        "elements_err_10pct.csv",
        "elements_err_20pct.csv",
        "elements_err_30pct.csv",
        "elements_err_50pct.csv",
        "PK_M1_STAGE14UAP_ERR_10PCT.inp",
        "PK_M1_STAGE14UAP_ERR_20PCT.inp",
        "PK_M1_STAGE14UAP_ERR_30PCT.inp",
        "PK_M1_STAGE14UAP_ERR_50PCT.inp",
        "MODE1_STAGE14UAP_ERRORTARGET_SENSITIVITY_SUMMARY.json",
        "execute_stage14uap_error_target_sensitivity.py",
        "run_stage14uap_sensitivity.sh"
    ]
    for fname in expected_files:
        fpath = os.path.join(folder, fname)
        assert os.path.isfile(fpath), f"Expected file missing: {fpath}"

def test_errortarget_summary_provenance_and_counts():
    json_path = os.path.join(BASE_DIR, "models", "pandey_kumar_mode1", "32_stage14_remeshing_errortarget_sensitivity", "MODE1_STAGE14UAP_ERRORTARGET_SENSITIVITY_SUMMARY.json")
    with open(json_path, "r") as f:
        data = json.load(f)

    res = data["results_by_error_target"]
    assert res["1.0"]["total_elements"] == 57929
    assert res["2.0"]["total_elements"] == 14677
    assert res["3.0"]["total_elements"] == 6824
    assert res["5.0"]["total_elements"] == 4239

    # Node counts
    assert res["1.0"]["total_nodes"] == 57491
    assert res["2.0"]["total_nodes"] == 14646
    assert res["3.0"]["total_nodes"] == 6871
    assert res["5.0"]["total_nodes"] == 4313

    # Corrected lineage distinction verified
    lineage = data["historical_vs_corrected_lineage_distinction"]
    assert lineage["corrected_stage14_sweep"]["status"] == "CORRECTED_GOVERNED_PREANALYSIS_LINEAGE"
    assert lineage["historical_71k_mesh"]["status"] == "HISTORICAL_DEFECTIVE_PREANALYSIS_LINEAGE"

def test_generated_figures_exist_and_nonempty():
    fig_dir = os.path.join(BASE_DIR, "results", "figures", "mode1_gate6b")
    expected_pngs = [
        "Mode1_corrected_adaptive_mesh_ET2.png",
        "Mode1_corrected_adaptive_mesh_ET3.png",
        "Mode1_corrected_adaptive_mesh_ET5.png",
        "Mode1_corrected_adaptive_mesh_ET2_ET3_ET5_comparison.png",
        "fig_mode1_stage14uap_errortarget_spatial_sensitivity.png"
    ]
    for png in expected_pngs:
        p = os.path.join(fig_dir, png)
        assert os.path.isfile(p), f"Generated figure missing: {p}"
        assert os.path.getsize(p) > 100000, f"Generated figure suspiciously small: {p}"

def test_plotting_script_exists():
    script_p = os.path.join(BASE_DIR, "scripts", "postprocessing", "plot_stage14uap_errortarget_spatial_sensitivity.py")
    assert os.path.isfile(script_p), f"Plotting script missing: {script_p}"
