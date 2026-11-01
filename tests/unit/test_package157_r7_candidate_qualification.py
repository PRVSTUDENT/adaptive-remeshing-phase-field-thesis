"""test_package157_r7_candidate_qualification.py

Unit tests for Package 157 Revision 7 candidate qualification,
manifest integrity, and predecessor dependency gating.
"""
import pytest
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
R7_DIR = REPO_ROOT / 'models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r7'
FROZEN_UEL_HASH = 'CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6'

def compute_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def test_package157_r7_specification_integrity():
    spec_path = REPO_ROOT / 'results/validation/package157_r7_candidate_specification.json'
    assert spec_path.is_file(), "Candidate specification file missing"
    spec = json.loads(spec_path.read_text(encoding='utf-8'))

    assert spec['schema'] == 1
    assert spec['candidate'] == 'package157_r7_restart_continuation'
    assert spec['status'] == 'OFFLINE_QUALIFIED__DISPATCH_WITHHELD_PREDECESSOR_RUNNING'

    # Check predecessor binding
    pred = spec['predecessor']
    assert pred['pbs_job_id'] == '1419359.mmaster02'
    assert pred['job_name'] == 'M1_C4_P157_C1_2_R6'
    assert pred['target_uy_mm'] == pytest.approx(0.0018653125442191958)

    # Check continuation schedule
    cont = spec['continuation_specification']
    assert cont['baseline_uy_mm'] == pytest.approx(0.0018653125442191958)
    assert cont['target_uy_mm'] == pytest.approx(0.0018753125442191958)
    assert cont['delta_uy_nm'] == pytest.approx(10.0)
    assert cont['max_outer'] == 120

    # Check mesh discretization
    disc = cont['discretization']
    assert disc['nodes'] == 7265
    assert disc['elements'] == 7056
    assert disc['gauss_points'] == 28224

    # Check frozen UEL hash
    assert cont['frozen_uel_sha256'] == FROZEN_UEL_HASH

    # Check resources
    res = spec['predicted_resource_requirements']
    assert res['cpus'] == 1
    assert res['memory_gb'] <= 16
    assert res['walltime_hours_ceiling'] <= 8.0

    # Check dispatch gating decision
    disp = spec['dispatch_decision']
    assert disp['eligible_for_submission'] is False
    assert 'Predecessor' in disp['blocker']

def test_package157_r7_manifest_and_driver_integrity():
    assert R7_DIR.is_dir(), "R7 package directory missing"
    pkg_manifest_path = R7_DIR / 'PACKAGE_MANIFEST.json'
    exec_manifest_path = R7_DIR / 'EXECUTION_MANIFEST.json'
    driver_path = REPO_ROOT / 'scripts/state_transfer/driver_package157_r7.py'

    assert pkg_manifest_path.is_file(), "PACKAGE_MANIFEST.json missing"
    assert exec_manifest_path.is_file(), "EXECUTION_MANIFEST.json missing"
    assert driver_path.is_file(), "driver_package157_r7.py missing"

    pkg_manifest = json.loads(pkg_manifest_path.read_text(encoding='utf-8'))
    exec_manifest = json.loads(exec_manifest_path.read_text(encoding='utf-8'))

    # Verify UEL integrity in R7 package
    uel_path = R7_DIR / 'f42_mixed_uel.for'
    assert uel_path.is_file(), "f42_mixed_uel.for missing from R7"
    assert compute_sha256(uel_path).upper() == FROZEN_UEL_HASH

    # Verify file hash integrity in PACKAGE_MANIFEST
    for name, expected_hash in pkg_manifest['files'].items():
        actual_hash = compute_sha256(R7_DIR / name).lower()
        assert actual_hash == expected_hash.lower(), f"Hash mismatch for {name}"

    # Verify file hash integrity in EXECUTION_MANIFEST
    for name, expected_hash in exec_manifest['files'].items():
        actual_hash = compute_sha256(R7_DIR / name).lower()
        assert actual_hash == expected_hash.lower(), f"Hash mismatch for {name}"

    # Verify job definition
    job = exec_manifest['jobs'][0]
    assert job['id'] == 'M1_C4_P157_C1_2_R7'
    assert job['cpus'] == 1
    assert job['memory_gb'] == 16
    assert job['walltime_hours'] == 8
    assert job['queue'] == 'entry_imfdfkmq'

    # Verify driver parameters
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    import scripts.state_transfer.driver_package157_r7 as r7_drv
    assert r7_drv.START == pytest.approx(0.0018653125442191958)
    assert r7_drv.TARGETS == [pytest.approx(0.0018753125442191958)]
