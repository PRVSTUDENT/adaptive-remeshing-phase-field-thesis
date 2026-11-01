"""test_package157_r7_candidate_qualification.py

Unit test for Package 157 Revision 7 candidate qualification and dependency gating.
"""
import pytest
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

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
    assert cont['frozen_uel_sha256'] == 'CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6'

    # Check resources
    res = spec['predicted_resource_requirements']
    assert res['cpus'] == 1
    assert res['memory_gb'] <= 16
    assert res['walltime_hours_ceiling'] <= 8.0

    # Check dispatch gating decision
    disp = spec['dispatch_decision']
    assert disp['eligible_for_submission'] is False
    assert 'Predecessor' in disp['blocker']
