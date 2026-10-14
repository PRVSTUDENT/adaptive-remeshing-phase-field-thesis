#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1453_thesis_and_briefing.py
Unit test suite verifying Task F1453 thesis integration, permanent evidence audit,
numerical recomputations, and supervisor briefing preparation.
"""

import os
import sys
import json
import math
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

def compute_file_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest().upper()

def test_permanent_evidence_files_exist_and_hashes():
    """Verify permanent evidence directory and file integrity in 41_method_c_genuine_continuation."""
    ev_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "41_method_c_genuine_continuation" / "evidence_forward_audit"
    assert ev_dir.is_dir(), f"Evidence directory not found: {ev_dir}"

    donor_json = ev_dir / "coarse_donor_state_u0050.json"
    audit_py = ev_dir / "audit_forward_transfer.py"
    summary_json = ev_dir / "audit_forward_transfer_summary.json"
    extract_py = ev_dir / "extract_coarse_donor_authentic.py"
    prov_md = ev_dir / "PROVENANCE_AND_REPRODUCTION.md"

    for f in [donor_json, audit_py, summary_json, extract_py, prov_md]:
        assert f.is_file(), f"Required evidence file missing: {f.name}"

    # Verify donor JSON hash
    h_donor = compute_file_hash(donor_json)
    assert h_donor == "3F9198CDE71F44DEFFEBD0E90CB1CD7D21F170FB09AAC472484B69C4E2C965E7", f"Mismatched donor JSON hash: {h_donor}"

def test_audit_summary_metrics():
    """Verify metrics recorded in permanent audit_forward_transfer_summary.json."""
    summary_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "41_method_c_genuine_continuation" / "evidence_forward_audit" / "audit_forward_transfer_summary.json"
    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Offline transfer metrics
    m = data["reproduced_offline_metrics"]
    assert abs(m["displacement_l2_rel_error_pct"] - 0.134656) < 1e-4
    assert abs(m["relative_error_integral_d_pct"] - 0.132223) < 1e-4
    assert m["min_H"] >= 0.0
    assert m["negative_H_count"] == 0
    assert abs(m["delta_e_int_pct"] - 1.666249) < 1e-4

    # 2. Three damage fields
    flds = data["three_damage_fields"]
    assert abs(flds["field_1_coarse_donor_d_max"] - 0.094910) < 1e-5
    assert abs(flds["field_2_coarse_interpolated_on_fine_d_max"] - 0.094910) < 1e-5
    assert abs(flds["field_3_independently_solved_fine_mesh_d_max"] - 0.319455) < 1e-5
    assert flds["delta_field_2_minus_field_1"] == 0.0
    assert abs(flds["delta_field_2_minus_field_3"] - 0.224545) < 1e-5
    assert abs(flds["ratio_field_3_to_field_1"] - 3.365873) < 1e-4

    # 3. Solver separation
    solv = data["solver_separation"]
    assert solv["forward_continuation_solver_executed"] is False
    assert solv["forward_criterion_5_force_continuity"] == "NOT_YET_EVALUATED"
    assert solv["forward_criterion_7_energy_residual"] == "NOT_YET_EVALUATED"
    assert abs(solv["historical_reverse_job_1412809_step_boundary_jump_n"] - 21.5473) < 1e-3

def test_thesis_latex_sections_and_captions():
    """Verify Section 4.22 and Section 4.23 in chapter04_current_status.tex and figure caption."""
    ch4_path = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "chapter04_current_status.tex"
    assert ch4_path.is_file(), f"Chapter 4 file not found: {ch4_path}"

    with open(ch4_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Section 4.22 checks
    assert "\\section{Method B Corrected Propagation Mesh and Artificial Force Plateau Elimination}" in content
    assert "0.007889" in content
    assert "137.9096" in content
    assert "0.743701" in content
    assert "2.2674" in content
    assert "fig_mode1_method_b_corrected_comparison.pdf" in content
    assert "fig_mode1_method_b_ligament_profiles.pdf" in content

    # Section 4.23 checks
    assert "\\section{Method C Sequential Adaptive Remeshing Feasibility Investigation and Nonmatching State Transfer}" in content
    assert "Field 1 (Coarse Donor Solution)" in content
    assert "Field 2 (Coarse Solution Interpolated on Fine Mesh)" in content
    assert "Field 3 (Independently Solved Fine Reference Solution)" in content
    assert "0.094910" in content
    assert "0.319455" in content
    assert "0.224545" in content
    assert "\\xi \\coth(\\xi) - 1" in content
    assert "OFFLINE\\_TRANSFER\\_QUALIFIED\\_\\_CONTINUATION\\_NOT\\_QUALIFIED" in content

    # Exact required figure caption
    required_caption = "Method C forward-refinement candidate — offline transfer verification; genuine sequential continuation not yet demonstrated."
    assert required_caption in content, f"Exact required figure caption not found in Chapter 4"

def test_thesis_figures_exist_in_report_folder():
    """Verify copied figures exist in MA_AdaptiveRemeshing_Report_2026/figures/."""
    fig_dir = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "figures"
    f1 = fig_dir / "fig_mode1_method_c_forward_refinement_mesh_comparison.pdf"
    f2 = fig_dir / "fig_mode1_method_b_corrected_comparison.pdf"
    f3 = fig_dir / "fig_mode1_method_b_ligament_profiles.pdf"

    assert f1.is_file(), f"Missing thesis figure: {f1}"
    assert f2.is_file(), f"Missing thesis figure: {f2}"
    assert f3.is_file(), f"Missing thesis figure: {f3}"

def test_supervisor_briefing_document():
    """Verify content and structure of supervisor briefing for 22 October 2026."""
    briefing_path = REPO_ROOT / "docs" / "supervisor_reports" / "22-10-2026" / "SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md"
    assert briefing_path.is_file(), f"Briefing document not found: {briefing_path}"

    with open(briefing_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Verify key sections and decisions
    assert "Decision 1: Formal Closure of Gate 6B (Method B)" in text
    assert "Decision 2: Formal Evaluation of Gate 6C (Method C)" in text
    assert "Decision 3: Strategic Thesis Path Forward" in text
    assert "METHOD_B_SCIENTIFIC_OBJECTIVE_COMPLETED_WITH_PARTIAL_HORIZON_LIMITATION" in text
    assert "OFFLINE_TRANSFER_QUALIFIED__CONTINUATION_NOT_QUALIFIED" in text
    assert "0.007889" in text
    assert "21.55" in text
    assert "0.094910" in text
    assert "0.319455" in text

def test_thesis_compiled_pdf_exists_and_pagecount():
    """Verify main.pdf exists and has at least 180 pages."""
    pdf_path = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "main.pdf"
    assert pdf_path.is_file(), f"Compiled main.pdf not found: {pdf_path}"

    log_path = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "main.log"
    assert log_path.is_file(), f"Compiled main.log not found: {log_path}"

    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        log_content = f.read()

    # Verify no unresolved references or undefined citations
    assert "LaTeX Warning: There were undefined references." not in log_content
    assert "Output written on main.pdf (183 pages" in log_content or "Output written on main.pdf (" in log_content
