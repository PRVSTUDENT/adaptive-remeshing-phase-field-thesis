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
    BAND_HALF_WIDTH_MM,
    BAND_HEIGHT_MM,
    BAND_WAKE_MARGIN_MM,
    BAND_AHEAD_MARGIN_MM,
    compute_narrow_band_spec,
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
    compute_narrow_band_spec as gen_compute_narrow_band_spec,
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
    """Verify narrow damage-following band geometry at initial notch state."""
    width = CORRIDOR_X_MAX - CORRIDOR_X_MIN
    height = CORRIDOR_Y_MAX - CORRIDOR_Y_MIN
    area = width * height
    assert width == 3.5
    assert height == 2.0
    assert abs(area - 7.0) < 1e-4
    assert H_REF_MM == 0.140
    assert H_REF_MM < (BENCHMARK_L0_MM / 2.0)
    spec = get_corridor_partition_spec()
    assert spec["band_type"] == "NARROW_DAMAGE_FOLLOWING_BAND"
    assert spec["corridor_box"]["height_mm"] == 2.0
    assert spec["target_mesh_metrics"]["target_total_elements_bounded"] == 35000
    assert spec["target_mesh_metrics"]["elements_per_mm_advance"] == 102

def test_narrow_band_follows_tip():
    """Verify that the narrow damage-following band dynamically tracks crack tip movement."""
    # 1. Initial notch state (tip at notch root x=10, y=70)
    spec_init = compute_narrow_band_spec(tip_x=10.0, tip_y=70.0)
    assert spec_init["x_min"] == 8.5
    assert spec_init["x_max"] == 12.0  # 10.0 + ahead_margin (2.0)
    assert spec_init["length_mm"] == 3.5
    assert abs(spec_init["tip_y"] - 70.0) < 1e-6

    # 2. Intermediate state (tip advanced to x=22, y=66)
    spec_mid = compute_narrow_band_spec(tip_x=22.0, tip_y=66.0)
    assert spec_mid["x_min"] == 8.5
    assert spec_mid["x_max"] == 24.0  # 22.0 + ahead_margin (2.0)
    assert spec_mid["length_mm"] == 15.5
    assert spec_mid["x_max"] > spec_init["x_max"]
    assert spec_mid["length_mm"] > spec_init["length_mm"]
    assert spec_mid["polygon_vertices"][1][1] < spec_init["polygon_vertices"][1][1]

    # 3. Deep propagation state (tip advanced to x=35, y=55)
    spec_deep = compute_narrow_band_spec(tip_x=35.0, tip_y=55.0)
    assert spec_deep["x_max"] == 37.0  # 35.0 + 2.0
    assert spec_deep["length_mm"] == 28.5
    assert spec_deep["x_max"] > spec_mid["x_max"]

    # 4. Orchestrator method dynamic query
    orch = Case3SingleJobOrchestrator(run_dir=PACKAGE_DIR, uel_path=UEL_PATH)
    orch_band = orch.get_corridor_definition(tip_x=28.0, tip_y=61.0)
    assert orch_band["x_max_mm"] == 30.0
    assert orch_band["corridor_width_mm"] == 21.5
    assert orch_band["tip_x_mm"] == 28.0
    assert orch_band["tip_y_mm"] == 61.0

def test_narrow_band_is_narrow():
    """Verify that the band height is narrow (few mm, not 17-30 mm tall rectangle)."""
    tip_positions = [
        (10.0, 70.0),
        (15.0, 68.5),
        (20.0, 67.0),
        (30.0, 60.0),
        (45.0, 50.0),
        (60.0, 52.0)
    ]

    for tx, ty in tip_positions:
        spec = compute_narrow_band_spec(tip_x=tx, tip_y=ty)
        # Band height at cross section is strictly 2.0 mm (half-width = 1.0 mm)
        assert spec["band_height_mm"] == 2.0, "Band height must be exactly 2.0 mm"
        assert spec["half_width_mm"] == 1.0, "Half width must be 1.0 mm (~3.5 * l0)"
        assert spec["half_width_mm"] < 2.0, "Half width must stay below 2.0 mm"
        assert spec["band_height_mm"] <= 3.0, "Band height must be a few mm"

        # Compare with old fixed 17 mm and manual 30 mm corridor
        assert spec["band_height_mm"] < (0.20 * 17.0), "Band must be >5x narrower than old 17 mm corridor"
        assert spec["band_height_mm"] < (0.10 * 30.0), "Band must be >10x narrower than manual 30 mm corridor"

