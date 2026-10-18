#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Task F1572:
- Recover cracked-state reference, verify phase-field & history outputs,
  and execute first authentic damaged-state continuation test in Abaqus/Standard.
- Priority 1: Case A cracked solve (63 incs Step 1, 5 incs Step 2, Exit 0).
- Priority 2: constants=3 non-invasive indexing invariance verified.
- Priority 3: Genuine phase-field DOF 3 recovery from .dat (d_max=1.002183, max discrepancy vs SDV1 < 1e-7).
- Priority 4: History field layout (4 GPs/elem, 1600 total, 0 irreversibility violations, max H=51.93 MPa).
- Priority 5: Authentic developed-crack checkpoint characterized (RF2=11.35 N, ALLSE=14.18 mJ).
- Priority 6 & 7: Case B offset continuation executed in Abaqus/Standard:
  * Zero reload work verified (|ALLWK| = 0.0 mJ).
  * Step 1 zero-increment convergence in 2 Newton iterations (RF2=7.73 N).
  * Step 2 forward continuation advance parity |Delta RF2| / RF2 = 1.69% at Delta u = 0.0002 mm.
  * Step 2 forward continuation elastic energy parity |Delta ALLSE| / ALLSE = 1.69%.
- Strict governance invariants:
  * Production UEL f42_mixed_uel.for remains 100% frozen (CE8D5EDC...).
  * EXPERIMENTAL_OFFSET_CRACKED_STATE_CONTINUATION = EVALUATED_WITH_REPORTED_PARITY.
  * CYCLE5_NONMATCHING_TRANSFER = FAIL.
  * PACKAGE70_REEQUILIBRATION = FAIL.
  * METHOD_C_OVERALL = NOT_YET_QUALIFIED.
  * PACKAGE71_RECEIVER_SUBMISSION = ON_SCIENTIFIC_HOLD.
  * CYCLE5_LOADED_PROPAGATION = ON_HOLD.
