# -*- coding: utf-8 -*-
"""
test_package167_r3_predecessor_compatibility.py
Unit tests for Package 167 Predecessor Compatibility with Package 163-R3 and Package 157-R8.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.verify_package167_r3_predecessor_compatibility import (
    verify_package167_r3_predecessor_compatibility,
    OUTPUT_JSON
)
from scripts.state_transfer.stage_c2_2_specification import (
    ACTIVE_PREDECESSOR_JOB_ID,
    DISQUALIFIED_PREDECESSOR_JOB_IDS,
    ACTIVE_REFERENCE_JOB_ID,
    FROZEN_UEL_SHA256,
    BASELINE_UY_MM, TARGET_UY_MM, INCREMENT_UY_MM
)


def test_package167_r3_compatibility_full_pass():
    report = verify_package167_r3_predecessor_compatibility()
    assert report["decision"] == "PACKAGE167_R3_PREDECESSOR_COMPATIBILITY_PASS"
    assert report["all_criteria_passed"] is True
    assert OUTPUT_JSON.exists()


def test_criterion_1_r2_artifact_rejection():
    report = verify_package167_r3_predecessor_compatibility()
    c1 = report["criteria"]["criterion_1_r2_rejection"]
    assert c1["passed"] is True
    assert "1419489.mmaster02" in c1["disqualified_job_ids"]


def test_criterion_2_r3_exclusive_resolution():
    report = verify_package167_r3_predecessor_compatibility()
    c2 = report["criteria"]["criterion_2_r3_resolution"]
    assert c2["passed"] is True
    assert c2["active_predecessor_job_id"] == "1419499.mmaster02"
    assert c2["unaccepted_r3_checkpoint_blocks_submission"] is True


def test_criterion_3_discretization_invariants():
    report = verify_package167_r3_predecessor_compatibility()
    c3 = report["criteria"]["criterion_3_discretization_invariants"]
    assert c3["passed"] is True
    assert c3["elements"] == 12996
    assert c3["nodes"] == 13278
    assert c3["gauss_points"] == 51984
    assert c3["history_svars"] == 207936


def test_criterion_4_step_schedule_invariants():
    report = verify_package167_r3_predecessor_compatibility()
    c4 = report["criteria"]["criterion_4_step_scope_invariants"]
    assert c4["passed"] is True
    assert c4["initial_uy_mm"] == pytest.approx(0.0018653125442191958, abs=1e-12)
    assert c4["increment_uy_mm"] == pytest.approx(0.000005, abs=1e-12)
    assert c4["target_uy_mm"] == pytest.approx(0.0018703125442191958, abs=1e-12)


def test_criterion_5_reference_benchmark_lineage():
    report = verify_package167_r3_predecessor_compatibility()
    c5 = report["criteria"]["criterion_5_reference_benchmark_lineage"]
    assert c5["passed"] is True
    assert c5["reference_benchmark_job_id"] == "1419490.mmaster02"
    assert c5["target_displacement_uy_mm"] == pytest.approx(0.0018703125442191958, abs=1e-12)


def test_criterion_6_fail_closed_guard():
    report = verify_package167_r3_predecessor_compatibility()
    c6 = report["criteria"]["criterion_6_fail_closed_guard"]
    assert c6["passed"] is True
    assert c6["live_eligibility_status"] == "NO_SUBMISSION_FALLBACK"
    assert c6["live_builder_status"] == "NO_SUBMISSION_FALLBACK"
    assert c6["live_gates_status"] == "SUBMISSION_BLOCKED_BY_PREDECESSOR_DEPENDENCY"
    assert "GATE_1_PREDECESSOR_CHECKPOINT_02" in c6["blocking_gates"]
    assert "GATE_8_INDEPENDENT_C4_REFERENCE" in c6["blocking_gates"]


def test_criterion_7_frozen_production_uel():
    report = verify_package167_r3_predecessor_compatibility()
    c7 = report["criteria"]["criterion_7_frozen_production_uel"]
    assert c7["passed"] is True
    assert c7["canonical_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert c7["bitwise_identical"] is True
