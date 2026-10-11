"""
Unit test suite for Task F1414: Method A/B/C Classification Correction,
Independent Stiffness Reproduction Audit, and Automated Harvesting Activation.
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_method_abc_definitions_in_decision_doc():
    doc_path = os.path.join(REPO_ROOT, "docs", "decisions", "SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md")
    assert os.path.exists(doc_path), "Decision document must exist"

    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify Method A definition
    assert "Method A (Two-Pass Offline error-guided pre-refinement)" in content or "Method A (Two-Pass Offline Error-Guided Pre-Refinement)" in content
    assert "Method A involves zero state transfer and zero in-analysis restarts" in content

    # Verify Method B definition
    assert "Method B (Configurable Load-Partition Pre-Refinement)" in content
    assert "The scientific research variable in Method B is load-partitioning invariance, NOT state transfer" in content
    assert "Method B performs zero state transfer" in content

    # Verify Method C definition
    assert "Method C (Sequential Multi-Pass Adaptive Remeshing with Nonmatching State Transfer)" in content
    assert "strictly on hold" in content

    # Verify intercept value in Section 13 table
    assert "+4.472368 \\times 10^{-5}" in content or "+4.472368" in content

def test_independent_stiffness_reproduction_results():
    audit_json = os.path.join(REPO_ROOT, "runs", "mode1", "method_b_live_audit", "tri_model_stiffness_audit.json")
    assert os.path.exists(audit_json), "Tri-model stiffness audit JSON must exist"

    with open(audit_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    models = data["models"]

    # 1. Canonical Reference 15k
    ref = models["reference_15k"]
    assert abs(ref["K0_kN_per_mm"] - 137.945520) < 1e-4, f"Ref K0 mismatch: {ref['K0_kN_per_mm']}"
    assert abs(ref["intercept_kN"] - 4.472368e-5) < 1e-9, f"Ref intercept mismatch: {ref['intercept_kN']}"
    assert ref["R2"] > 0.9999995
    assert ref["fit_points"] == 400

    # 2. Historical ET2 6k
    et2 = models["historical_et2_6k"]
    assert abs(et2["K0_kN_per_mm"] - 137.976065) < 1e-4
    assert abs(et2["delta_K0_pct"] - 0.0221) < 0.005
    assert abs(et2["intercept_kN"] - 4.478782e-5) < 1e-8
    assert abs(et2["delta_intercept_kN"]) < 1e-7
    assert et2["R2"] > 0.9999995
    assert et2["fit_points"] == 400

    # 3. Method B Native 14k
    nat = models["genuine_method_b_14k"]
    assert abs(nat["K0_kN_per_mm"] - 137.891881) < 1e-4
    assert abs(nat["delta_K0_pct"] - (-0.0389)) < 0.005
    assert abs(nat["intercept_kN"] - 4.477719e-5) < 1e-8
    assert abs(nat["delta_intercept_kN"]) < 1e-7
    assert nat["R2"] > 0.9999995
    assert nat["fit_points"] == 400

def test_extractor_python27_compatibility_and_optimization():
    extractor_path = os.path.join(REPO_ROOT, "scripts", "postprocessing", "extract_mode1_fracture_odb.py")
    assert os.path.exists(extractor_path), "Extractor script must exist"

    with open(extractor_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Must NOT contain exist_ok=True (which fails in Python 2.7 / Abaqus Python)
    assert "exist_ok=True" not in code, "Must avoid exist_ok=True for Python 2.7 compatibility"
    assert "if not os.path.exists" in code, "Must use standard os.path.exists check"

    # Must contain O(1) rp_set optimization
    assert "rp_set" in code, "Must implement rp_set node set optimization"
    assert "getSubset(region=rp_set)" in code, "Must use getSubset for fast O(1) frame extraction"

def test_harvesting_scripts_and_chaining_setup():
    submit_pbs = os.path.join(REPO_ROOT, "scripts", "postprocessing", "submit_harvest_job.pbs")
    harvest_sh = os.path.join(REPO_ROOT, "scripts", "postprocessing", "harvest_mode1_terminal_results.sh")

    assert os.path.exists(submit_pbs), "submit_harvest_job.pbs must exist"
    assert os.path.exists(harvest_sh), "harvest_mode1_terminal_results.sh must exist"

    with open(submit_pbs, "r", encoding="utf-8") as f:
        pbs_code = f.read()

    assert "#PBS -N M1_HARVEST" in pbs_code
    assert "harvest_mode1_terminal_results.sh" in pbs_code
    assert "job_notifications.sh" in pbs_code

    with open(harvest_sh, "r", encoding="utf-8") as f:
        sh_code = f.read()

    assert "M1_MB_FINAL_1S" in sh_code
    assert "M1_MB_NATIVE_FINAL_1S" in sh_code
    assert "extract_mode1_fracture_odb.py" in sh_code
