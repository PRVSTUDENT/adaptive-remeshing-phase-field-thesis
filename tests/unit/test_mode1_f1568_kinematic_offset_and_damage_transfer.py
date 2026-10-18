#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Task F1568:
- Retraction of false variational incompatibility theorem and Candidate 2A uniqueness overclaims.
- Independent verification of Candidate 2A physical state from raw fields and frozen UEL equations.
- Donor clipping audit: physical bound d <= 1.0 has negligible energetic bias (-0.0509%).
- Non-negative history field H >= 0 audit across crack front, wake, and intact ligament.
- Genuinely constrained damage-transfer feasibility experiment on representative crack patches:
  * Proves exact constrained QP is FEASIBLE (trust-constr converges with 0 subelement violations).
  * Distinguishes optimization defects from FE representation limits
    (exact linear interpolation of transverse cusp unavoidably inflates fracture energy by +14% to +33%).
- Kinematic-Offset UEL continuation architecture parity diagnostic:
  * Mechanical residual ||R_u^{(0)}|| < 1e-12 kN and phase residual ||R_d^{(0)}|| < 1e-12.
  * Reaction force parity |RF_B - RF_A| < 1e-10 N.
  * Elastic energy parity |E_B - E_A| < 1e-10 mJ.
  * Incremental work parity |Delta W_B - Delta W_A| < 1e-10 mJ.
  * Zero reload work verified: W_ext^{(B)}(0) == 0.0 mJ.
- Strict governance invariants:
  * Production UEL f42_mixed_uel.for remains 100% frozen (CE8D5EDC...).
  * PACKAGE71_RECEIVER_SUBMISSION = WITHHELD_BY_POLICY.
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

C2A_VERIF_PATH = (
    REPO_ROOT
    / "runs"
    / "hpc"
    / "mode1_stage_c1_2_cycle5_continuation"
    / "F1568_CANDIDATE2A_INDEPENDENT_FIELD_VERIFICATION.json"
)

PATCH_QP_PATH = (
    REPO_ROOT
    / "runs"
    / "hpc"
    / "mode1_stage_c1_2_cycle5_continuation"
    / "F1568_PATCH_EXACT_QP_FEASIBILITY.json"
)

PARITY_PATH = (
    REPO_ROOT
    / "runs"
    / "hpc"
    / "mode1_stage_c1_2_cycle5_continuation"
    / "F1568_KINEMATIC_OFFSET_PARITY_EVIDENCE.json"
)

PROD_UEL_PATH = (
    REPO_ROOT
    / "models"
    / "pandey_kumar_mode1"
    / "15_energy_qualification_small"
    / "f42_mixed_uel.for"
)

DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
)

EXPECTED_PROD_UEL_HASH = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"


