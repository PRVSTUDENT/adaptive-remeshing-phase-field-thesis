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


def test_guard7_governance_reconciliation_invariants():
    """Guard 7: Enforce authoritative governance invariants across active documents:
    - Next supervisor meeting: Thursday 08 October 2026, 10:00 CEST.
    - Energy instrumentation status: UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE.
    - Gate 6B remains active pending the 57,929-FE spatial fine candidate.
    - Gate 6C remains on hold until Gate 6B is closed (no auto-promotion).
    - 8-thread shared-memory SMP is qualified; 16-thread execution remains unqualified.
    """
    current_state_path = REPO_ROOT / "project_coordination" / "CURRENT_STATE.md"
    assert current_state_path.exists()
    cs_text = current_state_path.read_text(encoding="utf-8")

    assert "Thursday, 08 October 2026, 10:00 CEST" in cs_text
    assert "UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE" in cs_text
    assert "8THREAD_SHARED_MEMORY_EXECUTION_EMPIRICALLY_QUALIFIED_FOR_THE_TESTED_MODE1_FORMULATION_AND_CONTROLS" in cs_text
    assert "16THREAD_SHARED_MEMORY_EXECUTION_UNQUALIFIED_PENDING_INDEPENDENT_STAGE_A_AND_B_VERIFICATION" in cs_text
    assert "ON_HOLD_PENDING_GATE6B_CLOSURE" in cs_text
    assert "no auto-promotion" in cs_text

    checklist_path = REPO_ROOT / "docs" / "project" / "PROJECT_PHASE_CHECKLIST.md"
    assert checklist_path.exists()
    cl_text = checklist_path.read_text(encoding="utf-8")

    assert "Thursday, 08 October 2026, 10:00" in cl_text
    assert "UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE" in cl_text
    assert "G6B-07" in cl_text
    assert "G6C-01" in cl_text
    assert "must NOT auto-promote" in cl_text

    sup_summary_path = REPO_ROOT / "docs" / "supervisor_reports" / "08-10-2026" / "MODE1_GATE6B_PROVEN_VS_PENDING_SUMMARY.md"
    assert sup_summary_path.exists()
    ss_text = sup_summary_path.read_text(encoding="utf-8")

    assert "Thursday, 08 October 2026, 10:00 CEST" in ss_text
    assert "13. Shared-Memory 8-Thread Parallelism" in ss_text
    assert "16-thread execution remains unqualified" in ss_text
    assert "no auto-promotion" in ss_text

    # Controller script governance check if available
    controller_path = Path(r"C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1")
    if controller_path.exists():
        ctrl_text = controller_path.read_text(encoding="utf-8", errors="ignore")
        assert "01 October 2026" not in ctrl_text
        assert "01-Oct-2026" not in ctrl_text
        assert "UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED" not in ctrl_text
        assert "Thursday, 08 October 2026, 10:00 CEST" in ctrl_text
        assert "UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE" in ctrl_text

def test_guard8_bridge_rules_and_handoff_invariants():
    """Guard 8: Enforce bridge rules, alignment guard, and bridge launcher invariants:
    - bridge_rules.txt must contain 08-Oct meeting date, qualified UEL energy, Gate 6B active,
      Gate 6C hold without auto-promotion, 8T SMP qualified, 16T SMP unqualified, MPI disqualified.
    - Zero superseded strings (01 October 2026, 01-Oct, UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED).
    - project_alignment_guard.txt clean of superseded strings and containing authoritative definitions.
    - Invoke-ChatGPTBridge.ps1 supporting DryRun and prompt reconciliation.
    """
    repo_rules = REPO_ROOT / ".agents" / "scripts" / "bridge_rules.txt"
    assert repo_rules.exists()
    rr_text = repo_rules.read_text(encoding="utf-8")

    assert "01 October 2026" not in rr_text
    assert "01-Oct" not in rr_text
    assert "UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED" not in rr_text
    assert "MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE" not in rr_text
    assert "Thursday, 08 October 2026, 10:00 CEST" in rr_text
    assert "UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE" in rr_text
    assert "GATE_6B_ACTIVE_EVALUATION_AND_CONTINUATION" in rr_text
    assert "ON_HOLD_PENDING_GATE6B_CLOSURE" in rr_text
    assert "8-thread shared-memory SMP execution is empirically qualified" in rr_text
    assert "16-thread shared-memory execution is UNQUALIFIED" in rr_text
    assert "Distributed multi-rank MPI execution is STRICTLY DISQUALIFIED" in rr_text

    repo_guard = REPO_ROOT / ".agents" / "scripts" / "project_alignment_guard.txt"
    assert repo_guard.exists()
    rg_text = repo_guard.read_text(encoding="utf-8")

    assert "01 October 2026" not in rg_text
    assert "01-Oct-2026" not in rg_text
    assert "UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED" not in rg_text
    assert "MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE" not in rg_text
    assert "MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION" in rg_text
    assert "Thursday, 08 October 2026, 10:00 CEST" in rg_text
    assert "UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE" in rg_text

    repo_bridge = REPO_ROOT / ".agents" / "scripts" / "Invoke-ChatGPTBridge.ps1"
    assert repo_bridge.exists()
    rb_text = repo_bridge.read_text(encoding="utf-8")

    assert "DryRun" in rb_text
    assert "project_alignment_guard.txt" in rb_text
    assert "bridge_rules.txt" in rb_text

    rescue_script = REPO_ROOT / "scripts" / "validation" / "rescue_bridge_request.py"
    assert rescue_script.exists()
    rs_text = rescue_script.read_text(encoding="utf-8")
    assert "MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE" not in rs_text
    assert "MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION" in rs_text

    # Also check external OpenClawPAD files if present
    pad_rules = Path(r"C:\Users\pruth\OpenClawPAD\ChatGPTBridge\bridge_rules.txt")
    if pad_rules.exists():
        pr_text = pad_rules.read_text(encoding="utf-8", errors="ignore")
        assert "01 October 2026" not in pr_text
        assert "01-Oct" not in pr_text
        assert "UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED" not in pr_text
        assert "MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE" not in pr_text
        assert "Thursday, 08 October 2026, 10:00 CEST" in pr_text
        assert "UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE" in pr_text

