"""Unit test for Mode-I Task F1597 Turn 214 evidence-only recovery."""

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_recovery_preparation_artifact_integrity():
    prep_path = REPO_ROOT / "results" / "validation" / "preparation-eae8fa6c-4467-4d9a-a08d-ba1dbf88b65d.json"
    assert prep_path.exists(), f"Missing preparation artifact: {prep_path}"

    with open(prep_path, "r", encoding="utf-8") as f:
        prep = json.load(f)

    assert prep.get("schema") == 1
    assert prep.get("status") == "PREPARATION_COMPLETE"
    assert prep.get("task_id") == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert prep.get("run_id") == "eae8fa6c-4467-4d9a-a08d-ba1dbf88b65d"
    assert prep.get("verification_passed") is True
    assert len(prep.get("finding", "")) >= 20

    # Verify all referenced evidence sources exist and their hashes match
    for rel_path, expected_hash in prep.get("evidence_sources", {}).items():
        full_path = REPO_ROOT / rel_path
        assert full_path.exists(), f"Evidence source file missing: {full_path}"
        actual_hash = hashlib.sha256(full_path.read_bytes()).hexdigest().upper()
        assert actual_hash == expected_hash, f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}"


def test_checkpoint_reference_integrity():
    prep_path = REPO_ROOT / "results" / "validation" / "preparation-eae8fa6c-4467-4d9a-a08d-ba1dbf88b65d.json"
    with open(prep_path, "r", encoding="utf-8") as f:
        prep = json.load(f)

    ckpt_info = prep.get("checkpoint_recovery", {})
    assert ckpt_info.get("interrupted_run_id") == "4518c2ef-8f99-4f79-8b4f-c2935b975cbc"
    assert ckpt_info.get("verification_status") == "MATCHED_AND_VERIFIED"
    expected_hash = "2325F72847C9D6650F8E894F7409DD779C61EA2FC040918D98CB46DA261CAA02"
    assert ckpt_info.get("checkpoint_sha256") == expected_hash

    ckpt_path = Path(ckpt_info["checkpoint_path"])
    if ckpt_path.exists():
        actual_hash = hashlib.sha256(ckpt_path.read_bytes()).hexdigest().upper()
        assert actual_hash == expected_hash


def test_package115_convergence_metrics():
    summary_path = (
        REPO_ROOT
        / "models"
        / "pandey_kumar_mode1"
        / "115_c4_inc79_direct_transfer"
        / "c4_inc79_direct_transfer_summary.json"
    )
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["status"] == "CONVERGED_STATIONARY_STATE"
    assert summary["cycles_completed"] == 7
    final_state = summary["final_state"]
    assert final_state["cycle"] == 7
    assert final_state["healing_violations"] == 0
    assert final_state["max_delta_d"] <= 1.0e-3
    assert abs(final_state["rf2_diff_pct"]) <= 1.0  # -0.15% is well within 1%
