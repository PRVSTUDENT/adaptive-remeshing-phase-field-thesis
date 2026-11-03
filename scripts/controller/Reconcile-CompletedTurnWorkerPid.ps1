[CmdletBinding()]
param(
    [string]$Workspace = 'D:\Master thesis\Adaptive remeshing',
    [string]$CheckpointPath = '',
    [string]$ExpectedCheckpointHash = '3F8D57704BA4629E9587C57F4EBC1CC2D68A9803A605C8B9B04963690FB8AB3E',
    [string]$ExpectedRunId = '158e8df8-db39-4d5e-8033-0f22b618fbf4',
    [int]$ExpectedTurn = 10,
    [string]$BackupDir = '',
    [string]$MaintenanceSessionTask = ''
)

$ErrorActionPreference = 'Stop'
$recoveryPath = Join-Path $PSScriptRoot 'Controller-Recovery.ps1'
if (-not (Test-Path -LiteralPath $recoveryPath)) {
    $recoveryPath = Join-Path $Workspace 'scripts/controller/Controller-Recovery.ps1'
}
. $recoveryPath

if (-not $CheckpointPath) {
    $CheckpointPath = Join-Path $env:USERPROFILE 'OpenClawPAD/controller_turn_checkpoint.json'
}
if (-not (Test-Path -LiteralPath $CheckpointPath)) {
    throw "BLOCKED: checkpoint file not found: $CheckpointPath"
}

