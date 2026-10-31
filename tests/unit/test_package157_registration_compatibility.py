"""Existing controller operations must not become new registration requests."""
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def invoke(code):
    result=subprocess.run(['powershell','-NoProfile','-Command',"$ErrorActionPreference='Stop'; . './scripts/controller/Controller-Registration.ps1'; . './scripts/controller/Controller-Preparation.ps1'; "+code],
        cwd=str(ROOT),stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stdout+result.stderr


def test_builtin_preparation_keeps_original_route():
    invoke("$t=[pscustomobject]@{}; $p=Get-ControllerRegistrationDispatchPlan (Get-Location).Path 'OPERATION_ID: research_preparation' $t; if($null -ne $p){throw 'Builtin erroneously gated'}")


def test_existing_registered_operation_keeps_normal_qualification_resolver():
    invoke("function Get-ControllerOperation {return [pscustomobject]@{executable=$true}}; $t=[pscustomobject]@{}; $p=Get-ControllerRegistrationDispatchPlan (Get-Location).Path 'OPERATION_ID: execute_existing_qualified' $t; if($null -ne $p){throw 'Existing operation erroneously gated'}")


def test_new_scientific_evidence_changes_event_without_model_dispatch(tmp_path):
    path=str(tmp_path).replace("'","''")
    invoke("$root='"+path+"'; $e=Join-Path $root 'review.json'; [IO.File]::WriteAllText($e,'first'); "+
        "$t=[pscustomobject]@{operation_transition=[pscustomobject]@{operation_id='execute_new_reviewed_case';scientific_review='review.json'}}; "+
        "$a=Get-ControllerRegistrationDispatchPlan $root '' $t; [IO.File]::WriteAllText($e,'distinct science'); "+
        "$b=Get-ControllerRegistrationDispatchPlan $root '' $t; "+
        "if($a.event_fingerprint -eq $b.event_fingerprint -or $a.dispatch_ready -or $b.dispatch_ready){throw 'Scientific event gate failed'}")
