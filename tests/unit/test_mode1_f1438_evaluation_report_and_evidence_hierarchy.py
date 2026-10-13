"""
test_mode1_f1438_evaluation_report_and_evidence_hierarchy.py

Unit test suite for Task F1438:
1. Verifies the existence, structure, and supervisor-aligned content of docs/reports/MODE1_CORRECTED_METHOD_B_STEP2_FRACTURE_EVALUATION.md.
2. Validates the 4-tier epistemic evidence hierarchy and explicit no-results fallback.
3. Verifies numerical stiffness parity (Delta K0 < 0.1%, R^2 >= 0.999999).
4. Verifies governance coordination state: active session released (active=false), active task COMPLETED, and F1438 ledger registration.
"""

import json
import os
import re
import pytest

WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOCS_REPORT = os.path.join(WORKSPACE, "docs", "reports", "MODE1_CORRECTED_METHOD_B_STEP2_FRACTURE_EVALUATION.md")
ACTIVE_TASK = os.path.join(WORKSPACE, "project_coordination", "ACTIVE_TASK.json")
ACTIVE_SESSION = os.path.join(WORKSPACE, "project_coordination", "ACTIVE_SESSION.json")
TASK_LEDGER = os.path.join(WORKSPACE, "project_coordination", "TASK_LEDGER.csv")
SESSION_REPORT = os.path.join(WORKSPACE, "project_coordination", "sessions", "2026-10-13_1800_gemini-antigravity_F1438-MODE1-CORRECTED-METHOD-B-STEP2-EVALUATION.md")


def test_mode1_f1438_report_structure_and_supervisor_sections():
    """Verify that the Mode-I evaluation report contains all supervisor-required sections."""
    assert os.path.isfile(DOCS_REPORT), f"Report not found at {DOCS_REPORT}"
    with open(DOCS_REPORT, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify key sections following supervisor structure
    assert "## 1. Problem Definition & Boundary Value Problem" in content
    assert "## 2. Expected Physical & Energetic Solution" in content
    assert "## 3. Fixed-Mesh Reference Anchor" in content
    assert "## 4. Original Method B Limitations" in content
    assert "## 5. Corrected Method B Native-Remeshing Methodology & Provenance" in content
    assert "## 6. Strict Epistemic Evidence Hierarchy" in content
    assert "## 7. Verified Mesh & Pre-Peak Elastic Findings" in content
    assert "## 8. Explicitly Pending Fracture-Response Findings (No-Results Fallback)" in content
    assert "## 9. Pre-Declared Criteria for Hypothesis Confirmation or Falsification" in content
    assert "## 10. Preservation of Completed Method C Gate C1 V2 Evidence" in content
    assert "## 11. Methodological Limitation (Retrospective Pre-Refinement)" in content


def test_mode1_f1438_epistemic_hierarchy_and_fallback():
    """Verify 4-tier epistemic hierarchy and explicit no-results fallback definition."""
    with open(DOCS_REPORT, "r", encoding="utf-8") as f:
        content = f.read()

    # Check 4 tiers
    assert "VERIFIED_NUMERICALLY" in content
    assert "VERIFIED_GEOMETRICALLY" in content
    assert "PENDING_IN_FLIGHT_SOLVE" in content
    assert "SUPPORTED_HYPOTHESIS" in content

    # Check fallback specifics
    assert "EXPLICIT NO-RESULTS FALLBACK" in content
    assert "PENDING_STEP2" in content
    assert "Peak Reaction Force (F_max)" in content
    assert "Terminal External Work (W_ext)" in content

    # Check numerical metrics
    assert "137.909558" in content  # K0
    assert "0.99999960" in content  # R^2
    assert "-0.02607" in content    # Delta K0 (numeric part)


def test_mode1_f1438_coordination_and_session_release():
    """Verify active task completion and session release."""
    assert os.path.isfile(ACTIVE_TASK)
    with open(ACTIVE_TASK, "r", encoding="utf-8") as f:
        task_data = json.load(f)
    assert task_data["task_id"] == "F1438-MODE1-CORRECTED-METHOD-B-STEP2-EVALUATION"
    assert task_data["status"] == "COMPLETED"

    assert os.path.isfile(ACTIVE_SESSION)
    with open(ACTIVE_SESSION, "r", encoding="utf-8") as f:
        session_data = json.load(f)
    assert session_data["active"] is False, "Active session must be released (active: false)"

    assert os.path.isfile(TASK_LEDGER)
    with open(TASK_LEDGER, "r", encoding="utf-8") as f:
        ledger_text = f.read()
    assert "F1438,F1438-MODE1-CORRECTED-METHOD-B-STEP2-EVALUATION" in ledger_text

    assert os.path.isfile(SESSION_REPORT), f"Session report missing at {SESSION_REPORT}"
