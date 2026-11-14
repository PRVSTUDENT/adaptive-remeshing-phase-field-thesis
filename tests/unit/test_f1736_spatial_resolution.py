# -*- coding: utf-8 -*-
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import pytest
from scripts.remeshing.audit_f1736_spatial_resolution import audit_all_benchmarks
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
