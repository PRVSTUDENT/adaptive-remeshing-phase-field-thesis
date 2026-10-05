"""
test_mode1_gate6b_closure_matrix_and_consistency_guard.py

Regression and consistency unit tests for Task F1253:
Mode-I Gate-6B Evidence & Claims Consistency Audit and Closure Freeze.

Guards enforced:
1. Guard 1: Stale String & Energy Classification Integrity (no active UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED).
2. Guard 2: 15-Point Gate-6B Closure Decision Matrix Completeness & Classification.
3. Guard 3: Decoupled Multi-Quantity Synthesis Logic (Crack Path vs Global Mechanical / No Forward-Filling).
4. Guard 4: Governed Energy Balance Formulation Contract (E_elas, E_frac, E_model, W_ext, Delta_book, eps_book).
5. Guard 5: Telemetry Displacement Mapping Contract (F1251 Two-Step Loading).
6. Guard 6: Supervisor Report Structure & Frozen 08-Oct-2026 Date.
"""

from __future__ import annotations

import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_guard1_no_stale_energy_qualification_string():
    """Guard 1: Ensure stale string UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED does not exist in CURRENT_STATE.md, START_HERE.md, or active checklist."""
    stale_pattern = "UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED"
    governing_pattern = "UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE"

    core_status_files = [
        REPO_ROOT / "project_coordination" / "CURRENT_STATE.md",
        REPO_ROOT / "project_coordination" / "START_HERE.md",
        REPO_ROOT / "docs" / "project" / "PROJECT_PHASE_CHECKLIST.md",
    ]

    for p in core_status_files:
        assert p.exists(), f"Missing core status file: {p}"
        text = p.read_text(encoding="utf-8", errors="ignore")
        assert stale_pattern not in text, (
            f"Found stale status string '{stale_pattern}' in {p.name}. "
            f"Must be updated to '{governing_pattern}'."
        )

    # In methods docs, ensure governing pattern is present
    methods_audit = REPO_ROOT / "docs" / "methods" / "MODE1_GATE6B_CLOSURE_DECISION_MATRIX_AND_CONSISTENCY_AUDIT.md"
    assert methods_audit.exists()
    assert governing_pattern in methods_audit.read_text(encoding="utf-8")


def test_guard2_15_point_closure_matrix_completeness():
    """Guard 2: Verify all 15 points of the Gate-6B Closure Decision Matrix are defined and correctly classified."""
    audit_file = REPO_ROOT / "docs" / "methods" / "MODE1_GATE6B_CLOSURE_DECISION_MATRIX_AND_CONSISTENCY_AUDIT.md"
    assert audit_file.exists(), f"Missing audit document: {audit_file}"
    content = audit_file.read_text(encoding="utf-8")

    # Check for presence of all 15 matrix items (e.g. '| **1** |' or '| 1 |')
    for item_idx in range(1, 16):
        pattern = rf"\|\s*(?:\*\*)?{item_idx}(?:\*\*)?\s*\|"
        assert re.search(pattern, content), f"Matrix Item {item_idx} missing from closure decision table in {audit_file.name}"

    # Verify specific classifications
    assert "CONVERGED / STABLE" in content
    assert "TEMPORALLY_SENSITIVE_POSTPEAK" in content or "MESH-SENSITIVE" in content
    assert "CONVERGENCE_CONTROL_DIAGNOSTIC_ACTIVE" in content
    assert "PENDING_JOB_1410179" in content

    # Verify key job assignments
    assert "1409982" in content  # Baseline
    assert "1410027" in content  # Refined
    assert "1410180" in content  # Cn=0.50 diagnostic
    assert "1410179" in content  # Spatial 58k
    assert "1410357" in content  # ET2
    assert "1410358" in content  # ET3
    assert "1410359" in content  # ET5


def test_guard3_decoupled_multi_quantity_synthesis_logic():
    """Guard 3: Ensure multi-quantity synthesis decouples spatial crack path from global mechanics and forbids forward-filling."""
    audit_file = REPO_ROOT / "docs" / "methods" / "MODE1_GATE6B_CLOSURE_DECISION_MATRIX_AND_CONSISTENCY_AUDIT.md"
    content = audit_file.read_text(encoding="utf-8")

    assert "Decoupled Convergence Assessment" in content
    assert "Crack-Path vs Mechanical Convergence" in content
    assert "Strict Zero Forward-Filling & Extrapolation Guard" in content
    assert "NOT_REACHED" in content

    # Crack path stability must cite yc centroid deviation <= 0.5 um and w0.5 approx 20.8 um
    assert "0.500" in content
    assert "20.8" in content


def test_guard4_governed_energy_balance_formulation():
    """Guard 4: Verify 6 governed energy fields and non-invasive energy balance contract."""
    audit_file = REPO_ROOT / "docs" / "methods" / "MODE1_GATE6B_CLOSURE_DECISION_MATRIX_AND_CONSISTENCY_AUDIT.md"
    content = audit_file.read_text(encoding="utf-8")

    # Math terms present in document
    assert "\\mathcal{E}_{\\text{elas}}" in content or "E_{\\text{elas}}" in content
    assert "\\mathcal{E}_{\\text{frac}}" in content or "E_{\\text{frac}}" in content
    assert "\\mathcal{E}_{\\text{model}}" in content or "E_{\\text{model}}" in content
    assert "\\mathcal{W}_{\\text{ext}}" in content or "W_{\\text{ext}}" in content
    assert "\\Delta_{\\text{book}}" in content or "\\Delta_{book}" in content
    assert "\\varepsilon_{\\text{book}}" in content or "\\varepsilon_{book}" in content

    # Verify bitwise parity citation
    assert "1409734" in content
    assert "7,000" in content or "7000" in content


def test_guard5_telemetry_displacement_mapping():
    """Guard 5: Verify kinematic displacement contract from Task F1251."""
    audit_file = REPO_ROOT / "docs" / "methods" / "MODE1_GATE6B_CLOSURE_DECISION_MATRIX_AND_CONSISTENCY_AUDIT.md"
    content = audit_file.read_text(encoding="utf-8")

    # Step 1: 0.0050 * t1, Step 2: 0.0050 + 0.0050 * t2
    assert "0.0050" in content
    assert "2.50" in content  # nm/inc
    assert "1.00" in content  # nm/inc


def test_guard6_supervisor_summary_structure_and_date():
    """Guard 6: Verify supervisor summary exists, targets 08-Oct-2026, and contains required sections."""
    sup_file = REPO_ROOT / "docs" / "supervisor_reports" / "08-10-2026" / "MODE1_GATE6B_PROVEN_VS_PENDING_SUMMARY.md"
    assert sup_file.exists(), f"Supervisor summary file missing: {sup_file}"
    content = sup_file.read_text(encoding="utf-8")

    # Verify date
    assert "08 October 2026" in content or "08-Oct-2026" in content
    assert "10:00 CEST" in content

    # Verify key sections
    assert "What Is Already Proven" in content
    assert "What Remains Actively Solving" in content
    assert "Summary Blocker Status" in content
