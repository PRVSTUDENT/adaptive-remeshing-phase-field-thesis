# -*- coding: utf-8 -*-
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import pytest
from scripts.remeshing.audit_f1736_spatial_resolution import audit_all_benchmarks, parse_abaqus_inp
from scripts.remeshing.register_f1736_artifacts import main as register_artifacts

def test_f1736_spatial_resolution_audit():
    results = audit_all_benchmarks()
    assert len(results) == 5
    
    # Assert zero negative Jacobians across all final meshes
    for case_key, data in results.items():
        fm = data["final_mesh"]["metrics"]
        assert fm["negative_jacobian_count"] == 0, f"{case_key} has negative Jacobians!"
        assert fm["num_elements"] > 1000
        assert fm["quad_percentage"] > 95.0
        
    # Check specific element counts
    assert results["case_1"]["final_mesh"]["metrics"]["num_elements"] == 14147
    assert results["case_2"]["final_mesh"]["metrics"]["num_elements"] == 23965
    assert results["case_3"]["final_mesh"]["metrics"]["num_elements"] == 12110
    assert results["case_4"]["final_mesh"]["metrics"]["num_elements"] == 13017
    assert results["case_5"]["final_mesh"]["metrics"]["num_elements"] == 15708

def test_f1736_artifact_registration():
    register_artifacts()
    reg_path = os.path.join(REPO_ROOT, "project_coordination", "ARTIFACT_REGISTRY.csv")
    with open(reg_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "DOC_F1736_REASSESSMENT_REPORT" in content
    assert "FIG_F1736_FIVE_CASE_CORRECTED_PNG" in content
    assert "JSON_F1736_SPATIAL_AUDIT" in content

def test_f1736_coarse_meshes():
    coarse_candidates = [
        os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "00_aux_continuum_preanalysis", "PK_MODE1_AUX_CONTINUUM.inp"),
        os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "220_f1729_case2_recovery_datacheck", "PK_HOLE_COMPANION_RECOVERY.inp"),
        os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "188_pk_sec43_hole_plate", "PK_SEC43_COARSE_PHYS.inp"),
        os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "209_f1718_five_hole_recovery", "PK_F1718_RECOVERY_PHYS.inp"),
        os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_COARSE_PHYS.inp")
    ]
    for p in coarse_candidates:
        nodes, elements, _ = parse_abaqus_inp(p)
        print(f"Coarse mesh {os.path.basename(p)}: {len(elements)} elements, {len(nodes)} nodes")
        assert os.path.exists(p)
