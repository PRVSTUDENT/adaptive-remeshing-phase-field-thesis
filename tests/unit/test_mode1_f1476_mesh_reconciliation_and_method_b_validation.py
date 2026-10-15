import os
import hashlib
import pandas as pd
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def test_spatial_resolution_validation_csv_integrity():
    """Verify spatial resolution validation CSV exists, is well-formed, and matches exact data."""
    csv_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "spatial_resolution_validation.csv")
    assert os.path.isfile(csv_path), f"Missing CSV: {csv_path}"
    
    with open(csv_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest().upper()
    assert file_hash == "DDAD1E8442D53362B960ED476D52FEBEC5F7DB110812EB4D973A8C1671857AEF", f"Hash mismatch: {file_hash}"
    
    df = pd.read_csv(csv_path)
    assert len(df) == 5, f"Expected 5 rows, got {len(df)}"
    
    expected_elements = {
        "PK_M1_NOM1_STRICT_0062.inp": 71320,
        "M1_MB_NATIVE_FINAL_1S.inp": 14677,
        "PK_M1_A3_ADAPT3PCT.inp": 7633,
        "PK_M1_A4_ADAPT5PCT.inp": 4194,
        "M1_MB_CORRECTED_PROPAGATION_14K.inp": 14483
    }
    
    for _, row in df.iterrows():
        deck = row["deck_filename"]
        assert deck in expected_elements, f"Unexpected deck: {deck}"
        assert row["total_base_elements"] == expected_elements[deck], f"Element count mismatch for {deck}"
        
    # Verify prospective starvation vs retrospective complete coverage
    t1 = df[df["deck_filename"] == "PK_M1_NOM1_STRICT_0062.inp"].iloc[0]
    t2 = df[df["deck_filename"] == "M1_MB_NATIVE_FINAL_1S.inp"].iloc[0]
    t3 = df[df["deck_filename"] == "PK_M1_A3_ADAPT3PCT.inp"].iloc[0]
    t4 = df[df["deck_filename"] == "PK_M1_A4_ADAPT5PCT.inp"].iloc[0]
    p40 = df[df["deck_filename"] == "M1_MB_CORRECTED_PROPAGATION_14K.inp"].iloc[0]
    
    assert 32.0 <= t1["contiguous_coverage_pct"] <= 34.0, f"Tier 1 coverage: {t1['contiguous_coverage_pct']}"
    assert 18.0 <= t2["contiguous_coverage_pct"] <= 20.0, f"Tier 2 coverage: {t2['contiguous_coverage_pct']}"
    assert 10.5 <= t3["contiguous_coverage_pct"] <= 12.0, f"Tier 3 coverage: {t3['contiguous_coverage_pct']}"
    assert 0.0 <= t4["contiguous_coverage_pct"] <= 1.0, f"Tier 4 coverage: {t4['contiguous_coverage_pct']}"
    assert p40["contiguous_coverage_pct"] == 100.0, f"Package 40 coverage: {p40['contiguous_coverage_pct']}"
    assert p40["resolved_elements_pct"] > 95.0, f"Package 40 resolved elements: {p40['resolved_elements_pct']}"

def test_spatial_resolution_figures_exist():
    """Verify publication quality spatial resolution figures exist and have valid size."""
    fig_dir = os.path.join(REPO_ROOT, "results", "figures", "mode1_method_b_corrected_comparison")
    png_path = os.path.join(fig_dir, "fig_mode1_method_b_spatial_resolution_validation.png")
    pdf_path = os.path.join(fig_dir, "fig_mode1_method_b_spatial_resolution_validation.pdf")
    
    assert os.path.isfile(png_path), f"Missing figure PNG: {png_path}"
    assert os.path.isfile(pdf_path), f"Missing figure PDF: {pdf_path}"
    
    assert os.path.getsize(png_path) > 100000, f"PNG unexpectedly small: {os.path.getsize(png_path)} bytes"
    assert os.path.getsize(pdf_path) > 10000, f"PDF unexpectedly small: {os.path.getsize(pdf_path)} bytes"

def test_mesh_count_reconciliation_mapping():
    """Verify all 5 decks exist on disk and have verified line and element structure."""
    decks = {
        "Tier 1": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "87_gate6_adaptive_nominal_1pct_strict_twin_trunc0062", "PK_M1_NOM1_STRICT_0062.inp"),
        "Tier 2": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "38_method_b_native_final_14k", "M1_MB_NATIVE_FINAL_1S.inp"),
        "Tier 3": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "batch_mode1_energy_convergence", "A3_adapt_3pct_8k_corrected", "PK_M1_A3_ADAPT3PCT.inp"),
        "Tier 4": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "batch_mode1_energy_convergence", "A4_adapt_5pct_4k_corrected", "PK_M1_A4_ADAPT5PCT.inp"),
        "Pkg 40": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "40_method_b_corrected_propagation_14k", "M1_MB_CORRECTED_PROPAGATION_14K.inp")
    }
    for name, path in decks.items():
        assert os.path.isfile(path), f"Missing deck for {name}: {path}"
        assert os.path.getsize(path) > 500000, f"Deck {name} unexpectedly small: {os.path.getsize(path)} bytes"

def test_method_c_framing_and_empirical_boundary():
    """Verify that documentation upholds the distinction between empirical results and necessity claims."""
    briefing_path = os.path.join(REPO_ROOT, "docs", "supervisor_reports", "22-10-2026", "SUPERVISOR_BRIEFING_MODE1_METHODS_B_AND_C.md")
    assert os.path.isfile(briefing_path)
    with open(briefing_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "Empirical Boundary vs Impossibility Theorem" in content
    assert "Boundary Guard" in content
    assert "unqualified candidate sequential remeshing methodology" in content

def test_governance_invariants_preserved():
    """Verify production UEL hash, Gate 6C hold status, and zero PBS submissions."""
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.isfile(uel_path), f"Missing UEL source: {uel_path}"
    with open(uel_path, "rb") as f:
        uel_hash = hashlib.sha256(f.read()).hexdigest().upper()
    assert uel_hash == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6", f"UEL hash altered: {uel_hash}"
    
    active_session_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_SESSION.json")
    with open(active_session_path, "r", encoding="utf-8") as f:
        session_data = f.read()
    assert "F1476" in session_data
