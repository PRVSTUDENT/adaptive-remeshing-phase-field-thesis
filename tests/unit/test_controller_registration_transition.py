"""Real PowerShell routing: no model redispatch on an unchanged missing registry."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]


def powershell(code):
    result=subprocess.run(['powershell','-NoProfile','-Command',"$ErrorActionPreference='Stop'; "+code],
        cwd=str(ROOT),stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
    return result.stdout


def test_missing_registration_has_one_event_and_no_dispatch(tmp_path):
    path=str(tmp_path).replace("'","''")
    output=powershell(". './scripts/controller/Controller-Registration.ps1'; "+
        "$t=[pscustomobject]@{requested_operation_id='execute_reviewed_pending_operation'}; "+
        "$p=Get-ControllerRegistrationPlan '"+path+"' '' $t; "+
        "if($p.dispatch_ready -or $p.status -ne 'DEFINITION_REVIEW_REQUIRED'){throw 'Unsafe dispatch'}; "+
        "Write-ControllerDefinitionReviewEvent '"+path+"' $p; "+
        "$f=Join-Path '"+path+"' 'project_coordination/controller/definition-review-execute_reviewed_pending_operation.json'; "+
        "$before=(Get-Item $f).LastWriteTimeUtc; Write-ControllerDefinitionReviewEvent '"+path+"' $p; "+
        "if((Get-Item $f).LastWriteTimeUtc -ne $before){throw 'Duplicate event write'}; 'PASS'")
    assert 'PASS' in output


def test_reviewed_definition_routes_qualification_before_execution(tmp_path):
    directory=tmp_path/'project_coordination/operation_definitions';directory.mkdir(parents=True)
    (tmp_path/'review.json').write_text('{"reviewed":true}')
    digest=hashlib.sha256((tmp_path/'review.json').read_bytes()).hexdigest().upper()
    operation='execute_reviewed_pending_operation'
    (directory/(operation+'.json')).write_text(json.dumps(dict(schema=1,operation_id=operation,
        registration_status='REVIEWED_FOR_TECHNICAL_QUALIFICATION',reviewed_by='maintainer',
        evidence_sources={'review.json':digest},execution_script='execute.py',preparation_script='prepare.py')))
    path=str(tmp_path).replace("'","''")
    result=powershell(". './scripts/controller/Controller-Registration.ps1'; "+
        "function Get-ControllerDynamicQualification {return $null}; "+
        "$t=[pscustomobject]@{requested_operation_id='"+operation+"'}; "+
        "$p=Get-ControllerRegistrationPlan '"+path+"' '' $t; "+
        "if($p.task_type -ne 'RESEARCH_PREPARATION' -or $p.recipe -ne 'registered-technical-qualification'){throw 'Wrong transition'}; "+
        "function Get-ControllerDynamicQualification {return [pscustomobject]@{canonical_path='execute.py'}}; "+
        "$p=Get-ControllerRegistrationPlan '"+path+"' '' $t; "+
        "if($p.task_type -ne 'QUALIFIED_EXECUTION'){throw 'Qualified transition absent'}; 'PASS'")
    assert 'PASS' in result


def test_guarded_upload_rejects_outside_workspace_before_network():
    result=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',
        str(ROOT/'.agents/scripts/Invoke-GuardedSsh.ps1'),'-UploadFile','C:/Windows/win.ini',
        '-RemotePath','/scratch9/pr21vyci/runs/mode1_bad/test.txt'],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=15)
    assert result.returncode!=0 and 'FAIL_CLOSED_UNSAFE_UPLOAD' in result.stderr
