"""
Unit tests for Mode-I Active Job 1409912 Source Provenance Integrity Audit.
"""

import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
AUDIT_JSON = REPO_ROOT / "models/pandey_kumar_mode1/MODE1_ACTIVE_1409912_SOURCE_PROVENANCE_AUDIT.json"
AUDIT_MD = REPO_ROOT / "models/pandey_kumar_mode1/MODE1_ACTIVE_1409912_SOURCE_PROVENANCE_AUDIT.md"
P89_FORTRAN = REPO_ROOT / "models/pandey_kumar_mode1/89_mode1_preanalysis_uel_canonical_2906/f42_mixed_uel.for"
P89_MANIFEST = REPO_ROOT / "models/pandey_kumar_mode1/89_mode1_preanalysis_uel_canonical_2906/PACKAGE_MANIFEST.json"
DECK_AUDIT_MD = REPO_ROOT / "models/pandey_kumar_mode1/MODE1_ARCHITECTURE_ISOLATION_DECK_AUDIT.md"
DECK_AUDIT_CSV = REPO_ROOT / "models/pandey_kumar_mode1/MODE1_ARCHITECTURE_ISOLATION_AUDIT_MATRIX.csv"
DECK_AUDIT_JSON = REPO_ROOT / "models/pandey_kumar_mode1/MODE1_ARCHITECTURE_ISOLATION_AUDIT.json"

CORRECT_SHA256 = "91ad75b0ff65dbd25967feae42af531239a99b3f76d9ef49d7359a66403dea6b"
INQUIRY_TYPO_SHA256 = "91ad75b06d48b1968fa3d9daee630248f760ca51d9d701041914ebc2901a1db1"


def test_provenance_artifacts_exist():
    assert AUDIT_JSON.exists(), f"Missing {AUDIT_JSON}"
    assert AUDIT_MD.exists(), f"Missing {AUDIT_MD}"


def test_authoritative_fortran_source_sha256():
    actual_bytes = P89_FORTRAN.read_bytes()
    actual_sha256 = hashlib.sha256(actual_bytes).hexdigest()
    assert actual_sha256 == CORRECT_SHA256
    assert len(actual_bytes) == 32129

    manifest_data = json.loads(P89_MANIFEST.read_text(encoding="utf-8"))
    assert manifest_data["artifacts"]["fortran_subroutine"]["sha256"] == CORRECT_SHA256


def test_provenance_json_verdict_and_categorization():
    data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    assert data["formal_verdict"] == "ACTIVE_1409912_SOURCE_PROVENANCE_VERIFIED"
    assert data["categorization"] == "REPORTING_TYPING_ERROR"
    assert data["consequences"]["new_pbs_job_required"] is False
    assert data["consequences"]["isolation_experiment_status"] == "ARCHITECTURE_ISOLATION_CONTROL_VALID"
    assert data["diff_analysis"]["diff_lines_count"] == 0
    assert data["diff_analysis"]["executable_changes"] is False


def test_inquiry_typo_hash_does_not_exist_in_models():
    """Verify that the typo string 91ad75b06d48 does not exist in any file under models/, excluding the provenance audit files."""
    excluded_names = {
        "MODE1_ACTIVE_1409912_SOURCE_PROVENANCE_AUDIT.json",
        "MODE1_ACTIVE_1409912_SOURCE_PROVENANCE_AUDIT.md"
    }
    for p in (REPO_ROOT / "models/pandey_kumar_mode1").rglob("*"):
        if p.is_file() and p.name not in excluded_names and p.suffix in (".inp", ".for", ".json", ".md", ".csv"):
            text = p.read_text(encoding="utf-8", errors="ignore")
            assert INQUIRY_TYPO_SHA256 not in text, f"Found typo hash in {p}"


def test_architecture_audit_claims_discipline():
    """Verify that 'SPR/ZZ' and 'whole-element centroids' are eliminated from architecture audit files."""
    for audit_file in [DECK_AUDIT_MD, DECK_AUDIT_CSV, DECK_AUDIT_JSON]:
        text = audit_file.read_text(encoding="utf-8")
        assert "SPR/ZZ" not in text, f"'SPR/ZZ' still present in {audit_file.name}"
        assert "whole-element centroids" not in text, f"'whole-element centroids' still present in {audit_file.name}"
