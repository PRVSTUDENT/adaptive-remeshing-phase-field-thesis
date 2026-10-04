"""
test_stage14uw_energy_claims_discipline.py

Unit and regression test suite for Gate-6B Mode-I Stage 14U-W:
Energy-Claims Discipline, Matched-State Consistency, and Thermodynamic-Interpretation Correction Audit.

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
REPORT_JSON_PATH = STAGE14_DIR / "MODE1_STAGE14UW_ENERGY_CLAIMS_DISCIPLINE_REPORT.json"
REPORT_MD_PATH = STAGE14_DIR / "MODE1_STAGE14UW_ENERGY_CLAIMS_DISCIPLINE_REPORT.md"

EXPECTED_SUBROUTINE_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_VERDICT = "ENERGY_EVOLUTION_AND_BOOKKEEPING_AUDITED__FINAL_BASELINE_QUALIFICATION_PENDING"


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest().upper()


def test_fortran_subroutine_hash_and_energy_mapping():
    """Verify Fortran subroutine SHA-256 and exact energy variable implementations."""
    assert FORTRAN_SUBROUTINE.exists(), f"Subroutine not found at {FORTRAN_SUBROUTINE}"
    actual_hash = sha256_file(FORTRAN_SUBROUTINE)
    assert actual_hash == EXPECTED_SUBROUTINE_HASH, f"Hash mismatch: {actual_hash} != {EXPECTED_SUBROUTINE_HASH}"

    code = FORTRAN_SUBROUTINE.read_text(encoding="utf-8", errors="ignore")
    # Verify ENERGY(2) (strain energy), ENERGY(7) (fracture energy), TOT_E_INT expressions
    assert "ENERGY(2)" in code
    assert "ENERGY(7)" in code
    assert "TOT_E_INT" in code
    assert "SV_E_ELAS" in code
    assert "SV_E_FRAC" in code


def test_report_files_existence_and_meta():
    """Verify JSON and MD report files exist and have compliant metadata."""
    assert REPORT_JSON_PATH.exists(), f"Missing JSON report at {REPORT_JSON_PATH}"
    assert REPORT_MD_PATH.exists(), f"Missing MD report at {REPORT_MD_PATH}"

    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("meta", {})
    assert meta.get("stage") == "14U-W"
    assert meta.get("fortran_subroutine_hash") == EXPECTED_SUBROUTINE_HASH
    assert meta.get("epistemic_verdict") == EXPECTED_VERDICT
    assert "THERMODYNAMICALLY_CONSISTENT_AND_QUALIFIED" in meta.get("withdrawn_verdicts", [])


def test_epistemic_verdict_and_terminology_discipline():
    """Verify forbidden thermodynamic claims are withdrawn and proper terminology used."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data["meta"]
    withdrawn = meta.get("withdrawn_terminology", [])
    assert any("dissipated" in t.lower() for t in withdrawn)

    identities = data.get("mathematical_energy_identities", {})
    e_frac = identities.get("fracture_functional_energy", {})
    assert "Bourdin" in e_frac.get("description", "")
    assert "NOT cumulative thermodynamic dissipation" in e_frac.get("description", "")


def test_distinct_endpoints_and_censoring_discipline():
    """Verify all 9 audited cases record explicit, separate terminal endpoints and reasons."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    cases = data.get("endpoint_and_censoring_discipline", {}).get("cases_audited", [])
    assert len(cases) == 9, f"Expected 9 cases, got {len(cases)}"

    case_map = {c["case_id"]: c for c in cases}
    
    # Check 15k Reference S1
    assert case_map["S1_ref_15k"]["termination_reason"] == "COMPLETE"
    assert math.isclose(case_map["S1_ref_15k"]["actual_terminal_u_mm"], 0.0100, abs_tol=1e-4)

    # Check 32k Fixed S2
    assert case_map["S2_fix_32k"]["termination_reason"] == "CUTBACK_TERMINATED"
    assert math.isclose(case_map["S2_fix_32k"]["actual_terminal_u_mm"], 0.006816, abs_tol=1e-4)

    # Check 42k Fixed S3
    assert case_map["S3_fix_42k"]["termination_reason"] == "CUTBACK_TERMINATED"
    assert math.isclose(case_map["S3_fix_42k"]["actual_terminal_u_mm"], 0.007836, abs_tol=1e-4)

    # Check Stage 14 Adaptive
    assert case_map["Stage14_953"]["termination_reason"] == "FRACTURE_COMPLETE"
    assert math.isclose(case_map["Stage14_953"]["actual_terminal_u_mm"], 0.007889, abs_tol=1e-4)


def test_matched_state_energy_partitioning():
    """Verify matched-state energy values at common displacement levels across cases."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    evals = {e["target_displacement_mm"]: e["cases"] for e in data["matched_state_comparisons"]["evaluations"]}

    # Linear Elastic u = 0.0010 mm
    u_001 = evals[0.0010]
    s1_001 = u_001["S1_ref_15k"]
    stage14_001 = u_001["Stage14_953"]
    assert math.isclose(s1_001["e_elas_mJ"], 0.06894, abs_tol=1e-4)
    assert math.isclose(stage14_001["e_elas_mJ"], 0.06894, abs_tol=1e-4)
    assert s1_001["e_frac_mJ"] < 1e-4
    assert stage14_001["e_frac_mJ"] < 1e-4

    # Peak Vicinity u = 0.0050 mm
    u_005 = evals[0.0050]
    s1_005 = u_005["S1_ref_15k"]
    stage14_005 = u_005["Stage14_953"]
    assert 1.65 <= s1_005["e_elas_mJ"] <= 1.66
    assert 1.65 <= stage14_005["e_elas_mJ"] <= 1.66
    assert 0.036 <= s1_005["e_frac_mJ"] <= 0.038
    assert 0.036 <= stage14_005["e_frac_mJ"] <= 0.038

    # Common Post-Peak Reached State u = 0.0065 mm
    u_0065 = evals[0.0065]
    s1_0065 = u_0065["S1_ref_15k"]
    stage14_0065 = u_0065["Stage14_953"]
    assert math.isclose(s1_0065["e_frac_mJ"], 2.3364, abs_tol=1e-2)
    assert math.isclose(stage14_0065["e_frac_mJ"], 2.2835, abs_tol=1e-2)
    # Stage 14 matches S1 reference within 3%
    diff_pct = abs(stage14_0065["e_frac_mJ"] - s1_0065["e_frac_mJ"]) / s1_0065["e_frac_mJ"] * 100.0
    assert diff_pct < 3.0, f"Stage 14 E_frac differs by {diff_pct:.2f}% from reference at u=0.0065 mm"


def test_bookkeeping_residual_bounded():
    """Verify numerical bookkeeping residual remains bounded (< 5%) for Stage 14 across all matched states."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for evaluation in data["matched_state_comparisons"]["evaluations"]:
        u_tgt = evaluation["target_displacement_mm"]
        st14 = evaluation["cases"]["Stage14_953"]
        if st14.get("status") == "REACHED":
            eps = abs(st14["eps_book_pct"])
            assert eps < 5.0, f"Stage 14 bookkeeping error {eps:.2f}% exceeds 5% bound at u={u_tgt} mm"
