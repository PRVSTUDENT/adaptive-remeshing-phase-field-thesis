import hashlib
import json
import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXPECTED_PRODUCTION_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
EXPECTED_OFFSET_UEL_SHA256 = "ef92ed58dbe3ea921b48cb328128ab950ba2cafd698e05381e2b29f61412514d"
EXPECTED_PKG52_INP_SHA256 = "7d3e8ca3bacc9846cf7b4b46e287ef1f727f51d4e75811278f52086d721ad9e3"


def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_production_and_offset_subroutines_frozen():
    # Production UEL in Package 52
    pkg52_uel = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "52_continuous_650_element_reference", "f42_mixed_uel.for")
    assert os.path.exists(pkg52_uel), f"Missing Package 52 UEL at {pkg52_uel}"
    assert compute_sha256(pkg52_uel) == EXPECTED_PRODUCTION_UEL_SHA256

    # Offset UEL in Package 50 and Package 51
    pkg50_uel = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "50_method_c_experimental_offset_continuation", "f42_experimental_offset_uel.for")
    pkg51_uel = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "51_method_c_nonmatching_transfer_continuation", "f42_experimental_offset_uel.for")
    assert os.path.exists(pkg50_uel)
    assert os.path.exists(pkg51_uel)
    assert compute_sha256(pkg50_uel) == EXPECTED_OFFSET_UEL_SHA256
    assert compute_sha256(pkg51_uel) == EXPECTED_OFFSET_UEL_SHA256


def test_package52_input_integrity():
    pkg52_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "52_continuous_650_element_reference", "M1_650_CONTINUOUS_REF.inp")
    assert os.path.exists(pkg52_inp), f"Missing Package 52 INP at {pkg52_inp}"
    assert compute_sha256(pkg52_inp) == EXPECTED_PKG52_INP_SHA256


def test_job_1415044_execution_and_metrics():
    eval_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "52_continuous_650_element_reference", "evidence_1415044", "JOB_1415044_EVALUATION.json")
    assert os.path.exists(eval_path), f"Missing evaluation file at {eval_path}"
    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["pbs_job_id"] == "1415044.mmaster02"
    assert data["status"] == "COMPLETED"
    assert data["exit_code"] == 0
    assert data["exec_host"] == "mnode097/0"
    assert data["queue"] == "normal_imfdfkmq"
    assert data["solver_metrics"]["step1_increments"] == 45
    assert data["solver_metrics"]["step1_cutbacks"] == 0
    assert data["solver_metrics"]["step2_increments"] == 5
    assert data["solver_metrics"]["step2_cutbacks"] == 0
    assert data["solver_metrics"]["step2_iterations"] == [2, 2, 2, 2, 2]

    # Plateau checkpoint (u = 0.00258 mm)
    p = data["checkpoint_metrics"]["plateau_u00258"]
    assert pytest.approx(p["u2_mm"], rel=1e-5) == 0.002580
    assert pytest.approx(p["rf2_n"], rel=1e-3) == 64.7848
    assert pytest.approx(p["e_fracture_knmm"], rel=1e-3) == 3.21315e-04
    assert pytest.approx(p["d_max"], rel=1e-3) == 0.9982

    # Continuation endpoint (u = 0.00270 mm)
    c = data["checkpoint_metrics"]["continuation_endpoint_u00270"]
    assert pytest.approx(c["u2_mm"], rel=1e-5) == 0.002700
    assert pytest.approx(c["rf2_n"], rel=1e-3) == 64.5444
    assert pytest.approx(c["e_fracture_knmm"], rel=1e-3) == 3.25438e-04
    assert pytest.approx(c["d_max"], rel=1e-3) == 0.9984


def test_three_way_triangulation_and_root_cause_diagnosis():
    tri_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "52_continuous_650_element_reference", "evidence_1415044", "THREE_WAY_TRIANGULATION_ANALYSIS.json")
    assert os.path.exists(tri_path), f"Missing triangulation file at {tri_path}"
    with open(tri_path, "r", encoding="utf-8") as f:
        tri = json.load(f)

    # Slit lengths
    assert tri["cases"]["Case_A"]["initial_slit_length_a0_mm"] == 0.040
    assert tri["cases"]["Case_B"]["initial_slit_length_a0_mm"] == 0.020
    assert tri["cases"]["Case_C"]["initial_slit_length_a0_mm"] == 0.020

    # Geometric discrepancy & physical mechanism verified
    root_cause = tri["scientific_synthesis"]["root_cause_diagnosis"]
    assert "a0 = 0.040 mm" in root_cause["geometric_discrepancy"]
    assert "slit_a = 0.020 mm" in root_cause["geometric_discrepancy"]
    assert "welded" in root_cause["consequence_for_case_b"]
    assert "3,046 sample points" in root_cause["irreversibility_reinterpretation"]
