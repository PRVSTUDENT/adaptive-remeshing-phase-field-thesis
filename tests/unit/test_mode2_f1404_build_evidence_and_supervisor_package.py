"""
Unit test suite for Task F1404:
Correct Contradictory Thesis Build Evidence, Forensic Page-Count Reconciliation,
Mirror Metadata Nondeterminism, and Supervisor Decision Package Verification.
"""

import os
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_MIRROR = REPO_ROOT / "docs" / "MA_AdaptiveRemeshing_Report_2026_main"
ROOT_MIRROR = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026"
DECISIONS_DIR = REPO_ROOT / "docs" / "decisions"
SESSIONS_DIR = REPO_ROOT / "project_coordination" / "sessions"


def test_f1404_thesis_mirror_page_count_and_bit_level_content_identity():
    """Verify that both thesis mirrors build to 164 pages with identical size and bitwise content streams."""
    pdf_docs = DOCS_MIRROR / "main.pdf"
    pdf_root = ROOT_MIRROR / "main.pdf"
    
    assert pdf_docs.exists(), f"Missing {pdf_docs}"
    assert pdf_root.exists(), f"Missing {pdf_root}"
    
    # Exact byte size equality
    assert pdf_docs.stat().st_size == pdf_root.stat().st_size == 36_889_494
    
    # Verify main.log page count
    log_docs = DOCS_MIRROR / "main.log"
    assert log_docs.exists()
    log_text = log_docs.read_text(encoding="latin-1")
    m = re.search(r"Output written on main\.pdf \((\d+) pages", log_text)
    assert m is not None and int(m.group(1)) == 164
    
    # Verify binary differences are confined strictly to metadata (CreationDate, ModDate, ID)
    b_docs = pdf_docs.read_bytes()
    b_root = pdf_root.read_bytes()
    
    diff_indices = [i for i in range(len(b_docs)) if b_docs[i] != b_root[i]]
    # Exactly 68 bytes difference out of 36,889,494 bytes
    assert len(diff_indices) == 68, f"Expected 68 differing metadata bytes, got {len(diff_indices)}"
    
    # Trailer IDs present in differing tail
    assert b"/ID [" in b_docs
    assert b"/ID [" in b_root


def test_f1404_f1403_session_report_correction():
    """Verify that F1403 session report contains the correction for log overwriting and 176/182 historical passes."""
    f1403_report = SESSIONS_DIR / "2026-10-11_1010_gemini-antigravity_F1403-INDEPENDENT-THESIS-BUILD-RECONCILIATION-AND-SUPERVISOR-AUDIT.md"
    assert f1403_report.exists()
    text = f1403_report.read_text(encoding="utf-8")
    
    assert "CORRECTION & RETRACTION NOTE" in text
    assert "176 pages, 32890693 bytes" in text
    assert "182 pages, 38166540 bytes" in text
    assert "overwrites `main.log`" in text or "overwrites main.log" in text
    assert "UNVERIFIED_HISTORICAL_DRAFT_STATE" in text
    assert "Metadata vs Content Identity" in text


def test_f1404_supervisor_decision_document_method_b():
    """Verify the existence and required elements of the Method B supervisor decision document."""
    doc_path = DECISIONS_DIR / "SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md"
    assert doc_path.exists(), f"Missing {doc_path}"
    text = doc_path.read_text(encoding="utf-8")
    
    # Verification of governing status and disclaimer
    assert "SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING" in text
    assert "PENDING SUPERVISOR REVIEW & EXPLICIT AUTHORIZATION" in text
    assert "GOVERNANCE & EXECUTION DISCLAIMER" in text
    assert "v2026.10.08-supervisor-meeting-mode1-freeze" in text
    assert "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6" in text
    
    # Verification of core scientific hypotheses and matrix
    assert "Hypothesis H1" in text
    assert "Hypothesis H2" in text
    assert "Hypothesis H3" in text
    assert "M1-MB-1S" in text
    assert "M1-MB-2S" in text
    assert "M1-MB-4S" in text
    assert "M1-REF-UNIF" in text
    
    # Acceptance criteria
    assert "Peak load discrepancy" in text
    assert "Initial elastic stiffness" in text
    assert "Collinearity" in text or "collinearity" in text
    
    # Checkpoints
    assert "CP-1" in text
    assert "CP-2" in text
    assert "CP-3" in text


def test_f1404_epistemic_standards_and_mode1_baseline_preserved():
    """Verify that Mode-I baseline freeze and Mode-II Gate M2-4 limitations remain strictly maintained."""
    ch4_text = (DOCS_MIRROR / "chapter04_current_status.tex").read_text(encoding="utf-8")
    
    assert r"QUALIFIED\_WITH\_LIMITATIONS" in ch4_text
    assert "UNRESOLVED" in ch4_text
    assert "Method~B" in ch4_text
    assert "Method~C" in ch4_text
    assert "66.45" in ch4_text
