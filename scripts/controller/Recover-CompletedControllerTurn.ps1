[CmdletBinding()]
param([string]$Workspace='D:\Master thesis\Adaptive remeshing',
      [Parameter(Mandatory)][string]$ArchiveDirectory,
      [Parameter(Mandatory)][string]$RunId,
      [Parameter(Mandatory)][string]$MaintenanceSessionHash)
$ErrorActionPreference='Stop'
. (Join-Path $Workspace 'scripts/controller/Controller-Recovery.ps1')
$sessionPath=Join-Path $Workspace 'project_coordination/ACTIVE_SESSION.json'
if((Get-FileHash $sessionPath).Hash -cne $MaintenanceSessionHash){throw 'BLOCKED: maintenance owner changed'}
$session=Get-Content $sessionPath -Raw|ConvertFrom-Json
if(-not $session.active -or $session.agent -ne 'codex' -or $session.task_id -ne 'RECOVER-4040433D-OWNERSHIP'){throw 'BLOCKED: explicit owned maintenance session required'}
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$mutex=[Threading.Mutex]::new($false,('Global\AdaptiveRemeshing.AgyController.'+$sid))
$locked=$false
try {
    try{$locked=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$locked=$true}
    if(-not $locked){throw 'BLOCKED: live autonomous controller owns workspace'}
    if(Get-Process agy -ErrorAction SilentlyContinue){throw 'BLOCKED: live AGY process; reconcile owner first'}
    $originalPath=Join-Path $ArchiveDirectory 'controller_turn_checkpoint.json'
    $original=Read-ControllerCheckpoint $originalPath
    if($original.run_id -cne $RunId -or $original.state -ne 'BLOCKED'){throw 'BLOCKED: original run identity mismatch'}
    if(Get-Process -Id $original.process_id -ErrorAction SilentlyContinue){throw 'BLOCKED: original worker still exists'}
    $sourceArchives=@{
        'scripts/controller/Controller-Recovery.ps1'=(Join-Path $ArchiveDirectory 'Controller-Recovery.ps1')
        'tests/unit/test_controller_hpc_ledger_growth.ps1'=(Join-Path $ArchiveDirectory 'test_controller_hpc_ledger_growth.ps1')
    }
    $proof=Get-ControllerCompletedPreparationEvidence $Workspace $original $sourceArchives
    $livePath=Join-Path $env:USERPROFILE 'OpenClawPAD/controller_turn_checkpoint.json'
    if((Get-FileHash $livePath).Hash -cne (Get-FileHash $originalPath).Hash){throw 'BLOCKED: runtime checkpoint changed since archive'}
    $original.state='COMPLETED'
    $original.block_reason=''
    $original.conversation_id=''
    $original | Add-Member next_instruction '' -Force
    $original.next_safe_action='Evaluate authentic Package160 exact-load reference and R6 physical gates; never replay the completed controller-repair turn.'
    $original | Add-Member reconciliation ([pscustomobject]@{
        status='COMPLETED_RELEASED_TURN_RECONCILED';original_checkpoint=$originalPath
        original_sha256=(Get-FileHash $originalPath).Hash;source_archives=$sourceArchives;proof=$proof
        hpc_ledger_sha256=$original.sources.'project_coordination/HPC_JOB_LEDGER.csv'
    }) -Force
    Assert-ControllerDispatchCheckpoint $Workspace $original
    if((Get-FileHash $sessionPath).Hash -cne $MaintenanceSessionHash){throw 'BLOCKED: ownership changed during reconciliation'}
    Write-ControllerCheckpoint $livePath $original
    Write-Output ('COMPLETED_TURN_RECOVERED_WITHOUT_REPLAY: '+$RunId)
} finally {
    if($locked){$mutex.ReleaseMutex()};$mutex.Dispose()
}
