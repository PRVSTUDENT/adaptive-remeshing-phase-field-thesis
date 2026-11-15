# -*- coding: utf-8 -*-
"""
tests/unit/test_f1791_observable_extractor.py
Task F1791: Unit test suite for Mode-I Method C Observable Extractor & Execution Qualification.

Covers:
1. Dynamic spatial crack-tip node resolution from (0.5, 0.5) mm.
2. Strict fail-closed behavior on missing files, missing fields, or empty outputs.
3. Accurate evaluation on synthetic PASS fixture.
4. Accurate evaluation on individual synthetic FAIL fixtures (C1-C5).
5. PBS script guarded execution trap and entry queue audit.
6. Inactive DOF 2 connectivity audit on N_TOP (98 nodes).
7. Frozen UEL and framework bitwise invariance.
8. Execution route qualification via Invoke-Mode1Execution.ps1 -DryRun.
9. Zero new PBS submissions governance (35 preserved).
"""

import hashlib
import json
import math
import os
import re
import subprocess
from pathlib import Path

import pytest

from scripts.state_transfer.extract_f1791_observables import (
    DEFAULT_DONOR_REFERENCE,
    DEFAULT_THRESHOLDS,
    evaluate_physical_gates,
    find_crack_tip_node_from_inp,
    parse_energy_csv,
    parse_reaction_force_dat,
    parse_residual_norm_msg,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

FROZEN_UEL_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

SHARED_FRAMEWORK_PATH = REPO_ROOT / "scripts" / "remeshing" / "reusable_2d_adaptive_framework.py"
ALLOWED_FRAMEWORK_HASHES = [
    "181CB4E5A8CE765CBE0765D71BA9C3CCA934A33140BC61F5B9A4CD7A6AEFCD40",
    "49B2E1B7706594941B4DD58ABAA4C2DB9090B4C06D2358EAF157289AAD3BAE3F",
    "907EE548BB28B920038E8C51D8A4DAA584E9DCE84DD99EEB6A10ECB259DBCAC0",
]

DIAGNOSTIC_INP_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "PK_F1790_CASE1_RELEASE_DIAGNOSTIC.inp"
PBS_F1791_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "submit_f1791_case1_diagnostic.pbs"
MANIFEST_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "55_f1791_method_c_diagnostic" / "METHOD_C_F1791_DIAGNOSTIC_AUTHORIZATION.json"
ACTIVE_TASK_PATH = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"


def get_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_frozen_codebases_invariance():
    """Verify bitwise invariance of frozen Fortran UEL and Python framework."""
    assert FROZEN_UEL_PATH.exists(), f"Missing frozen UEL: {FROZEN_UEL_PATH}"
    actual_uel_sha = get_sha256(FROZEN_UEL_PATH)
    assert actual_uel_sha == FROZEN_UEL_SHA256, f"UEL hash altered: {actual_uel_sha} != {FROZEN_UEL_SHA256}"

    assert SHARED_FRAMEWORK_PATH.exists(), f"Missing framework: {SHARED_FRAMEWORK_PATH}"
    actual_fw_sha = get_sha256(SHARED_FRAMEWORK_PATH)
    assert actual_fw_sha in ALLOWED_FRAMEWORK_HASHES, f"Framework hash altered: {actual_fw_sha} not in {ALLOWED_FRAMEWORK_HASHES}"


def test_dynamic_spatial_crack_tip_resolution():
    """Verify dynamic spatial crack-tip identification finds Node 209 at (0.5000, 0.5000) mm."""
    assert DIAGNOSTIC_INP_PATH.exists(), f"Missing diagnostic deck: {DIAGNOSTIC_INP_PATH}"
    tip_info = find_crack_tip_node_from_inp(DIAGNOSTIC_INP_PATH, target_x=0.5, target_y=0.5, tol=1.0e-4)

    assert tip_info["found"] is True, f"Crack tip not found: {tip_info.get('reason')}"
    assert tip_info["tip_node"] == 209, f"Expected Node 209, got {tip_info['tip_node']}"
    assert math.isclose(tip_info["tip_coords"][0], 0.5, abs_tol=1.0e-6)
    assert math.isclose(tip_info["tip_coords"][1], 0.5, abs_tol=1.0e-6)
    assert tip_info["min_dist"] < 1.0e-7

    # Verify crack tip cluster nodes within 5 um
    cluster_nodes = [c["node"] for c in tip_info["cluster_nodes"]]
    assert 209 in cluster_nodes
    assert 2844 in cluster_nodes
    assert 16591 in cluster_nodes

    # Negative test: search non-existent point with tight tolerance
    neg_info = find_crack_tip_node_from_inp(DIAGNOSTIC_INP_PATH, target_x=0.25, target_y=0.25, tol=1.0e-4)
    assert neg_info["found"] is False


def test_fail_closed_on_missing_outputs(tmp_path):
    """Verify strict fail-closed behavior: missing observations emit NOT_MEASURABLE / FAIL, never PASS."""
    # Completely empty solver data
    empty_solver = {}
    res = evaluate_physical_gates(empty_solver, DEFAULT_DONOR_REFERENCE)

    assert res["all_gates_pass"] is False
    assert res["overall_status"] == "NOT_YET_MEASURABLE_PENDING_PHYSICAL_SOLVE"
    assert res["verdict"] == "UNQUALIFIED_PENDING_PHYSICAL_SOLVE"

    for gname, gdata in res["gates"].items():
        assert gdata["status"] == "NOT_MEASURABLE", f"{gname} should be NOT_MEASURABLE"
        assert gdata["verdict"] == "FAIL", f"{gname} should be FAIL"
        assert "reason" in gdata, f"{gname} must state an explicit failure reason"

    # Missing CSV file
    non_existent_csv = tmp_path / "non_existent.csv"
    csv_data = parse_energy_csv(non_existent_csv)
    assert csv_data["found"] is False

    # Missing DAT file
    non_existent_dat = tmp_path / "non_existent.dat"
    dat_data = parse_reaction_force_dat(non_existent_dat)
    assert dat_data["found"] is False

    # Missing MSG file
    non_existent_msg = tmp_path / "non_existent.msg"
    msg_data = parse_residual_norm_msg(non_existent_msg)
    assert msg_data["found"] is False


def test_accurate_evaluation_on_synthetic_pass_fixture(tmp_path):
    """Verify evaluation on synthetic PASS observations where all Gates C1-C5 are compliant."""
    pass_solver_data = {
        "residual_norm": {
            "found": True,
            "R_max_norm": 4.5e-4,  # <= 1.0e-3
            "R_max": 0.29,
            "q_avg": 650.0,
        },
        "reaction_force": {
            "found": True,
            "RF2_N": 654.10,  # |654.10 - 653.0886| / 653.0886 = 0.155% <= 0.50%
        },
        "internal_energy": {
            "found": True,
            "E_total_mJ": 1.6660,  # |1.6660 - 1.663384| / 1.663384 = 0.157% <= 0.50%
        },
        "damage_field": {
            "found": True,
            "min_delta_d": -2.5e-5,  # >= -1.0e-4
            "delta_d_tip": 4.0e-4,   # <= 1.0e-3
            "tip_node": 209,
        },
    }

    out_json = tmp_path / "pass_eval.json"
    res = evaluate_physical_gates(pass_solver_data, DEFAULT_DONOR_REFERENCE, DEFAULT_THRESHOLDS, out_json)

    assert res["all_gates_pass"] is True
    assert res["overall_status"] == "MEASURED_ALL_GATES_PASS"
    assert res["verdict"] == "PASS"

    assert res["gates"]["gate_c1_equilibrium_residual"]["verdict"] == "PASS"
    assert res["gates"]["gate_c2_reaction_force_parity"]["verdict"] == "PASS"
    assert res["gates"]["gate_c3_internal_energy_continuity"]["verdict"] == "PASS"
    assert res["gates"]["gate_c4_pointwise_damage_irreversibility"]["verdict"] == "PASS"
    assert res["gates"]["gate_c5_artificial_crack_tip_damage_cap"]["verdict"] == "PASS"
    assert out_json.exists()


def test_accurate_evaluation_on_synthetic_fail_fixtures():
    """Verify each individual gate threshold violation produces FAIL and all_gates_pass=False."""
    base_pass = {
        "residual_norm": {"found": True, "R_max_norm": 4.5e-4},
        "reaction_force": {"found": True, "RF2_N": 654.10},
        "internal_energy": {"found": True, "E_total_mJ": 1.6660},
        "damage_field": {"found": True, "min_delta_d": -2.5e-5, "delta_d_tip": 4.0e-4, "tip_node": 209},
    }

    # 1. Gate C1 Fail: residual norm too large
    fail_c1 = dict(base_pass)
    fail_c1["residual_norm"] = {"found": True, "R_max_norm": 2.5e-3}  # > 1.0e-3
    r1 = evaluate_physical_gates(fail_c1)
    assert r1["all_gates_pass"] is False
    assert r1["gates"]["gate_c1_equilibrium_residual"]["verdict"] == "FAIL"

    # 2. Gate C2 Fail: reaction force discrepancy > 0.50%
    fail_c2 = dict(base_pass)
    fail_c2["reaction_force"] = {"found": True, "RF2_N": 660.0}  # ~1.06%
    r2 = evaluate_physical_gates(fail_c2)
    assert r2["all_gates_pass"] is False
    assert r2["gates"]["gate_c2_reaction_force_parity"]["verdict"] == "FAIL"

    # 3. Gate C3 Fail: internal energy discrepancy > 0.50%
    fail_c3 = dict(base_pass)
    fail_c3["internal_energy"] = {"found": True, "E_total_mJ": 1.6800}  # ~1.00%
    r3 = evaluate_physical_gates(fail_c3)
    assert r3["all_gates_pass"] is False
    assert r3["gates"]["gate_c3_internal_energy_continuity"]["verdict"] == "FAIL"

    # 4. Gate C4 Fail: pointwise healing min_delta_d < -1.0e-4
    fail_c4 = dict(base_pass)
    fail_c4["damage_field"] = {"found": True, "min_delta_d": -5.0e-4, "delta_d_tip": 4.0e-4, "tip_node": 209}
    r4 = evaluate_physical_gates(fail_c4)
    assert r4["all_gates_pass"] is False
    assert r4["gates"]["gate_c4_pointwise_damage_irreversibility"]["verdict"] == "FAIL"

    # 5. Gate C5 Fail: crack tip damage surge > 1.0e-3
    fail_c5 = dict(base_pass)
    fail_c5["damage_field"] = {"found": True, "min_delta_d": -2.5e-5, "delta_d_tip": 2.5e-3, "tip_node": 209}
    r5 = evaluate_physical_gates(fail_c5)
    assert r5["all_gates_pass"] is False
    assert r5["gates"]["gate_c5_artificial_crack_tip_damage_cap"]["verdict"] == "FAIL"


def test_pbs_wrapper_guarded_execution():
    """Verify submit_f1791_case1_diagnostic.pbs has proper set +e error trap and entry queue."""
    assert PBS_F1791_PATH.exists(), f"Missing PBS script: {PBS_F1791_PATH}"
    content = PBS_F1791_PATH.read_text(encoding="utf-8", errors="replace")

    # Queue directive
    assert "#PBS -q entry_imfdfkmq" in content, "PBS queue must be entry_imfdfkmq per cluster routing contract"

    # Solver call error trap
    assert "set +e" in content, "Solver execution must disable bare set -e abort"
    assert "EXIT_CODE=$?" in content, "Solver exit code must be captured"
    assert "set -e" in content, "Strict error handling must be restored after exit code capture"

    # Observable extractor invocation on failure as well as success
    assert "extract_f1791_observables.py" in content
    assert "exit ${EXIT_CODE}" in content


def test_inactive_dof2_audit_on_n_top():
    """Verify the 98 nodes with inactive DOF 2 correspond to N_TOP tied via *EQUATION."""
    assert DIAGNOSTIC_INP_PATH.exists(), f"Missing diagnostic deck: {DIAGNOSTIC_INP_PATH}"
    content = DIAGNOSTIC_INP_PATH.read_text(encoding="utf-8", errors="replace")

    # Locate N_TOP
    match = re.search(r"\*NSET, NSET=N_TOP\n(.*?)(?=\*|\Z)", content, re.DOTALL)
    assert match is not None, "N_TOP set not found"
    n_top_nodes = [int(p.strip()) for p in match.group(1).replace("\n", ",").split(",") if p.strip()]
    assert len(n_top_nodes) == 98, f"N_TOP should contain exactly 98 nodes, found {len(n_top_nodes)}"

    # Confirm *EQUATION ties DOF 2 of N_TOP to N_RP
    eq_match = re.search(r"\*EQUATION\s*\n\s*2\s*\n\s*N_TOP,\s*2,\s*1\.0,\s*N_RP,\s*2,\s*-1\.0", content)
    assert eq_match is not None, "*EQUATION tying N_TOP to N_RP must be present"


def test_execution_routing_manifest_and_dryrun():
    """Verify METHOD_C_F1791_DIAGNOSTIC_AUTHORIZATION.json passes Invoke-Mode1Execution.ps1 -DryRun."""
    assert MANIFEST_PATH.exists(), f"Missing manifest: {MANIFEST_PATH}"

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["batch_name"] == "MODE1_METHOD_C_F1791_DIAGNOSTIC"
    assert manifest["max_submissions"] == 1
    assert manifest["scientific_scope"] == "MODE1"
    assert len(manifest["jobs"]) == 1

    # Run Invoke-Mode1Execution.ps1 -DryRun via PowerShell
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(REPO_ROOT / "scripts" / "hpc" / "Invoke-Mode1Execution.ps1"),
        "-ManifestPath",
        str(MANIFEST_PATH),
        "-DryRun",
    ]
    proc = subprocess.run(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, f"Invoke-Mode1Execution.ps1 -DryRun failed: {proc.stderr}\n{proc.stdout}"
    assert "DRY_RUN: technical preflight then once-only execution" in proc.stdout


def test_zero_new_pbs_submissions_and_governance():
    """Verify cumulative PBS submissions remain strictly preserved at 35 with 0 new consumed."""
    assert ACTIVE_TASK_PATH.exists(), f"Missing ACTIVE_TASK.json: {ACTIVE_TASK_PATH}"
    with open(ACTIVE_TASK_PATH, "r", encoding="utf-8") as f:
        task = json.load(f)

    assert task["max_new_pbs_submissions"] == 0
    assert task["submissions_consumed"] == 0
    assert task["cumulative_pbs_submissions"] == 35
    assert task["master_goal_status"] == "OPEN"
    assert task["task_id"] in [
        "F1791-MODE-I-METHOD-C-DIAGNOSTIC_OBSERVABILITY_REPAIR_AND_EXECUTION_QUALIFICATION",
        "F1792-MODE-I-METHOD-C-EXTRACTOR_RUNTIME_AND_RELEASE_GATE_INTEGRATION_REPAIR",
        "F1793-METHOD-A-CAUSAL-ADAPTIVITY-AND-NON-HINDSIGHT-VERIFICATION",
        "F1794-CASE2-NATIVE-MISESERI-CAUSAL-REMESHING-NUMERICAL-DEMONSTRATION",
    ]
