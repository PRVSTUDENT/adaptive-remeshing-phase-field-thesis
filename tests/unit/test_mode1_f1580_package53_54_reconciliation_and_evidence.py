"""
Unit and regression test suite for Task F1580:
Package 53 and Package 54 Reconciliation, Slit Topology Defect Resolution,
and Energy Preservation Audit.
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXPECTED_PRODUCTION_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
EXPECTED_OFFSET_UEL_SHA256 = "ef92ed58dbe3ea921b48cb328128ab950ba2cafd698e05381e2b29f61412514d"
EXPECTED_PKG53_INP_SHA256 = "bdfee81485c7b3ebb050397841bae3f6437936db5d207c879c6bcb363d9cf285"
EXPECTED_PKG54_INP_SHA256 = "3a959cad7e56132b4854d994e2bf3c72abbbb3ebba77df2c999ed48cfc507214"


def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_subroutines_frozen_and_invariant():
    pkg54_uel = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "54_continuous_650_element_corrected_reference", "f42_mixed_uel.for")
    assert os.path.exists(pkg54_uel), f"Missing Package 54 UEL at {pkg54_uel}"
    assert compute_sha256(pkg54_uel) == EXPECTED_PRODUCTION_UEL_SHA256, "Production UEL must remain 100% bitwise frozen"

    pkg53_uel = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "53_method_c_corrected_nonmatching_transfer", "f42_experimental_offset_uel.for")
    assert os.path.exists(pkg53_uel), f"Missing Package 53 UEL at {pkg53_uel}"
    assert compute_sha256(pkg53_uel) == EXPECTED_OFFSET_UEL_SHA256, "Experimental offset UEL must match qualified revision"


def test_input_deck_hashes():
    pkg53_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "53_method_c_corrected_nonmatching_transfer", "M1_EXP_NONMATCHING_CONT_650.inp")
    assert os.path.exists(pkg53_inp)
    assert compute_sha256(pkg53_inp) == EXPECTED_PKG53_INP_SHA256

    pkg54_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "54_continuous_650_element_corrected_reference", "M1_650_CONTINUOUS_CORRECTED_REF.inp")
    assert os.path.exists(pkg54_inp)
    assert compute_sha256(pkg54_inp) == EXPECTED_PKG54_INP_SHA256


def test_package53_job_1415063_evaluation():
    eval_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "53_method_c_corrected_nonmatching_transfer", "evidence_1415063", "JOB_1415063_EVALUATION.json")
    assert os.path.exists(eval_path), f"Missing evaluation file at {eval_path}"
    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["pbs_job_id"] == "1415063.mmaster02"
    assert data["status"] == "COMPLETED"
    assert data["exit_code"] == 0
    assert data["mesh_properties"]["receiver_slit_a0_mm"] == 0.04
    assert data["mesh_properties"]["receiver_slit_duplicate_node_pairs"] == 11
    assert data["solver_metrics"]["step1_increments"] == 1
    assert data["solver_metrics"]["step1_iterations"] == 18
    assert data["solver_metrics"]["step1_cutbacks"] == 0
    assert data["solver_metrics"]["step2_increments"] == 3
    assert data["solver_metrics"]["step2_cutbacks"] == 0
    assert data["solver_metrics"]["energy_dissipation_monotonic"] is True

    # Check energy preservation against donor
    assert pytest.approx(data["solver_metrics"]["delta_e_fracture_pct"], rel=1e-2) == 2.945
    assert pytest.approx(data["solver_metrics"]["delta_e_total_pct"], rel=1e-2) == 1.121


def test_package54_job_1415065_evaluation():
    eval_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "54_continuous_650_element_corrected_reference", "evidence_1415065", "JOB_1415065_EVALUATION.json")
    assert os.path.exists(eval_path), f"Missing evaluation file at {eval_path}"
    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["pbs_job_id"] == "1415065.mmaster02"
    assert data["status"] == "COMPLETED"
    assert data["exit_code"] == 0
    assert data["mesh_properties"]["slit_a0_mm"] == 0.04
    assert data["mesh_properties"]["slit_duplicate_node_pairs"] == 11
    assert data["solver_metrics"]["step1_increments"] == 57
    assert data["solver_metrics"]["step2_increments"] == 5
    assert data["solver_metrics"]["step2_cutbacks"] == 0
    assert pytest.approx(data["solver_metrics"]["peak_reaction_force_n"], rel=1e-2) == 183.96
    assert pytest.approx(data["solver_metrics"]["checkpoint_u00258"]["rf2_n"], rel=1e-2) == 12.27
    assert pytest.approx(data["solver_metrics"]["continuation_endpoint_u00270"]["rf2_n"], rel=1e-2) == 3.86


def test_continuation_endpoint_parity_between_transferred_and_continuous_650():
    # Package 53 transferred continuation endpoint at u = 0.00270 mm
    pkg53_eval = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "53_method_c_corrected_nonmatching_transfer", "evidence_1415063", "JOB_1415063_EVALUATION.json")
    with open(pkg53_eval, "r", encoding="utf-8") as f:
        d53 = json.load(f)

    # Package 54 continuous reference endpoint at u = 0.00270 mm
    pkg54_eval = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "54_continuous_650_element_corrected_reference", "evidence_1415065", "JOB_1415065_EVALUATION.json")
    with open(pkg54_eval, "r", encoding="utf-8") as f:
        d54 = json.load(f)

    e_frac_53 = d53["solver_metrics"]["step2_inc3_e_fracture_knmm"]
    e_frac_54 = d54["solver_metrics"]["continuation_endpoint_u00270"]["e_fracture_knmm"]
    delta_frac_pct = (e_frac_53 - e_frac_54) / e_frac_54 * 100.0

    e_tot_53 = d53["solver_metrics"]["step2_inc3_e_total_knmm"]
    e_tot_54 = d54["solver_metrics"]["continuation_endpoint_u00270"]["e_total_knmm"]
    delta_tot_pct = (e_tot_53 - e_tot_54) / e_tot_54 * 100.0

    # Verify tight energetic parity at continuation endpoint
    assert abs(delta_frac_pct) < 1.0, f"Fracture energy error too high: {delta_frac_pct}%"
    assert abs(delta_tot_pct) < 1.0, f"Total energy error too high: {delta_tot_pct}%"
    assert pytest.approx(delta_frac_pct, abs=0.1) == 0.34
    assert pytest.approx(delta_tot_pct, abs=0.1) == -0.53
