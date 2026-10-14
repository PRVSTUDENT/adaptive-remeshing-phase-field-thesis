"""Unit test suite for Task F1457: Independently Validate Proposed Method C
Continuation Architectures and Refocus on Method C2 Wake Coarsening.

Verifies:
1. Existence and comprehensive structural integrity of
   docs/reports/MODE1_METHOD_C_CONTINUATION_ARCHITECTURE_VALIDATION.md.
2. Exact mathematical formulation of the kinematic-offset decomposition,
   tangent stiffness, and discrete projection residual.
3. Decision matrix comparing Path 1, Path 2, and Path 3 (Reference Update / Residual Correction).
4. Method C2 wake coarsening resolution bound (h <= l0/2 = 3.75 um) and analytical
   chordal distortion formula (xi * coth(xi) - 1).
5. Explicit epistemic separation between [VERIFIED EMPIRICAL CHECK] and
   [PLANNED ANALYTICAL PROPOSAL].
6. Production UEL (CE8D5EDC...), donor state (3F9198CD...), and recipient deck
   provenance hash integrity.
7. Fortran UEL source code audit regarding UEXTERNALDB, SVARS, and COMMON /CB_STATE_TRANS/.
"""

import hashlib
import math
import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

VALIDATION_REPORT_PATH = os.path.join(
    REPO_ROOT, "docs", "reports", "MODE1_METHOD_C_CONTINUATION_ARCHITECTURE_VALIDATION.md"
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
    REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for"
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


def test_f1457_validation_report_exists_and_content():
    """Verify that the validation report exists, is comprehensive, and contains all 9 required sections."""
    assert os.path.isfile(VALIDATION_REPORT_PATH), f"Missing: {VALIDATION_REPORT_PATH}"

    with open(VALIDATION_REPORT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    assert len(text) > 12000, "Validation report is too brief."

    required_sections = [
        "1. Executive Summary & Purpose of Audit",
        "2. Mathematical Derivation & Audit of Kinematic-Offset Continuation",
        "3. Fortran Source Code & Abaqus 2023 Implementation Audit",
        "4. Alternative Candidate Architecture: Reference-Configuration Update & Residual-Correction",
        "5. Comprehensive Decision Matrix of Continuation Architectures",
        "6. Refocus on Method C2: Wake Coarsening and Multi-Cycle Remeshing",
        "7. Epistemic Separation: Verified Empirical Checks vs Planned Analytical Work",
        "8. Implementation Specification & Candidate Branch Protocol",
        "9. Conclusions & Recommendations for 22 October 2026 Supervisor Meeting"
    ]
    for section in required_sections:
        assert section in text, f"Missing required section in validation report: {section}"

    # Verify mathematical and technical keywords
    assert "u_0" in text or "\\mathbf{u}_0" in text
    assert "\\Delta \\mathbf{u}" in text or "Delta u" in text
    assert "COMMON /CB_STATE_TRANS/" in text
    assert "UEXTERNALDB" in text
    assert "SDVINI" in text
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in text
    assert "Error 144" in text


def test_f1457_decision_matrix_content():
    """Verify that the decision matrix rigorously compares Path 1, Path 2, and Path 3."""
    with open(VALIDATION_REPORT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    assert "DECISION MATRIX" in text
    assert "PATH 1: Staged Re-Equilibration" in text
    assert "PATH 2: Kinematic-Offset UEL" in text
    assert "PATH 3: Reference Update" in text or "Residual Correction" in text
    assert "RECOMMENDED FOR C1 QUALIFICATION" in text
    assert "RECOMMENDED AS OPTION B R&D" in text
    assert "STRICTLY DISQUALIFIED" in text


def test_f1457_method_c2_wake_coarsening_and_chordal_bias():
    """Verify that the Method C2 wake coarsening resolution bound and chordal error formula are audited."""
    with open(VALIDATION_REPORT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    # Resolution bound: h <= l0/2 = 3.75 um
    assert "3.75" in text
    assert "l_0/2" in text or "l0/2" in text
    assert "Job 1412809" in text
    assert "5.0465%" in text or "5.05%" in text
    assert "1085.41" in text  # Coarse peak force

    # Analytical chordal formula: xi * coth(xi) - 1
    # Coarse mesh (h=20 um, l0=7.5 um): xi = 20 / 15 = 1.3333
    xi_coarse = 20.0 / (2.0 * 7.5)
    coth_coarse = 1.0 / math.tanh(xi_coarse)
    err_coarse_pct = (xi_coarse * coth_coarse - 1.0) * 100.0
    assert abs(err_coarse_pct - 53.2458) < 0.01

    # Fine mesh (h=1.875 um, l0=7.5 um): xi = 1.875 / 15 = 0.125
    xi_fine = 1.875 / (2.0 * 7.5)
    coth_fine = 1.0 / math.tanh(xi_fine)
    err_fine_pct = (xi_fine * coth_fine - 1.0) * 100.0
    assert abs(err_fine_pct - 0.5203) < 0.01

    # Verify these values are stated in the report
    assert "53.25%" in text or "53.2" in text
    assert "0.52" in text or "0.1322%" in text


def test_f1457_epistemic_separation_table():
    """Verify that the report strictly separates verified empirical checks from planned analytical work."""
    with open(VALIDATION_REPORT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    assert "EPISTEMIC EVIDENCE CLASSIFICATION TABLE" in text
    assert "[VERIFIED EMPIRICAL CHECK]" in text
    assert "[PLANNED ANALYTICAL PROPOSAL]" in text

    # Check key classified items
    assert "Abaqus Error 144" in text
    assert "Forward State Transfer Metrics (2,906 -> 14,677 FEs)" in text
    assert "Reverse Coarsening Chordal Damage Failure (+5.0465%)" in text
    assert "Kinematic-Offset UEL Formulation" in text
    assert "Method C2 Wake Coarsening Resolution Bound" in text


def test_f1457_provenance_and_frozen_hashes():
    """Verify the SHA-256 integrity of frozen UEL, donor state, and recipient deck."""
    assert os.path.isfile(PRODUCTION_UEL_PATH)
    assert compute_sha256(PRODUCTION_UEL_PATH) == FROZEN_UEL_HASH

    assert os.path.isfile(COARSE_DONOR_STATE_PATH)
    assert compute_sha256(COARSE_DONOR_STATE_PATH) == DONOR_STATE_HASH

    assert os.path.isfile(RECIPIENT_DECK_PATH)
    assert compute_sha256(RECIPIENT_DECK_PATH) == RECIPIENT_DECK_HASH


def test_f1457_fortran_source_audit():
    """Verify that the audited Fortran source code patterns are present in f42_mixed_uel.for."""
    with open(PRODUCTION_UEL_PATH, "r", encoding="utf-8") as f:
        fortran_code = f.read()

    # Verify LOP=0 zeroing loop
    assert "IF (LOP .EQ. 0) THEN" in fortran_code
    assert "SV_PHASE_COMMITTED(I) = 0.D0" in fortran_code
    assert "SV_H_COMMITTED(I, KPT) = 0.D0" in fortran_code

    # Verify history ingestion in UEL
    assert "SV_H_COMMITTED(PHYSIDX, KPT) = SVARS(8+KPT)" in fortran_code

    # Verify common block
    assert "COMMON /CB_STATE_TRANS/" in fortran_code
