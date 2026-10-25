import pytest
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_production_uel_bitwise_frozen():
    prod_uel = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
    expected = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
    actual = compute_sha256(prod_uel)
    assert actual.lower() == expected, f"Production UEL modified: {actual}"

def test_r5_solver_status_completed():
    sta_path = REPO_ROOT / "models/pandey_kumar_mode1/108_r5_c3_multi_increment_continuation/M1_C3_STAGGERED_R5.sta"
    assert sta_path.exists(), "R5 status file missing"
    content = sta_path.read_text(encoding="utf-8")
    assert "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in content
    # Check that Step 16 is present
    assert "  16     1   1" in content

def test_r5_evaluation_summary_schema():
    eval_path = REPO_ROOT / "results/validation/mode1_f1597/r5_evaluation_summary.json"
    assert eval_path.exists(), "R5 evaluation summary missing"
    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["pbs_job_id"] == "1417255.mmaster02"
    assert data["acceptance_status"] == "REJECTED_NUMERICAL_FAILURE"
    assert data["gate_decision"] == "GATE_C1_1_UNPROMOTED"
    assert len(data["step_evolution"]) == 16

def test_r5_displacement_freeze_defect():
    eval_path = REPO_ROOT / "results/validation/mode1_f1597/r5_evaluation_summary.json"
    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    terminal = data["terminal_state_inc5_mech2"]
    # Target was 0.00197010735 mm
    assert terminal["prescribed_target_u_mm"] == 0.00197010735
    # Actual achieved displacement remained frozen at stage A value
    assert abs(terminal["u_rp_mm"] - 0.001965107396) < 1e-6
    assert abs(terminal["u_error_mm"]) > 4.9e-6

def test_r5_fracture_energy_gate_breach():
    eval_path = REPO_ROOT / "results/validation/mode1_f1597/r5_evaluation_summary.json"
    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    terminal = data["terminal_state_inc5_mech2"]
    # Reference is 0.062404 mJ, gate window [0.061156, 0.063652]
    # Authentic R5 reached 0.071065 mJ (+13.88%)
    assert terminal["e_frac_mJ"] > 0.070
    assert terminal["e_frac_pass"] is False
    assert terminal["e_frac_error_pct"] > 10.0

def test_r5_damage_escalation():
    eval_path = REPO_ROOT / "results/validation/mode1_f1597/r5_evaluation_summary.json"
    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    terminal = data["terminal_state_inc5_mech2"]
    # d_max reached 0.715148 (+5.89% vs reference 0.675399)
    assert terminal["d_max"] > 0.71
    assert terminal["d_max_pass"] is False
    assert terminal["healing_detected"] is False
