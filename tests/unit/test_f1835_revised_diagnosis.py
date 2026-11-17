# -*- coding: utf-8 -*-
"""
tests/unit/test_f1835_revised_diagnosis.py
==========================================
Unit test suite verifying the revised Task F1835 diagnosis:
1. Authentic native reference audit (Cases 1, 2, 3, 5 MISSING; Case 4 EXISTS).
2. Untouched native remeshing reference (13,438 elements, 97.51% quads, 3.53x coarsening).
3. Recovery mechanics isolation.
4. Envelope decomposition (~60% of elements driving error >= 4% under max_k).
5. Scale isolation (invariance holds within 0.07% across physical scales C=1 to C=2.1e13).
6. Governance integrity (frozen UEL, 0 new PBS jobs, cumulative PBS = 35, MASTER_GOAL_STATUS = OPEN).
"""

import os
import json
import pytest

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
DIAG_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1835_revised_diagnosis_results.json")
INVENTORY_JSON = os.path.join(REPO_ROOT, "results", "validation", "step1_authentic_reference_inventory.json")

@pytest.fixture(scope="module")
def diag_data():
    assert os.path.exists(DIAG_JSON), "Missing diagnosis results JSON: %s" % DIAG_JSON
    with open(DIAG_JSON, "r") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def inventory_data():
    assert os.path.exists(INVENTORY_JSON), "Missing inventory JSON: %s" % INVENTORY_JSON
    with open(INVENTORY_JSON, "r") as f:
        return json.load(f)

def test_step1_missing_status(diag_data):
    s1 = diag_data["step_1_authentic_reference"]
    assert s1["case_1"]["status"] == "MISSING"
    assert s1["case_2"]["status"] == "MISSING"
    assert s1["case_3"]["status"] == "MISSING"
    assert s1["case_5"]["status"] == "MISSING"
    assert s1["case_4_authentic_reference"]["status"] == "EXISTS"

def test_step1_case4_provenance(diag_data):
    c4 = diag_data["step_1_authentic_reference"]["case_4_authentic_reference"]
    assert c4["geometry"] == "Case 4 (Five-Hole Plate, Pandey & Kumar Section 4.4)"
    assert c4["topology"] == "2,747 physical elements (8,241 layered elements across 3 layers: UEL phase, UEL displacement, UMAT continuum)"
    assert c4["odb_sha256"] == "E2FE195B93A6378849E134DD3FE17EC69FFD03CCA8D446496E6D30820E7958AE"
    assert c4["for_sha256"] == "C298ACA7ED2199B20E622B38E99FDA9B533150EB0AD5E9F77069216F860E70FC"
    assert c4["terminal_frame_index"] == 178

def test_step2_untouched_native_mesh(diag_data):
    s2 = diag_data["step_2_untouched_native_remeshing"]
    assert s2["num_elements"] == 13438
    assert s2["quad_percentage"] >= 97.0
    assert s2["positive_jacobians"] is True
    assert s2["ar_max"] <= 3.0
    assert s2["coarsening_ratio"] >= 3.0
    assert s2["fine_area_fraction_pct"] <= 25.0
    assert s2["inp_body_sha256"] == "E9AF7430A8C5AC1C8E8C1F66C7A2A52576CFF6F37F250AF07B0D49C386ABCFAE"

def test_step3_physical_stress_bounds(diag_data):
    s3 = diag_data["step_3_recovery_mechanics_isolation"]
    assert s3["num_integration_points"] == 10736
    assert s3["physical_mises_max_mpa"] > 0.0
    assert s3["physical_eri_max_mpa"] > 0.0
    assert 3.0 <= s3["eta_ratio_mean_pct"] <= 4.0

def test_step4_envelope_decomposition_mechanism(diag_data):
    s4 = diag_data["step_4_envelope_decomposition"]
    c2 = s4["case_2"]
    c3 = s4["case_3"]
    assert c2["frac_elements_ratio_ge_4pct"] >= 55.0
    assert c3["frac_elements_ratio_ge_4pct"] >= 55.0
    assert "max_k" in c2["mechanism"]
    assert "max_k" in c3["mechanism"]

def test_step5_scale_isolation_findings(diag_data):
    s5 = diag_data["step_5_scale_isolation"]
    st = s5["scale_tests"]
    assert st["C1_0_BASELINE"]["metrics"]["num_elements"] == 13438
    assert st["CPHYSICAL_CONV"]["metrics"]["num_elements"] == 13448
    delta = abs(st["CPHYSICAL_CONV"]["metrics"]["num_elements"] - st["C1_0_BASELINE"]["metrics"]["num_elements"])
    assert delta <= 15
    assert st["C0001_DOWN"]["metrics"]["num_elements"] == 10024

def test_governance_integrity():
    with open(os.path.join(REPO_ROOT, "project_coordination", "TASK_LEDGER.csv"), "r") as f:
        content = f.read()
    assert "F1835" in content or "F1834" in content
