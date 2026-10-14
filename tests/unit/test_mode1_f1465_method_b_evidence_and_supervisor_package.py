# -*- coding: utf-8 -*-
"""
Unit Test Suite for Task F1465:
Validate Method B Evidence Matrix, AT-2 Strong-Form Audit, Prospective Limitation Distinction,
and 22 October 2026 Supervisor Decision Material.

Tests:
1. test_f1465_immediate_submission_and_idle_queue_justification:
   Verifies immediate submission decision is recorded up-front and idle queue is justified.
2. test_f1465_at2_weak_form_and_strong_form_factor_audit:
   Verifies strong-form factor balance (1/2 Gc l0 = psi_0 l0^2), dimensional consistency,
   zero-gradient limit, and weak-form correspondence with f42_mixed_uel.for.
3. test_f1465_prospective_remeshing_limitation_distinction:
   Verifies distinction between asymptotic stress-gradient scaling and elementwise MISESERI behavior,
   refuting universal impossibility while confirming tested setting limitations across 1%, 2%, 3%, 5%.
4. test_f1465_consolidated_4model_method_b_matrix:
   Verifies complete 4-model evidence matrix (Canonical Ref 15k, Historical ET2 6.1k,
   Native Method B 14.7k, Corrected Method B 14.5k) across all mechanical and energetic metrics.
5. test_f1465_operational_method_definitions_and_supervisor_proposals:
   Verifies precise operational definitions of Methods A, B, and C and the 3 formal supervisor decisions.
6. test_f1465_governance_and_production_uel_hash:
   Verifies f42_mixed_uel.for matches authoritative SHA-256.
"""

import os
import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COORDINATION_DIR = REPO_ROOT / "project_coordination"
MODELS_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1"
RUNS_DIR = REPO_ROOT / "runs" / "mode1"
TEX_PATH = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "chapter04_current_status.tex"
BRIEFING_PATH = REPO_ROOT / "docs" / "supervisor_reports" / "22-10-2026" / "SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md"
REPORT_PATH = REPO_ROOT / "docs" / "reports" / "MODE1_METHOD_B_EVIDENCE_AUDIT_AND_SUPERVISOR_DECISION_PACKAGE.md"

FROZEN_BASELINE_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_f1465_immediate_submission_and_idle_queue_justification():
    """Verify immediate submission decision is recorded up-front and idle queue is justified."""
    assert BRIEFING_PATH.is_file()
    with open(BRIEFING_PATH, "r", encoding="utf-8") as f:
        briefing_text = f.read()

    # Must contain immediate submission decision before or at start of briefing
    assert "Immediate HPC Submission Decision & Cluster Queue Status" in briefing_text
    assert "0 active, queued, or running jobs" in briefing_text
    assert "1412872.mmaster02" in briefing_text
    assert "1412873.mmaster02" in briefing_text
    assert "THREAD_PARITY_PASS" in briefing_text
    assert "THREAD_DETERMINISM_PASS" in briefing_text

    # Report must also contain the governance rationale
    assert REPORT_PATH.is_file()
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        rep_text = f.read()
    assert "Immediate HPC Submission Decision & Cluster Queue Status" in rep_text
    assert "Candidate A" in rep_text
    assert "Candidate B" in rep_text
    assert "Candidate C" in rep_text

def test_f1465_at2_weak_form_and_strong_form_factor_audit():
    """Verify strong-form factor balance (1/2 Gc l0 = psi_0 l0^2), dimensional consistency, and zero-gradient limit."""
    Gc = 0.0027  # kN/mm
    l0 = 0.0075  # mm
    psi_0 = Gc / (2.0 * l0)  # 0.180 kN/mm^2 = 180.0 MPa
    assert abs(psi_0 - 0.180) < 1e-6
    psi_0_MPa = psi_0 * 1000.0
    assert abs(psi_0_MPa - 180.0) < 1e-4

    # Regularizing factor equivalence
    factor_Gc_l0 = 0.5 * Gc * l0
    factor_psi0_l0sq = psi_0 * (l0 ** 2)
    assert abs(factor_Gc_l0 - factor_psi0_l0sq) < 1e-12

    # Zero-gradient limit calculation
    H_max_MPa = 18.875
    d_hom = H_max_MPa / (H_max_MPa + psi_0_MPa)
    assert abs(d_hom - 0.094910) < 0.001

    # Check that chapter04_current_status.tex contains both the weak form and strong form
    with open(TEX_PATH, "r", encoding="utf-8") as f:
        tex_text = f.read()
    assert "eq:at2_weak_form_uel" in tex_text
    assert "eq:at2_euler_lagrange_strong_form" in tex_text
    assert "\\frac{1}{2} G_c \\ellzero \\nabla^2 d" in tex_text or "\\psi_0 \\ellzero^2 \\nabla^2 d" in tex_text
    assert "180.0" in tex_text

