"""Unit tests for Package 163-R3 runtime integrity and execution configuration."""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_PATH = REPO_ROOT / "results/validation/package163_r3_runtime_integrity_verification.json"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
CHECKPOINT_01_SHA256 = "DCFD31186061FA81111DA18071CF8ADFB9BAF2C5CB343CB60F08416741C1B64A"


def test_runtime_integrity_artifact_exists():
    assert ARTIFACT_PATH.exists(), f"Artifact must exist: {ARTIFACT_PATH}"
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("schema") == 1
    assert data.get("verification_type") == "PACKAGE_163_R3_RUNTIME_INTEGRITY"
    assert data.get("decision") == "R3_RUNTIME_INTEGRITY_PASS"
    assert data.get("verification_passed") is True


def test_subproblem_naming_isolation():
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    naming = data.get("subproblem_naming_audit", {})
    assert naming.get("defined_in_driver") is True
    assert naming.get("directory_isolation_verified") is True

    isolation = data.get("directory_isolation", {})
    assert isolation.get("paths_disjoint") is True
    assert isolation.get("artifact_collision_risk") == "ZERO"
    assert isolation.get("r2_run_dir") != isolation.get("r3_run_dir")
    assert isolation.get("r2_job_output") != isolation.get("r3_job_output")


def test_max_outer_300_enforcement():
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("max_outer_300_verified") is True
    res = data.get("pbs_resources", {})
    assert res.get("cpus") == 1
    assert res.get("memory_gb") == 16
    assert res.get("walltime_hours") == 8
    assert res.get("queue") == "entry_imfdfkmq"


def test_exact_5nm_load_increment():
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    load = data.get("load_schedule", {})
    assert load.get("baseline_uy_mm") == 0.0018603125442191958
    assert load.get("target_uy_mm") == 0.0018653125442191958
    assert load.get("increment_nm") == 5.0
    assert load.get("exact_5nm_continuation") is True


def test_predecessor_checkpoint_and_uel_hashes():
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    chkpt = data.get("predecessor_binding", {})
    assert chkpt.get("expected_sha256") == CHECKPOINT_01_SHA256
    assert chkpt.get("actual_sha256") == CHECKPOINT_01_SHA256
    assert chkpt.get("matched") is True

    uel = data.get("frozen_uel_verification", {})
    assert uel.get("expected_sha256") == FROZEN_UEL_SHA256
    assert uel.get("actual_sha256") == FROZEN_UEL_SHA256
    assert uel.get("matched") is True