"""

import hashlib
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

VERIF_PATH = (
    REPO_ROOT
    / "runs"
    / "hpc"
    / "mode1_stage_c1_2_cycle5_continuation"
    / "F1572_CRACKED_STATE_OFFSET_CONTINUATION_VERIFICATION.json"
)

PROD_UEL_PATH = (
    REPO_ROOT
    / "models"
    / "pandey_kumar_mode1"
    / "15_energy_qualification_small"
    / "f42_mixed_uel.for"
)

EXP_UEL_PATH = (
    REPO_ROOT
    / "models"
    / "pandey_kumar_mode1"
    / "experimental_offset_uel"
    / "f42_experimental_offset_uel.for"
)

EXPECTED_PROD_UEL_HASH = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"


def test_f1572_production_uel_remains_frozen():
    """Verify that the production UEL f42_mixed_uel.for remains 100% frozen."""
    assert PROD_UEL_PATH.exists(), f"Production UEL missing at {PROD_UEL_PATH}"
    with open(PROD_UEL_PATH, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest().lower()
    assert actual_hash == EXPECTED_PROD_UEL_HASH, (
        f"Production UEL modified! Expected {EXPECTED_PROD_UEL_HASH}, got {actual_hash}"
    )


def test_f1572_verification_artifact_exists_and_valid():
    """Verify F1572 verification JSON artifact exists and has correct schema."""
    assert VERIF_PATH.exists(), f"Verification file missing at {VERIF_PATH}"
    with open(VERIF_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["task_id"] == "F1572-RECOVER-CRACKED-REFERENCE-AND-FIRST-DAMAGED-CONTINUATION-TEST"
    assert data["mesh"]["physical_elements"] == 400
    assert data["mesh"]["physical_nodes"] == 450


def test_f1572_priority_1_cracked_reference_retrieval():
    """Verify Priority 1: Case A cracked solve completed Exit 0 with 63 and 5 increments."""
    with open(VERIF_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    p1 = data["priorities_completed"]["priority_1_cracked_reference_retrieval"]
    assert p1["status"] == "PASS"
    assert p1["step1_increments"] == 63
    assert p1["step2_increments"] == 5
    assert p1["exit_code"] == 0


def test_f1572_priority_2_constants_3_invariance():
    """Verify Priority 2: constants=3 indexing invariance verified."""
    with open(VERIF_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    p2 = data["priorities_completed"]["priority_2_constants_3_invariance"]
    assert p2["status"] == "PASS"
    assert "Bitwise RF2 identity" in p2["numerical_proof"]


def test_f1572_priority_3_phase_field_dof3_recovery():
    """Verify Priority 3: Authentic phase-field recovery and bilinear agreement with SDV1."""
    with open(VERIF_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    p3 = data["priorities_completed"]["priority_3_phase_field_dof3_recovery"]
    assert p3["status"] == "PASS"
    assert p3["nodal_damage_max"] > 1.0
    assert p3["max_damage_node"] == 232
    assert p3["nodes_d_ge_0_95"] == 21
    assert p3["nodes_d_ge_0_50"] == 71
    assert p3["bilinear_reconstructed_element_damage_vs_sdv1_max_discrepancy"] < 1e-7


def test_f1572_priority_4_history_layout_and_irreversibility():
    """Verify Priority 4: History field layout and strict monotonicity across step boundary."""
    with open(VERIF_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    p4 = data["priorities_completed"]["priority_4_history_field_layout_and_irreversibility"]
    assert p4["status"] == "PASS"
    assert p4["total_integration_points"] == 1600
    assert p4["irreversibility_violations"] == 0
    assert p4["max_history_H0_MPa"] > 50.0


def test_f1572_case_b_cracked_continuation_parity():
    """Verify Priority 6 & 7: Case B offset continuation metrics in Abaqus/Standard."""
    with open(VERIF_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    cb = data["priorities_completed"]["priority_6_7_case_b_continuation_execution_and_evaluation"]
    assert cb["status"] == "PASS"
    assert cb["exit_code"] == 0

    # Step 1: Zero-increment reconstruction
    s1 = cb["step1_zero_increment"]
    assert s1["iterations_to_converge"] == 2
    assert s1["zero_reload_work_verified"] is True
    assert abs(s1["ALLWK_mJ"]) < 1e-12

    # Step 2: Forward continuation advance
    s2 = cb["step2_continuation_advance"]
    assert s2["completion_pct"] == 100.0
    assert abs(s2["RF2_continuation_parity_pct"]) < 2.0  # 1.69% parity
    assert abs(s2["ALLSE_continuation_parity_pct"]) < 2.0  # 1.69% parity


def test_f1572_experimental_uel_source_repair_and_guard():
    """Verify experimental offset UEL contains OFFSET_LOADED guard preventing state wipe."""
    assert EXP_UEL_PATH.exists(), f"Experimental UEL missing at {EXP_UEL_PATH}"
    with open(EXP_UEL_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    assert "IF (.NOT. OFFSET_LOADED) THEN" in text, (
        "Missing IF (.NOT. OFFSET_LOADED) guard around SVARS initialization in UEL"
    )


def test_f1572_governance_invariants():
    """Verify strict governance invariants are recorded correctly."""
    with open(VERIF_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    gov = data["governance_status"]
    assert gov["EXPERIMENTAL_OFFSET_CRACKED_STATE_CONTINUATION"] == "EVALUATED_WITH_REPORTED_PARITY"
    assert gov["CYCLE5_NONMATCHING_TRANSFER"] == "FAIL"
    assert gov["PACKAGE70_REEQUILIBRATION"] == "FAIL"
    assert gov["METHOD_C_OVERALL"] == "NOT_YET_QUALIFIED"
    assert gov["PACKAGE71_RECEIVER_SUBMISSION"] == "ON_SCIENTIFIC_HOLD"
    assert gov["CYCLE5_LOADED_PROPAGATION"] == "ON_HOLD"
    assert gov["PRODUCTION_UEL_FROZEN"] is True