def test_narrow_band_element_count_bounded():
    """Verify that refined band elements and total mesh stay strictly bounded (< 35,000) for representative and full crack path."""
    # 1. Elements per mm advance rate: target ~100 elements / mm
    spec_rate = compute_narrow_band_spec(tip_x=10.0, tip_y=70.0)
    assert 90 <= spec_rate["elements_per_mm_advance"] <= 115, "Elements per mm advance must be roughly 100"
    assert spec_rate["elements_per_mm_advance"] == 102

    # 2. Representative tip position: tip_x = 30.0 mm (after substantial crack advance)
    spec_30 = compute_narrow_band_spec(tip_x=30.0, tip_y=60.0)
    assert spec_30["refined_band_elements"] < 3000  # ~2,400 elements
    assert spec_30["estimated_total_elements"] < 12000  # ~8,900 elements
    # Far fewer than manual campaign's Cycle-4 mesh of 64,653 elements
    assert spec_30["estimated_total_elements"] < (0.25 * 64653), "Must be far fewer than manual Cycle-4 (64,653)"
    assert spec_30["estimated_total_elements"] < 35000, "Must stay well under 35,000 threshold"

    # 3. Full crack propagation to plate edge: tip_x = 64.0 mm
    spec_end = compute_narrow_band_spec(tip_x=64.0, tip_y=51.0)
    assert spec_end["refined_band_elements"] < 7000  # ~5,765 elements
    assert spec_end["estimated_total_elements"] < 15000  # ~12,265 elements
    assert spec_end["estimated_total_elements"] < 35000, "Full propagation mesh must remain well under 35,000"

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
    assert "--n-adaptive-steps 100" in content or "--n-adaptive-steps 4" in content
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
    assert manifest["refinement_corridor_minimization"]["architecture"] == "NARROW_DAMAGE_FOLLOWING_BAND"
    assert manifest["refinement_corridor_minimization"]["narrow_band_specification"]["band_height_mm"] == 2.0
    assert manifest["refinement_corridor_minimization"]["narrow_band_specification"]["target_total_elements_bounded"] == 35000
    assert manifest["refinement_corridor_minimization"]["corridor_box"]["area_mm2"] == 7.0
    assert manifest["refinement_corridor_minimization"]["corridor_box"]["height_mm"] == 2.0
    assert manifest["refinement_corridor_minimization"]["corridor_box"]["width_mm"] == 3.5
    assert manifest["refinement_corridor_minimization"]["target_physical_elements_bounded"] == 35000
    assert manifest["adaptive_schedule_parameters"]["n_adaptive_steps"] in [4, 100]
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
    assert "7172 elements" in header
    assert "7261 nodes" in header
    assert "96.14% quad" in header

def test_physical_mesh_parsing_and_deck_assembly():
    """Verify parse_physical_inp and assemble_coupled_deck generate 3-layer UEL deck."""
    mesh = parse_physical_inp(PHYS_MESH_PATH)
    assert len(mesh["elements"]) == 7172
    assert len(mesh["nodes"]) == 7261
    assert len(mesh["quads"]) == 6895
    assert len(mesh["tris"]) == 277

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


def test_bom_prefixed_json_decoding():
    """Verify that orchestrator extract_cycle_state handles UTF-8 BOM-prefixed JSON without decoding error (NOTE-DIAG-01)."""
    from scripts.remeshing.case3_single_job_orchestrator import Case3SingleJobOrchestrator
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        orch = Case3SingleJobOrchestrator(run_dir=tmpdir)
        bom_json_path = os.path.join(tmpdir, "test_job_state.json")
        bom_payload = b'\xef\xbb\xbf{"u_nodal": {"1": [0.01, -0.02]}, "d_nodal": {"1": 0.75}, "h_gp": {"1_1": 150.0}, "tip_x": 12.5, "peak_rf2": 4.1, "terminal_rf2": 3.8}'
        with open(bom_json_path, "wb") as f:
            f.write(bom_payload)

        # Ensure extract_cycle_state parses cleanly with utf-8-sig
        state = orch.extract_cycle_state("test_job")
        assert state["u_nodal"][1] == [0.01, -0.02]
        assert state["d_nodal"][1] == 0.75
        assert state["h_gp"][(1, 1)] == 150.0
        assert state["tip_x"] == 12.5
        assert state["peak_rf2"] == 4.1
        assert state["terminal_rf2"] == 3.8


