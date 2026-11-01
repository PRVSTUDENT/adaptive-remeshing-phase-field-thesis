"""Gate tests, never PBS jobs or production policy activation."""
import json
from pathlib import Path
import subprocess

import pytest

from scripts.controller.method_c_eligibility import ROOT, eligible, scientific_receipt
from scripts.validation.evaluate_package157_r6_checkpoint import assess, exact_reference


@pytest.mark.parametrize('status', ['REVIEW_REQUIRED', 'PREPARED_FOR_INDEPENDENT_REGISTRATION_REVIEW'])
def test_prepared_routes_to_one_pending_review_event(tmp_path, status):
    operation='execute_mode1_package157_c1_2_r6_adaptive_continuation'
    directory=tmp_path/'project_coordination/operation_definitions';directory.mkdir(parents=True)
    (directory/(operation+'.json')).write_text(json.dumps(dict(schema=1,operation_id=operation,
        registration_status=status,reviewed_by='gemini-antigravity')))
    code=". './scripts/controller/Controller-Registration.ps1'; "+\
        "$t=[pscustomobject]@{requested_operation_id='"+operation+"'}; "+\
        "$p=Get-ControllerRegistrationPlan '"+str(tmp_path)+"' '' $t; "+\
        "if($p.dispatch_ready -or $p.task_type -ne 'EXTERNAL_REVIEW_DISPATCH'){throw 'Prepared became approved'}; "+\
        "Write-ControllerDefinitionReviewEvent '"+str(tmp_path)+"' $p; "+\
        "$f=Join-Path '"+str(tmp_path)+"' 'project_coordination/controller/definition-review-"+operation+".json'; "+\
        "$before=(Get-Item $f).LastWriteTimeUtc; Write-ControllerDefinitionReviewEvent '"+str(tmp_path)+"' $p; "+\
        "if((Get-Item $f).LastWriteTimeUtc -ne $before){throw 'Duplicate review event'}; 'PASS'"
    result=subprocess.run(['powershell','-NoProfile','-Command',"$ErrorActionPreference='Stop'; "+code],
        cwd=ROOT,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
    assert 'PASS' in result.stdout


def test_policy_cannot_self_activate_from_candidate_metadata():
    with pytest.raises(ValueError,match='POLICY_INDEPENDENT_ACTIVATION_MISSING'):
        eligible(ROOT,'execute_mode1_package157_c1_2_r6_adaptive_continuation',
                 'results/validation/package157_r6_checkpoint_scientific_review.json')


def test_no_nearest_or_interpolated_reference():
    assert exact_reference([dict(u_top_mm='0.00186359370',rf2_kN='0.186')],0.0018603125442191958)==[]


@pytest.fixture(scope='module')
def authentic_assessment():
    return assess(ROOT)


def test_authentic_full_state_numerical_gates(authentic_assessment):
    m=authentic_assessment['measurements']
    assert m['nodes_checked']==7265 and m['history_values_checked']==28224
    assert m['checkpoint_displacement_max_difference']==m['checkpoint_damage_max_difference']==0
    assert m['checkpoint_history_vs_saved_checkpoint_max_difference']==0
    assert m['dual_error']==0 and m['complementarity']<=1e-6
    assert m['delta_h_MPa']<=1e-6 and m['delta_d']<=1e-5 and m['delta_u_mm']<=1e-9
    assert m['min_delta_d']>=-1e-6


def test_missing_exact_reference_never_becomes_acceptance(authentic_assessment):
    assert authentic_assessment['physical_acceptance']=='UNVERIFIED'
    assert authentic_assessment['gates']['force'] is None
    assert authentic_assessment['gates']['raw_energy'] is None
    assert authentic_assessment['reference']['interpolation_used'] is False


def test_unverified_predecessor_blocks_eligibility():
    with pytest.raises(ValueError,match='PREDECESSOR_PHYSICAL_ACCEPTANCE_REQUIRED'):
        scientific_receipt(ROOT,'results/validation/package157_r6_checkpoint_scientific_review.json','unused')
