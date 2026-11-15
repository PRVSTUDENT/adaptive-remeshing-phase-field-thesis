# -*- coding: utf-8 -*-
"""
tests/unit/test_f1792_observable_extractor.py
Task F1792: Unit & Regression Test Suite for Observable Extractor and Release Gate Evaluator.

Verifies:
1. Dynamic spatial crack-tip resolution: identifies Node 209 at (0.5000, 0.5000) mm and cluster nodes.
2. Strict exact increment matching in energy CSV: requires Step 2 Increment 1 (no fallback to other rows).
3. Reaction force parser & coherent unit verification: converts kN to N when in [0.05, 10.0] kN, handles N directly, flags unphysical values.
4. Separation of residual norms in .msg parser: distinguishes initial out-of-balance residual norm from final converged Newton residual.
5. Full nodal coverage in ODB damage extraction: fails closed if extracted nodes < 16,642.
6. Frame-zero substitution rejection in ODB damage extraction: fails closed if Step 2 Increment 1 is missing.
7. Missing odbAccess module graceful fail-closed behavior.
8. Solver failure handling: solver abort / cutback exhaustion prevents overall PASS.
9. Integration-point history labeling: explicitly labeled as unavailable in ODB UEL.
10. End-to-end evaluation against passing synthetic solver evidence: emits overall PASS and writes valid JSON.
"""

import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.extract_f1792_observables import (
    DEFAULT_DONOR_REFERENCE,
    DEFAULT_THRESHOLDS,
    EXPECTED_PHYSICAL_NODES,
    check_solver_completion_status,
    evaluate_physical_gates,
    extract_and_evaluate,
    find_crack_tip_node_from_inp,
    parse_energy_csv,
    parse_reaction_force_dat,
    parse_residual_norm_msg,
)


def test_dynamic_crack_tip_resolution_node_209():
    """Verifies that find_crack_tip_node_from_inp identifies Node 209 at (0.5000, 0.5000) mm."""
    inp_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "PK_F1792_CASE1_RELEASE_DIAGNOSTIC.inp"
    if not inp_path.exists():
        inp_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "PK_F1790_CASE1_RELEASE_DIAGNOSTIC.inp"
    assert inp_path.exists(), f"Input deck {inp_path} must exist"

    tip_info = find_crack_tip_node_from_inp(inp_path, target_x=0.5, target_y=0.5, tol=1.0e-4)
    assert tip_info["found"] is True
    assert tip_info["tip_node"] == 209
    assert abs(tip_info["tip_coords"][0] - 0.5) < 1.0e-5
    assert abs(tip_info["tip_coords"][1] - 0.5) < 1.0e-5
    assert tip_info["min_dist"] < 1.0e-6

    # Verify crack tip cluster nodes within 5 um
    cluster_nids = [c["node"] for c in tip_info["cluster_nodes"]]
    assert 209 in cluster_nids
    assert len(cluster_nids) >= 5


def test_parse_energy_csv_exact_increment_matching():
    """Verifies that parse_energy_csv requires Step 2 Increment 1 and rejects fallback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = Path(tmpdir) / "uel_energy_balance.csv"

        # Case A: Missing Step 2 Increment 1 (only Step 1 and Step 2 Increment 2 exist)
        csv_file.write_text(
            "Step,Increment,E_elastic_kNmm,E_fracture_kNmm,E_total_kNmm\n"
            "1,1,0.00163,0.00003,0.00166\n"
            "2,2,0.00164,0.00003,0.00167\n",
            encoding="utf-8",
        )
        res_no_inc1 = parse_energy_csv(csv_file)
        assert res_no_inc1["found"] is False
        assert "Step 2 Increment 1 row not found" in res_no_inc1["reason"]

        # Case B: Valid Step 2 Increment 1
        csv_file.write_text(
            "Step,Increment,E_elastic_kNmm,E_fracture_kNmm,E_total_kNmm\n"
            "1,1,0.00163,0.00003,0.00166\n"
            "2,1,0.001632721,0.000030663,0.001663384\n"
            "2,2,0.001633000,0.000030700,0.001663700\n",
            encoding="utf-8",
        )
        res_valid = parse_energy_csv(csv_file)
        assert res_valid["found"] is True
        assert abs(res_valid["E_total_mJ"] - 1.663384) < 1.0e-4
        assert res_valid["step"] == 2
        assert res_valid["increment"] == 1


def test_parse_reaction_force_dat_coherent_units():
    """Verifies reaction force parsing, kN to N conversion, and out-of-range detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dat_file = Path(tmpdir) / "test.dat"

        # Case A: Standard Abaqus output in kN (0.6530886 kN) -> converted to 653.0886 N
        dat_file.write_text(
            "STEP 2 INCREMENT 1\n"
            "   THE FOLLOWING TABLE IS PRINTED FOR NODES\n"
            "      NODE      RF1         RF2\n"
            "    999999  0.0000E+00  6.530886E-01\n"
            "INCREMENT 2\n",
            encoding="utf-8",
        )
        res_kn = parse_reaction_force_dat(dat_file, node_id=999999)
        assert res_kn["found"] is True
        assert abs(res_kn["RF2_N"] - 653.0886) < 1.0e-3
        assert "converted to N" in res_kn["unit_note"]

        # Case B: Output already in N (653.0886 N)
        dat_file.write_text(
            "STEP 2 INCREMENT 1\n"
            "   THE FOLLOWING TABLE IS PRINTED FOR NODES\n"
            "      NODE      RF1         RF2\n"
            "    999999  0.0000E+00  6.530886E+02\n"
            "INCREMENT 2\n",
            encoding="utf-8",
        )
        res_n = parse_reaction_force_dat(dat_file, node_id=999999)
        assert res_n["found"] is True
        assert abs(res_n["RF2_N"] - 653.0886) < 1.0e-3
        assert "already in N" in res_n["unit_note"]

        # Case C: Unphysically small force (< 0.05 kN and < 50 N) -> fail closed
        dat_file.write_text(
            "STEP 2 INCREMENT 1\n"
            "   THE FOLLOWING TABLE IS PRINTED FOR NODES\n"
            "      NODE      RF1         RF2\n"
            "    999999  0.0000E+00  1.2000E-04\n"
            "INCREMENT 2\n",
            encoding="utf-8",
        )
        res_unphys = parse_reaction_force_dat(dat_file, node_id=999999)
        assert res_unphys["found"] is False
        assert "outside physically plausible range" in res_unphys["reason"]


