# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_framework_package.py
===================================================
Task: METHOD-C-CASE3-SINGLE-JOB-FRAMEWORK-BUILD
Correlation: HND-METHOD-C-CASE3-FRAMEWORK-PREP-001

Unit test suite validating the single-job multi-cycle adaptive remeshing framework:
1. Frozen UEL bitwise verification (CE8D5EDC...)
2. Minimized corridor geometry (x in [8.5, 20], y in [60, 77], area 195.5 mm^2, h_ref <= l0/2)
3. 5-cycle progression schedule (0.05 -> 0.4125 -> 0.7750 -> 1.1375 -> 1.5000 mm)
4. Cutback floor detection and terminal converged frame extraction from .sta
5. Force, energy (Gc-normalized), and non-healing gate evaluation
6. PBS script configuration (16 CPUs, 48 GB, 72 h, dual-channel notifications)
7. Framework manifest schema and accounting integrity (cumulative 67 preserved)
8. Element area and characteristic size h = sqrt(Area) calculation
"""

from __future__ import print_function, division
import os
import sys
import json
import tempfile
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.case3_single_job_orchestrator import (
    Case3SingleJobOrchestrator,
    parse_sta_file,
    compute_sha256,
    FROZEN_UEL_SHA256,
    BENCHMARK_GC_KN_MM,
    BENCHMARK_L0_MM,
    H_REF_MM,
    CORRIDOR_X_MIN,
    CORRIDOR_X_MAX,
    CORRIDOR_Y_MIN,
    CORRIDOR_Y_MAX,
    CYCLE_TARGETS,
)
from scripts.remeshing.generate_case3_adaptive_corridor_mesh import (
    compute_element_area_and_h,
    evaluate_corridor_audit,
    get_corridor_partition_spec,
)

PACKAGE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")
MANIFEST_PATH = os.path.join(PACKAGE_DIR, "METHOD_C_CASE3_FRAMEWORK_MANIFEST.json")
PBS_PATH = os.path.join(PACKAGE_DIR, "submit_case3_single_job_framework.pbs")
UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")

def test_frozen_uel_sha256():
    """Verify bitwise integrity of f42_mixed_uel.for."""
    assert os.path.isfile(UEL_PATH), "Frozen UEL file not found"
    actual_hash = compute_sha256(UEL_PATH)
    assert actual_hash == FROZEN_UEL_SHA256, "Frozen UEL SHA256 mismatch"
    assert actual_hash == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def test_orchestrator_initialization_and_verification():
    """Verify Case3SingleJobOrchestrator verifies prerequisites and generates plan."""
    orch = Case3SingleJobOrchestrator(run_dir=PACKAGE_DIR, uel_path=UEL_PATH, dry_run=True)
    assert orch.verify_prerequisites() is True
    plan = orch.run_dry_run_plan()
    assert plan["architecture"] == "SINGLE_PBS_JOB_IN_ALLOCATION_ORCHESTRATOR"
    assert len(plan["cycles"]) == 5
    assert plan["pbs_allocation"]["ncpus"] == 16
    assert plan["pbs_allocation"]["mem_gb"] == 48
    assert plan["pbs_allocation"]["walltime_hours"] == 72

def test_minimized_corridor_geometry():
    """Verify corridor partition box dimensions and area."""
    width = CORRIDOR_X_MAX - CORRIDOR_X_MIN
    height = CORRIDOR_Y_MAX - CORRIDOR_Y_MIN
    area = width * height
    assert width == 11.5
    assert height == 17.0
    assert abs(area - 195.5) < 1e-4
    assert H_REF_MM == 0.140
    assert H_REF_MM < (BENCHMARK_L0_MM / 2.0)
    spec = get_corridor_partition_spec()
    assert spec["corridor_box"]["area_mm2"] == 195.5
    assert spec["target_mesh_metrics"]["target_total_elements"] == 30000

def test_cycle_schedule_monotonicity():
    """Verify the 5-cycle schedule and increasing load targets."""
    targets = [c["u2_target_mm"] for c in CYCLE_TARGETS]
    assert targets == [0.0500, 0.4125, 0.7750, 1.1375, 1.5000]
    for i in range(len(targets) - 1):
        assert targets[i] < targets[i + 1], "Cycle targets must strictly increase"

def test_sta_cutback_parsing():
    """Verify .sta file parser detects cutback floor and terminal converged state."""
    sample_sta = """
 SUMMARY OF JOB INFORMATION:
 STEP  INC ATT SEVERE EQUIP    TOTAL TIME  STEP TIME    INC TIME
                DISCON DISCON
   1     1   1      0     0     0.00500     0.00500      0.00500
   1     2   1      0     0     0.01000     0.01000      0.00500
   1    11   1      0     0     0.04500     0.0021379    0.00010
   1    12   1U     0     0     0.04500     0.0021379    1.000E-15
 ***ERROR: TIME INCREMENT REQUIRED IS LESS THAN THE MINIMUM SPECIFIED
 THE ANALYSIS HAS NOT BEEN COMPLETED
