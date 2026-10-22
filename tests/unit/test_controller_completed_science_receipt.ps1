# Offline regression for run-bound completion receipts. No HPC, credentials, or network.
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')
$root=Join-Path ([IO.Path]::GetTempPath()) ('closeout-receipt-test-'+[guid]::NewGuid().ToString('N'))
foreach($folder in @('project_coordination','project_coordination/sessions','project_coordination/controller','results/validation')) {
    [void](New-Item -ItemType Directory -Path (Join-Path $root $folder) -Force)
}
function Put([string]$Rel,[string]$Text) { [IO.File]::WriteAllText((Join-Path $root $Rel),$Text,[Text.UTF8Encoding]::new($false)) }
function Check([bool]$Okay,[string]$Message) { if(-not $Okay){throw "FAIL: $Message"}; Write-Host "PASS: $Message" }
$run=[guid]::NewGuid().ToString()
$reportRel="project_coordination/sessions/2026_test_$run.md"
$bootRel="project_coordination/controller/turn-$run.json"
$prepRel="results/validation/preparation-$run.json"
Put 'project_coordination/ACTIVE_TASK.json' '{"task_id":"F1597-CORRECT-PACKAGE72-STATE-TRANSFER","status":"PREPARATION_COMPLETE"}'
Put 'project_coordination/CURRENT_STATE.md' 'Authentic completed scientific receipt fixture.'
Put 'project_coordination/TASK_LEDGER.csv' "task_id,status`nF1597-CORRECT-PACKAGE72-STATE-TRANSFER,preparation_complete"
Put 'project_coordination/HPC_JOB_LEDGER.csv' "pbs_id,status`n1416301.mmaster02,SUBMITTED"
Put 'project_coordination/MODE1_EXECUTION_LEDGER.json' '{"jobs":["1416301.mmaster02"]}'
Put 'project_coordination/ACTIVE_SESSION.json' (@{active=$false;task_id='F1597-CORRECT-PACKAGE72-STATE-TRANSFER';agent='gemini-antigravity';controller_run_id=$run;session_report=$reportRel}|ConvertTo-Json)
Put $reportRel "Scientific completed research for $run; PBS 1416301.mmaster02; checkpoint measurements verified.`nFinished`n"
$h=(Get-FileHash (Join-Path $root 'project_coordination/HPC_JOB_LEDGER.csv')).Hash
$prep=@{schema=1;status='PREPARATION_COMPLETE';finding='Genuine completed research with measured convergence and traceable PBS receipt.';verification_passed=$true;evidence_sources=@{'project_coordination/HPC_JOB_LEDGER.csv'=$h}}
Put $prepRel ($prep|ConvertTo-Json -Depth 7)
$pHash=(Get-FileHash (Join-Path $root $prepRel)).Hash
$record=@{controller_run_id=$run;task_id='F1597-CORRECT-PACKAGE72-STATE-TRANSFER';bootstrap_status='COMPLETE';stage='COMPLETE';session_report=$reportRel;scientific_checkpoint=@{kind='PREPARATION_CHECKPOINT';operation='research_preparation';exit_code=0;artifact=$prepRel;sha256=$pHash}}
Put $bootRel ($record|ConvertTo-Json -Depth 8)
$path=Join-Path $root 'controller_checkpoint.json'
function New-State {
    $e=Get-ControllerEvidence $root
    $s=New-ControllerTurnState $e 19 'distinct validated next task'
    $s.run_id=$run
    $s.bootstrap_record_path=Join-Path $root $bootRel
    return $s
}
$s=New-State
Check (Test-ControllerCompletedScienceReceipt $root $s) 'Matching completed receipt is independently accepted'
Check ((Complete-ControllerTurn $root $path $s 'AGY returned scientific narrative without trailing marker') -eq 'COMPLETED') 'Normal AGY completion advances via verified receipt despite omitted marker'
$s=New-State
Check ((Complete-ControllerTurn $root $path $s 'BLOCKED: scientific result invalid') -eq 'BLOCKED') 'Explicit BLOCKED response still fails closed'
Put $reportRel "Wrong report for $run without terminal completion marker"
$s=New-State
Check (-not(Test-ControllerCompletedScienceReceipt $root $s)) 'Incomplete on-disk report is rejected'
Check ((Complete-ControllerTurn $root $path $s 'Partial AGY response') -eq 'BLOCKED') 'Incomplete receipt plus missing final marker fails closed'
Put $reportRel "Science completed $run`nFinished`n"
$record.stage='PREPARATION'
Put $bootRel ($record|ConvertTo-Json -Depth 8)
$s=New-State
Check (-not(Test-ControllerCompletedScienceReceipt $root $s)) 'Unfinished controller bootstrap stage is rejected'
$record.stage='COMPLETE'
Put $bootRel ($record|ConvertTo-Json -Depth 8)
$ss=Get-Content (Join-Path $root 'project_coordination/ACTIVE_SESSION.json') -Raw|ConvertFrom-Json
$ss.controller_run_id=[guid]::NewGuid().ToString()
Put 'project_coordination/ACTIVE_SESSION.json' ($ss|ConvertTo-Json -Depth 6)
$s=New-State
Check (-not(Test-ControllerCompletedScienceReceipt $root $s)) 'Stale or mismatched session run is rejected'
$ss.controller_run_id=$run
Put 'project_coordination/ACTIVE_SESSION.json' ($ss|ConvertTo-Json -Depth 6)
$prep.finding='Altered output no longer matching checkpoint hash'
Put $prepRel ($prep|ConvertTo-Json -Depth 7)
$s=New-State
Check (-not(Test-ControllerCompletedScienceReceipt $root $s)) 'Modified scientific artifact is rejected by SHA256 gate'
Write-Host 'PASS: fail-closed receipt regression suite (no real solver or PBS jobs).'