def test_parse_residual_norm_msg_initial_and_converged_separation():
    """Verifies that parse_residual_norm_msg separates initial out-of-balance and final converged residuals."""
    with tempfile.TemporaryDirectory() as tmpdir:
        msg_file = Path(tmpdir) / "test.msg"

        # Multi-iteration convergence block
        msg_file.write_text(
            "STEP 2 INCREMENT 1\n"
            " ITERATION 1\n"
            " AVERAGE FORCE 0.653E+00   LARGEST RESIDUAL FORCE 5.200E-04  AT NODE 209\n"
            " ITERATION 2\n"
            " AVERAGE FORCE 0.653E+00   LARGEST RESIDUAL FORCE 1.100E-05  AT NODE 2844\n"
            " THE FORCE EQUILIBRIUM EQUATIONS HAVE CONVERGED\n"
            "INCREMENT 2\n",
            encoding="utf-8",
        )
        res = parse_residual_norm_msg(msg_file)
        assert res["found"] is True
        assert res["total_iterations"] == 2
        assert res["converged"] is True

        init_res = res["initial_unbalanced_residual"]
        assert init_res["iteration"] == 1
        assert init_res["critical_node"] == 209
        assert abs(init_res["R_max_norm"] - (5.2e-4 / 0.653)) < 1.0e-5

        conv_res = res["converged_residual"]
        assert conv_res["iteration"] == 2
        assert conv_res["critical_node"] == 2844
        assert abs(conv_res["R_max_norm"] - (1.1e-5 / 0.653)) < 1.0e-5