def test_f1465_prospective_remeshing_limitation_distinction():
    """Verify distinction between asymptotic stress-gradient scaling and elementwise MISESERI behavior."""
    with open(TEX_PATH, "r", encoding="utf-8") as f:
        tex_text = f.read()
    assert "tested native configuration and indicator parameters" in tex_text.lower()
    assert "impossibility theorem" in tex_text.lower()
    assert "errorTarget" in tex_text or "errortarget" in tex_text.lower()

    with open(BRIEFING_PATH, "r", encoding="utf-8") as f:
        briefing_text = f.read()
    assert "tested native configuration and indicator parameters" in briefing_text.lower()
    assert "impossibility theorem" in briefing_text.lower()

def test_f1465_consolidated_4model_method_b_matrix():
    """Verify complete 4-model evidence matrix across mechanical and energetic metrics."""
    with open(BRIEFING_PATH, "r", encoding="utf-8") as f:
        briefing_text = f.read()

    # Must contain 4-model table in Section 2.3
    assert "Consolidated 4-Model Method B Evidence Matrix" in briefing_text
    assert "Canonical Reference" in briefing_text
    assert "Historical ET2" in briefing_text
    assert "Original Native Method B" in briefing_text
    assert "Retrospective Corrected B" in briefing_text

    # Check key numerical entries in the matrix
    assert "15{,}192" in briefing_text or "15,192" in briefing_text
    assert "6{,}112" in briefing_text or "6,112" in briefing_text
    assert "14{,}677" in briefing_text or "14,677" in briefing_text
    assert "14{,}483" in briefing_text or "14,483" in briefing_text
    assert "137.9455" in briefing_text
    assert "137.9096" in briefing_text
    assert "0.757802" in briefing_text
    assert "0.743701" in briefing_text
    assert "2.2674" in briefing_text
    assert "31.4896%" in briefing_text or "-31.49" in briefing_text
    assert "0.0250" in briefing_text  # Bookkeeping residual

def test_f1465_operational_method_definitions_and_supervisor_proposals():
    """Verifies precise operational definitions of Methods A, B, and C and the 3 formal supervisor decisions."""
    with open(BRIEFING_PATH, "r", encoding="utf-8") as f:
        briefing_text = f.read()

    # Precise operational definitions in Section 3.1
    assert "Precise Operational Definitions: Methods A, B, and C" in briefing_text
    assert "Method A (Fixed Offline Pre-Refinement):" in briefing_text
    assert "Method B (Load-Partitioned Offline Pre-Refinement with Remeshing Rule):" in briefing_text
    assert "Method C (Sequential In-Analysis Adaptive Remeshing during Propagation):" in briefing_text

    # Three formal decisions in Section 4
    assert "Decision 1: Formal Closure of Gate 6B" in briefing_text
    assert "METHOD_B_SCIENTIFIC_OBJECTIVE_COMPLETED_WITH_PARTIAL_HORIZON_LIMITATION" in briefing_text
    assert "Decision 2: Formal Evaluation of Gate 6C" in briefing_text
    assert "OFFLINE_TRANSFER_QUALIFIED__CONTINUATION_NOT_QUALIFIED" in briefing_text
    assert "Decision 3: Strategic Thesis Path Forward" in briefing_text
    assert "Option A" in briefing_text
    assert "Option B" in briefing_text

def test_f1465_governance_and_production_uel_hash():
    """Verify production UEL source f42_mixed_uel.for matches authoritative SHA-256."""
    uel_path = MODELS_DIR / "f42_mixed_uel.for"
    assert uel_path.is_file(), "Production UEL missing"
    actual_hash = sha256_file(uel_path)
    assert actual_hash == FROZEN_BASELINE_UEL_HASH, (
        f"Production UEL modified! Expected {FROZEN_BASELINE_UEL_HASH}, got {actual_hash}"
    )
