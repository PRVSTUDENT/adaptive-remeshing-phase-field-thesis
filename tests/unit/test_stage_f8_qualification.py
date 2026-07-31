import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def text(path):
    return (ROOT / path).read_text()


def test_m106_explicit_mixed_schema():
    module = text("scripts/validation/analyze_h2_irreversibility_forensic.py")
    assert '"rp_u1", "rp_rf1"' in module
    assert "float(row[u_col])" in module
    assert "float(v)" not in module


def test_paired_decks_identical_and_sources_distinct():
    b = ROOT / "models/generated/mode_ii/f8_irreversibility_baseline"
    c = ROOT / "models/generated/mode_ii/f8_irreversibility_candidate"
    assert (b / "M2IRR_PATCH.inp").read_bytes() == (c / "M2IRR_PATCH.inp").read_bytes()
    assert hashlib.sha256((b / "M2IRR_PATCH.for").read_bytes()).hexdigest() == (
        "49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37"
    )
    assert (b / "M2IRR_PATCH.for").read_bytes() != (c / "M2IRR_PATCH.for").read_bytes()


def test_candidate_modifies_residual_and_tangent_not_output_only():
    source = text("models/generated/mode_ii/f8_irreversibility_candidate/M2IRR_PATCH.for")
    assert "PENALTY*GAP" in source
    assert "AINTW(INPT)*PENALTY" in source
    assert "IF (GAP.LT.ZERO)" in source
    assert "SDV(1)=MAX" not in source.upper()


def test_load_unload_protocol_and_fixed_point_extractor():
    deck = text("models/generated/mode_ii/f8_irreversibility_baseline/M2IRR_PATCH.inp")
    assert "name=MONOTONIC" in deck
    assert "name=UNLOAD_RELOAD" in deck
    assert "0.003, 1.5, 0.001, 2.0, 0.006" in deck
    extractor = text("scripts/postprocessing/extract_stage_f8_minimal_patch.py")
    assert "integrationPoint" in extractor
    assert "delta_sdv15" in extractor


def test_type_matrix_is_cae_only_and_byte_unicode_controlled():
    source = text("scripts/remeshing/qualify_stage_f8_remeshing_variable_type.py")
    assert '("byte_str", "MISESERI")' in source
    assert "unicode(\"MISESERI\").encode(\"ascii\")" in source
    assert "mdb.Job" not in source
    assert "waitForCompletion" not in source


def test_orchestrator_allowlist_counters_and_two_running_limit():
    source = text("scripts/hpc/stage_f/submit_stage_f8_three_job_batch.sh")
    assert '["M2IRRBAS1","M2IRRCAN1","M2RMTYPE1"]' in source
    assert "attempts=$((attempts+1))" in source
    assert 'depend=afterany:${job_a}' in source
    assert '"qsub_attempts":3' in source


def test_manifests_are_json():
    for rel in (
        "models/generated/mode_ii/f8_irreversibility_baseline/PACKAGE_MANIFEST.json",
        "models/generated/mode_ii/f8_irreversibility_candidate/PACKAGE_MANIFEST.json",
    ):
        json.loads(text(rel))
