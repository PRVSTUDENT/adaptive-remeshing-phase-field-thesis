# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_package.py
=========================================
Task: METHOD-C-CASE3-ADAPTATION-PACKAGE
Comprehensive test suite verifying the Method C Case 3 adaptation package:
1. Configuration consistency (configs/remeshing/method_c_case3_notched_plate.json)
2. Coarse physical mesh quality gates (models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_PHYS.inp)
3. 3-layer production deck syntax and layer integrity (PK_METHOD_C_CASE3_COARSE_JOB1.inp)
4. Transfer-operator readiness on Case 3 geometry (PK_METHOD_C_CASE3_TRANSFER_READINESS_RECEIPT.json)
5. Generalized incremental loop driver execution on Case 3
6. Zero PBS submissions governance (preserving cumulative submissions at 62)
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "remeshing", "method_c_case3_notched_plate.json")
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")
PHYS_INP = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_COARSE_PHYS.inp")
COARSE_DECK = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_COARSE_JOB1.inp")
MESH_AUDIT_JSON = os.path.join(CASE_DIR, "method_c_case3_mesh_audit.json")
COARSE_RECEIPT_JSON = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_COARSE_RECEIPT.json")
TRANSFER_RECEIPT_JSON = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_TRANSFER_READINESS_RECEIPT.json")

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def test_case3_config_consistency():
    """Validates configs/remeshing/method_c_case3_notched_plate.json schema and physical parameters."""
    assert os.path.isfile(CONFIG_PATH), "Config file missing: %s" % CONFIG_PATH
    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)

    assert cfg["case_id"] == "method_c_case3"
    assert cfg["geometry"]["plate_width"] == 65.0
    assert cfg["geometry"]["plate_height"] == 120.0
    assert cfg["geometry"]["notch_length"] == 10.0
    assert cfg["geometry"]["notch_y"] == 70.0
    assert cfg["geometry"]["notch_slit_opening"] == 0.2

    # Voids
    voids = {v["name"]: v for v in cfg["geometry"]["voids"]}
    assert "central_hole" in voids
    assert voids["central_hole"]["x"] == 36.5
    assert voids["central_hole"]["y"] == 51.0
    assert voids["central_hole"]["r"] == 10.0

    assert "lower_pin_hole" in voids
    assert voids["lower_pin_hole"]["x"] == 20.0
    assert voids["lower_pin_hole"]["y"] == 20.0
    assert voids["lower_pin_hole"]["r"] == 5.0

    assert "upper_pin_hole" in voids
    assert voids["upper_pin_hole"]["x"] == 20.0
    assert voids["upper_pin_hole"]["y"] == 100.0
    assert voids["upper_pin_hole"]["r"] == 5.0

    # Material
    mat = cfg["material"]
    assert mat["youngs_modulus_mpa"] == 210000.0
    assert mat["poisson_ratio"] == 0.30
    assert mat["length_scale_l0_mm"] == 0.285
    assert mat["gc_kn_per_mm"] == 0.00228
    assert mat["residual_stiffness_k"] == 1.0e-7

    # Loading schedule
    sched = cfg["load_schedule"]
    assert sched["num_cycles"] == 4
    assert sched["step1_u2_mm"] == 0.05
    assert sched["step2_final_u2_mm"] == 1.50
    assert sched["cycle_targets_u2_mm"] == [0.05, 0.4125, 0.775, 1.1375, 1.50]
    assert len(sched["cycles"]) == 4

