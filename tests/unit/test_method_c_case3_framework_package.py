# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_framework_package.py
===================================================
Task: METHOD-C-CASE3-SINGLE-JOB-FRAMEWORK-BUILD-AND-TEST
Correlation: HND-METHOD-C-CASE3-FRAMEWORK-TEST-001

Unit test suite validating the revised single-job multi-cycle adaptive remeshing framework:
1. Frozen UEL bitwise verification (CE8D5EDC...)
2. Parameterised n_adaptive_steps and equal-load-division schedule (no 1.5 mm cap)
3. Crack completion criteria (tip x >= 64 mm or RF2 < 5% of peak)
4. Minimized corridor geometry (x in [8.5, 20], y in [60, 77], area 195.5 mm^2, h_ref <= l0/2)
5. Cutback floor detection and terminal converged frame extraction from .sta
6. Force (with authentic Job-5 RF2 values), energy (Gc-normalized), and non-healing gate evaluation
7. PBS script configuration (16 CPUs, 48 GB, 72 h, dual-channel notifications, live execution call)
8. Framework manifest schema, parameters, and accounting integrity
9. Notification script job_notifications.sh presence in package folder
10. Generated minimized corridor physical mesh audit (24,832 elements, 97.41% quad)
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
    parse_physical_inp,
    assemble_coupled_deck,
    transfer_nodal_fields,
    transfer_gp_history,
    FROZEN_UEL_SHA256,
    BENCHMARK_GC_KN_MM,
    BENCHMARK_L0_MM,
    H_REF_MM,
    CORRIDOR_X_MIN,
    CORRIDOR_X_MAX,
    CORRIDOR_Y_MIN,
    CORRIDOR_Y_MAX,
    CRACK_COMPLETION_X_MM,
    LOAD_DROP_COMPLETION_RATIO,
    DEFAULT_N_ADAPTIVE_STEPS,
    DEFAULT_LOAD_INCREMENT_MM,
)
from scripts.remeshing.generate_case3_adaptive_corridor_mesh import (
    compute_element_area_and_h,
    get_corridor_partition_spec,
)

PACKAGE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")
MANIFEST_PATH = os.path.join(PACKAGE_DIR, "METHOD_C_CASE3_FRAMEWORK_MANIFEST.json")
PBS_PATH = os.path.join(PACKAGE_DIR, "submit_case3_single_job_framework.pbs")
NOTIF_PATH = os.path.join(PACKAGE_DIR, "job_notifications.sh")
PHYS_MESH_PATH = os.path.join(PACKAGE_DIR, "PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp")
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
    assert plan["configuration"]["n_adaptive_steps"] == DEFAULT_N_ADAPTIVE_STEPS
    assert plan["configuration"]["load_increment_mm"] == DEFAULT_LOAD_INCREMENT_MM
    assert plan["configuration"]["no_displacement_cap"] is True
    assert len(plan["planned_initial_cycles"]) == 5  # Coarse + 4 adaptive
    assert plan["pbs_allocation"]["ncpus"] == 16
    assert plan["pbs_allocation"]["mem_gb"] == 48
    assert plan["pbs_allocation"]["walltime_hours"] == 72

def test_parameterised_steps_and_equal_load_division():
    """Verify user-settable n_adaptive_steps and equal load increment without cap."""
    orch6 = Case3SingleJobOrchestrator(run_dir=PACKAGE_DIR, n_adaptive_steps=6, load_increment_mm=0.015, uel_path=UEL_PATH)
    plan6 = orch6.generate_plan()
    assert len(plan6) == 7  # Coarse + 6 adaptive
    # Check monotonic equal progression
    for i in range(1, 7):
        assert plan6[i]["load_increment_mm"] == 0.015
        expected_target = round(0.05 + i * 0.015, 6)
        assert abs(plan6[i]["u2_target_mm"] - expected_target) < 1e-6

