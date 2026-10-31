"""Audit Segment 2 restart readiness and checkpoint ingestion integrity.

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Validates that Segment 2 continuation can initialize deterministically from an
authentic committed checkpoint without changing displacement, damage, driving history,
or convergence criteria, while preserving all 7,265 nodal states and 28,224 GP histories.
"""
from __future__ import print_function, division
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.state_transfer.checkpoint_ingestion import (
    validate_checkpoint_structure,
    generate_restart_assets,
    make_fixture_checkpoint_from_accepted_step1,
    format_solution_cards,
    verify_solution_cards,
    NUM_PHYSICAL_NODES,
    NUM_PHYSICAL_ELEMENTS,
    TOTAL_HISTORY_POINTS,
    HEALING_TOLERANCE,
    ROUNDTRIP_CARD_TOLERANCE_MPA,
)
from scripts.state_transfer.driver_package157_r5_seg2 import (
    START as SEG2_START,
    TARGETS as SEG2_TARGETS,
)
from scripts.state_transfer.driver_package146_147_pdas_continuation import (
    FROZEN_UEL_SHA256,
)

OUT_DIR = ROOT / "results/validation/package157_r5_seg2_preparation"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def main():
    print("=== Starting Segment 2 Restart Readiness Audit ===")

    # 1. Step 1 Authentic Fixture Generation
    ep_path = ROOT / "results/validation/step1_equilibrium_checkpoint_1419113_endpoint.json"
    hist_path = ROOT / "results/validation/step1_equilibrium_checkpoint_1419113_full_history.json"
    fixture_path = OUT_DIR / "test_fixture_checkpoint_step1.json"

    print("Generating authentic test fixture checkpoint from Step 1 data...")
    fixture_checkpoint = make_fixture_checkpoint_from_accepted_step1(ep_path, hist_path, fixture_path)
    assert fixture_path.is_file()
    fixture_sha = sha(fixture_path)
    print("Test fixture checkpoint written: SHA-256 =", fixture_sha)

    # 2. Structural and Schema Validation of Authentic Fixture
    print("Validating test fixture checkpoint structure...")
    parsed = validate_checkpoint_structure(fixture_checkpoint, expected_target_uy=fixture_checkpoint["target_uy_mm"])
    assert len(parsed["u"]) == NUM_PHYSICAL_NODES == 7265
    assert len(parsed["d"]) == NUM_PHYSICAL_NODES == 7265
    assert len(parsed["h"]) == TOTAL_HISTORY_POINTS == 28224
    print("Checkpoint structure valid: 7,265 nodes, 28,224 integration points.")

    # 3. Asset Generation and Card Verification
    fixture_assets_dir = OUT_DIR / "test_fixture_assets"
    print("Generating restart assets into", fixture_assets_dir)
    assets_summary = generate_restart_assets(parsed, fixture_assets_dir)

    for fname in assets_summary["files_generated"]:
        fpath = fixture_assets_dir / fname
        assert fpath.is_file(), "Missing asset file: %s" % fname
        print("Asset generated:", fname, "size:", fpath.stat().st_size, "bytes")

    assert assets_summary["max_card_difference_MPa"] < ROUNDTRIP_CARD_TOLERANCE_MPA
    print("Solution cards verified with max error: %.17g MPa < 1e-12 MPa" % assets_summary["max_card_difference_MPa"])

    # 4. Invariant Tests: Monotonicity and Error Handling
    print("Testing invariant enforcement and negative rejection cases...")
    test_cases_passed = 0

    # Negative Case 1: Schema mismatch
    corrupted = copy.deepcopy(fixture_checkpoint)
    corrupted["schema"] = 2
    try:
        validate_checkpoint_structure(corrupted)
        raise AssertionError("Failed to reject schema != 1")
    except ValueError as e:
        assert "Unsupported checkpoint schema" in str(e)
        test_cases_passed += 1

    # Negative Case 2: Incomplete nodes
    corrupted = copy.deepcopy(fixture_checkpoint)
    corrupted["displacement"] = corrupted["displacement"][:-1]
    try:
        validate_checkpoint_structure(corrupted)
        raise AssertionError("Failed to reject incomplete displacement")
    except ValueError as e:
        assert "Incomplete displacement list" in str(e)
        test_cases_passed += 1

    # Negative Case 3: Incomplete history
    corrupted = copy.deepcopy(fixture_checkpoint)
    corrupted["history"] = corrupted["history"][:-1]
    try:
        validate_checkpoint_structure(corrupted)
        raise AssertionError("Failed to reject incomplete history")
    except ValueError as e:
        assert "Incomplete history list" in str(e)
        test_cases_passed += 1

    # Negative Case 4: Non-finite displacement
    corrupted = copy.deepcopy(fixture_checkpoint)
    corrupted["displacement"][0][1] = float("nan")
    try:
        validate_checkpoint_structure(corrupted)
        raise AssertionError("Failed to reject NaN displacement")
    except ValueError as e:
        assert "Non-finite displacement" in str(e)
        test_cases_passed += 1

    # Negative Case 5: Damage out of bounds (> 1.0)
    corrupted = copy.deepcopy(fixture_checkpoint)
    corrupted["damage"][10][1] = 1.05
    try:
        validate_checkpoint_structure(corrupted)
        raise AssertionError("Failed to reject damage > 1.0")
    except ValueError as e:
        assert "Damage out of physical bounds" in str(e)
        test_cases_passed += 1

    # Negative Case 6: Coupled convergence False
    corrupted = copy.deepcopy(fixture_checkpoint)
    corrupted["coupled_convergence"] = False
    try:
        validate_checkpoint_structure(corrupted)
        raise AssertionError("Failed to reject coupled_convergence=False")
    except ValueError as e:
        assert "coupled_convergence is not True" in str(e)
        test_cases_passed += 1

    # Negative Case 7: Unintended unloading against predecessor
    pred_chk = copy.deepcopy(fixture_checkpoint)
    corrupted = copy.deepcopy(fixture_checkpoint)
    corrupted["target_uy_mm"] = pred_chk["target_uy_mm"] - 1.0e-5
    try:
        validate_checkpoint_structure(corrupted, predecessor_data=pred_chk)
        raise AssertionError("Failed to reject unintended unloading")
    except ValueError as e:
        assert "Unintended unloading" in str(e)
        test_cases_passed += 1

    # Negative Case 8: Healing violation against predecessor
    pred_chk = copy.deepcopy(fixture_checkpoint)
    corrupted = copy.deepcopy(fixture_checkpoint)
    corrupted["target_uy_mm"] = pred_chk["target_uy_mm"] + 1.0e-5
    # Force damage decrease of 0.01 at node 100
    corrupted["damage"][100][1] = max(0.0, pred_chk["damage"][100][1] - 0.01)
    pred_chk["damage"][100][1] = 0.5
    corrupted["damage"][100][1] = 0.48
    try:
        validate_checkpoint_structure(corrupted, predecessor_data=pred_chk)
        raise AssertionError("Failed to reject healing violation")
    except ValueError as e:
        assert "Damage healing violation" in str(e)
        test_cases_passed += 1

    # Negative Case 9: History monotonicity violation against predecessor
    pred_chk = copy.deepcopy(fixture_checkpoint)
    corrupted = copy.deepcopy(fixture_checkpoint)
    corrupted["target_uy_mm"] = pred_chk["target_uy_mm"] + 1.0e-5
    pred_chk["history"][50][2] = 0.05
    corrupted["history"][50][2] = 0.04
    try:
        validate_checkpoint_structure(corrupted, predecessor_data=pred_chk)
        raise AssertionError("Failed to reject history monotonicity violation")
    except ValueError as e:
        assert "History monotonicity violation" in str(e)
        test_cases_passed += 1

    print("All 9 negative invariant rejection cases PASSED!")

    # 5. Segment 2 Continuation Configuration Checks
    print("Verifying Segment 2 continuation configuration...")
    assert abs(SEG2_START - 0.0019003125442191958) < 1.0e-12
    assert len(SEG2_TARGETS) == 5
    assert abs(SEG2_TARGETS[0] - 0.0019103125442191958) < 1.0e-12
    assert abs(SEG2_TARGETS[-1] - 0.0019503125442191958) < 1.0e-12
    print("Segment 2 baseline and targets verified: span = [0.00190031, 0.00195031] mm.")

    # 6. Frozen UEL Verification
    uel_path = ROOT / "models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r5/f42_mixed_uel.for"
    uel_sha = sha(uel_path)
    assert uel_sha == FROZEN_UEL_SHA256
    print("Frozen UEL SHA-256 verified:", uel_sha)

    # 7. Compile Evidence Sources
    evidence_sources = {
        "scripts/state_transfer/checkpoint_ingestion.py": sha(ROOT / "scripts/state_transfer/checkpoint_ingestion.py"),
        "scripts/state_transfer/driver_package157_r5_seg2.py": sha(ROOT / "scripts/state_transfer/driver_package157_r5_seg2.py"),
        "scripts/state_transfer/build_package157_r5_seg2.py": sha(ROOT / "scripts/state_transfer/build_package157_r5_seg2.py"),
        "results/validation/package157_r5_seg2_preparation/test_fixture_checkpoint_step1.json": fixture_sha,
        "results/validation/step1_equilibrium_checkpoint_1419113_endpoint.json": sha(ep_path),
        "results/validation/step1_equilibrium_checkpoint_1419113_full_history.json": sha(hist_path),
        "models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r5/f42_mixed_uel.for": uel_sha,
    }

    report = {
        "schema": 1,
        "status": "SEGMENT2_RESTART_TECHNICALLY_PREPARED",
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "checkpoint_ingestion_summary": {
            "checkpoint_schema": 1,
            "physical_nodes": NUM_PHYSICAL_NODES,
            "physical_elements": NUM_PHYSICAL_ELEMENTS,
            "gauss_points": TOTAL_HISTORY_POINTS,
            "solution_card_format": "7+8+3 canonical cards",
            "solution_card_max_history_error_MPa": assets_summary["max_card_difference_MPa"],
            "damage_bounds": [0.0, 1.0],
            "healing_tolerance": HEALING_TOLERANCE,
            "negative_invariant_test_cases_passed": test_cases_passed,
        },
        "segment_2_continuation_specification": {
            "baseline_uy_mm": SEG2_START,
            "targets_mm": SEG2_TARGETS,
            "substep_count": len(SEG2_TARGETS),
            "increment_span_nm": 50.0,
            "substep_increment_nm": 10.0,
            "max_outer": 100,
            "max_phase": 20,
            "timeout_seconds": 27000,
            "walltime_hours_ceiling": 8.0,
            "estimated_runtime_hours": 4.22,
            "frozen_uel_sha256": FROZEN_UEL_SHA256,
        },
        "state_continuity_contract": {
            "displacement_continuity": "Exact nodal matching with zero unintended unloading",
            "damage_continuity": "Active-set lower bounds strictly enforce non-healing d_next >= d_prev - 1e-6",
            "history_continuity": "Canonical solution card injection guarantees non-decreasing history H_next >= H_prev",
            "coupled_convergence_criteria": "Delta_H <= 1e-6 MPa, Delta_d <= 1e-5, Delta_u <= 1e-9 mm",
            "physical_acceptance_criteria": "Reaction force <= 5%, Raw total energy <= 2% against matching-load reference",
        },
        "live_predecessor_status": {
            "job_id": "1419162.mmaster02",
            "job_name": "M1_C4_P157_C1_2_R5_SEG1",
            "status": "RUNNING",
            "execution_policy": "NO_DEPENDENT_SUBMISSION_WHILE_PREDECESSOR_RUNNING",
        },
        "evidence_sources": evidence_sources,
        "verification_passed": True,
    }

    report_path = OUT_DIR / "segment2_restart_readiness.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Segment 2 restart readiness report written:", report_path)
    print("Report SHA-256:", sha(report_path))
    print("=== Segment 2 Restart Readiness Audit Complete ===")


if __name__ == "__main__":
    main()