def test_case3_coarse_physical_mesh_quality():
    """Validates PK_METHOD_C_CASE3_COARSE_PHYS.inp against FE quality gates."""
    assert os.path.isfile(PHYS_INP), "Physical mesh missing: %s" % PHYS_INP
    assert os.path.isfile(MESH_AUDIT_JSON), "Mesh audit JSON missing: %s" % MESH_AUDIT_JSON

    with open(MESH_AUDIT_JSON, "r") as f:
        audit = json.load(f)

    stats = audit["statistics"]
    assert stats["total_elements"] == 4671
    assert stats["quad_elements"] == 4542
    assert stats["tri_elements"] == 129
    assert stats["total_nodes"] == 4812
    assert stats["quad_fraction_pct"] >= 85.0, "Quad fraction below 85%: %.2f%%" % stats["quad_fraction_pct"]

    metrics = audit["quality_metrics"]
    assert metrics["min_det_j"] > 0.0, "Non-positive Jacobian detected: %.6e" % metrics["min_det_j"]
    assert metrics["non_positive_jacobians"] == 0
    assert metrics["mean_aspect_ratio"] <= 2.5, "Mean aspect ratio exceeds 2.5: %.4f" % metrics["mean_aspect_ratio"]

    gates = audit["gates"]
    assert gates["gate_01_jacobian"] == "PASS"
    assert gates["gate_02_quad_fraction"] == "PASS"
    assert gates["gate_03_aspect_ratio"] == "PASS"
    assert gates["all_gates_pass"] is True

def test_case3_coarse_3layer_deck_structure_and_syntax():
    """Validates PK_METHOD_C_CASE3_COARSE_JOB1.inp syntax, 3 layers, and kinematics."""
    assert os.path.isfile(COARSE_DECK), "Coarse deck missing: %s" % COARSE_DECK
    assert os.path.isfile(COARSE_RECEIPT_JSON), "Receipt missing: %s" % COARSE_RECEIPT_JSON

    with open(COARSE_RECEIPT_JSON, "r") as f:
        receipt = json.load(f)

    assert receipt["mesh_statistics"]["physical_elements"] == 4671
    assert receipt["mesh_statistics"]["layered_elements"] == 14013
    assert receipt["mesh_statistics"]["physical_nodes"] == 4812
    assert receipt["mesh_statistics"]["rp_node_id"] == 999999

    computed_sha = compute_sha256(COARSE_DECK)
    assert receipt["artifacts"]["coupled_inp_sha256"] == computed_sha, "Deck SHA mismatch"

    with open(COARSE_DECK, "r") as f:
        deck_text = f.read()

    # Layer element counts
    assert "*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD" in deck_text
    assert "*ELEMENT, TYPE=U3, ELSET=PHASE_TRI" in deck_text
    assert "*ELEMENT, TYPE=U2, ELSET=DISP_QUAD" in deck_text
    assert "*ELEMENT, TYPE=U4, ELSET=DISP_TRI" in deck_text
    assert "*ELEMENT, TYPE=CPE4, ELSET=umatelem_quad" in deck_text
    assert "*ELEMENT, TYPE=CPE3, ELSET=umatelem_tri" in deck_text

    # UEL Properties
    assert "*UEL PROPERTY, ELSET=PHASE_QUAD" in deck_text
    assert "0.2850, 0.002280, 210.0, 0.30, 1.0e-07, 4671.0" in deck_text

    # Companion material
    assert "*USER MATERIAL, CONSTANTS=3" in deck_text
    assert "210.0, 0.30, 4671.0" in deck_text

    # Kinematics: Pin hole pull
    assert "*NSET, NSET=N_LOWER_HOLE" in deck_text
    assert "*NSET, NSET=N_UPPER_HOLE" in deck_text
    assert "*NSET, NSET=N_RP" in deck_text
    assert "*EQUATION" in deck_text
    assert ", 2, 1.0, 999999, 2, -1.0" in deck_text

    # Initial Conditions: TYPE=SOLUTION only, strictly no TYPE=DISPLACEMENT
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in deck_text
    assert "*INITIAL CONDITIONS, TYPE=DISPLACEMENT" not in deck_text, (
        "Forbidden *INITIAL CONDITIONS, TYPE=DISPLACEMENT found in deck"
    )

    # Step definitions
    assert "*STEP, NAME=Step-1, NLGEOM=NO, INC=1000" in deck_text
    assert "N_RP, 2, 2, 0.0500" in deck_text
    assert "*STEP, NAME=Step-2, NLGEOM=NO, INC=5000" in deck_text
    assert "N_RP, 2, 2, 0.4125" in deck_text
    assert "*END STEP" in deck_text

