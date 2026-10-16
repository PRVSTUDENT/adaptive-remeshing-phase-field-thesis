[CmdletBinding()]
param([Parameter(Mandatory)][ValidateSet('restart_prod','restart_diag')][string]$Job,[switch]$DryRun)
$ErrorActionPreference='Stop'
$repo='D:\Master thesis\Adaptive remeshing'
$package=Join-Path $repo 'models/pandey_kumar_mode1/48_method_c_stage_c1_0_restart_positive_control'
$batch=Get-Content (Join-Path $package 'METHOD_C_RESTART_RECOVERY_AUTHORIZATION.json') -Raw|ConvertFrom-Json
$candidate=@($batch.jobs|Where-Object {$_.id -eq $Job})
if($candidate.Count -ne 1){throw 'Job absent or ambiguous'}
$candidate=$candidate[0]
$remote='qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_package48_restart_control/'+$candidate.pbs
$expected='powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "'+$remote+'"'
if($candidate.command -cne $expected){throw 'Command differs from exact guarded adapter'}
if($DryRun){Write-Output "DRY_RUN: $Job; gate consumes once before submission; notify_submitted after accepted PBS ID; no remote operations";return}
Push-Location $repo
try{
 # Run the actual gate, including atomic reservation, before crossing SSH boundary.
 $payload=@{toolCall=@{args=@{CommandLine=$candidate.command}}}|ConvertTo-Json -Depth 5 -Compress
 $decision=$payload|& powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\qsub-safety-gate.ps1|ConvertFrom-Json
 if($decision.decision -ne 'allow'){throw $decision.reason}
 $result=& powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand $remote
 $status=$LASTEXITCODE
 # Print immediately, even if notification fails. Never repeat qsub on uncertainty.
 Write-Output $result
 if($status -ne 0){throw 'Submission returned nonzero; inspect scheduler and ledgers before any further action; permit remains consumed'}
 $id=($result|Out-String).Trim()
 if($id -notmatch '^\d+\.mmaster02$'){throw 'Unrecognized scheduler response; reconcile scheduler before any further action; no retry'}
 $name=if($Job -eq 'restart_prod'){'M1_MB_RST_PROD'}else{'M1_MB_RST_DIAG'}
 # Source real helper, which resolves NOTIFICATION_CONFIG (mode600); both transports.
 $notification='source /scratch9/pr21vyci/runs/mode1_package48_restart_control/job_notifications.sh; notification_load_config; notify_submitted '+$id+' '+$name+' entry_imfdfkmq'
 & powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand $notification
 if($LASTEXITCODE -ne 0){throw "PBS accepted $id; SUBMITTED notification failed; preserve job and do not resubmit"}
}finally{Pop-Location}