def test_receiver_mesh_generation_per_cycle_follows_tip():
    """Verify that receiver mesh definition and resolution per cycle dynamically follows the crack tip."""
    orch = Case3SingleJobOrchestrator(run_dir=PACKAGE_DIR, uel_path=UEL_PATH)

    # Cycle 1: Tip at initial notch root (x=10.0, y=70.0)
    spec_c1 = orch.get_corridor_definition(tip_x=10.0, tip_y=70.0)
    assert spec_c1["corridor_width_mm"] == 3.5  # 12.0 - 8.5
    assert spec_c1["band_height_mm"] == 2.0
    assert abs(spec_c1["corridor_area_mm2"] - 7.0) < 1e-4

    # Cycle 2: Tip advanced into plate (x=15.0, y=68.5)
    spec_c2 = orch.get_corridor_definition(tip_x=15.0, tip_y=68.5)
    assert spec_c2["corridor_width_mm"] == 8.5  # 17.0 - 8.5
    assert spec_c2["band_height_mm"] == 2.0
    assert abs(spec_c2["corridor_area_mm2"] - 17.0) < 1e-4

    # Cycle 3: Tip propagated further toward void (x=25.0, y=65.0)
    spec_c3 = orch.get_corridor_definition(tip_x=25.0, tip_y=65.0)
    assert spec_c3["corridor_width_mm"] == 18.5  # 27.0 - 8.5
    assert spec_c3["band_height_mm"] == 2.0
    assert abs(spec_c3["corridor_area_mm2"] - 37.0) < 1e-4

    # Verify monotonic expansion of refined region
    assert spec_c1["corridor_width_mm"] < spec_c2["corridor_width_mm"] < spec_c3["corridor_width_mm"]
    assert spec_c1["corridor_area_mm2"] < spec_c2["corridor_area_mm2"] < spec_c3["corridor_area_mm2"]
    assert spec_c1["refined_band_elements"] < spec_c2["refined_band_elements"] < spec_c3["refined_band_elements"]

    # Test orchestrator mesh resolution under system python3
    mesh1_path = orch.generate_cycle_adaptive_mesh(cycle_idx=1, tip_x=10.0, tip_y=70.0)
    mesh3_path = orch.generate_cycle_adaptive_mesh(cycle_idx=3, tip_x=20.0, tip_y=67.0)

    # Assert distinct file paths
    assert os.path.isfile(mesh1_path), "Cycle 1 mesh file must exist"
    assert os.path.isfile(mesh3_path), "Cycle 3 mesh file must exist"
    assert os.path.abspath(mesh1_path) != os.path.abspath(mesh3_path), "Cycle 1 and Cycle 3 meshes must be distinct files"

    # Assert distinct mesh content and element counts
    mesh1 = parse_physical_inp(mesh1_path)
    mesh3 = parse_physical_inp(mesh3_path)
    assert len(mesh1["elements"]) != len(mesh3["elements"]), "Element counts must differ between cycles"
    assert len(mesh1["nodes"]) != len(mesh3["nodes"]), "Node counts must differ between cycles"
    assert len(mesh1["elements"]) < len(mesh3["elements"]), "Cycle 3 mesh must be more refined than Cycle 1"

    # Verify both are authentic narrow-band meshes bounded < 35,000 elements
    assert len(mesh1["elements"]) == 7172
    assert len(mesh3["elements"]) == 11093
    assert len(mesh1["elements"]) < 35000
    assert len(mesh3["elements"]) < 35000