def test_case3_transfer_operator_readiness():
    """Validates PK_METHOD_C_CASE3_TRANSFER_READINESS_RECEIPT.json gates."""
    assert os.path.isfile(TRANSFER_RECEIPT_JSON), "Transfer receipt missing: %s" % TRANSFER_RECEIPT_JSON
    with open(TRANSFER_RECEIPT_JSON, "r") as f:
        rec = json.load(f)

    assert rec["case_id"] == "method_c_case3"
    assert rec["transfer_operator"] == "isoparametric_gp_transfer.py"
    assert rec["limiter_mode"] == "convex_clamp"
    assert rec["mesh_elements"] == 4671

    res = rec["verification_results"]
    assert res["same_mesh_shortcut_identity"] == "PASS"
    assert res["max_shortcut_history_error"] == 0.0
    assert res["full_interpolation_identity"] == "PASS"
    assert res["max_interpolation_history_error"] < 1.0e-6
    assert res["non_negativity_guard"] == "PASS"
    assert res["min_transferred_history"] >= 0.0
    assert res["void_penetration_guard"] == "PASS"
    assert res["all_gates_pass"] is True
    assert rec["readiness_status"] == "READY_FOR_CASE3_METHOD_C"

def test_case3_generalized_incremental_loop():
    """Validates generalized incremental loop driver running on Case 3 configuration."""
    import sys
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)
    from scripts.remeshing.method_c_incremental_loop import MethodCIncrementalLoop

    loop = MethodCIncrementalLoop(config_path=CONFIG_PATH, dry_run=True)
    assert loop.case_id == "method_c_case3"
    assert loop.loading_type == "PIN_HOLE_PULL"
    assert loop.step1_u2 == 0.05
    assert loop.step2_final_u2 == 1.50
    assert len(loop.cycle_targets) == 5

    # Run dry-run loop for all 5 increments reaching the 1.50 mm final target
    summary = loop.run_orchestration_loop(max_increments=5)
    assert summary["case_id"] == "method_c_case3"
    assert len(summary["cycles"]) == 5
    assert summary["governance"]["max_new_pbs_submissions"] == 0
    assert summary["governance"]["master_goal_status"] == "OPEN"

    # Increment targets match 4-cycle schedule and reach final 1.50 mm target
    assert summary["cycles"][0]["target_u2_mm"] == 0.05
    assert summary["cycles"][1]["target_u2_mm"] == 0.4125
    assert summary["cycles"][2]["target_u2_mm"] == 0.775
    assert summary["cycles"][3]["target_u2_mm"] == 1.1375
    assert summary["cycles"][4]["target_u2_mm"] == 1.50

def test_governance_and_pbs_accounting_invariance():
    """Validates 0 new PBS submissions and active task status."""
    active_task_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(active_task_path, "r", encoding="utf-8-sig") as f:
        active_task = json.load(f)

    assert active_task["task_id"] in ("METHOD-C-CASE3-ADAPTATION-PACKAGE", "METHOD-C-CASE3-JOB1-COARSE-SOLVE", "METHOD-C-CASE3-JOB1-FAILURE-DIAGNOSIS", "METHOD-C-CASE3-CYCLE1-REFINEMENT-PACKAGE")
    assert active_task["master_goal_status"] == "OPEN"
    assert active_task["task_status"] in ("IN_PROGRESS", "SUBMITTED_AND_RUNNING", "COMPLETED_READY_FOR_INDEPENDENT_REVIEW", "REVIEWED_APPROVED")
    assert active_task["max_new_pbs_submissions"] in (0, 1)
    assert active_task["submissions_consumed"] in (0, 1)
    assert active_task["cumulative_pbs_submissions"] in (62, 63)