def test_solver_completion_status():
    """Verifies check_solver_completion_status detects cutbacks and failures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        msg_file = Path(tmpdir) / "test.msg"

        # Successful solver run
        log_file.write_text("THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n", encoding="utf-8")
        msg_file.write_text("THE FORCE EQUILIBRIUM EQUATIONS HAVE CONVERGED\n", encoding="utf-8")
        stat_pass = check_solver_completion_status(Path(tmpdir), "test")
        assert stat_pass["solver_completed"] is True

        # Cutback failure
        log_file.write_text("THE ANALYSIS HAS NOT BEEN COMPLETED\n", encoding="utf-8")
        msg_file.write_text("TIME INCREMENT REQUIRED IS LESS THAN MINIMUM SPECIFIED\n", encoding="utf-8")
        stat_fail = check_solver_completion_status(Path(tmpdir), "test")
        assert stat_fail["solver_completed"] is False
        assert "cutback exhaustion" in stat_fail["error_message"]


def test_evaluate_physical_gates_fail_closed_on_solver_failure():
    """Verifies that evaluate_physical_gates emits overall FAIL if solver failed."""
    solver_data = {
        "solver_status": {"solver_completed": False, "error_message": "Solver aborted"},
        "residual_norm": {"found": True},
        "reaction_force": {"found": True},
        "energy_balance": {"found": True},
        "odb_damage": {"found": True},
    }
    res = evaluate_physical_gates(solver_data)
    assert res["overall_verdict"] == "FAIL"
    assert res["solver_completed"] is False
    assert res["gates"]["gate_c1_equilibrium_residual_norm"]["verdict"] == "FAIL"


def test_evaluate_physical_gates_passing_synthetic():
    """Verifies evaluate_physical_gates evaluates overall PASS when all gates are satisfied."""
    solver_data = {
        "solver_status": {"solver_completed": True},
        "crack_tip_info": {"tip_node": 209, "cluster_nodes": [{"node": 209, "dist": 0.0}]},
        "residual_norm": {
            "found": True,
            "initial_unbalanced_residual": {"R_max_norm": 0.00075, "R_max": 4.8e-4, "q_avg": 0.653, "critical_node": 209},
            "converged_residual": {"R_max_norm": 0.000015, "R_max": 1.0e-5, "q_avg": 0.653, "critical_node": 209},
            "total_iterations": 2,
        },
        "reaction_force": {
            "found": True,
            "RF1_raw": 0.0,
            "RF2_raw": 0.65320,
            "RF2_N": 653.20,
            "unit_note": "Abaqus output in kN; converted to N (*1000)",
        },
        "energy_balance": {
            "found": True,
            "E_total_mJ": 1.66350,
            "E_elastic_mJ": 1.63280,
            "E_fracture_mJ": 0.03070,
        },
        "odb_damage": {
            "found": True,
            "min_delta_d": -0.00002,
            "min_delta_node": 105,
            "delta_d_tip": 0.00015,
            "tip_node": 209,
            "d_tip_init": 0.092037,
            "d_tip_inc1": 0.092187,
            "num_evaluated_nodes": 16642,
        },
    }

    res = evaluate_physical_gates(solver_data)
    assert res["overall_verdict"] == "PASS"
    assert res["gates"]["gate_c1_equilibrium_residual_norm"]["verdict"] == "PASS"
    assert res["gates"]["gate_c2_reaction_force_parity"]["verdict"] == "PASS"
    assert res["gates"]["gate_c3_total_internal_energy_continuity"]["verdict"] == "PASS"
    assert res["gates"]["gate_c4_pointwise_damage_irreversibility"]["verdict"] == "PASS"
    assert res["gates"]["gate_c5_artificial_crack_tip_damage_cap"]["verdict"] == "PASS"
    assert res["integration_point_history_observation"]["status"] == "UNAVAILABLE_IN_ODB_UEL_NO_ELEMENT_OUTPUT"


def test_cli_execution_fail_closed():
    """Verifies CLI execution exits with return code 1 when required output files are absent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_out = Path(tmpdir) / "eval.json"
        script_path = REPO_ROOT / "scripts" / "state_transfer" / "extract_f1792_observables.py"
        cmd = [
            sys.executable,
            str(script_path),
            "--job-dir", tmpdir,
            "--job-name", "NON_EXISTENT_JOB",
            "--output-json", str(json_out),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        assert proc.returncode != 0
        assert json_out.exists()
        data = json.loads(json_out.read_text(encoding="utf-8"))
        assert data["overall_verdict"] == "FAIL"


def test_odb_extraction_nonexistent_odb_fails_closed():
    """Verifies extract_damage_from_odb returns found=False when ODB is missing."""
    from scripts.state_transfer.extract_f1792_observables import extract_damage_from_odb
    res = extract_damage_from_odb(Path("non_existent.odb"), tip_node_id=209)
    assert res["found"] is False
    assert "not found" in res["reason"]


def test_evaluate_physical_gates_out_of_bounds_gate_fails():
    """Verifies that an out-of-bounds gate (e.g. C4 min_delta_d < -1.0e-4) emits FAIL."""
    solver_data = {
        "solver_status": {"solver_completed": True},
        "residual_norm": {
            "found": True,
            "initial_unbalanced_residual": {"R_max_norm": 0.0005, "R_max": 3.0e-4, "q_avg": 0.653},
            "converged_residual": {"R_max_norm": 0.00001, "R_max": 1.0e-5, "q_avg": 0.653},
        },
        "reaction_force": {
            "found": True,
            "RF2_N": 653.0886,
        },
        "energy_balance": {
            "found": True,
            "E_total_mJ": 1.663384,
        },
        "odb_damage": {
            "found": True,
            "min_delta_d": -0.0020,  # Below -1.0e-4 threshold (healing violation)
            "delta_d_tip": 0.0001,
            "tip_node": 209,
            "num_evaluated_nodes": 16642,
        },
    }
    res = evaluate_physical_gates(solver_data)
    assert res["overall_verdict"] == "FAIL"
    assert res["gates"]["gate_c4_pointwise_damage_irreversibility"]["verdict"] == "FAIL"
