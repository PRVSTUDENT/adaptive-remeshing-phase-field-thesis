"""
Unit test suite for Task F1403:
Independent Thesis Build Reconciliation, Page-Count Audit, and Gate M2-4/M2-5 Supervisor-Readiness Verification.
"""

import os
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_MIRROR = REPO_ROOT / "docs" / "MA_AdaptiveRemeshing_Report_2026_main"
ROOT_MIRROR = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026"


def test_f1403_thesis_pdf_build_and_pages():
    """Verify that both thesis mirrors have clean compiled PDFs with exactly 164 pages."""
    pdf_docs = DOCS_MIRROR / "main.pdf"
    pdf_root = ROOT_MIRROR / "main.pdf"
    
    assert pdf_docs.exists(), f"Missing {pdf_docs}"
    assert pdf_root.exists(), f"Missing {pdf_root}"
    
    size_docs = pdf_docs.stat().st_size
    size_root = pdf_root.stat().st_size
    assert size_docs > 30_000_000, f"docs main.pdf too small: {size_docs} bytes"
    assert size_root > 30_000_000, f"root main.pdf too small: {size_root} bytes"
    
    # Check log file for exact page count: 164 pages
    log_docs = DOCS_MIRROR / "main.log"
    assert log_docs.exists()
    log_text = log_docs.read_text(encoding="latin-1")
    match = re.search(r"Output written on main\.pdf \((\d+) pages", log_text)
    assert match is not None, "Page count not found in main.log"
    assert int(match.group(1)) == 164, f"Expected 164 pages, got {match.group(1)}"


def test_f1403_root_mirror_synchronization():
    """Verify that all core thesis files are synchronized between both mirrors."""
    core_files = [
        "main.tex",
        "preambel.tex",
        "newcommands.tex",
        "titlepage.tex",
        "abstract.tex",
        "declaration_ai.tex",
        "chapter01_introduction_theory.tex",
        "chapter02_baseline.tex",
        "chapter03_mesh_refinement.tex",
        "chapter04_current_status.tex",
        "literature.bib",
        "abbrvnat_custom.bst",
    ]
    for fname in core_files:
        f_docs = DOCS_MIRROR / fname
        f_root = ROOT_MIRROR / fname
        assert f_docs.exists(), f"Missing in docs mirror: {fname}"
        assert f_root.exists(), f"Missing in root mirror: {fname}"
        assert f_docs.read_text(encoding="utf-8") == f_root.read_text(encoding="utf-8"), (
            f"Content mismatch between mirrors for {fname}"
        )


def test_f1403_page_count_discrepancy_root_cause():
    """Verify the root cause of the phantom 176 and 182 page count artifacts."""
    toc_file = DOCS_MIRROR / "main.toc"
    aux_file = DOCS_MIRROR / "main.aux"
    assert toc_file.exists()
    assert aux_file.exists()
    
    toc_text = toc_file.read_text(encoding="latin-1")
    aux_text = aux_file.read_text(encoding="latin-1")
    
    # Anchor paragraph*.182 is the hyperref internal unnumbered paragraph counter
    assert "paragraph*.182" in toc_text, "paragraph*.182 anchor missing in main.toc"
    assert "paragraph*.182" in aux_text, "paragraph*.182 anchor missing in main.aux"
    
    # Bookmark IDs 176 and 182 are internal sequential bookmark entries
    assert r"\BKM@entry{id=176" in aux_text, r"BKM@entry{id=176 missing in main.aux"
    assert r"\BKM@entry{id=182" in aux_text, r"BKM@entry{id=182 missing in main.aux"


def test_f1403_zero_undefined_references_and_citations():
    """Verify that the compiled LaTeX log has 0 undefined references and 0 undefined citations."""
    log_docs = DOCS_MIRROR / "main.log"
    log_text = log_docs.read_text(encoding="latin-1")
    
    assert "There were undefined references" not in log_text
    assert "There were undefined citations" not in log_text
    assert "??" not in log_text


def test_f1403_numerical_consistency_fine_reference():
    """Verify numerical consistency of Fine 72k reference values in chapter04."""
    ch4_text = (DOCS_MIRROR / "chapter04_current_status.tex").read_text(encoding="utf-8")
    
    assert "71{,}824" in ch4_text  # FEs
    assert "415.98953" in ch4_text or "415.99" in ch4_text  # F_max
    assert "9.47000" in ch4_text or "9.470" in ch4_text  # u_peak
    assert "45.77" in ch4_text  # K_0
    assert "387.46924" in ch4_text or "387.47" in ch4_text  # RF_final
    assert "4{,}022" in ch4_text  # converged increments


def test_f1403_numerical_consistency_adaptive_et3():
    """Verify numerical consistency of Adaptive ET3 values in chapter04."""
    ch4_text = (DOCS_MIRROR / "chapter04_current_status.tex").read_text(encoding="utf-8")
    
    assert "21{,}063" in ch4_text  # FEs
    assert "-70.67" in ch4_text or "70.67" in ch4_text  # FE reduction
    assert "412.21" in ch4_text  # F_max
    assert "-0.91" in ch4_text or "0.91" in ch4_text  # peak error
    assert "45.57" in ch4_text  # K_0
    assert "-0.43" in ch4_text or "0.43" in ch4_text  # stiffness error
    assert "2.46" in ch4_text  # workflow speedup
    assert "59.31" in ch4_text or "59.3" in ch4_text  # walltime savings
    assert "4.25" in ch4_text  # global NRMSE
    assert "66.45" in ch4_text  # localized phase shift discrepancy


def test_f1403_epistemic_discipline_and_gate_verdict():
    """Verify epistemic standards and Gate M2-4 verdict in chapter04."""
    ch4_text = (DOCS_MIRROR / "chapter04_current_status.tex").read_text(encoding="utf-8")
    
    assert r"QUALIFIED\_WITH\_LIMITATIONS" in ch4_text
    assert "HYPOTHESIS" in ch4_text and "NOT" in ch4_text and "TESTED" in ch4_text
    assert "Method~B" in ch4_text
    assert "Method~C" in ch4_text
    assert "future methodological directions" in ch4_text.lower()
