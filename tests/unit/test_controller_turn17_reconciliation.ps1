param([Parameter(Mandatory)][string]$ArchivedCheckpoint)
$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$r=Join-Path $env:TEMP ('turn17-test-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$r/scripts/controller","$r/project_coordination","$r/evidence"|Out-Null
Get-ChildItem "$repo/scripts/controller" -Filter '*.ps1' -File | Copy-Item -Destination "$r/scripts/controller"
Copy-Item $ArchivedCheckpoint "$r/checkpoint.json";Copy-Item $ArchivedCheckpoint "$r/evidence/original-blocked-checkpoint.json"
@{active=$true;agent='codex';task_id='TURN17-EVIDENCE-RECONCILIATION'}|ConvertTo-Json|Set-Content "$r/project_coordination/ACTIVE_SESSION.json"
'Synthetic local fixture ledger, no jobs'|Set-Content "$r/project_coordination/HPC_JOB_LEDGER.csv"
'Fixture monitoring report, no scientific acceptance'|Set-Content "$r/report.md"
@{job_id='1419488.mmaster02';classification='PHYSICAL_FAIL';scheduler_observation=@{state='F';run_count=1}}|ConvertTo-Json|Set-Content "$r/evidence/acceptance.json"
$before=(Get-FileHash "$r/project_coordination/HPC_JOB_LEDGER.csv").Hash
& "$repo/scripts/controller/Reconcile-InterruptedTurn.ps1" -Workspace $r -CheckpointPath "$r/checkpoint.json" -RunId '315b7bd6-8d75-4d6a-912d-2aa0f2a54dc4' -MonitoringEvidence "$r/evidence/acceptance.json" -MonitoringReport 'report.md' -NextAction 'Read-only diagnosis; no execution'
. "$r/scripts/controller/Controller-Recovery.ps1"
$s=Read-ControllerCheckpoint "$r/checkpoint.json"
if($s.turn -ne 17 -or $s.state -ne 'COMPLETED' -or $s.response -or $s.reconciliation.scientific_completion){throw 'Closeout fabricated scientific completion'}
'PASS monitoring-only closeout retains turn and empty response'
if((Get-FileHash "$r/project_coordination/HPC_JOB_LEDGER.csv").Hash -cne $before){throw 'Ledger changed'}
'PASS once-only accounting unchanged'
$caught=$false;try{& "$repo/scripts/controller/Reconcile-InterruptedTurn.ps1" -Workspace $r -CheckpointPath "$r/checkpoint.json" -RunId '315b7bd6-8d75-4d6a-912d-2aa0f2a54dc4' -MonitoringEvidence "$r/evidence/acceptance.json" -MonitoringReport 'report.md'}catch{$caught=$true}
if(-not $caught){throw 'Duplicate reconciliation accepted'}
'PASS duplicate closeout rejected'
(Get-Item "$r/evidence/original-blocked-checkpoint.json").IsReadOnly=$false; Add-Content "$r/evidence/original-blocked-checkpoint.json" 'tampered';$caught=$false
try{Assert-ControllerDispatchCheckpoint $r $s}catch{$caught=$true}
if(-not $caught){throw 'Tampered original accepted'}
'PASS altered archived failure blocks restart'
'ALL 4 TURN17 CHECKS PASS; synthetic fixture only'
