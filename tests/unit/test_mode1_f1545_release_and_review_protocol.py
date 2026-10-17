"""
Unit test suite for Task F1545: Method C Propagation Release Verification and Independent Review Protocol.
"""

import os
import sys
import json
import zipfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIGURES_DIR = REPO_ROOT / "method_c_propagation_figures"
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
ZIP_SIGNATURE = b'PK\x03\x04'

def test_active_task_and_running_job():
    active_task_path = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"
    assert active_task_path.exists()
    active_task = json.loads(active_task_path.read_text(encoding="utf-8"))
    assert "1414859.mmaster02" in active_task["active_pbs_job_ids"]

def test_four_remesh_images_existence():
    """Verify that all four remesh images (Stages 1, 2, 3, 4) plus coarse and propagation exist."""
    required_figures = [
        # Stage 0: Initial Coarse
        "mesh_stage0_coarse_2906.png",
        "closeup_stage0_coarse_2906.png",
        # Stage 1: Cycle 1 Remesh
        "mesh_stage1_cycle1_17913.png",
        "closeup_stage1_cycle1_17913.png",
        # Stage 2: Cycle 2 Remesh
        "mesh_stage2_cycle2_21546.png",
        "closeup_stage2_cycle2_21546.png",
        # Stage 3: Cycle 3 Remesh
        "mesh_stage3_cycle3_25085.png",
        "closeup_stage3_cycle3_25085.png",
        # Stage 4: Cycle 4 Remesh
        "mesh_stage4_cycle4_29293.png",
        "closeup_stage4_cycle4_29293.png",
        # Stage 5: Propagation Continuation
        "mesh_stage5_propagation_29293.png",
        "closeup_stage5_propagation_29293.png",
        "overlay_stage5_propagation_29293.png",
        # Multi-panel comparisons
        "method_c_propagation_full_meshes_comparison.png",
        "method_c_propagation_crack_tip_closeups_comparison.png",
        "method_c_propagation_damage_overlay_comparison.png",
    ]
    for fig_name in required_figures:
        p = FIGURES_DIR / fig_name
        assert p.exists(), f"Required figure {fig_name} missing from {FIGURES_DIR}"
        assert p.stat().st_size > 100_000, f"Figure {fig_name} unexpectedly small ({p.stat().st_size} bytes)"
        with open(p, "rb") as f:
            assert f.read(8) == PNG_SIGNATURE, f"Figure {fig_name} has invalid PNG signature"

def test_zip_archive_integrity():
    zip_path = FIGURES_DIR / "method_c_propagation_figures.zip"
    assert zip_path.exists(), "ZIP archive missing"
    assert zip_path.stat().st_size > 30_000_000, f"ZIP archive unexpectedly small ({zip_path.stat().st_size} bytes)"
    with open(zip_path, "rb") as f:
        assert f.read(4) == ZIP_SIGNATURE, "Invalid ZIP signature"

def test_https_verification_summary():
    summary_path = FIGURES_DIR / "https_verification_summary.json"
    assert summary_path.exists(), "HTTPS verification summary missing"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert len(summary) >= 18, f"Expected at least 18 verified assets, got {len(summary)}"
    for item in summary:
        assert item["status"] == 200, f"Asset {item['asset']} failed HTTP 200 check: status {item['status']}"
        assert item["valid"] is True, f"Asset {item['asset']} header invalid: {item['header']}"

def test_chatgpt_independent_verdict_preservation():
    ledger_path = REPO_ROOT / "project_coordination" / "METHOD_C_VALIDATION_LEDGER.csv"
    assert ledger_path.exists(), "Validation ledger missing"
    content = ledger_path.read_text(encoding="utf-8")
    # Verify that Antigravity has NOT self-graded Package 64
    assert "UNREVIEWED_AWAITING_CHATGPT_INDEPENDENT_EVALUATION" in content
    # Verify that historical exceedance is recorded truthfully
    assert "HISTORICAL_BASELINE_PARTIAL_EXCEEDANCE" in content

def test_three_outcome_protocol_definition():
    protocol_path = REPO_ROOT / "docs" / "project" / "METHOD_C_INDEPENDENT_VALIDATION_PROTOCOL.md"
    assert protocol_path.exists(), "Validation protocol missing"
    text = protocol_path.read_text(encoding="utf-8")
    assert "PASS" in text
    assert "FAIL" in text
    assert "NOT YET QUALIFIED" in text
    assert "AWAITING_INDEPENDENT_REVIEW" in text or "UNREVIEWED_AWAITING_CHATGPT_INDEPENDENT_EVALUATION" in text