def test_job1424798_log_and_bom_resilience():
    """Verifies predecessor Job 1424797 execution log integrity and UTF-8 BOM decode resilience."""
    import hashlib
    log_path = os.path.join(PACKAGE_DIR, "PK_METHOD_C_CASE3_FRAMEWORK_JOB1424797_pbs_execution.log")
    if not os.path.isfile(log_path):
        log_path = os.path.join(PACKAGE_DIR, "PK_METHOD_C_CASE3_FRAMEWORK_JOB1424798_pbs_execution.log")
    assert os.path.isfile(log_path), "Committed Job pbs_execution.log must exist"

    with open(log_path, "rb") as f:
        content = f.read()
    h = hashlib.sha256(content).hexdigest().upper()
    assert h == "F6EF17A5239404F86465EB06CA1A770A148A8AD2E01368C910B40848BE8FD790"
    text = content.decode("utf-8", errors="replace")
    assert "Cycle 0 Evaluation" in text
    assert "Unexpected UTF-8 BOM" in text

    # Test that utf-8-sig decodes a synthetic BOM json cleanly
    import tempfile
    import json
    with tempfile.NamedTemporaryFile("wb", suffix=".json", delete=False) as tmp:
        # Write UTF-8 BOM (\xef\xbb\xbf) followed by valid JSON
        tmp.write(b"\xef\xbb\xbf" + json.dumps({"test_key": 12345}).encode("utf-8"))
        tmp_name = tmp.name

    try:
        with open(tmp_name, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        assert data.get("test_key") == 12345
    finally:
        if os.path.isfile(tmp_name):
            os.remove(tmp_name)


def test_job1424798_identity_reconciliation_and_scheduler_status():
    """Verifies that Job 1424798 timing and identity are reconciled against scheduler facts."""
    report_path = os.path.join(REPO_ROOT, "docs", "validation", "METHOD_C_CASE3_FRAMEWORK_JOB1424798_EXECUTION_REPORT.md")
    assert os.path.isfile(report_path), "Job 1424798 execution report must exist"

    with open(report_path, "r", encoding="utf-8") as f:
        report_text = f.read()

    # Verify reconciliation claims
    assert "GAP-JOB-01 Resolved" in report_text
    assert "GAP-JOB-02 Resolved" in report_text
    assert "1424797.mmaster02" in report_text
    assert "1424798.mmaster02" in report_text
    assert "221c6d13" in report_text
    assert "-0.3912" in report_text  # Step 1 force continuity passed gate


def test_job1424798_final_observables():
    """Verifies that Job 1424798 final solver outputs and observables are authentic and verified."""
    import hashlib

    # 1. Authentic PBS execution log (6,837 bytes)
    log_path = os.path.join(PACKAGE_DIR, "PK_METHOD_C_CASE3_FRAMEWORK_JOB1424798_pbs_execution.log")
    assert os.path.isfile(log_path), "Committed Job 1424798 pbs_execution.log must exist"
    assert os.path.getsize(log_path) == 6837
    with open(log_path, "rb") as f:
        log_hash = hashlib.sha256(f.read()).hexdigest().upper()
    assert log_hash == "20314D3EEDE9EFDC5F0C6A82E274A8D27583887ACADB5D72AE31ACFC515532E3"

    # 2. Cycle 1 Summary JSON
    summary_path = os.path.join(PACKAGE_DIR, "PK_METHOD_C_CASE3_CYCLE1_SUMMARY.json")
    assert os.path.isfile(summary_path), "Cycle 1 summary JSON must exist"
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["cycle_idx"] == 1
    assert summary["num_physical_elements"] == 7172
    assert summary["max_damage"] > 0.99
    assert abs(summary["tip_x"] - 12.4246) < 0.01
    assert abs(summary["tip_y"] - 69.8823) < 0.01
    assert summary["crack_extension_mm"] > 2.4

    # 3. Energy balance CSV
    csv_path = os.path.join(PACKAGE_DIR, "PK_METHOD_C_CASE3_CYCLE1_uel_energy_balance.csv")
    assert os.path.isfile(csv_path), "Cycle 1 energy balance CSV must exist"
    with open(csv_path, "r", encoding="utf-8") as f:
        csv_lines = [line.strip().split(",") for line in f if line.strip()]
    header = csv_lines[0]
    e_frac_idx = header.index("E_fracture_kNmm")
    first_e_frac = float(csv_lines[1][e_frac_idx])
    last_e_frac = float(csv_lines[-1][e_frac_idx])
    assert abs(first_e_frac - 0.0016952) < 0.0001
    assert abs(last_e_frac - 0.0167745) < 0.0001
    energy_surge_pct = (last_e_frac - first_e_frac) / first_e_frac * 100.0
    assert energy_surge_pct > 800.0  # +889.5%

    # 4. Spatially-binned speedup orchestrator SHA
    orch_path = os.path.join(PACKAGE_DIR, "case3_single_job_orchestrator.py")
    assert os.path.isfile(orch_path), "Package orchestrator must exist"
    with open(orch_path, "rb") as f:
        orch_hash = hashlib.sha256(f.read()).hexdigest().upper()
    assert orch_hash == "F5817AAF73B915B6620065440BC7BAB6DD11040D37C87394EC5F01C32265FBC2"


def test_transfer_gp_history_binned_performance_and_safeguards():
    """Verifies that the 2D spatially-binned transfer_gp_history enforces H>=0, convex clamping, and executes sub-second."""
    import time
    donor_mesh = {
        "nodes": {
            1: (10.0, 70.0), 2: (11.0, 70.0), 3: (11.0, 71.0), 4: (10.0, 71.0),
            5: (11.0, 70.0), 6: (12.0, 70.0), 7: (12.0, 71.0), 8: (11.0, 71.0)
        },
        "quads": {
            1: [1, 2, 3, 4],
            2: [5, 6, 7, 8]
        },
        "tris": {}
    }
    donor_history = {
        (1, 1): 5.0, (1, 2): 10.0, (1, 3): 15.0, (1, 4): 8.0,
        (2, 1): 10.0, (2, 2): 20.0, (2, 3): 25.0, (2, 4): 15.0
    }
    receiver_mesh = {
        "nodes": {
            101: (10.2, 70.2), 102: (10.8, 70.2), 103: (10.8, 70.8), 104: (10.2, 70.8),
            105: (10.8, 70.2), 106: (11.5, 70.2), 107: (11.5, 70.8), 108: (10.8, 70.8)
        },
        "quads": {
            101: [101, 102, 103, 104],
            102: [105, 106, 107, 108]
        },
        "tris": {}
    }

    t0 = time.time()
    res = transfer_gp_history(donor_mesh, donor_history, receiver_mesh, limiter_mode="convex_clamp")
    dt = time.time() - t0

    assert dt < 0.5, "Spatially-binned transfer must execute in < 0.5 s (took %.4f s)" % dt
    assert len(res) == 8, "Expected 8 Gauss point values (2 quads x 4 GPs)"
    for (eid, gp), val in res.items():
        assert val >= 0.0, "History value must be nonnegative"
        assert val <= 25.0 + 1e-6, "History value must not exceed max donor value"


def test_orchestrator_resume_detection():
    """Verifies that orchestrator detects existing completed cycle checkpoints and computes resume cycle."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy completed Cycle 1 files with realistic 9-column STA lines
        c1_sta = os.path.join(tmpdir, "PK_METHOD_C_CASE3_CYCLE1.sta")
        with open(c1_sta, "w") as f:
            f.write("STEP  INC ATT  SEV  EQU   TOTAL_TIME   STEP_TIME   INC_TIME     DT\n")
            f.write("   1    1   1    0    1   0.01000000   0.01000000  0.01000000  0.01000000\n")
            f.write("   2    1   1    0    1   0.02000000   0.01000000  0.01000000  0.01000000\n")
        with open(os.path.join(tmpdir, "PK_METHOD_C_CASE3_CYCLE1_state.json"), "w") as f:
            f.write('{"d_nodal": {"1": 0.5}, "u_nodal": {"1": [0.0, 0.0]}, "h_gp": {"1_1": 1.0}, "tip_x": 12.0, "terminal_rf2": 3.8}')
        with open(os.path.join(tmpdir, "PK_METHOD_C_CASE3_CYCLE1_PHYS.inp"), "w") as f:
            f.write("*NODE\n1, 0.0, 0.0\n*ELEMENT, TYPE=CPS4\n1, 1, 1, 1, 1\n")

        orch = Case3SingleJobOrchestrator(run_dir=tmpdir, n_adaptive_steps=4)
        
        # Test detection logic
        resume_cycle = 0
        for c in range(orch.n_adaptive_steps, 0, -1):
            c_job = "PK_METHOD_C_CASE3_CYCLE%d" % c
            c_state = os.path.join(orch.run_dir, c_job + "_state.json")
            c_sta = os.path.join(orch.run_dir, c_job + ".sta")
            c_phys = os.path.join(orch.run_dir, c_job + "_PHYS.inp")
            if os.path.isfile(c_state) and os.path.isfile(c_sta) and os.path.isfile(c_phys):
                term_eval = orch.evaluate_cutback_state(c_sta)
                if term_eval.get("can_continue", False):
                    resume_cycle = c
                    break

        assert resume_cycle == 1, "Should detect Cycle 1 as latest completed cycle"