def test_crack_completion_criteria():
    """Verify completion check on crack tip position (>= 64 mm) and load drop (< 5% of peak)."""
    orch = Case3SingleJobOrchestrator(run_dir=PACKAGE_DIR, uel_path=UEL_PATH)

    # In-progress state
    done, reason = orch.check_completion(current_tip_x=14.0, current_rf2=3.80, peak_rf2=4.00)
    assert done is False
    assert reason is None

    # Criterion A: Tip reached plate edge (x >= 64 mm)
    done_a, reason_a = orch.check_completion(current_tip_x=64.2, current_rf2=2.00, peak_rf2=4.00)
    assert done_a is True
    assert "CRACK_FULLY_PROPAGATED_TO_PLATE_EDGE" in reason_a

    # Criterion B: Structural load drop < 5% of peak (severed plate)
    done_b, reason_b = orch.check_completion(current_tip_x=35.0, current_rf2=0.15, peak_rf2=4.00)  # 0.15 < 0.20 (5%)
    assert done_b is True
    assert "PLATE_SEVERED_LOAD_DROP_BELOW_5PCT" in reason_b

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
    """Verify force continuity (using authentic Job-5 values), Gc-normalized energy, and non-healing."""
    orch = Case3SingleJobOrchestrator(run_dir=PACKAGE_DIR, uel_path=UEL_PATH)

    # Authentic Job-5 transition values (NOTE-FW-01 resolved)
    donor_rf2_j5 = 3.9063646
    receiver_rf2_j5 = 3.8692487  # -0.9501%
    gates_j5 = orch.evaluate_gates(
        donor_rf2=donor_rf2_j5,
        receiver_step1_rf2=receiver_rf2_j5,
        donor_e_frac=0.015924724,
        receiver_step1_e_frac=0.014849132,  # -6.75%
        donor_d_max=0.9999,
        terminal_d_max=1.0000,
        donor_gc=0.00270,
        receiver_gc=0.00228
    )
    assert abs(gates_j5["force_continuity_delta_pct"] - (-0.9501)) < 1e-3
    assert gates_j5["force_continuity_pass"] is True
    assert gates_j5["energy_continuity_status"] == "DISCLOSED_PARAMETER_DEVIATION"
    assert gates_j5["normalized_gamma_delta_pct"] > 0
    assert gates_j5["zero_healing_pass"] is True

def test_pbs_script_directives_and_execution_call():
    """Verify PBS script configuration and live orchestrator call."""
    assert os.path.isfile(PBS_PATH), "submit_case3_single_job_framework.pbs missing"
    with open(PBS_PATH, "r") as f:
        content = f.read()

    assert "#PBS -l select=1:ncpus=16:mpiprocs=1:ompthreads=16:mem=48gb" in content
    assert "#PBS -l walltime=72:00:00" in content
    assert "#PBS -m abe" in content
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in content
    assert "case3_single_job_orchestrator.py" in content
    assert "--n-adaptive-steps 4" in content
    assert "--load-increment-mm 0.01" in content
    assert "job_notifications.sh" in content

def test_manifest_schema_and_integrity():
    """Verify METHOD_C_CASE3_FRAMEWORK_MANIFEST.json structure, parameters, and accounting."""
    assert os.path.isfile(MANIFEST_PATH), "Framework manifest missing"
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    assert manifest["benchmark"]["material_parameters"]["Gc_kN_per_mm"] == 0.00228
    assert manifest["benchmark"]["material_parameters"]["l0_mm"] == 0.285
    assert manifest["single_job_architecture"]["frozen_uel"]["sha256"] == FROZEN_UEL_SHA256
    assert manifest["refinement_corridor_minimization"]["corridor_box"]["area_mm2"] == 195.5
    assert manifest["adaptive_schedule_parameters"]["n_adaptive_steps"] == 4
    assert manifest["adaptive_schedule_parameters"]["load_increment_mm"] == 0.0100
    assert manifest["adaptive_schedule_parameters"]["no_displacement_cap"] is True
    assert manifest["adaptive_schedule_parameters"]["crack_completion_criteria"]["terminal_tip_x_mm"] == 64.0
    assert manifest["runtime_policies"]["dt_min_floor_behaviour"]["floor_threshold"] == 1.0e-14
    assert manifest["accounting"]["current_cumulative_pbs_submissions"] == 67
    assert manifest["accounting"]["authorized_test_run_pbs_submissions"] == 1

