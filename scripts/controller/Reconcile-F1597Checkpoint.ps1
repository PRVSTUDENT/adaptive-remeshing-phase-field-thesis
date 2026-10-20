[CmdletBinding()]
param([string]$Workspace='D:/Master thesis/Adaptive remeshing',
      [string]$Checkpoint="$env:USERPROFILE/OpenClawPAD/controller_turn_checkpoint.json")
$ErrorActionPreference='Stop'
. (Join-Path $Workspace 'scripts/controller/Controller-Recovery.ps1')
function Git-Verified([string[]]$Arguments){
    $output=& git -C $Workspace @Arguments
    if($LASTEXITCODE -ne 0){throw 'Historical Git evidence verification failed'}
    return ($output|Out-String).Trim()
}
$s=Read-ControllerCheckpoint $Checkpoint
if($s.state -eq 'COMPLETED' -and $s.reconciliation.status -eq 'COMPLETED_SCIENCE_CREDENTIAL_REPAIR_VERIFIED'){Assert-ControllerDispatchCheckpoint $Workspace $s;'ALREADY_RECONCILED';return}
if($s.state -ne 'BLOCKED' -or -not $s.scientific_step_completed -or $s.scientific_commit -ne '0720bbd1901eb17fb932f0fa4412d5bc34343dfd' -or
    $s.run_id -ne '91e48944-19c2-4e7a-b3bc-57609b2f6bda' -or $s.block_reason -notmatch 'POST_AGY.*ID_TOKEN_MISSING'){throw 'Unrecognized checkpoint; no reconciliation permitted'}
if(Get-Process agy -ErrorAction SilentlyContinue){throw 'Live AGY process; reconciliation forbidden'}
$e=Get-ControllerEvidence $Workspace
if($e.session.active -and $e.session.agent -ne 'codex'){throw 'Foreign session active'}
$op=Resolve-ControllerOperation $e.task $Workspace
if(@($e.task.completed_operations) -notcontains 'mapped_frozen_history_lower_bound_kkt_probe'){throw 'Completed operation missing'}
$record=Get-Content -LiteralPath $s.bootstrap_record_path -Raw|ConvertFrom-Json
if($record.stage -ne 'COMPLETE' -or -not(Test-ControllerScientificCheckpoint $Workspace $s -Historical)){throw 'Historical scientific result not independently verified'}
if($e.task.task_id -ne $s.task_id -or $e.task.scientific_checkpoint.artifact -ne $record.scientific_checkpoint.artifact -or
    $e.task.scientific_checkpoint.sha256 -ne $record.scientific_checkpoint.sha256){throw 'Active task does not preserve the completed scientific basis'}
foreach($path in @('project_coordination/HPC_JOB_LEDGER.csv','project_coordination/MODE1_EXECUTION_LEDGER.json')){
    if($e.sources.$path -ne $s.sources.$path){throw 'Once-only accounting changed; do not reconcile automatically'}
}
$artifact=$record.scientific_checkpoint.artifact
if((Git-Verified @('rev-parse',($s.scientific_commit+':'+$artifact))) -ne (Git-Verified @('hash-object','--',$artifact))){throw 'Scientific artifact differs from preserved commit'}
$null=Git-Verified @('merge-base','--is-ancestor',$s.scientific_commit,'HEAD')
$repair='7186c5c880a714786866445c83f88c069a89d664'
$null=Git-Verified @('merge-base','--is-ancestor',$repair,'HEAD')
$report='project_coordination/sessions/2026-10-20_codex_credential_lifecycle.md'
if((Git-Verified @('rev-parse',($repair+':'+$report))) -ne (Git-Verified @('hash-object','--',$report))){throw 'Credential repair report differs from preserved commit'}
& (Join-Path $Workspace 'scripts/controller/Invoke-AgyCredentialValidation.ps1') -Profile account3
$originalHash=(Get-FileHash -LiteralPath $Checkpoint).Hash
$archive=Join-Path (Split-Path $Checkpoint) ('backups/checkpoint-'+$s.run_id+'-before-dispatch-reconciliation.json')
if(Test-Path -LiteralPath $archive){if((Get-FileHash -LiteralPath $archive).Hash -ne $originalHash){throw 'Conflicting checkpoint archive'}}else{
    New-Item -ItemType Directory -Path (Split-Path $archive) -Force|Out-Null
    Copy-Item -LiteralPath $Checkpoint -Destination $archive
}
$s|Add-Member reconciliation ([pscustomobject]@{status='COMPLETED_SCIENCE_CREDENTIAL_REPAIR_VERIFIED';original_checkpoint=$archive;original_sha256=$originalHash;scientific_commit=$s.scientific_commit;credential_repair_commit=$repair;credential_report_sha256=(Get-FileHash -LiteralPath (Join-Path $Workspace $report)).Hash;reconciled_at=[datetimeoffset]::Now.ToString('o');next_operation=$op.id}) -Force
# The earlier failure is preserved verbatim in block_reason and in the exact archive.
$s.state='COMPLETED';$s.next_safe_action='Dispatch only the new registered mechanical/history investigation; never replay completed KKT'
Write-ControllerCheckpoint $Checkpoint $s
'RECONCILED_COMPLETED_SCIENCE_AND_VERIFIED_CREDENTIAL_REPAIR; historical checkpoint and block reason preserved'
