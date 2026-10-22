[CmdletBinding()]
param(
    [string]$Workspace = "D:\Master thesis\Adaptive remeshing",
    [string]$RunId = "88c0997c-5343-47cc-a839-319765c0764b",
    [string]$Status = "INTERRUPTED_TURN_FILE_REPLACE_RECONCILED",
    [string]$NextAction = "Dispatch Turn 31: await and evaluate completed PBS job 1416368.mmaster02 (Package 82 staggered mechanical-phase-field re-equilibration diagnostic), extract multi-step solver telemetry and ODB field outputs, verify KKT complementarity and reaction force continuity under Method C Gate C1-1, and evaluate readiness for sequential adaptive remeshing cycles."
)

$ErrorActionPreference = 'Stop'
. (Join-Path $Workspace 'scripts/controller/Controller-Recovery.ps1')

$checkpointPath = Join-Path $env:USERPROFILE 'OpenClawPAD/controller_turn_checkpoint.json'
if (-not (Test-Path -LiteralPath $checkpointPath)) {
    throw "Checkpoint file not found: $checkpointPath"
}

# 1. Read existing checkpoint
$existing = Read-ControllerCheckpoint $checkpointPath
if ($existing.run_id -ne $RunId) {
    throw "Checkpoint run ID mismatch: expected $RunId, got $($existing.run_id)"
}
if ($existing.state -notin @('RUNNING', 'CHECKPOINTED', 'BLOCKED')) {
    throw "Checkpoint is not in an interrupted/running/blocked state: $($existing.state)"
}

# 2. Archive original interrupted checkpoint
$backupsDir = Join-Path $env:USERPROFILE 'OpenClawPAD/backups'
if (-not (Test-Path -LiteralPath $backupsDir)) {
    $null = New-Item -ItemType Directory -Path $backupsDir -Force
}
$archivePath = Join-Path $backupsDir "checkpoint-$RunId-interrupted.json"
Copy-Item -LiteralPath $checkpointPath -Destination $archivePath -Force
$archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash

# 3. Verify session report
$sessionReportRel = "project_coordination/sessions/2026-10-22_gemini-antigravity_F1597_$RunId.md"
$sessionReportPath = Join-Path $Workspace $sessionReportRel
if (-not (Test-Path -LiteralPath $sessionReportPath)) {
    throw "Session report not found: $sessionReportPath"
}
$sessionReportHash = (Get-FileHash -LiteralPath $sessionReportPath -Algorithm SHA256).Hash

# 4. Verify bootstrap record
$bootstrapRecordRel = "project_coordination/controller/turn-$RunId.json"
$bootstrapRecordPath = Join-Path $Workspace $bootstrapRecordRel
if (-not (Test-Path -LiteralPath $bootstrapRecordPath)) {
    throw "Bootstrap record not found: $bootstrapRecordPath"
}
$bootstrapRecordHash = (Get-FileHash -LiteralPath $bootstrapRecordPath -Algorithm SHA256).Hash

# 5. Verify preparation artifact
$prepRel = "results/validation/preparation-$RunId.json"
$prepPath = Join-Path $Workspace $prepRel
if (-not (Test-Path -LiteralPath $prepPath)) {
    throw "Preparation artifact not found: $prepPath"
}
$prepHash = (Get-FileHash -LiteralPath $prepPath -Algorithm SHA256).Hash

# 6. Verify HPC ledger
$hpcLedgerPath = Join-Path $Workspace 'project_coordination/HPC_JOB_LEDGER.csv'
if (-not (Test-Path -LiteralPath $hpcLedgerPath)) {
    throw "HPC ledger not found: $hpcLedgerPath"
}
$hpcLedgerText = Get-Content -LiteralPath $hpcLedgerPath -Raw
if ($hpcLedgerText -notmatch '1416368\.mmaster02') {
    throw "HPC ledger does not contain Package 82 job ID 1416368.mmaster02"
}
$hpcLedgerHash = (Get-FileHash -LiteralPath $hpcLedgerPath -Algorithm SHA256).Hash

# 7. Reconcile checkpoint
$reconciled = $existing
$reconciled.state = 'COMPLETED'
$reconciled.stop_reason = 'RECONCILED'
$reconciled.block_reason = ''
$reconciled.process_id = 0
$reconciled.conversation_id = ''  # Fresh conversation on Turn 31
$reconciled | Add-Member -NotePropertyName next_instruction -NotePropertyValue $NextAction -Force
$reconciled.next_safe_action = $NextAction

$reconciliationRecord = [ordered]@{
    status = $Status
    original_checkpoint = $archivePath
    original_sha256 = $archiveHash
    run_id = $RunId
    task_id = $existing.task_id
    pbs_job_id = "1416368.mmaster02"
    session_report = $sessionReportRel
    session_report_sha256 = $sessionReportHash
    bootstrap_record = $bootstrapRecordRel
    bootstrap_record_sha256 = $bootstrapRecordHash
    preparation_artifact = $prepRel
    preparation_artifact_sha256 = $prepHash
    hpc_ledger_sha256 = $hpcLedgerHash
    scientific_progress_fabricated = $false
    next_operation = if ($existing.scientific_operation) { [string]$existing.scientific_operation } else { 'research_preparation' }
    reconciled_at = [DateTimeOffset]::UtcNow.ToString('o')
}

if ($reconciled.PSObject.Properties['reconciliation']) {
    $reconciled.reconciliation = [pscustomobject]$reconciliationRecord
} else {
    $reconciled | Add-Member -NotePropertyName reconciliation -NotePropertyValue ([pscustomobject]$reconciliationRecord) -Force
}

# Write updated checkpoint
Write-ControllerCheckpoint $checkpointPath $reconciled

# 8. Reconcile antigravity_loop_state.json
$loopStatePath = Join-Path $env:USERPROFILE 'OpenClawPAD/antigravity_loop_state.json'
if (Test-Path -LiteralPath $loopStatePath) {
    $loopState = Get-Content -LiteralPath $loopStatePath -Raw | ConvertFrom-Json
    $loopState.completed_turn = 30
    $loopState.conversation_id = ''  # Fresh conversation on next dispatch
    $loopState.loop_status = 'PENDING_NEXT_TURN'
    $loopState.last_updated = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $loopState.action = 'FILE_REPLACE_RECONCILED'
    $loopState.tier = 'CONTROLLER'
    $loopState.next_instruction = $NextAction
    $loopJson = $loopState | ConvertTo-Json -Depth 6
    [IO.File]::WriteAllText($loopStatePath, $loopJson, [Text.UTF8Encoding]::new($false))
    Write-Host "Updated loop state: completed_turn=30, conversation_id cleared." -ForegroundColor Green
}

# 9. Validate with Assert-ControllerDispatchCheckpoint
$checkRead = Read-ControllerCheckpoint $checkpointPath
Assert-ControllerDispatchCheckpoint $Workspace $checkRead

Write-Host "Checkpoint $RunId reconciled successfully." -ForegroundColor Green
Write-Host "Archive: $archivePath (SHA: $archiveHash)"
Write-Host "Reconciliation Status: $($checkRead.reconciliation.status)"
