"""Unit test suite for Task F1456: Verify Method C Continuation Feasibility
and Prepare a Controlled Implementation Plan for Mode-I C1.

Verifies:
1. Existence and comprehensive structural integrity of
   docs/reports/MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md.
2. Exact formulation of the six pre-declared quantitative acceptance criteria.
3. Donor and recipient discretization specifications and provenance links.
4. Frozen production UEL SHA-256 integrity (CE8D5EDC...).
5. Exhaustive classification of the four Abaqus 2023 continuation mechanisms.
6. Synchronization of Decision Proposal 3 in the supervisor briefing document.
"""

import hashlib
import json
import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

FEASIBILITY_REPORT_PATH = os.path.join(
    REPO_ROOT, "docs", "reports", "MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md"
)
SUPERVISOR_BRIEFING_PATH = os.path.join(
    REPO_ROOT, "docs", "supervisor_reports", "22-10-2026", "SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md"
)
COARSE_DONOR_STATE_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "41_method_c_genuine_continuation",
    "evidence_forward_audit", "coarse_donor_state_u0050.json"
)
RECIPIENT_DECK_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "38_method_b_native_final_14k", "M1_MB_NATIVE_FINAL_1S.inp"
)
PRODUCTION_UEL_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "41_method_c_genuine_continuation", "f42_mixed_uel.for"
)

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
DONOR_STATE_HASH = "3F9198CDE71F44DEFFEBD0E90CB1CD7D21F170FB09AAC472484B69C4E2C965E7"
RECIPIENT_DECK_HASH = "39CFD486C87A48A72F145919998E4FE698367DDA452B0F20C2E8F43EA13B0A6D"


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_f1456_feasibility_report_exists_and_content():
    """Verify that the feasibility report exists, is substantial, and contains all 8 required sections."""
    assert os.path.isfile(FEASIBILITY_REPORT_PATH), f"Missing: {FEASIBILITY_REPORT_PATH}"
    
    with open(FEASIBILITY_REPORT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    assert len(text) > 8000, "Feasibility report is too brief."
    
    # Required Section Headings
    required_sections = [
        "1. Executive Summary & Purpose of Investigation",
        "2. Forensic Audit of Existing Method C Experiments",
        "3. Investigation of Feasible Abaqus 2023 Continuation Mechanisms",
        "4. Minimum Experimental Changes for Nonzero Displacement Initialization",
        "5. Architecture of the Isolated Mode-I C1 Validation Experiment",
        "6. The Six Pre-Declared Acceptance Criteria & Mathematical Definitions",
        "7. Risk Analysis, Governance, and UEL Integrity Guard",
        "8. Implementation Readiness & Step-by-Step Execution Plan"
    ]
    for section in required_sections:
        assert section in text, f"Missing required section in feasibility report: {section}"

    # Verify key technical findings are stated
    assert "Error 144" in text or "TYPE=DISPLACEMENT" in text
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in text
    assert "COMMON /CB_STATE_TRANS/" in text
    assert "21.55" in text  # Forensic step boundary force jump
    assert "0.1347" in text  # Forward L2
    assert "1.6662" in text or "1.67" in text  # Stored energy / compliance disparity


def test_f1456_six_predeclared_acceptance_criteria():
    """Verify that all six quantitative acceptance criteria are explicitly documented with exact bounds."""
    with open(FEASIBILITY_REPORT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    # Criterion 1: Boundary force continuity <= 5.0 N
    assert "5.0 N" in text or "5.0\\,\\text{N}" in text
    assert "|\\Delta RF|" in text or "Delta RF" in text

    # Criterion 2: Transfer-induced energy error <= 5.0%
    assert "\\Delta E_{\\text{transfer}}" in text or "Delta E_trans" in text
    assert "5.0%" in text

    # Criterion 3: Global energy balance <= 10.0%
    assert "10.0%" in text
    assert "energy balance" in text.lower()

    # Criterion 4: Damage irreversibility / no healing
    assert "irreversibility" in text.lower() or "healing" in text.lower()
    assert "-10^{-6}" in text or "-1e-6" in text

    # Criterion 5: Physical fracture response agreement vs fixed reference
    assert "137.9" in text  # K0 reference stiffness
    assert "0.75" in text or "0.743" in text  # Fmax peak reference
    assert "pinning" in text.lower()

    # Criterion 6: Repeatability / determinism
    assert "repeatability" in text.lower() or "determinism" in text.lower()


def test_f1456_donor_and_recipient_mesh_lineage():
    """Verify that donor state JSON and recipient deck exist and have matching frozen hashes."""
    assert os.path.isfile(COARSE_DONOR_STATE_PATH), f"Missing donor state: {COARSE_DONOR_STATE_PATH}"
    actual_donor_hash = compute_sha256(COARSE_DONOR_STATE_PATH)
    assert actual_donor_hash == DONOR_STATE_HASH, f"Donor state hash mismatch: {actual_donor_hash}"

    assert os.path.isfile(RECIPIENT_DECK_PATH), f"Missing recipient deck: {RECIPIENT_DECK_PATH}"
    actual_recipient_hash = compute_sha256(RECIPIENT_DECK_PATH)
    assert actual_recipient_hash == RECIPIENT_DECK_HASH, f"Recipient deck hash mismatch: {actual_recipient_hash}"

    # Load donor state JSON and verify handoff parameters
    with open(COARSE_DONOR_STATE_PATH, "r", encoding="utf-8") as f:
        donor_data = json.load(f)

    assert donor_data["job_name"] == "M1_PRE_1S"
    assert donor_data["num_elements"] == 2906
    assert abs(donor_data["u_rp_mm"] - 0.0050) < 1e-6
    assert abs(donor_data["rf_rp_N"] - 653.088) < 0.01
    assert abs(donor_data["max_d_nodal"] - 0.094910) < 1e-4
    assert donor_data["min_H"] >= 0.0


def test_f1456_frozen_uel_integrity():
    """Verify that production UEL remains byte-identical to frozen canonical hash."""
    assert os.path.isfile(PRODUCTION_UEL_PATH), f"Missing UEL: {PRODUCTION_UEL_PATH}"
    actual_uel_hash = compute_sha256(PRODUCTION_UEL_PATH)
    assert actual_uel_hash == FROZEN_UEL_HASH, (
        f"CRITICAL: Production UEL has been modified! Expected {FROZEN_UEL_HASH}, got {actual_uel_hash}"
    )


def test_f1456_abaqus_continuation_mechanisms_classified():
    """Verify that all four candidate continuation mechanisms are classified in the report."""
    with open(FEASIBILITY_REPORT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    assert "Built-in Abaqus Adaptive Remeshing" in text
    assert "Standard Restart" in text
    assert "Mesh-to-Mesh Solution Mapping" in text
    assert "Custom UEL Continuation" in text

    # Verify disqualification of standard features
    assert "STRICTLY DISQUALIFIED" in text or "Disqualified" in text
    assert "TOPOLOGICALLY DISQUALIFIED" in text or "identical" in text


def test_f1456_supervisor_briefing_updated():
    """Verify that SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md references the feasibility report."""
    assert os.path.isfile(SUPERVISOR_BRIEFING_PATH), f"Missing briefing: {SUPERVISOR_BRIEFING_PATH}"
    with open(SUPERVISOR_BRIEFING_PATH, "r", encoding="utf-8") as f:
        briefing_text = f.read()

    assert "MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md" in briefing_text, (
        "Supervisor briefing does not reference the new feasibility report in Decision Proposal 3."
    )
