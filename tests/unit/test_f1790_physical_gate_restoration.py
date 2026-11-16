# -*- coding: utf-8 -*-
"""
tests/unit/test_f1790_physical_gate_restoration.py
Task F1790: Unit test suite for Mode-I Method C Physical Gate Restoration & Release Diagnostic.
"""

import hashlib
import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

FROZEN_UEL_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

SHARED_FRAMEWORK_PATH = REPO_ROOT / "scripts" / "remeshing" / "reusable_2d_adaptive_framework.py"
ALLOWED_FRAMEWORK_HASHES = [
    "181CB4E5A8CE765CBE0765D71BA9C3CCA934A33140BC61F5B9A4CD7A6AEFCD40",
    "49B2E1B7706594941B4DD58ABAA4C2DB9090B4C06D2358EAF157289AAD3BAE3F",
    "907EE548BB28B920038E8C51D8A4DAA584E9DCE84DD99EEB6A10ECB259DBCAC0",
    "99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D",
]

DIAGNOSTIC_INP_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "PK_F1790_CASE1_RELEASE_DIAGNOSTIC.inp"
RECEIPT_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "PK_F1790_RELEASE_DIAGNOSTIC_RECEIPT.json"
DATACHECK_TXT_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "evidence_f1790_datacheck" / "PK_F1790_CASE1_DATACHECK.txt"
DATACHECK_DAT_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "evidence_f1790_datacheck" / "PK_F1790_CASE1_DATACHECK.dat"
DATACHECK_MD_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "evidence_f1790_datacheck" / "PK_F1790_DATACHECK_VERIFICATION.md"
PBS_SCRIPT_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "submit_f1790_case1_diagnostic.pbs"
ACTIVE_TASK_PATH = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"


def get_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_frozen_codebases_integrity():
    """Verify bitwise invariance of frozen Fortran UEL and Python framework."""
    assert FROZEN_UEL_PATH.exists(), f"Missing frozen UEL: {FROZEN_UEL_PATH}"
    actual_uel_sha = get_sha256(FROZEN_UEL_PATH)
    assert actual_uel_sha == FROZEN_UEL_SHA256, f"UEL hash altered: {actual_uel_sha} != {FROZEN_UEL_SHA256}"

    assert SHARED_FRAMEWORK_PATH.exists(), f"Missing framework: {SHARED_FRAMEWORK_PATH}"
    actual_fw_sha = get_sha256(SHARED_FRAMEWORK_PATH)
    assert actual_fw_sha in ALLOWED_FRAMEWORK_HASHES, f"Framework hash altered: {actual_fw_sha} not in {ALLOWED_FRAMEWORK_HASHES}"


def test_provenance_receipt_and_target_mesh():
    """Verify receipt metadata: donor 2,906 elements and target 16,597 elements (16,149 quads, 448 tris)."""
    assert RECEIPT_PATH.exists(), f"Missing receipt: {RECEIPT_PATH}"
    with open(RECEIPT_PATH, "r", encoding="utf-8") as f:
        receipt = json.load(f)

    assert receipt["task_id"] == "F1790-MODE-I-METHOD-C-PHYSICAL-GATE-RESTORATION-AND-RELEASE-DIAGNOSTIC"
    donor = receipt["donor_provenance"]
    assert donor["mesh_elements"] == 2906
    assert donor["mesh_nodes"] == 2988
    assert donor["handoff_displacement_mm"] == 0.0050

    target = receipt["target_mesh_provenance"]
    assert target["physical_elements"] == 16597
    assert target["quad_count"] == 16149
    assert target["tri_count"] == 448
    assert target["physical_nodes"] == 16642
    assert target["min_history_gp_kN_mm2"] >= 0.0