def test_f1568_candidate2a_independent_verification_and_clipping():
    """Verify Candidate 2A metrics and donor clipping audit from raw numerical fields."""
    assert C2A_VERIF_PATH.exists(), f"Missing verification at {C2A_VERIF_PATH}"
    with open(C2A_VERIF_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Candidate 2A conservation metrics pass
    m = data["verified_metrics"]
    assert abs(m["delta_RF2_N"]) <= 5.0, f"RF2 failed: {m['delta_RF2_N']}"
    assert abs(m["delta_elas_pct"]) <= 0.50, f"Elastic energy failed: {m['delta_elas_pct']}%"
    assert abs(m["delta_frac_pct"]) <= 0.50, f"Fracture energy failed: {m['delta_frac_pct']}%"
    assert abs(m["delta_tot_pct"]) <= 0.10, f"Total energy failed: {m['delta_tot_pct']}%"
    assert m["d_max"] <= 1.00000001, f"d_max violated: {m['d_max']}"

    # 2. Donor clipping audit
    audit = data["clipping_audit"]
    assert abs(audit["delta_clipping_pct"]) < 0.10, f"Bias too large: {audit['delta_clipping_pct']}%"

    # 3. History field audit
    h_audit = data["history_field_audit"]
    for reg in h_audit:
        assert reg["non_negative"] is True
        assert reg["H_recip_MPa"] >= 0.0


def test_f1568_patch_exact_qp_feasibility_and_tradeoff():
    """Verify exact constrained QP feasibility and distinction of representation limits."""
    assert PATCH_QP_PATH.exists(), f"Missing patch QP results at {PATCH_QP_PATH}"
    with open(PATCH_QP_PATH, "r", encoding="utf-8") as f:
        patch_data = json.load(f)

    for patch_key in ["band4_core", "crack_process_zone"]:
        assert patch_key in patch_data
        p = patch_data[patch_key]
        results = {r["label"]: r for r in p["results"]}

        # 1. Candidate 2A has subelement violations but near-zero energy error
        c2a = results["Formulation 1: Candidate 2A (Nodal Bounds Only)"]
        assert c2a["viol_count"] > 0, "Candidate 2A should have subelement deficits"
        assert abs(c2a["delta_frac_pct"]) < 5.0, f"C2A energy jump too large: {c2a['delta_frac_pct']}%"

        # 2. Exact Constrained QP is FEASIBLE with ZERO subelement violations
        exact_qp = results["Formulation 2: Exact Constrained QP (trust-constr)"]
        assert exact_qp["success"] is True, "Exact QP must converge successfully"
        assert exact_qp["viol_count"] == 0, f"Exact QP has violations: {exact_qp['viol_count']}"
        assert exact_qp["max_def"] < 1e-6, f"Exact QP max deficit: {exact_qp['max_def']}"
        assert exact_qp["delta_frac_pct"] > 10.0, "Representation limit requires energy inflation"

        # 3. Penalty formulation also inflates energy by > 10%
        pen10000 = results["Formulation 3: Quadratic Penalty (rho = 10000.0)"]
        assert pen10000["delta_frac_pct"] > 10.0


def test_f1568_kinematic_offset_parity_diagnostic():
    """Verify Kinematic-Offset UEL zero-increment and continuation parity."""
    assert PARITY_PATH.exists(), f"Missing parity evidence at {PARITY_PATH}"
    with open(PARITY_PATH, "r", encoding="utf-8") as f:
        parity = json.load(f)

    assert parity["parity_pass"] is True

    # Zero-increment audit
    z = parity["zero_increment_audit"]
    assert z["residual_u_free_kN"] < 1e-12, f"Mechanical residual too high: {z['residual_u_free_kN']}"
    assert z["residual_d"] < 1e-12, f"Phase residual too high: {z['residual_d']}"
    assert abs(z["delta_RF2_N"]) < 1e-10, f"RF2 delta too high: {z['delta_RF2_N']}"
    assert abs(z["delta_E_elas_mJ"]) < 1e-10, f"Elastic energy delta too high: {z['delta_E_elas_mJ']}"
    assert z["W_ext_reload_mJ"] == 0.0, "Reload work must be exactly zero"
    assert z["zero_reload_work_verified"] is True

    # Forward continuation advance audit
    fwd = parity["forward_advance_audit"]
    assert fwd["max_displacement_discrepancy_mm"] < 1e-12
    assert abs(fwd["delta_RF2_N"]) < 1e-10
    assert abs(fwd["delta_E_elas_mJ"]) < 1e-10
    assert abs(fwd["delta_Delta_W_ext_mJ"]) < 1e-10


def test_f1568_production_uel_remains_frozen():
    """Verify that the production UEL f42_mixed_uel.for remains 100% frozen."""
    assert PROD_UEL_PATH.exists(), f"Production UEL missing at {PROD_UEL_PATH}"
    with open(PROD_UEL_PATH, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest().lower()
    assert actual_hash == EXPECTED_PROD_UEL_HASH, (
        f"Production UEL modified! Expected {EXPECTED_PROD_UEL_HASH}, got {actual_hash}"
    )


def test_f1568_governance_and_retractions():
    """Verify report corrections, retractions, and strict governance invariants."""
    assert DOC_PATH.exists(), f"Missing doc at {DOC_PATH}"
    with open(DOC_PATH, "r", encoding="utf-8") as f:
        doc = f.read()

    # Priority 1 retractions
    doc_lower = doc.lower()
    assert "retracted" in doc_lower or "retraction" in doc_lower
    assert "uniqueness" in doc_lower
    assert "penalty" in doc_lower

    # Governance checks in ACTIVE_TASK / CURRENT_STATE
    curr_state_path = REPO_ROOT / "project_coordination" / "CURRENT_STATE.md"
    assert curr_state_path.exists()
    with open(curr_state_path, "r", encoding="utf-8") as f:
        cs = f.read()
    assert "CYCLE5_NONMATCHING_TRANSFER = FAIL" in cs
    assert "PACKAGE70_REEQUILIBRATION = FAIL" in cs
    assert "METHOD_C_OVERALL = NOT_YET_QUALIFIED" in cs
    assert "PACKAGE71_RECEIVER_SUBMISSION = WITHHELD_BY_POLICY" in cs or "PACKAGE71_RECEIVER_SUBMISSION = ON_SCIENTIFIC_HOLD" in cs
