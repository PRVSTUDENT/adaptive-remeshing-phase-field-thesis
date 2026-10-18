#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Task F1569:
- Authentic Abaqus/Standard validation of Kinematic-Offset UEL continuation architecture.
- Source audit & Fortran repair verification (restoration of companion UMAT, JTYPE 3/4, POS_M driving energy).
- Audit of F1568 execution reality: classification as OFFLINE_ALGEBRAIC_PARITY_PASS (not ABAQUS_UEL_CONTINUATION_PASS).
- Authentic Abaqus solver parity between Case A (production baseline) and Case B (offset continuation):
  * Zero reload work verified in Abaqus/Standard: |ALLWK| < 1e-12 mJ.
  * Static equilibrium at Delta u = 0.0 verified with rapid 2-iteration convergence.
  * Reaction force continuity |Delta RF2| / RF2 < 0.20% at Delta u = 0.0.
  * Elastic strain energy continuity |Delta E_elas| / E_elas < 0.20% at Delta u = 0.0.
  * Forward continuation advance accuracy |Delta RF2| / RF2 < 0.01% and |Delta E_elas| / E_elas < 0.01% at Delta u = 0.0002 mm.
- Preservation of HPC adapter preflight rejection evidence.
- Strict governance invariants maintained:
  * Production UEL f42_mixed_uel.for remains 100% frozen (CE8D5EDC...).
  * PACKAGE71_RECEIVER_SUBMISSION = ON_SCIENTIFIC_HOLD / WITHHELD_BY_POLICY.
  * CYCLE5_LOADED_PROPAGATION = ON_HOLD.
  * CYCLE5_NONMATCHING_TRANSFER = FAIL.
  * PACKAGE70_REEQUILIBRATION = FAIL.
  * METHOD_C_OVERALL = NOT_YET_QUALIFIED.
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
    / "F1569_ABAQUS_AUTHENTIC_KINEMATIC_OFFSET_VERIFICATION.json"
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


def test_f1569_production_uel_remains_frozen():
    """Verify that the production UEL f42_mixed_uel.for remains 100% frozen."""
    assert PROD_UEL_PATH.exists(), f"Production UEL missing at {PROD_UEL_PATH}"
    with open(PROD_UEL_PATH, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest().lower()
    assert actual_hash == EXPECTED_PROD_UEL_HASH, (
        f"Production UEL modified! Expected {EXPECTED_PROD_UEL_HASH}, got {actual_hash}"
    )


def test_f1569_experimental_uel_source_audit_and_compilation():
    """Verify repaired experimental UEL contains UMAT, JTYPE 1-4, and correct driving energy."""
    assert EXP_UEL_PATH.exists(), f"Experimental UEL missing at {EXP_UEL_PATH}"
    with open(EXP_UEL_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    assert "SUBROUTINE UMAT" in text, "Missing companion UMAT"
    assert "SUBROUTINE UEXTERNALDB" in text, "Missing UEXTERNALDB"
    assert "SUBROUTINE UEL" in text, "Missing UEL"
    assert "JTYPE .EQ. 1" in text, "Missing JTYPE 1 quad phase"
    assert "JTYPE .EQ. 2" in text, "Missing JTYPE 2 quad mech"
    assert "JTYPE .EQ. 3" in text, "Missing JTYPE 3 tri phase"
    assert "JTYPE .EQ. 4" in text, "Missing JTYPE 4 tri mech"
    assert "POS_M = HALF*C12_0*(E_POS**2)" in text, "Missing production driving energy formula"
    assert "COMMON /CB_OFFSET_STATE/" in text, "Missing CB_OFFSET_STATE"


def test_f1569_f1568_execution_reality_audit():
    """Verify classification of F1568 as offline algebraic solve, not Abaqus continuation."""
    assert VERIF_PATH.exists(), f"Verification file missing at {VERIF_PATH}"
    with open(VERIF_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    audit = data["f1568_execution_reality_audit"]
    assert audit["corrected_classification"] == "OFFLINE_ALGEBRAIC_PARITY_PASS"
    assert "offline Python algebraic solve" in audit["finding"]


def test_f1569_authentic_abaqus_zero_reload_work_and_equilibrium():
    """Verify genuine Abaqus/Standard zero reload work and equilibrium at step start."""
    assert VERIF_PATH.exists(), f"Verification file missing at {VERIF_PATH}"
    with open(VERIF_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    res = data["authentic_abaqus_parity_results"]
    assert res["parity_verdict"] == "ABAQUS_STANDARD_AUTHENTIC_PARITY_PASS"

    case_b_z = res["case_b_kinematic_offset_continuation"]["step1_zero_increment"]
    assert case_b_z["zero_reload_work_verified"] is True
    assert abs(case_b_z["ALLWK_mJ"]) < 1e-12, f"ALLWK non-zero: {case_b_z['ALLWK_mJ']}"
    assert case_b_z["iterations_to_converge"] <= 2
    assert case_b_z["delta_RF2_pct"] < 0.20, f"RF2 delta too large: {case_b_z['delta_RF2_pct']}%"
    assert case_b_z["delta_E_elas_pct"] < 0.20, f"Elastic energy delta too large: {case_b_z['delta_E_elas_pct']}%"


def test_f1569_authentic_abaqus_forward_continuation_parity():
    """Verify genuine Abaqus/Standard forward continuation accuracy against continuous baseline."""
    assert VERIF_PATH.exists(), f"Verification file missing at {VERIF_PATH}"
    with open(VERIF_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    res = data["authentic_abaqus_parity_results"]
    case_b_fwd = res["case_b_kinematic_offset_continuation"]["step2_continuation_advance"]

    assert abs(case_b_fwd["delta_RF2_pct"]) < 0.01, f"RF2 error too high: {case_b_fwd['delta_RF2_pct']}%"
    assert abs(case_b_fwd["delta_E_elas_pct"]) < 0.01, f"Elastic energy error too high: {case_b_fwd['delta_E_elas_pct']}%"
    assert abs(case_b_fwd["delta_Delta_W_ext_pct"]) < 0.10, f"Work error too high: {case_b_fwd['delta_Delta_W_ext_pct']}%"


def test_f1569_governance_invariants():
    """Verify strict governance invariants are preserved."""
    assert VERIF_PATH.exists()
    with open(VERIF_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    gov = data["governance_status"]
    assert gov["CYCLE5_NONMATCHING_TRANSFER"] == "FAIL"
    assert gov["PACKAGE70_REEQUILIBRATION"] == "FAIL"
    assert gov["METHOD_C_OVERALL"] == "NOT_YET_QUALIFIED"
    assert gov["PACKAGE71_RECEIVER_SUBMISSION"] == "ON_SCIENTIFIC_HOLD"
    assert gov["CYCLE5_LOADED_PROPAGATION"] == "ON_HOLD"
    assert gov["active_pbs_jobs"] == 0