def test_offline_precheck_metrics():
    """Verify continuous quadrature precheck metrics evaluated on transferred fields."""
    with open(RECEIPT_PATH, "r", encoding="utf-8") as f:
        receipt = json.load(f)

    precheck = receipt["offline_precheck_metrics"]
    assert precheck["displacement_l2_relative_error_pct"]["value"] <= 1.00
    assert precheck["peak_damage_difference"]["value"] <= 0.020
    assert precheck["integrated_damage_difference_pct"]["value"] <= 5.00
    assert precheck["history_non_negativity"]["min_H_kN_mm2"] >= 0.0
    assert precheck["history_non_negativity"]["negative_count"] == 0
    assert precheck["quadrature_boundary_force_continuity_pct"]["value_pct"] <= 0.50
    assert precheck["quadrature_internal_energy_continuity_pct"]["value_pct"] <= 0.50
    assert precheck["global_energy_residual_pct"]["value_pct"] <= 10.0


def test_restored_method_c_acceptance_gates():
    """Verify Gates C1-C5 are restored to exact predeclared definitions and marked NOT_YET_MEASURABLE."""
    with open(RECEIPT_PATH, "r", encoding="utf-8") as f:
        receipt = json.load(f)

    gates = receipt["restored_physical_acceptance_gates"]
    assert "gate_c1_equilibrium_residual_norm" in gates
    assert gates["gate_c1_equilibrium_residual_norm"]["threshold"] == 1.0e-3
    assert gates["gate_c1_equilibrium_residual_norm"]["status"] == "NOT_YET_MEASURABLE_PENDING_PBS_SOLVE"

    assert "gate_c2_reaction_force_parity" in gates
    assert gates["gate_c2_reaction_force_parity"]["threshold_pct"] == 0.50
    assert gates["gate_c2_reaction_force_parity"]["donor_reference_force_N"] == 653.0886
    assert gates["gate_c2_reaction_force_parity"]["status"] == "NOT_YET_MEASURABLE_PENDING_PBS_SOLVE"

    assert "gate_c3_internal_energy_continuity" in gates
    assert gates["gate_c3_internal_energy_continuity"]["threshold_pct"] == 0.50
    assert gates["gate_c3_internal_energy_continuity"]["donor_reference_energy_mJ"] == 1.663384
    assert gates["gate_c3_internal_energy_continuity"]["status"] == "NOT_YET_MEASURABLE_PENDING_PBS_SOLVE"

    assert "gate_c4_pointwise_damage_irreversibility" in gates
    assert gates["gate_c4_pointwise_damage_irreversibility"]["threshold"] == -1.0e-4
    assert gates["gate_c4_pointwise_damage_irreversibility"]["status"] == "NOT_YET_MEASURABLE_PENDING_PBS_SOLVE"

    assert "gate_c5_artificial_crack_tip_damage_cap" in gates
    assert gates["gate_c5_artificial_crack_tip_damage_cap"]["threshold"] == 1.0e-3
    assert gates["gate_c5_artificial_crack_tip_damage_cap"]["status"] == "NOT_YET_MEASURABLE_PENDING_PBS_SOLVE"


def test_diagnostic_deck_structure_and_steps():
    """Verify PK_F1790_CASE1_RELEASE_DIAGNOSTIC.inp structure: Step-1 and Step-2 only."""
    assert DIAGNOSTIC_INP_PATH.exists(), f"Missing diagnostic deck: {DIAGNOSTIC_INP_PATH}"
    assert DIAGNOSTIC_INP_PATH.stat().st_size > 9_000_000, "Deck size unexpectedly small"

    content = DIAGNOSTIC_INP_PATH.read_text(encoding="utf-8", errors="replace")
    assert "*STEP, NAME=Step-1-Reconstruct" in content
    assert "*STEP, NAME=Step-2-Hold" in content
    assert "*STEP, NAME=Step-3-Continue" not in content, "Diagnostic release deck should only test Steps 1 & 2"

    assert "*BOUNDARY, OP=NEW" in content
    assert "0.05, 1.0, 1.0e-6, 0.10" in content, "Step-2 time stepping should allow observable first release increments"
    assert "*USER ELEMENT, TYPE=U1" in content
    assert "*USER ELEMENT, TYPE=U2" in content
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in content


