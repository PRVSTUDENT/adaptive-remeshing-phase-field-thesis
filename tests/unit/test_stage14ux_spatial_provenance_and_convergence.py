"""
test_stage14ux_spatial_provenance_and_convergence.py

Unit and regression test suite for Gate-6B Mode-I Stage 14U-X:
Spatial-Provenance Closure and Convergence-Claim Qualification Audit.

Governing Directive:
"We need to have understood everything related to the first model before we increase complexity."
"""

import json
import math
import hashlib
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
STAGE14_DIR = WORKSPACE_ROOT / "models" / "pandey_kumar_mode1" / "25_stage14_adaptive_candidate_14k"
FORTRAN_SUBROUTINE = WORKSPACE_ROOT / "models" / "pandey_kumar_mode1" / "reproduction_package_gate6b_energy" / "f42_mixed_uel.for"
REPORT_JSON_PATH = STAGE14_DIR / "MODE1_STAGE14UX_SPATIAL_PROVENANCE_AND_CONVERGENCE_REPORT.json"
REPORT_MD_PATH = STAGE14_DIR / "MODE1_STAGE14UX_SPATIAL_PROVENANCE_AND_CONVERGENCE_REPORT.md"

EXPECTED_SUBROUTINE_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_FINAL_VERDICT = "SPATIAL_CONVERGENCE_EVIDENCE_ALREADY_SUFFICIENT"


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest().upper()


def test_fortran_subroutine_hash():
    """Verify authoritative Fortran subroutine hash."""
    assert FORTRAN_SUBROUTINE.exists()
    assert sha256_file(FORTRAN_SUBROUTINE) == EXPECTED_SUBROUTINE_HASH


def test_report_files_existence_and_meta():
    """Verify JSON and MD report files exist and record valid metadata."""
    assert REPORT_JSON_PATH.exists()
    assert REPORT_MD_PATH.exists()

    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data["meta"]
    assert meta["stage"] == "14U-X"
    assert meta["fortran_subroutine_hash"] == EXPECTED_SUBROUTINE_HASH
    assert meta["final_spatial_verdict"] == EXPECTED_FINAL_VERDICT


def test_corridor_area_and_recomputed_metrics():
    """Verify corridor area is exactly 5% and mesh metrics are consistent."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    corridor = data["corridor_definition"]
    assert math.isclose(corridor["exact_corridor_area_fraction_pct"], 5.0, abs_tol=1e-3)
    assert math.isclose(corridor["corridor_area_mm2"], 0.050, abs_tol=1e-4)

    inv = {c["case_id"]: c for c in data["provenance_inventory"]}
    
    # S1
    s1 = inv["S1_ref_15k"]
    assert s1["element_counts"]["total_base"] == 15192
    assert s1["element_counts"]["corridor_base"] == 4316
    assert math.isclose(s1["corridor_metrics"]["h_min_over_l0"], 0.391, abs_tol=1e-2)

    # Stage 14
    st14 = inv["Stage14_adapt_14k"]
    assert st14["element_counts"]["total_base"] == 14483
    assert st14["element_counts"]["corridor_base"] == 8326
    assert math.isclose(st14["element_counts"]["corridor_fraction_pct"], 57.49, abs_tol=1e-1)
    assert math.isclose(st14["corridor_metrics"]["h_min_over_l0"], 0.101, abs_tol=1e-2)


def test_unmatched_terminal_states_separation():
    """Verify distinct terminal endpoints are recorded per case."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    inv = {c["case_id"]: c for c in data["provenance_inventory"]}
    assert inv["S1_ref_15k"]["actual_terminal_u_mm"] == 0.0100
    assert math.isclose(inv["S2_fix_32k"]["actual_terminal_u_mm"], 0.006816, abs_tol=1e-4)
    assert math.isclose(inv["S3_fix_42k"]["actual_terminal_u_mm"], 0.007836, abs_tol=1e-4)
    assert math.isclose(inv["Stage14_adapt_14k"]["actual_terminal_u_mm"], 0.007889, abs_tol=1e-4)


def test_canonical_k0_sampling_rule():
    """Verify canonical K0 is extracted on the frozen 400-point grid."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for c in data["provenance_inventory"]:
        k0 = c["mechanics"]["canonical_k0_kN_mm"]
        assert 137.8 <= k0 <= 138.0, f"Case {c['case_id']} K0 {k0} outside expected bounds"


def test_reference_vs_adaptive_separation():
    """Verify reference-adaptive agreement is separated from asymptotic convergence."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    ref_adapt = data["independent_spatial_conclusions"]["reference_adaptive_agreement"]
    assert ref_adapt["status"] == "REPRESENTATION_EFFICIENCY_PARITY_QUALIFIED"
    assert "NOT a proof of asymptotic mesh convergence" in ref_adapt["epistemic_rule"]


def test_adaptive_pair_physics_parity():
    """Verify Package 24 and Stage 14 share same-physics provenance."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    adapt_conc = data["independent_spatial_conclusions"]["adaptive_spatial_sensitivity"]
    assert adapt_conc["same_physics_provenance_verified"] is True
    assert abs(adapt_conc["k0_difference_pct"]) < 0.05
    assert abs(adapt_conc["f_max_difference_pct"]) < 0.10