def test_package_notification_script():
    """Verify job_notifications.sh exists directly inside package directory."""
    assert os.path.isfile(NOTIF_PATH), "job_notifications.sh missing from package"
    assert os.path.getsize(NOTIF_PATH) > 10000

def test_generated_adaptive_physical_mesh():
    """Verify generated PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp mesh metrics."""
    assert os.path.isfile(PHYS_MESH_PATH), "PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp not found"
    with open(PHYS_MESH_PATH, "r") as f:
        lines = f.readlines()[:10]
    header = "".join(lines)
    assert "24832 elements" in header
    assert "24738 nodes" in header
    assert "97.41% quad" in header

def test_physical_mesh_parsing_and_deck_assembly():
    """Verify parse_physical_inp and assemble_coupled_deck generate 3-layer UEL deck."""
    mesh = parse_physical_inp(PHYS_MESH_PATH)
    assert len(mesh["elements"]) == 24832
    assert len(mesh["nodes"]) == 24738
    assert len(mesh["quads"]) == 24189
    assert len(mesh["tris"]) == 643

    # Test assemble_coupled_deck on temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".inp") as tf:
        tmp_deck = tf.name

    try:
        # Dummy field dictionaries
        recip_d = {nid: 0.10 for nid in mesh["nodes"]}
        recip_h_gp = {}
        for eid in mesh["quads"]:
            for gp in range(1, 5):
                recip_h_gp[(eid, gp)] = 0.005
        for eid in mesh["tris"]:
            recip_h_gp[(eid, 1)] = 0.005

        assemble_coupled_deck(
            receiver_phys_inp=PHYS_MESH_PATH,
            out_deck_path=tmp_deck,
            recip_d=recip_d,
            recip_h_gp=recip_h_gp,
            donor_u2=0.0500,
            target_u2=0.0600,
            cycle_idx=1
        )

        assert os.path.isfile(tmp_deck)
        with open(tmp_deck, "r") as f:
            content = f.read()

        assert "*USER ELEMENT, NODES=4, TYPE=U1" in content  # Phase UEL quad
        assert "*USER ELEMENT, NODES=4, TYPE=U2" in content  # Disp UEL quad
        assert "*USER ELEMENT, NODES=3, TYPE=U3" in content  # Phase UEL tri
        assert "*USER ELEMENT, NODES=3, TYPE=U4" in content  # Disp UEL tri
        assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in content
        assert "*EQUATION" in content
        assert "Step-1-Hold" in content
        assert "Step-2-Advance" in content
        assert "0.0500" in content
        assert "0.0600" in content
    finally:
        if os.path.exists(tmp_deck):
            os.remove(tmp_deck)

def test_transfer_routines_bounds():
    """Verify transfer_nodal_fields and transfer_gp_history enforce physical bounds."""
    donor_mesh = {
        "nodes": {1: (0.0, 0.0), 2: (1.0, 0.0), 3: (1.0, 1.0), 4: (0.0, 1.0)},
        "quads": {1: (1, 2, 3, 4)},
        "tris": {},
        "elements": {1: (1, 2, 3, 4)}
    }
    receiver_mesh = {
        "nodes": {1: (0.5, 0.5)},
        "quads": {1: (1, 1, 1, 1)},
        "tris": {},
        "elements": {1: (1, 1, 1, 1)}
    }
    donor_u = {1: (0.0, 0.0), 2: (0.01, 0.0), 3: (0.01, 0.02), 4: (0.0, 0.02)}
    donor_d = {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.2}

    recip_u, recip_d = transfer_nodal_fields(donor_mesh, donor_u, donor_d, receiver_mesh, slit_y=70.0, slit_a0=10.0)
    assert 1 in recip_d
    assert 0.0 <= recip_d[1] <= 1.0
    assert abs(recip_d[1] - 0.2) < 1e-3

    donor_h = {(1, 1): 0.01, (1, 2): 0.02, (1, 3): 0.03, (1, 4): 0.02}
    recip_h = transfer_gp_history(donor_mesh, donor_h, receiver_mesh, limiter_mode="convex_clamp")
    for val in recip_h.values():
        assert val >= 0.0

