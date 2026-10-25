import hashlib
import json
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R15_DIR = ROOT / "models/pandey_kumar_mode1/108_r15_c3_autonomous_active_set"
AUTH_FILE = R15_DIR / "M1_C3_ACTIVE_SET_R15_AUTHORIZATION.json"
MANIFEST_FILE = R15_DIR / "PACKAGE_MANIFEST.json"

def test_r15_files_exist_and_hashes_match():
    assert AUTH_FILE.is_file(), "Missing authorization file"
    assert MANIFEST_FILE.is_file(), "Missing package manifest"
    with AUTH_FILE.open(encoding="utf-8") as f:
        auth = json.load(f)
    for name, expected_hash in auth["files"].items():
        p = R15_DIR / name
        assert p.is_file(), f"Missing package file: {name}"
        actual_hash = hashlib.sha256(p.read_bytes()).hexdigest()
        assert actual_hash.lower() == expected_hash.lower(), f"Hash mismatch for {name}: {actual_hash} vs {expected_hash}"

def test_r15_manifest_structure_and_governance():
    with AUTH_FILE.open(encoding="utf-8") as f:
        auth = json.load(f)
    assert auth["schema"] == 1
    assert auth["adapter"] == "mode1-experimental-12dof-v1"
    assert auth["scientific_scope"] == "MODE1"
    assert auth["technical_stage"] == "C1-1"
    assert auth["configuration"] == "UNIFIED_12DOF_AUTONOMOUS_ACTIVE_SET"
    assert auth["max_submissions"] == 1
    assert auth["automatic_retry"] is False

    job = auth["jobs"][0]
    assert job["id"] == "M1_C3_ACTIVE_SET_R15"
    assert job["cpus"] == 1
    assert job["memory_gb"] == 16
    assert job["walltime_hours"] == 8
    assert job["queue"] == "entry_imfdfkmq"
    assert job["execution"] == "single-rank serial"

    cmd = job["command"]
    cmd_hash = hashlib.sha256(cmd.encode()).hexdigest()
    assert cmd_hash == job["command_sha256"], "Command SHA256 mismatch"

def test_r15_uel_repaired_signs_parity():
    uel_path = R15_DIR / "f42_unified_12dof_active_set_uel.for"
    content = uel_path.read_text(encoding="utf-8")
    assert "- 2.0D0 * (1.0D0 - D_VAL) * H_TRIAL_VAL" in content, "Missing repaired Rd coupling minus sign"
    assert "+ 2.0D0 * H_TRIAL_VAL" in content, "Missing repaired Kdd coupling plus sign"
    assert hashlib.sha256(uel_path.read_bytes()).hexdigest().lower() == "ab0a5a71335ecb445e91ec13a645e280ff3310b561a5e78aba4a49c8e81dd8ac"

def test_r15_driver_safeguarded_ranked_batch_semantics():
    driver_path = R15_DIR / "driver_r15_autonomous_continuation.py"
    content = driver_path.read_text(encoding="utf-8")
    assert "B_max = 20" in content, "Missing B_max=20 batch limit"
    assert "5.0e-8" in content, "Missing tau_release=5.0e-8 cutoff"
    assert "KINEMATIC_DISPLACEMENT_ERROR" in content, "Missing kinematic displacement error check"
    assert "SOLVER_ABORT_EXIT" in content, "Missing solver abort check"
    assert "CYCLE_OSCILLATION_DETECTED" in content, "Missing cycle oscillation check"

def test_r15_continuation_deck_structure():
    inp_path = R15_DIR / "M1_C3_ACTIVE_SET_R15_CONTINUATION.inp"
    content = inp_path.read_text(encoding="utf-8")
    assert "*Step, name=Stage-A, nlgeom=NO, inc=25" in content
    assert "*Step, name=Inc1-Coupled, nlgeom=NO, inc=200" in content
    assert "1.0, 1.0, 1.0E-8, 1.0" in content, "Missing robust dt_min=1e-8 control"
    assert "N_RP, 2, 2, 0.00196610735" in content

def test_r15_dual_channel_notifications():
    pbs_path = R15_DIR / "submit_M1_C3_ACTIVE_SET_R15.pbs"
    content = pbs_path.read_text(encoding="utf-8")
    assert "#PBS -m abe" in content
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in content
    assert "source ./job_notifications.sh" in content
    assert "notification_install_terminal_trap" in content
    assert "notify_start" in content