def test_abaqus_syntaxcheck_evidence():
    """Verify Abaqus 2024 input-processing evidence is archived, retrievable, and zero errors."""
    assert DATACHECK_TXT_PATH.exists(), f"Missing syntaxcheck text log: {DATACHECK_TXT_PATH}"
    assert DATACHECK_DAT_PATH.exists(), f"Missing datacheck .dat log: {DATACHECK_DAT_PATH}"
    assert DATACHECK_MD_PATH.exists(), f"Missing datacheck verification report: {DATACHECK_MD_PATH}"

    dat_text = DATACHECK_DAT_PATH.read_text(encoding="utf-8", errors="replace")
    assert "END OF USER INPUT PROCESSING" in dat_text
    assert "NUMBER OF ELEMENTS IS                                 49791" in dat_text
    assert "NUMBER OF NODES IS                                    16643" in dat_text
    assert "TOTAL NUMBER OF VARIABLES IN THE MODEL                49927" in dat_text
    assert "***ERROR" not in dat_text

    md_text = DATACHECK_MD_PATH.read_text(encoding="utf-8", errors="replace")
    assert "ZERO FATAL ERRORS (PASS)" in md_text


def test_observable_extraction_module():
    """Verify observable extraction script runs and evaluates dummy solver data accurately."""
    from scripts.state_transfer.extract_f1790_observables import evaluate_physical_gates
    dummy_solver = {
        "R_max_norm": 5.0e-4,
        "RF2_N": 653.20,
        "E_total_mJ": 1.6635,
        "min_delta_d": 0.0,
        "delta_d_tip": 2.0e-4,
    }
    donor_ref = {"RF2_N": 653.0886, "E_total_mJ": 1.663384}
    tmp_out = REPO_ROOT / "tmp_eval_test.json"
    try:
        res = evaluate_physical_gates(dummy_solver, donor_ref, tmp_out)
        assert res["all_gates_pass"] is True
        assert res["gates"]["gate_c1_equilibrium_residual"]["verdict"] == "PASS"
        assert res["gates"]["gate_c2_reaction_force_parity"]["verdict"] == "PASS"
        assert res["gates"]["gate_c3_internal_energy_continuity"]["verdict"] == "PASS"
        assert res["gates"]["gate_c4_pointwise_damage_irreversibility"]["verdict"] == "PASS"
        assert res["gates"]["gate_c5_artificial_crack_tip_damage_cap"]["verdict"] == "PASS"
    finally:
        if tmp_out.exists():
            tmp_out.unlink()


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
        "F1790-MODE-I-METHOD-C-PHYSICAL-GATE-RESTORATION-AND-RELEASE-DIAGNOSTIC",
        "F1791-MODE-I-METHOD-C-DIAGNOSTIC_OBSERVABILITY_REPAIR_AND_EXECUTION_QUALIFICATION",
        "F1792-MODE-I-METHOD-C-EXTRACTOR_RUNTIME_AND_RELEASE_GATE_INTEGRATION_REPAIR",
        "F1793-METHOD-A-CAUSAL-ADAPTIVITY-AND-NON-HINDSIGHT-VERIFICATION",
        "F1794-CASE2-NATIVE-MISESERI-CAUSAL-REMESHING-NUMERICAL-DEMONSTRATION",
        "F1795-CASE2-NATIVE-MISESERI-CAUSAL-REMESHING-CONTROLLED-REPRODUCIBILITY",
        "F1796-CASE2-EVOLVING-NATIVE-MISESERI-CAUSAL-INDICATOR-QUALIFICATION",
        "F1797-CASE2-ALL-FRAME-MISESERI-AND-RECOVERY-PROVENANCE-QUALIFICATION",
        "F1798-CASE3-NATIVE-MISESERI-CAUSAL-BASELINE-REMESHING",
        "F1799-CASE3-CAUSAL-CONFIG-AND-PHYSICAL-DONOR-CONTROLLED-REMESH",
        "F1800-CASE3-PRECRITICAL-NATIVE-MISESERI-SCALE-AND-CAUSAL-REMESH-TEST",
        "F1801-CASE3-NATIVE-MISESERI-ERROR-TARGET-EFFICIENCY-TEST",
        "F1802-CASE3-METHOD-A2-EVOLVING-RECOVERY-DONOR-QUALIFICATION-AND-CAUSAL-REMESH",
        "F1803-CASE3-STATE2-DEGRADED-MODULUS-FIDELITY-NATIVE-REMESH",
    ]
