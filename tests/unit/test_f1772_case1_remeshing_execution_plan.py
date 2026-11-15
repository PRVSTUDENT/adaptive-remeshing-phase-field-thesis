"""Unit tests for Task F1772: Case 1 Method A Advancing Adaptive Remeshing Execution Plan,

Preflight Hash Verification & Predeclared Gates G1-G8.
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
    REPO_ROOT, "models", "pandey_kumar_mode1", "239_f1772_case1_remesh", "submit_f1772_case1_remesh.pbs"
)
EXPECTED_PBS_SHA = "668F98748F2B5E0FDE3F6C9521132A922D27489F8F86EAB0DA51FD2D05C9F5F5".lower()


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


def test_submit_f1772_script_directives_and_comprehensive_preflight():
    """Verify submit_f1772_case1_remesh.pbs has atomic directory guard,

    independent preflight hashing for UEL, config, and framework, and donor ODB checks.
    """
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

    # 4. Independent preflight hash verification (Finding F1771-R04)
    assert 'ACTUAL_UEL_SHA=$(sha256sum "${USER_SUB}"' in content
    assert 'ACTUAL_CFG_SHA=$(sha256sum "${CONFIG_FILE}"' in content
    assert 'ACTUAL_FW_SHA=$(sha256sum "${FRAMEWORK_SCRIPT}"' in content

    # 5. Donor ODB presence and size check
    assert 'DONOR_SIZE=$(stat -c%s "${RUN_DIR}/${DONOR_ODB}")' in content

    # 6. Resource bounds
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in content
    assert "#PBS -l walltime=01:00:00" in content
    assert "#PBS -q entry_imfdfkmq" in content
    assert "#PBS -m abe" in content
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in content


def test_f1772_execution_plan_report_integrity():
    """Verify execution plan report exists and documents gates G1-G8 and findings F1771-R01 to R06."""
    report_path = os.path.join(REPO_ROOT, "docs", "validation", "F1772_CASE1_REMESHING_EXECUTION_PLAN.md")
    assert os.path.exists(report_path), f"Report not found: {report_path}"
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "F1771-R01" in content
    assert "F1771-R04" in content
    assert "G1" in content
    assert "G8" in content
    assert "submit_f1772_case1_remesh.pbs" in content
    assert "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6" in content
