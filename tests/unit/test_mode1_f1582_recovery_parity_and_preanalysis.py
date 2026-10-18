"""
Unit and regression test suite for Task F1582:
Recovery of Packages 55 and 56, exact same-mesh continuation parity,
and independent native MISESERI continuum pre-analysis qualification (Package 46).
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXPECTED_PRODUCTION_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
EXPECTED_OFFSET_UEL_SHA256 = "ef92ed58dbe3ea921b48cb328128ab950ba2cafd698e05381e2b29f61412514d"
EXPECTED_PKG46_INP_SHA256 = "219acdf263f4f4096943b1ac976063722f927934c26458d593f7f714b84b8c56"


def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_subroutines_frozen_and_invariant():
    pkg55_uel = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "55_continuous_650_element_forward_reference", "f42_mixed_uel.for")
    assert os.path.exists(pkg55_uel)
    assert compute_sha256(pkg55_uel) == EXPECTED_PRODUCTION_UEL_SHA256, "Production UEL must remain 100% bitwise frozen"

    pkg56_uel = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "56_method_c_samemesh_reconstruction", "f42_experimental_offset_uel.for")
    assert os.path.exists(pkg56_uel)
    assert compute_sha256(pkg56_uel) == EXPECTED_OFFSET_UEL_SHA256, "Experimental offset UEL must match qualified revision"


def test_package55_job_1415067_continuous_forward_reference():
    eval_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "55_continuous_650_element_forward_reference", "evidence_1415067", "JOB_1415067_EVALUATION.json")
    assert os.path.exists(eval_path)
    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["pbs_job_id"] == "1415067.mmaster02"
    assert data["status"] == "COMPLETED"
    assert data["exit_code"] == 0
    assert data["mesh_properties"]["elements"] == 650
    assert data["mesh_properties"]["nodes"] == 713
    assert data["increments"]["total_increments"] == 72
    assert data["checkpoints"]["endpoint_u00290"]["u_mm"] == 0.00290


def test_package56_job_1415069_samemesh_reconstruction_and_continuation():
    eval_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "56_method_c_samemesh_reconstruction", "evidence_1415069", "JOB_1415069_EVALUATION.json")
    assert os.path.exists(eval_path)
    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["pbs_job_id"] == "1415069.mmaster02"
    assert data["status"] == "COMPLETED"
    assert data["exit_code"] == 0
    assert data["reconstruction_parity_u00270"]["step1_iterations"] == 2
    assert data["reconstruction_parity_u00270"]["step1_cutbacks"] == 0
    assert data["continuation_parity_u00290"]["step2_cutbacks"] == 0


def test_exact_continuation_parity_between_package55_and_56():
    eval_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "56_method_c_samemesh_reconstruction", "evidence_1415069", "JOB_1415069_EVALUATION.json")
    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cont = data["continuation_parity_u00290"]
    assert pytest.approx(cont["reference_rf2_n"], rel=1e-5) == cont["continued_rf2_n"]
    assert pytest.approx(cont["reference_e_frac_knmm"], rel=1e-5) == cont["continued_e_frac_knmm"]
    assert pytest.approx(cont["reference_e_tot_knmm"], rel=1e-5) == cont["continued_e_tot_knmm"]
    assert cont["delta_rf2_pct"] < 0.001
    assert cont["delta_e_frac_pct"] < 0.001
    assert cont["delta_e_tot_pct"] < 0.001


def test_damage_healing_deficit_resolved_on_identical_grid():
    eval_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "56_method_c_samemesh_reconstruction", "evidence_1415069", "JOB_1415069_EVALUATION.json")
    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    recon = data["reconstruction_parity_u00270"]
    # min_delta_d is -0.00012, proving spatial interpolation was 100% of the -0.0810 violation
    assert recon["min_delta_d"] > -0.001
    assert abs(recon["delta_e_tot_pct"]) < 0.05
    assert abs(recon["delta_e_frac_pct"]) < 0.10


def test_package46_job_1415074_continuum_preanalysis_evaluation():
    eval_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "46_mode1_coarse_preanalysis_density_sensitivity", "evidence_1415074", "JOB_1415074_EVALUATION.json")
    assert os.path.exists(eval_path)
    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["pbs_job_id"] == "1415074.mmaster02"
    assert data["status"] == "COMPLETED"
    assert data["exit_code"] == 0
    assert data["mesh_properties"]["elements"] == 4900
    assert data["mesh_properties"]["nodes"] == 5076
    assert data["mesh_properties"]["element_type"] == "CPE4"
    assert data["step_metrics"]["total_increments"] == 100
    assert data["step_metrics"]["total_cutbacks"] == 0
    assert pytest.approx(data["step_metrics"]["terminal_rf2_n"], rel=1e-2) == 674.22
    assert pytest.approx(data["step_metrics"]["structural_stiffness_k0_kn_per_mm"], rel=1e-2) == 134.84
    assert data["step_metrics"]["miseseri_output_available"] is True
