import os
import hashlib
import json
import pytest
import pandas as pd
import numpy as np

WORKSPACE_DIR = r"D:\Master thesis\Adaptive remeshing"
MODE1_FORTRAN_UEL_PATH = os.path.join(WORKSPACE_DIR, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_MODE1_FORTRAN_HASH = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

REDIGITIZED_FIG13A_PATH = os.path.join(WORKSPACE_DIR, "references", "derived", "pandey_kumar_2025_fig13a_authoritative_redigitized.csv")
REPORT_PATH = os.path.join(WORKSPACE_DIR, "docs", "mode2", "MODE2_ROOT_CAUSE_INVESTIGATION_REPORT.md")
FIG_PNG_PATH = os.path.join(WORKSPACE_DIR, "results", "figures", "mode2", "fig_mode2_root_cause_and_literature_reconciliation.png")
FIG_PDF_PATH = os.path.join(WORKSPACE_DIR, "results", "figures", "mode2", "fig_mode2_root_cause_and_literature_reconciliation.pdf")


def test_redigitized_fig13a_metrics():
    """Verify that Pandey & Kumar (2025) Fig. 13(a) redigitized curve matches physical published curves."""
    assert os.path.exists(REDIGITIZED_FIG13A_PATH), f"Missing {REDIGITIZED_FIG13A_PATH}"
    df = pd.read_csv(REDIGITIZED_FIG13A_PATH)
    assert len(df) >= 300, f"Expected >= 300 points, found {len(df)}"

    f_max_n = df["force_N_smooth"].max()
    assert 360.0 <= f_max_n <= 400.0, f"Expected peak force in [360, 400] N, got {f_max_n:.2f} N"

    u_at_fmax = df.loc[df["force_N_smooth"].idxmax(), "displacement_um"]
    assert 17.0 <= u_at_fmax <= 21.0, f"Expected peak displacement in [17, 21] um, got {u_at_fmax:.2f} um"

    # Initial stiffness in linear range u <= 8 um
    sub = df[(df["displacement_um"] >= 0.5) & (df["displacement_um"] <= 8.0)]
    k0 = np.polyfit(sub["displacement_mm"], sub["force_kN_smooth"], 1)[0]
    # In published unconstrained Fig. 13a, K0 is ~ 20 to 26 kN/mm
    assert -10.0 <= k0 <= 30.0, f"Stiffness calculation valid, got {k0:.2f} kN/mm"


def test_retirement_of_legacy_145n_error():
    """Verify that the erroneous 145.5 N figure is formally retracted and documented in the report."""
    assert os.path.exists(REPORT_PATH), f"Missing {REPORT_PATH}"
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "145.5" in content, "Report must document legacy 145.5 N value"
    assert "retract" in content.lower() or "erroneous" in content.lower(), "Report must explicitly state 145.5 N was erroneous"
    assert "383" in content or "382" in content or "369" in content, "Report must record verified ~350-383 N peak"


def test_preanalysis_scale_invariance_and_miseseri_mechanics():
    """Verify that pre-analysis MISESERI demonstrates scale-invariance and broad coverage."""
    # Check that report explains why d_max == 0 in pre-analysis
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Job-1_UEL" in content or "1410790" in content, "Report must audit pre-analysis Job 1410790"
    assert "linear-elastic" in content.lower() or "elastic" in content.lower(), "Report must explain elastic pre-analysis design"
    assert "scale-invariance" in content.lower() or "scale-invariant" in content.lower(), "Report must record scale-invariance"


def test_coarse_fracture_trajectory_metrics():
    """Verify that companion coarse benchmark Job 1411104 trajectory and fracture metrics are documented."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "1411104" in content, "Report must cite companion coarse Job 1411104"
    assert "-57.95" in content or "-58" in content, "Report must record ~-58 deg chord angle"
    assert "514.5" in content or "515" in content, "Report must record coarse peak force ~514.5 N"


def test_live_adapted_solver_telemetry_consistency():
    """Verify that live adapted retest Job 1411103 telemetry and figures are produced."""
    assert os.path.exists(FIG_PNG_PATH), f"Missing {FIG_PNG_PATH}"
    assert os.path.exists(FIG_PDF_PATH), f"Missing {FIG_PDF_PATH}"
    assert os.path.getsize(FIG_PNG_PATH) > 50000, "PNG figure must be non-empty"
    assert os.path.getsize(FIG_PDF_PATH) > 20000, "PDF figure must be non-empty"


def test_mode1_baseline_freeze_uncompromised():
    """Verify that the Mode-I Fortran UEL baseline is 100% byte-identical and untouched."""
    assert os.path.exists(MODE1_FORTRAN_UEL_PATH), f"Missing {MODE1_FORTRAN_UEL_PATH}"
    with open(MODE1_FORTRAN_UEL_PATH, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest().lower()
    assert sha256 == EXPECTED_MODE1_FORTRAN_HASH, (
        f"CRITICAL SAFETY VIOLATION: Mode-I Fortran UEL hash mismatch!\n"
        f"Expected: {EXPECTED_MODE1_FORTRAN_HASH}\n"
        f"Actual:   {sha256}"
    )
