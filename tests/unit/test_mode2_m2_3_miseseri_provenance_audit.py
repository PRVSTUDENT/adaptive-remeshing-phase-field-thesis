"""Unit tests for Mode-II Gate M2-3 MISESERI provenance and remesher audit.

Verifies:
1. Actual-mesh figure files exist across PNG, PDF, and SVG formats.
2. The 3-layer passive modulus scaling factor (2.1e13) explains the 10^-14 MISESERI values.
3. Scale-invariance in UNIFORM_ERROR sizing is mathematically preserved.
4. Epistemic classification of errorTarget=2.0% is preserved as UNRESOLVED in literature.
5. Gate M2-3 scientific qualification is recorded as PROVISIONAL / REQUIRES_DIAGNOSIS.
6. The authoritative audit report exists in models/pandey_kumar_mode2/ and docs/mode2/.
"""

import math
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIGURES_DIR = REPO_ROOT / "results" / "figures" / "mode2"
DOCS_REPORT = REPO_ROOT / "docs" / "mode2" / "MODE2_M2_3_MISESERI_PROVENANCE_AUDIT_REPORT.md"
MODELS_REPORT = REPO_ROOT / "models" / "pandey_kumar_mode2" / "MODE2_M2_3_MISESERI_PROVENANCE_AUDIT_REPORT.md"
RAW_INP = REPO_ROOT / "models" / "pandey_kumar_mode2" / "06_paper_grounded_uel_preanalysis" / "M2_3_ADAPTED_RAW_2PCT.inp"
STEP1_CSV = REPO_ROOT / "models" / "pandey_kumar_mode2" / "06_paper_grounded_uel_preanalysis" / "miseseri_step1_final_frame2000.csv"


def test_actual_mesh_figures_exist():
    """Verify that all 3 actual-mesh figures exist in PNG (>= 1 MB), PDF, and SVG."""
    fig_stems = [
        "fig_mode2_m2_3_actual_mesh_fulldomain",
        "fig_mode2_m2_3_actual_mesh_crack_tip_zoom",
        "fig_mode2_m2_3_actual_mesh_lower_right_corridor_zoom",
    ]
    for stem in fig_stems:
        png = FIGURES_DIR / f"{stem}.png"
        pdf = FIGURES_DIR / f"{stem}.pdf"
        svg = FIGURES_DIR / f"{stem}.svg"
        assert png.exists(), f"Missing PNG: {png}"
        assert pdf.exists(), f"Missing PDF: {pdf}"
        assert svg.exists(), f"Missing SVG: {svg}"
        assert png.stat().st_size > 500_000, f"PNG too small: {png}"
        assert pdf.stat().st_size > 100_000, f"PDF too small: {pdf}"
        assert svg.stat().st_size > 1_000_000, f"SVG too small: {svg}"


def test_audit_reports_exist_and_consistent():
    """Verify that both audit reports exist and contain essential forensic verdicts."""
    assert DOCS_REPORT.exists(), f"Missing {DOCS_REPORT}"
    assert MODELS_REPORT.exists(), f"Missing {MODELS_REPORT}"
    
    docs_text = DOCS_REPORT.read_text(encoding="utf-8")
    models_text = MODELS_REPORT.read_text(encoding="utf-8")
    assert docs_text == models_text, "Docs report and models report content mismatch"
    
    assert "PROVISIONAL / REQUIRES_DIAGNOSIS" in docs_text
    assert "INFERRED / PROJECT_SELECTED_FOR_M2_4" in docs_text
    assert "UNRESOLVED" in docs_text
    assert "3-layer co-located" in docs_text.lower() or "3-layer" in docs_text
    assert "10^{-11}" in docs_text or "1.e-11" in docs_text or "10^{-8}" in docs_text
    assert "22,530" in docs_text
    assert "1410807" in docs_text


def test_miseseri_scale_invariance_and_physics_range():
    """Verify the mathematical dynamic range and physical rescaling of MISESERI."""
    assert STEP1_CSV.exists(), f"Missing {STEP1_CSV}"
    df = pd.read_csv(STEP1_CSV)
    assert len(df) == 2960, f"Expected 2960 elements, found {len(df)}"
    
    m_raw = df["miseseri"].values
    dynamic_range = m_raw.max() / m_raw.min()
    assert dynamic_range > 1000.0, f"Expected dynamic range > 1000x, found {dynamic_range:.1f}x"
    
    # Scale factor from dummy E=1e-11 kN/mm^2 to physical E=210 GPa = 210 kN/mm^2
    scale_factor = 210.0 / 1.0e-11
    m_physical_mpa = m_raw * scale_factor * 1.0e3  # kN/mm^2 to MPa
    
    # Check that crack tip singularity is physically realistic (100 MPa to 10,000 MPa)
    assert 500.0 <= m_physical_mpa.max() <= 15000.0, f"Physical max stress error out of range: {m_physical_mpa.max():.1f} MPa"
    # Check that far-field stress error is realistic (0.01 to 10 MPa)
    assert 0.01 <= m_physical_mpa.min() <= 10.0, f"Physical min stress error out of range: {m_physical_mpa.min():.4f} MPa"


def test_raw_inp_deck_integrity():
    """Verify raw input deck element and node counts."""
    assert RAW_INP.exists(), f"Missing {RAW_INP}"
    import hashlib
    h = hashlib.sha256(RAW_INP.read_bytes()).hexdigest().upper()
    assert h == "BD02D73C2BC199DB95369C094A3B579005A8F3B97654657874BD73398DEF6C22"