"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
        tf.write(sample_sta)
        tf_name = tf.name

    try:
        res = parse_sta_file(tf_name)
        assert res["total_converged_increments"] == 3
        assert res["terminal_converged"]["increment"] == 11
        assert abs(res["terminal_converged"]["step_time"] - 0.0021379) < 1e-6
        assert res["cutback_floor_reached"] is True

        orch = Case3SingleJobOrchestrator(run_dir=PACKAGE_DIR, uel_path=UEL_PATH)
        eval_res = orch.evaluate_cutback_state(tf_name)
        assert eval_res["status"] == "CUTBACK_TERMINATED"
        assert eval_res["terminal_increment"] == 11
        assert eval_res["dt_min_floor_reached"] is True
        assert eval_res["no_further_dt_min_reduction"] is True
    finally:
        os.remove(tf_name)

def test_gate_evaluation_physics():
    """Verify force continuity, Gc-normalized energy, and non-healing gates."""
    orch = Case3SingleJobOrchestrator(run_dir=PACKAGE_DIR, uel_path=UEL_PATH)

    # Test case 1: Nominal passing transition
    gates1 = orch.evaluate_gates(
        donor_rf2=4.00,
        receiver_step1_rf2=3.95,  # -1.25%
        donor_e_frac=0.0100,
        receiver_step1_e_frac=0.0102,  # +2.0%
        donor_d_max=0.950,
        terminal_d_max=0.960
    )
    assert gates1["force_continuity_pass"] is True
    assert gates1["energy_continuity_status"] == "PASS"
    assert gates1["zero_healing_pass"] is True

    # Test case 2: Disclosed parameter deviation with Gc change (Job 5 case)
    gates2 = orch.evaluate_gates(
        donor_rf2=3.8767,
        receiver_step1_rf2=3.8767,  # 0.0%
        donor_e_frac=0.0159247,
        receiver_step1_e_frac=0.0148491,  # -6.75%
        donor_d_max=0.9999,
        terminal_d_max=1.0000,
        donor_gc=0.00270,
        receiver_gc=0.00228
    )
    assert gates2["force_continuity_pass"] is True
    assert gates2["energy_continuity_status"] == "DISCLOSED_PARAMETER_DEVIATION"
    assert gates2["normalized_gamma_delta_pct"] > 0  # Gamma increased
    assert gates2["zero_healing_pass"] is True

def test_pbs_script_directives():
    """Verify PBS submission script directives and structure."""
    assert os.path.isfile(PBS_PATH), "submit_case3_single_job_framework.pbs missing"
    with open(PBS_PATH, "r") as f:
        content = f.read()

    assert "#PBS -l select=1:ncpus=16:mpiprocs=1:ompthreads=16:mem=48gb" in content
    assert "#PBS -l walltime=72:00:00" in content
    assert "#PBS -m abe" in content
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in content
    assert "case3_single_job_orchestrator.py" in content
    assert "job_notifications.sh" in content

def test_manifest_schema_and_integrity():
    """Verify METHOD_C_CASE3_FRAMEWORK_MANIFEST.json structure and accounting."""
    assert os.path.isfile(MANIFEST_PATH), "Framework manifest missing"
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    assert manifest["benchmark"]["material_parameters"]["Gc_kN_per_mm"] == 0.00228
    assert manifest["benchmark"]["material_parameters"]["l0_mm"] == 0.285
    assert manifest["single_job_architecture"]["frozen_uel"]["sha256"] == FROZEN_UEL_SHA256
    assert manifest["refinement_corridor_minimization"]["corridor_box"]["area_mm2"] == 195.5
    assert len(manifest["cycle_schedule"]) == 5
    assert manifest["runtime_policies"]["dt_min_floor_behaviour"]["floor_threshold"] == 1.0e-14
    assert manifest["accounting"]["current_cumulative_pbs_submissions"] == 67
    assert manifest["accounting"]["framework_build_pbs_consumed"] == 0
    assert manifest["accounting"]["authorized_first_run_pbs_submissions"] == 1

def test_element_characteristic_size():
    """Verify compute_element_area_and_h computes sqrt(Area) correctly."""
    # Unit quad: area = 1.0, h = 1.0
    quad_coords = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    area_q, h_q = compute_element_area_and_h(quad_coords)
    assert abs(area_q - 1.0) < 1e-6
    assert abs(h_q - 1.0) < 1e-6

    # Triangle: base = 1.0, height = 2.0 -> area = 1.0, h = 1.0
    tri_coords = [(0.0, 0.0), (1.0, 0.0), (0.0, 2.0)]
    area_t, h_t = compute_element_area_and_h(tri_coords)
    assert abs(area_t - 1.0) < 1e-6
    assert abs(h_t - 1.0) < 1e-6
