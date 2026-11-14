# -*- coding: utf-8 -*-
"""
tests/unit/test_f1735_case2_adapted_fracture_qualification.py

Unit test suite validating the Task F1735 preflight audit, output architecture
mapping, incremental loading schedule, and HPC resource qualifications.
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.remeshing.audit_f1735_fracture_preflight import run_f1735_preflight_audit

@pytest.fixture(scope="module")
def preflight_results():
    return run_f1735_preflight_audit()

def test_source_files_and_hash_integrity(preflight_results):
    res = preflight_results
    assert res["deck_sha256"] == "805AF9D80126588C1A3E39FE3B5F7A0F53DB606106F2DBFE6260F1E1FBDDBF94"
    assert res["uel_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert res["physical_elements"] == 23965
    assert res["total_layered_elements"] == 71895

def test_output_architecture_mapping(preflight_results):
    out = preflight_results["output_mapping"]
    # Reaction force and displacement on reference point node 999999
    assert out["reaction_force_observable"]["node"] == 999999
    assert out["reaction_force_observable"]["component"] == "RF2"
    assert out["displacement_observable"]["node"] == 999999
    assert out["displacement_observable"]["component"] == "U2"
    # Phase-field damage on visualizer layer umatelem
    assert out["phase_field_damage_observable"]["variable"] == "SDV1"
    assert out["phase_field_damage_observable"]["backup_variable"] == "SDV14"
    # History field on visualizer layer
    assert out["history_field_observable"]["variable"] == "SDV2"
    assert out["history_field_observable"]["backup_variable"] == "SDV16"
    # Energies
    assert out["fracture_energy_observable"]["integrated_element_energy_kn_mm"] == "SDV17"
    assert out["strain_energy_observable"]["integrated_element_energy_kn_mm"] == "SDV18"
    # Cauchy stress zero by design in visualizer
    assert out["cauchy_stress_observable"]["status"] == "ZERO_BY_DESIGN_IN_VISUALIZER"

def test_incremental_loading_schedule(preflight_results):
    load = preflight_results["loading_audit"]
    # Step-1 is pre-critical
    assert load["step_1"]["target_uy_mm"] == 0.005
    assert load["step_1"]["target_uy_mm"] < load["step_1"]["coarse_peak_uy_mm"]
    assert load["step_1"]["regime"] == "PRECRITICAL_LINEAR_ELASTIC"
    # Step-2 traverses peak and softening
    assert load["step_2"]["target_uy_mm"] == 0.012
    assert load["step_2"]["total_step_delta_uy_mm"] == 0.007
    assert load["step_2"]["min_increment_dt"] == 1.0e-8
    assert load["step_2"]["max_increments"] == 20000

def test_hpc_resource_qualification(preflight_results):
    hpc = preflight_results["hpc_audit"]
    assert hpc["execution_mode"] == "SINGLE_RANK_SHARED_MEMORY_SMP"
    assert hpc["cpus"] == 8
    assert hpc["memory_request_gb"] == 32
    assert hpc["walltime_request_hrs"] == 8
    assert hpc["projected_runtime_hrs"] < hpc["walltime_request_hrs"]
    assert "MULTI_RANK_MPI_STRICTLY_DISQUALIFIED" in hpc["parallel_safety_rationale"].upper()

def test_predeclared_scientific_checks(preflight_results):
    checks = preflight_results["scientific_checks"]
    assert len(checks) == 6
    check_ids = [c["id"] for c in checks]
    assert "CHK-SCI-01" in check_ids
    assert "CHK-SCI-02" in check_ids
    assert "CHK-SCI-03" in check_ids
    assert "CHK-SCI-04" in check_ids
    assert "CHK-SCI-05" in check_ids
    assert "CHK-SCI-06" in check_ids

def test_preflight_verdict(preflight_results):
    assert preflight_results["preflight_verdict"] == "PREFLIGHT_AND_OUTPUT_ARCHITECTURE_QUALIFIED_READY_FOR_AUTHORIZATION_DISPATCH"