# 1. Require controller mutex ownership
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$mutexName = 'Global\AdaptiveRemeshing.AgyController.' + $sid
$mutex = [Threading.Mutex]::new($false, $mutexName)
$locked = $false
try {
    try { $locked = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $locked = $true }
    if (-not $locked) {
        throw 'BLOCKED: live autonomous controller owns workspace'
    }

    # 2. Require inactive repository session (or explicit maintenance session match)
    $sessionPath = Join-Path $Workspace 'project_coordination/ACTIVE_SESSION.json'
    if (Test-Path -LiteralPath $sessionPath) {
        $session = Get-Content -LiteralPath $sessionPath -Raw | ConvertFrom-Json
        if ($session.active) {
            if (-not $MaintenanceSessionTask -or $session.task_id -cne $MaintenanceSessionTask) {
                throw "BLOCKED: repository session is active for task $($session.task_id); close or reconcile session before maintenance"
            }
        }
    }

    # 3. Verify original checkpoint hash
    $actualHash = (Get-FileHash -LiteralPath $CheckpointPath -Algorithm SHA256).Hash
    if ($ExpectedCheckpointHash -and ($actualHash -cne $ExpectedCheckpointHash)) {
        throw "BLOCKED: checkpoint hash mismatch; expected $ExpectedCheckpointHash, got $actualHash"
    }

    # 4. Read checkpoint and verify identity
    $checkpoint = Read-ControllerCheckpoint $CheckpointPath
    if ($checkpoint.state -ne 'COMPLETED') {
        throw "BLOCKED: checkpoint state is not COMPLETED: $($checkpoint.state)"
    }
    if ($ExpectedRunId -and ($checkpoint.run_id -ne $ExpectedRunId)) {
        throw "BLOCKED: checkpoint run_id mismatch; expected $ExpectedRunId, got $($checkpoint.run_id)"
    }
    if ($ExpectedTurn -and ([int]$checkpoint.turn -ne $ExpectedTurn)) {
        throw "BLOCKED: checkpoint turn mismatch; expected $ExpectedTurn, got $($checkpoint.turn)"
    }

    # 5. Require no active research worker for the checkpoint
    $originalWorkerPid = [int]$checkpoint.process_id
    if ($originalWorkerPid -ne 0) {
        if (Get-Process -Id $originalWorkerPid -ErrorAction SilentlyContinue) {
            throw "BLOCKED: worker process $originalWorkerPid is still active"
        }
    }

    # 6. Verify exact instruction preservation
    if (-not $checkpoint.next_instruction -or [string]::IsNullOrWhiteSpace($checkpoint.next_instruction)) {
        throw 'BLOCKED: next_instruction is missing or empty in completed checkpoint'
    }
    $instructionTextHash = Get-ControllerTextHash $checkpoint.next_instruction

    # 7. Create immutable backup
    $backupsDir = if ($BackupDir) { $BackupDir } else { Join-Path (Split-Path $CheckpointPath -Parent) 'backups' }
    if (-not (Test-Path -LiteralPath $backupsDir)) {
        $null = New-Item -ItemType Directory -Path $backupsDir -Force
    }
    $archivePath = Join-Path $backupsDir ("checkpoint-" + $checkpoint.run_id + "-completed-worker-pid-reconciled.json")
    Copy-Item -LiteralPath $CheckpointPath -Destination $archivePath -Force
    $archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    if ($archiveHash -cne $actualHash) {
        throw 'BLOCKED: backup archive hash does not match original checkpoint'
    }

    # 8. Reconcile stale worker PID to 0 and invalidate conversation
    $reconciled = $checkpoint
    $reconciled.process_id = 0
    if ($reconciled.PSObject.Properties['conversation_id']) {
        $reconciled.conversation_id = ''  # Fresh clean conversation on Turn 11
    } else {
        $reconciled | Add-Member -NotePropertyName conversation_id -NotePropertyValue '' -Force
    }
    if ($reconciled.PSObject.Properties['stop_reason']) {
        $reconciled.stop_reason = 'RECONCILED'
    } else {
        $reconciled | Add-Member -NotePropertyName stop_reason -NotePropertyValue 'RECONCILED' -Force
    }
    if ($reconciled.PSObject.Properties['block_reason']) {
        $reconciled.block_reason = ''
    } else {
        $reconciled | Add-Member -NotePropertyName block_reason -NotePropertyValue '' -Force
    }

    $reconciliationRecord = [ordered]@{
        status = 'COMPLETED_WORKER_PID_RECONCILED'
        original_checkpoint = $archivePath
        original_sha256 = $archiveHash
        original_worker_pid = $originalWorkerPid
        worker_verified_dead = $true
        run_id = $reconciled.run_id
        turn = [int]$reconciled.turn
        task_id = $reconciled.task_id
        original_instruction_hash = $reconciled.original_instruction_hash
        next_instruction_sha256 = $instructionTextHash
        reconciled_by = 'gemini-antigravity'
        reconciled_at = [DateTimeOffset]::UtcNow.ToString('o')
    }

    if ($reconciled.PSObject.Properties['reconciliation']) {
        $reconciled.reconciliation = [pscustomobject]$reconciliationRecord
    } else {
        $reconciled | Add-Member -NotePropertyName reconciliation -NotePropertyValue ([pscustomobject]$reconciliationRecord) -Force
    }

    # 9. Atomic checkpoint write
    Write-ControllerCheckpoint $CheckpointPath $reconciled

    # 10. Verify canonical checkpoint reader and Assert-ControllerDispatchCheckpoint
    $readBack = Read-ControllerCheckpoint $CheckpointPath
    Assert-ControllerDispatchCheckpoint $Workspace $readBack

    if ($readBack.process_id -ne 0) {
        throw 'BLOCKED: reconciled checkpoint process_id is not 0'
    }
    if ((Get-ControllerTextHash $readBack.next_instruction) -cne $instructionTextHash) {
        throw 'BLOCKED: next_instruction was modified during reconciliation'
    }

    $newHash = (Get-FileHash -LiteralPath $CheckpointPath -Algorithm SHA256).Hash

    [PSCustomObject]@{
        status = 'RECONCILED'
        run_id = $readBack.run_id
        turn = [int]$readBack.turn
        original_worker_pid = $originalWorkerPid
        reconciled_worker_pid = $readBack.process_id
        original_checkpoint_sha256 = $actualHash
        reconciled_checkpoint_sha256 = $newHash
        backup_archive = $archivePath
        next_instruction_preserved = $true
        dispatch_checkpoint_assert_pass = $true
    }
} finally {
    if ($locked) {
        $mutex.ReleaseMutex()
    }
    $mutex.Dispose()
}
