"""Source-backed regression and fail-closed checks for the F1639 correction."""
import copy
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "f1631_reference", ROOT / "scripts/validation/reconstruct_f1631_early_divergence_forensics.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def sources():
    base = ROOT / MODULE.DONOR_EVIDENCE_DIR
    return tuple(json.loads((base / name).read_text(encoding="utf-8-sig")) for name in (
        "c5_forward_continuation_c2_2_summary.json", "converged_checkpoint_03.json", "live_iteration_telemetry.json"))


@pytest.mark.parametrize("field,component", [
    ("elastic_energy_kNmm", "elastic"), ("fracture_energy_kNmm", "fracture"),
    ("total_energy_kNmm", "total")])
def test_component_against_independent_frozen_uel_quadrature(field, component):
    reference = MODULE.load_donor_reference(ROOT)
    reconstruction = json.loads((ROOT / MODULE.DONOR_RECONCILIATION).read_text(encoding="utf-8-sig"))
    independently_integrated = next(row["independent_quadrature"] for row in reconstruction["comparison"] if row["component"] == component)
    assert reference[field] == pytest.approx(independently_integrated, rel=1e-7, abs=0)


def test_cancelling_component_errors_fail_even_when_total_is_unchanged():
    summary, checkpoint, telemetry = sources()
    summary["elastic_energy_kNmm"] += 3.263203e-5
    summary["fracture_energy_kNmm"] -= 3.263203e-5
    with pytest.raises(ValueError, match="component"):
        MODULE.validate_donor_energy_sources(summary, checkpoint, telemetry)


@pytest.mark.parametrize("failure", ["missing", "nonfinite", "wrong_outer", "not_accepted", "empty_telemetry"])
def test_missing_inconsistent_or_unaccepted_sources_fail(failure):
    summary, checkpoint, telemetry = sources()
    if failure == "missing": del summary["fracture_energy_kNmm"]
    if failure == "nonfinite": summary["elastic_energy_kNmm"] = float("nan")
    if failure == "wrong_outer": checkpoint["outer_iteration"] += 1
    if failure == "not_accepted": summary["physical_acceptance"] = "FAIL"
    if failure == "empty_telemetry": telemetry = []
    with pytest.raises((ValueError, KeyError)):
        MODULE.validate_donor_energy_sources(summary, checkpoint, telemetry)


@pytest.mark.parametrize("target", ["receipt", "source", "absent"])
def test_hash_or_missing_file_failure_preserves_source_integrity(tmp_path, target):
    receipt = tmp_path / MODULE.DONOR_RECONCILIATION
    receipt.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / MODULE.DONOR_RECONCILIATION, receipt)
    if target == "receipt":
        receipt.write_text("{}", encoding="utf-8")
    elif target == "source":
        path = tmp_path / MODULE.DONOR_EVIDENCE_DIR / "c5_forward_continuation_c2_2_summary.json"
        path.parent.mkdir(parents=True)
        path.write_text("{}", encoding="utf-8")
    with pytest.raises((ValueError, FileNotFoundError)):
        MODULE.load_donor_reference(tmp_path)


def test_existing_forensic_output_cannot_be_overwritten(tmp_path):
    target = tmp_path / "historical.json"
    target.write_text('{"original":true}', encoding="utf-8")
    with pytest.raises(FileExistsError):
        MODULE.run_forensics(tmp_path, tmp_path, target)
    assert target.read_text() == '{"original":true}'
