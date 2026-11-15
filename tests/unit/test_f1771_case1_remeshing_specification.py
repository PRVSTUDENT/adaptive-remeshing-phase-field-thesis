"""Unit tests for Task F1771: Case 1 Method A Advancing Adaptive Remeshing Specification,

Config Alignment, Shared Framework Verification & Pre-Execution Gates.
"""

import hashlib
import json
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

FROZEN_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6".lower()

FRAMEWORK_SCRIPT_PATH = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
EXPECTED_FRAMEWORK_SHA = "8D71F38F23867A23C1FC1BF5EC499533A8C75F538B77804ECE03B5C668F4BE08".lower()

CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case1_mode1_edge_crack.json")
EXPECTED_CONFIG_SHA = "954BE4473EBC79D54E18DA81DF00E6FCEA1E6B9F8430EA4A8DB52D920E5AA7F3".lower()

PBS_SCRIPT_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "238_f1771_case1_remesh", "submit_f1771_case1_remesh.pbs"
)
EXPECTED_PBS_SHA = "ED9B2B715F79A269602E5EFA8DB74CBC68465568C4C131D76770D3AD5B57D843".lower()


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_frozen_uel_immutability():
    """Verify production UEL f42_mixed_uel.for remains strictly bitwise frozen."""
    assert os.path.exists(FROZEN_UEL_PATH), f"UEL not found: {FROZEN_UEL_PATH}"
    actual_sha = compute_sha256(FROZEN_UEL_PATH)
    assert actual_sha == EXPECTED_UEL_SHA, f"UEL hash drift: {actual_sha} != {EXPECTED_UEL_SHA}"


def test_shared_framework_immutability():
    """Verify shared framework reusable_2d_adaptive_framework.py remains unchanged."""
    assert os.path.exists(FRAMEWORK_SCRIPT_PATH), f"Framework script not found: {FRAMEWORK_SCRIPT_PATH}"
    actual_sha = compute_sha256(FRAMEWORK_SCRIPT_PATH)
    assert actual_sha == EXPECTED_FRAMEWORK_SHA, f"Framework hash drift: {actual_sha} != {EXPECTED_FRAMEWORK_SHA}"


def test_case1_remeshing_config_alignment():
    """Verify f1728_case1_mode1_edge_crack.json specifies Step-2 ALL_INCREMENTS envelope."""
    assert os.path.exists(CONFIG_PATH), f"Config not found: {CONFIG_PATH}"
    actual_sha = compute_sha256(CONFIG_PATH)
    assert actual_sha == EXPECTED_CONFIG_SHA, f"Config hash mismatch: {actual_sha} != {EXPECTED_CONFIG_SHA}"

    with open(CONFIG_PATH, "r") as f:
        data = json.load(f)

    rule = data["remeshing_rule"]
    assert rule["step_name"] == "Step-2", "Must target Step-2 containing advancing crack"
    assert rule["output_frequency"] == "ALL_INCREMENTS", "Must evaluate ALL_INCREMENTS envelope"
    assert rule["error_target"] == 1.85
    assert rule["coarsening_factor"] == "NOT_ALLOWED"
    assert rule["variable"] == "MISESERI"
    assert rule["min_element_size_mm"] == 0.001
    assert rule["max_element_size_mm"] == 0.020


def test_canonical_manifest_case1_concordance():
    """Verify canonical_five_case_manifest.json points to authentic advancing donor ODB."""
    manifest_path = os.path.join(REPO_ROOT, "configs", "remeshing", "canonical_five_case_manifest.json")
    assert os.path.exists(manifest_path)
    with open(manifest_path, "r") as f:
        data = json.load(f)

    assert data["governing_rules"]["cumulative_pbs_submissions"] == 29
    c1 = data["benchmarks"]["case_1"]
    assert "PK_F1769_C1_DONOR.odb" in c1["donor_odb_cluster_path"]
    assert c1["donor_step_name"] == "Step-2"
    assert "ALL_INCREMENTS" in c1["donor_frame_selection_mechanism"]
    assert c1["published_elements"] == 13762


def test_submit_f1771_script_directives_and_atomic_lock_guard():
    """Verify submit_f1771_case1_remesh.pbs has atomic directory guard and safe directives."""
    assert os.path.exists(PBS_SCRIPT_PATH), f"Script not found: {PBS_SCRIPT_PATH}"
    actual_sha = compute_sha256(PBS_SCRIPT_PATH)
    assert actual_sha == EXPECTED_PBS_SHA, f"Script hash mismatch: {actual_sha} != {EXPECTED_PBS_SHA}"

    with open(PBS_SCRIPT_PATH, "r") as f:
        content = f.read()

    # 1. Atomic POSIX directory lock guard
    assert 'LOCK_GUARD_DIR="${RUN_DIR}/${JOB_NAME}.pbs_guard_d"' in content
    assert 'mkdir "${LOCK_GUARD_DIR}"' in content
    assert 'rmdir "${LOCK_GUARD_DIR}"' in content

    # 2. Fail closed on pre-existing Abaqus lock
    assert 'if [ -e "${RUN_DIR}/${JOB_NAME}.lck" ]; then' in content
    assert 'echo "ERROR: Pre-existing Abaqus lock file ${JOB_NAME}.lck detected. Failing closed."' in content

    # 3. Strictly ZERO unconditional rm -f of Abaqus lock files
    assert 'rm -f "${JOB_NAME}.lck"' not in content
    assert 'rm -f *.lck' not in content

    # 4. Resource bounds
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in content
    assert "#PBS -l walltime=01:00:00" in content
    assert "#PBS -q entry_imfdfkmq" in content
    assert "#PBS -m abe" in content
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in content


def test_f1770_donor_audit_data_availability():
    """Verify donor ODB telemetry audit confirms genuine crack advancement."""
    summary_path = os.path.join(REPO_ROOT, "results", "validation", "f1770_case1_donor_audit_summary.json")
    assert os.path.exists(summary_path)
    with open(summary_path, "r") as f:
        data = json.load(f)

    assert data["job_id"] == "1423604.mmaster02"
    assert data["crack_advancement_mm"] >= 0.45
    assert data["has_miseseri"] is True
    assert data["has_sdv"] is True
    assert data["gates"]["G1_exit_code"] == "PASS"
    assert data["gates"]["G5_crack_advancement"] == "PASS"
