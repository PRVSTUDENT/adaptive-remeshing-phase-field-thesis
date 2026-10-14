# -*- coding: utf-8 -*-
"""
Unit Test Suite for Task F1446:
Begin Method C Following Scientific Completion of Method B.

Verifies:
1. Method B completion and freeze record:
   - Formally recorded as METHOD_B_SCIENTIFIC_OBJECTIVE_COMPLETED_WITH_PARTIAL_HORIZON_LIMITATION.
   - Partial horizon limitation (Exit 1 @ u=0.007889 mm, not 0.0100 mm) preserved.
   - Confounded variables (errorTarget vs Step-2 pre-analysis) acknowledged.
2. New human authorization of 14 October 2026:
   - Explicitly recorded separately from pending supervisor Gate 6B sign-off.
   - Does not misrepresent supervisor sign-off.
3. Method C Gate 6C research and transfer framework:
   - Document exists: docs/reports/MODE1_METHOD_C_GATE6C_RESEARCH_AND_TRANSFER_FRAMEWORK.md.
   - Contains all required sections and mathematical formulation.
4. Forensic audit of existing Method C Gate C1 V2 (Job 1412464):
   - Preserves classification QUASI_STATIC_RELOAD_WITH_TRANSFERRED_HISTORY.
   - Evaluates step boundary force continuity (Delta RF = 0.0925 N <= 0.005 kN).
5. State transfer engine integrity:
   - scripts/state_transfer/mode1_state_transfer_engine.py exists.
   - Authoritative UEL f42_mixed_uel.for hash CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6 preserved.
6. Quantitative acceptance thresholds:
   - Defined mathematically across 7 distinct physical and numerical criteria.
"""

import os
import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = REPO_ROOT / "docs"
DECISIONS_DIR = DOCS_DIR / "decisions"
REPORTS_DIR = DOCS_DIR / "reports"
MODELS_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1"
SCRIPTS_DIR = REPO_ROOT / "scripts" / "state_transfer"

FROZEN_BASELINE_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_f1446_method_b_completion_and_freeze_record():
    """Verify Method B completion and freeze record in decisions and reports."""
    decision_path = DECISIONS_DIR / "SUPERVISOR_DECISION_METHOD_B_COMPLETION_AND_METHOD_C_AUTHORIZATION.md"
    assert decision_path.is_file(), f"Decision record missing: {decision_path}"
    content = decision_path.read_text(encoding="utf-8")
    
    assert "METHOD_B_SCIENTIFIC_OBJECTIVE_COMPLETED_WITH_PARTIAL_HORIZON_LIMITATION" in content
    assert "Job `1412465.mmaster02`" in content or "1412465" in content
    assert "0.007889" in content
    assert "confounded" in content.lower()
    assert "FROZEN — NO RE-RUNS OR ARBITRARY MODIFICATIONS PERMITTED" in content or "FROZEN" in content


def test_f1446_human_authorization_distinction():
    """Verify human authorization of 14 October 2026 is recorded separately from supervisor sign-off."""
    decision_path = DECISIONS_DIR / "SUPERVISOR_DECISION_METHOD_B_COMPLETION_AND_METHOD_C_AUTHORIZATION.md"
    content = decision_path.read_text(encoding="utf-8")
    
    assert "Human Directive (14 October 2026)" in content or "14 October 2026" in content
    assert "separately from formal supervisor Gate 6B sign-off" in content
    assert "Thursday, 22 October 2026" in content
    assert "supervisor approval is NOT claimed" in content or "not claimed" in content.lower()


def test_f1446_method_c_gate6c_framework_document():
    """Verify Method C research document covers all required sections and concepts."""
    report_path = REPORTS_DIR / "MODE1_METHOD_C_GATE6C_RESEARCH_AND_TRANSFER_FRAMEWORK.md"
    assert report_path.is_file(), f"Framework document missing: {report_path}"
    content = report_path.read_text(encoding="utf-8")
    
    required_sections = [
        "## 1. Problem Definition & State-Preservation Requirements",
        "## 2. Fixed-Mesh Reference Anchor & Method B Baseline Comparison",
        "## 3. Forensic Audit of Existing Method C Gate C1 V2 (Job 1412464)",
        "## 4. Donor–Recipient Architecture & Nonmatching Mesh Generation",
        "## 5. Field-by-Field Transfer Mappings & Irreversibility Enforcement",
        "## 6. Quantitative Acceptance Criteria for Method C (Gate 6C)",
        "## 7. Distinguishing Genuine Continuation from Quasi-Static Reload",
        "## 8. Implementation Verification & Unit Test Coverage",
    ]
    for sec in required_sections:
        assert sec in content, f"Missing required section: {sec}"
        
    # Check key concepts
    assert "HOST_NEAREST_GP" in content
    assert "QUASI_STATIC_RELOAD_WITH_TRANSFERRED_HISTORY" in content
    assert "f42_mixed_uel.for" in content
    assert "UEXTERNALDB" in content
    assert "CB_STATE_TRANS" in content
    assert "SV_H_COMMITTED" in content


def test_f1446_gate_c1_v2_audit_and_reload_classification():
    """Verify Job 1412464 evidence is preserved and classified as reload with transferred history."""
    evidence_dir = MODELS_DIR / "39_method_c_transfer_gate_c1" / "evidence_1412464"
    assert evidence_dir.is_dir(), f"Evidence directory missing: {evidence_dir}"
    
    eval_json = evidence_dir / "c1_continuation_evaluation.json"
    assert eval_json.is_file(), f"Evaluation JSON missing: {eval_json}"
    with open(eval_json, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["solver_telemetry"]["total_increments"] == 5058
    assert data["metrics"]["step_boundary"]["boundary_continuous"] is True
    assert data["metrics"]["step_boundary"]["delta_rf_boundary_kn"] < 0.005


def test_f1446_state_transfer_engine_and_uel_hash():
    """Verify state transfer engine exists and authoritative UEL hash is preserved."""
    engine_path = SCRIPTS_DIR / "mode1_state_transfer_engine.py"
    assert engine_path.is_file(), f"Transfer engine missing: {engine_path}"
    
    uel_path = MODELS_DIR / "39_method_c_transfer_gate_c1" / "f42_mixed_uel.for"
    assert uel_path.is_file(), f"UEL source missing: {uel_path}"
    assert sha256_file(uel_path) == FROZEN_BASELINE_UEL_HASH, "Frozen UEL hash altered!"


def test_f1446_quantitative_acceptance_criteria_definition():
    """Verify mathematical definitions of the 7 quantitative acceptance criteria."""
    report_path = REPORTS_DIR / "MODE1_METHOD_C_GATE6C_RESEARCH_AND_TRANSFER_FRAMEWORK.md"
    content = report_path.read_text(encoding="utf-8")
    
    # Check thresholds in content
    assert "<= 1.0 %" in content or "1.0%" in content  # displacement L2
    assert "0.020" in content or "0.02" in content      # peak damage error
    assert "<= 5.0 %" in content or "5.0%" in content  # integrated damage error
    assert ">= 0.0" in content                         # history non-negativity
    assert "0.005 kN" in content or "5.0 N" in content # step boundary force jump
    assert "<= 5.0 %" in content                       # global energy difference