def test_per_cycle_state_advancement_in_orchestrator():
    """Verify that extract_cycle_state updates orchestrator donor_state and observables."""
    orch = Case3SingleJobOrchestrator(run_dir=os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3"), dry_run=True)
    state = orch.extract_cycle_state("PK_METHOD_C_CASE3_COARSE_JOB1")
    assert state["tip_x"] == 10.0
    assert state["tip_y"] == 70.0
    assert state["step1_rf2"] == 3.928812
    assert state["terminal_rf2"] == 4.241979
    assert state["peak_rf2"] == 4.331821
    assert state["max_damage"] > 0.0
    assert state["max_history_MPa"] > 0.0

def test_donor_file_dynamic_observables_without_hardcoded_defaults():
    """Verify extract_cycle_state derives observables dynamically without hardcoded Job-1 fallbacks."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="_state.json") as tf:
        dummy_state = {
            "u_nodal": {"1": [0.01, 0.02]},
            "d_nodal": {"1": 0.55},
            "h_gp": {"1_1": 0.08},
            "tip_x": 12.5,
            "tip_y": 70.0,
            "peak_rf2": 4.10,
            "terminal_rf2": 3.95,
            "step1_rf2": 3.90,
            "e_frac": 0.0050
        }
        json.dump(dummy_state, tf)
        tmp_name = tf.name

    try:
        orch = Case3SingleJobOrchestrator(run_dir=os.path.dirname(tmp_name), dry_run=True)
        job_base = os.path.splitext(os.path.basename(tmp_name))[0].replace("_state", "")
        extracted = orch.extract_cycle_state(job_base)
        assert extracted["max_damage"] == 0.55
        assert extracted["max_history_MPa"] == 0.08
        assert extracted["tip_x"] == 12.5
        assert extracted["peak_rf2"] == 4.10
        assert extracted["terminal_rf2"] == 3.95
        assert extracted["step1_rf2"] == 3.90
        assert extracted["e_frac"] == 0.0050
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

def test_cycle0_run_artifacts_and_timing_reconciliation():
    """Verify committed Cycle-0 run artifacts and timing reconciliation (546 s solver CPU vs 559 s scheduler cput)."""
    case3_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")
    state_json = os.path.join(case3_dir, "PK_METHOD_C_CASE3_COARSE_JOB1_state.json")
    summary_json = os.path.join(case3_dir, "PK_METHOD_C_CASE3_COARSE_JOB1_SUMMARY.json")
    sta_file = os.path.join(case3_dir, "PK_METHOD_C_CASE3_COARSE_JOB1.sta")
    pbs_log = os.path.join(case3_dir, "PK_METHOD_C_CASE3_FRAMEWORK_CYCLE0_pbs_execution.log")

    for fpath in [state_json, summary_json, sta_file, pbs_log]:
        assert os.path.isfile(fpath), "Missing run artifact: %s" % fpath
        assert os.path.getsize(fpath) > 0, "Empty run artifact: %s" % fpath

    with open(state_json, "r") as f:
        state_data = json.load(f)

    assert state_data["solver_cpu_time_s"] == 546.0
    assert state_data["scheduler_cput_s"] == 559.0
    assert state_data["solver_walltime_s"] == 816.0
    assert state_data["scheduler_walltime_s"] == 2114.0
    assert state_data["tip_extraction_method"] == "nodal_damage_threshold_d_ge_0.95_and_notch_root_geometry"
    assert state_data["tip_damage_threshold"] == 0.95
    assert state_data["tip_x"] == 10.0
    assert state_data["tip_y"] == 70.0

    with open(summary_json, "r") as f:
        summary_data = json.load(f)

    assert summary_data["total_equilibrium_iterations"] == 256
    assert summary_data["step1_equilibrium_iterations"] == 160
    assert summary_data["step2_equilibrium_iterations"] == 96
    assert abs(summary_data["final_crack_tip_x_mm"] - 10.6727) < 0.001
    assert abs(summary_data["final_crack_tip_y_mm"] - 69.9342) < 0.001
    assert abs(summary_data["final_crack_extension_mm"] - 0.676) < 0.001
    assert summary_data["forward_crack_growth_demonstrated"] is True
    assert abs(summary_data["E_fracture_kNmm"] - 0.005743) < 0.0001


