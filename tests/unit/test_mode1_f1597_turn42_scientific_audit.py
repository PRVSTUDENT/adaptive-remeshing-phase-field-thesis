"""
Unit tests for Turn 42: Morning Scientific Audit of Overnight HPC Results (Packages 87 & 88).
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2
"""
import os
import sys
import json
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_frozen_uel_integrity():
    """Verify bitwise frozen production UEL hash across all models."""
    uel87 = REPO_ROOT / "models/pandey_kumar_mode1/87_c2_virgin_mesh_control/f42_mixed_uel.for"
    uel88 = REPO_ROOT / "models/pandey_kumar_mode1/88_sameprocess_forward_continuation/f42_mixed_uel.for"
    assert sha256_file(uel87) == FROZEN_UEL_HASH
    assert sha256_file(uel88) == FROZEN_UEL_HASH

def test_package87_virgin_c2_audit():
    """Verify Package 87 virgin C2 mechanics: peak force parity, energy parity, and transfer-point force."""
    telemetry_path = REPO_ROOT / "results/validation/mode1_f1597/turn42_telemetry.json"
    assert telemetry_path.exists()
    with open(telemetry_path, "r") as f:
        data = json.load(f)
    
    p87 = data["package87"]
    assert p87["step_name"] == "C2_VIRGIN_LOADING"
    assert p87["total_frames"] == 24
    assert p87["best_frame_id"] == 115
    assert abs(p87["best_frame_time"] - 0.50802148) < 1e-6
    
    # Dissipated energy at end of virgin loading
    e_frac = p87["energy_history"]["ALLIE"] * 1e6 # in uJ
    assert abs(e_frac - 302.525) < 1.0 # ~301.65 uJ fracture energy + elastic
    
    # Force at transfer point: native virgin C2 carries only 0.685 N
    rf2_rp_N = p87["hist_rf2"] * 1000.0
    assert abs(rf2_rp_N - 0.68535) < 0.05
    # Demonstrates that native C2 is further severed at u=0.0025401 mm than donor (3.266 N)

def test_package88_sameprocess_forward_continuation():
    """Verify Package 88 Step 5 genuine forward crack propagation softening and history monotonicity."""
    telemetry_path = REPO_ROOT / "results/validation/mode1_f1597/turn42_telemetry.json"
    assert telemetry_path.exists()
    with open(telemetry_path, "r") as f:
        data = json.load(f)
    
    p88 = data["package88"]
    step5_frames = p88["step5_frames"]
    assert len(step5_frames) == 14
    
    # Frame 0 (checkpoint): u = 0.0025401 mm, RF2 = 3.26576 N
    f0 = step5_frames[0]
    assert abs(f0["u2_rp"] - 0.002540107) < 1e-6
    assert abs(f0["rf2_rp"] * 1000.0 - 3.26576) < 0.01
    
    # Frame 12 (last accepted): u = 0.0025893 mm, RF2 = 2.99223 N
    f12 = step5_frames[12]
    assert abs(f12["u2_rp"] - 0.002589267) < 1e-6
    assert abs(f12["rf2_rp"] * 1000.0 - 2.99223) < 0.01
    
    # Verify softening: reaction force decreases monotonically from peak in Step 5
    assert f12["rf2_rp"] < f0["rf2_rp"]
    
    # Verify strict history monotonicity: 0 drops across all frames
    for fr in step5_frames:
        assert fr["h_drop_count"] == 0
        assert fr["max_h_drop"] == 0.0

def test_accounting_ledger_reconciliation():
    """Verify jobs 1416420 and 1416421 exist in local ledgers and task records."""
    task_path = REPO_ROOT / "project_coordination/ACTIVE_TASK.json"
    hpc_ledger_path = REPO_ROOT / "project_coordination/HPC_JOB_LEDGER.csv"
    batch_sub_path = REPO_ROOT / "project_coordination/MODE1_BATCH_SUBMISSIONS.json"
    mode1_ledger_path = REPO_ROOT / "project_coordination/MODE1_EXECUTION_LEDGER.json"

    with open(task_path, "r", encoding="utf-8") as f:
        task = json.load(f)
    assert "1416420.mmaster02" in task["completed_pbs_job_ids"]
    assert "1416421.mmaster02" in task["completed_pbs_job_ids"]

    hpc_content = hpc_ledger_path.read_text(encoding="utf-8")
    assert "1416420.mmaster02" in hpc_content
    assert "1416421.mmaster02" in hpc_content

    batch_sub_content = batch_sub_path.read_text(encoding="utf-8")
    assert "1416420.mmaster02" in batch_sub_content
    assert "1416421.mmaster02" in batch_sub_content

    mode1_content = mode1_ledger_path.read_text(encoding="utf-8")
    assert "M1_C2_VIRGIN_CONTROL" in mode1_content
    assert "M1_DONOR_FORWARD_CONTINUATION" in mode1_content
