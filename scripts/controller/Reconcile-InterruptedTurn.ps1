[CmdletBinding()]
param(
    [string]$Workspace = "D:\Master thesis\Adaptive remeshing",
    [string]$RunId = "dbb0e4b9-d64c-4385-87fb-3ad0a3321a6e",
    [string]$Status = "INTERRUPTED_TURN_PROGRESS_WATCHDOG_RECONCILED",
    [string]$NextAction = "Dispatch Turn 13 in fresh AGY conversation: verify executable Abaqus UEL state-initialization pathway on Candidate C2; never duplicate PBS submissions",
    [string]$MonitoringEvidence = '',
    [string]$MonitoringReport = '',
    [string]$CheckpointPath = ''
)

$ErrorActionPreference = 'Stop'
. (Join-Path $Workspace 'scripts/controller/Controller-Recovery.ps1')

if(-not $CheckpointPath){$CheckpointPath=Join-Path $env:USERPROFILE 'OpenClawPAD/controller_turn_checkpoint.json'}
if (-not (Test-Path -LiteralPath $checkpointPath)) {
    throw "Checkpoint file not found: $checkpointPath"
}

# 1. Read existing checkpoint
$existing = Read-ControllerCheckpoint $checkpointPath
if ([string]::IsNullOrWhiteSpace($RunId)) {
    $RunId = [string]$existing.run_id
}
if ($existing.run_id -ne $RunId) {
    throw "Checkpoint run ID mismatch: expected $RunId, got $($existing.run_id)"
}
if ($existing.state -ne 'BLOCKED') {
    throw "Checkpoint is not in BLOCKED state: $($existing.state)"
}

if($MonitoringEvidence){
    $owner=Get-Content (Join-Path $Workspace 'project_coordination/ACTIVE_SESSION.json') -Raw|ConvertFrom-Json
    if(-not $owner.active -or $owner.agent -ne 'codex' -or $owner.task_id -ne 'TURN17-EVIDENCE-RECONCILIATION'){throw 'Owned Turn17 reconciliation required'}
    if($RunId -cne '315b7bd6-8d75-4d6a-912d-2aa0f2a54dc4' -or $existing.turn -ne 17 -or $existing.task_id -cne 'F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE'){throw 'Exact interrupted monitoring identity required'}
    $e=Get-Content -LiteralPath $MonitoringEvidence -Raw|ConvertFrom-Json
    if($e.job_id -cne '1419488.mmaster02' -or $e.scheduler_observation.run_count -ne 1 -or $e.scheduler_observation.state -ne 'F' -or $e.classification -notin @('PHYSICAL_PASS','PHYSICAL_FAIL','INSUFFICIENT_EVIDENCE')){throw 'Authentic terminal monitoring evidence required'}
    $reportPath=Join-Path $Workspace $MonitoringReport
    if(-not(Test-Path $reportPath)){throw 'Monitoring reconciliation report required'}
    $archive=Join-Path (Split-Path $MonitoringEvidence -Parent) 'original-blocked-checkpoint.json'
    if(-not(Test-Path $archive) -or (Get-FileHash $archive).Hash -cne (Get-FileHash $CheckpointPath).Hash){throw 'Original blocked checkpoint backup mismatch'}
    $existing.state='COMPLETED' # Maintenance monitoring closeout only, never solver acceptance.
    $existing.conversation_id=''
    $existing|Add-Member response '' -Force
    $existing.block_reason=''
    $existing.next_safe_action=$NextAction
    $existing|Add-Member next_instruction $NextAction -Force
    $existing|Add-Member reconciliation ([pscustomobject]@{
        status='INTERRUPTED_TURN_PROGRESS_WATCHDOG_RECONCILED';original_checkpoint=$archive;original_sha256=(Get-FileHash $archive).Hash
        original_status='BLOCKED';original_failure='AGY_EMPTY_OUTPUT';scientific_completion=$false;antigravity_response_fabricated=$false
        monitoring_outcome=$e.classification;monitoring_job_id=$e.job_id;session_report=$MonitoringReport;session_report_sha256=(Get-FileHash $reportPath).Hash
        monitoring_evidence=$MonitoringEvidence;monitoring_evidence_sha256=(Get-FileHash $MonitoringEvidence).Hash
        hpc_ledger_sha256=(Get-FileHash (Join-Path $Workspace 'project_coordination/HPC_JOB_LEDGER.csv')).Hash;reconciled_by='codex';reconciled_at=[DateTimeOffset]::Now.ToString('o')
    }) -Force
    Assert-ControllerDispatchCheckpoint $Workspace $existing
    Write-ControllerCheckpoint $CheckpointPath $existing
    Assert-ControllerDispatchCheckpoint $Workspace (Read-ControllerCheckpoint $CheckpointPath)
    Write-Output 'TURN17_MONITORING_RECONCILED_WITHOUT_REPLAY'
    return
}

# 2. Archive original blocked checkpoint
$backupsDir = Join-Path $env:USERPROFILE 'OpenClawPAD/backups'
if (-not (Test-Path -LiteralPath $backupsDir)) {
    $null = New-Item -ItemType Directory -Path $backupsDir -Force
}
$archivePath = Join-Path $backupsDir "checkpoint-$RunId-interrupted.json"
Copy-Item -LiteralPath $checkpointPath -Destination $archivePath -Force
$archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash

# 3. Verify session report
$sessionReportRel = if ($existing.session_report) {
    [string]$existing.session_report
} else {
    $matchedReports = @(Get-ChildItem -Path (Join-Path $Workspace 'project_coordination/sessions') -Filter "*$RunId.md" | Select-Object -ExpandProperty Name)
    if ($matchedReports.Count -gt 0) {
        "project_coordination/sessions/$($matchedReports[0])"
    } else {
        "project_coordination/sessions/2026-10-21_gemini-antigravity_F1597_$RunId.md"
    }
}
$sessionReportPath = Join-Path $Workspace $sessionReportRel
if (-not (Test-Path -LiteralPath $sessionReportPath)) {
    throw "Session report not found: $sessionReportPath"
}
$sessionReportHash = (Get-FileHash -LiteralPath $sessionReportPath -Algorithm SHA256).Hash

# 4. Verify bootstrap record
$bootstrapRecordRel = if ($existing.bootstrap_record_path) {
    $root = [IO.Path]::GetFullPath($Workspace).TrimEnd([char[]]'\/') + [IO.Path]::DirectorySeparatorChar
    $fullBoot = [IO.Path]::GetFullPath($existing.bootstrap_record_path)
    if ($fullBoot.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
        $fullBoot.Substring($root.Length).Replace('\', '/')
    } else {
        "project_coordination/controller/turn-$RunId.json"
    }
} else {
    "project_coordination/controller/turn-$RunId.json"
}
$bootstrapRecordPath = Join-Path $Workspace $bootstrapRecordRel
if (-not (Test-Path -LiteralPath $bootstrapRecordPath)) {
    throw "Bootstrap record not found: $bootstrapRecordPath"
}
$bootstrapRecordHash = (Get-FileHash -LiteralPath $bootstrapRecordPath -Algorithm SHA256).Hash

# 5. Verify HPC ledger
$hpcLedgerPath = Join-Path $Workspace 'project_coordination/HPC_JOB_LEDGER.csv'
if (-not (Test-Path -LiteralPath $hpcLedgerPath)) {
    throw "HPC ledger not found: $hpcLedgerPath"
}
$hpcLedgerHash = (Get-FileHash -LiteralPath $hpcLedgerPath -Algorithm SHA256).Hash

# 6. Resolve clean next instruction
$loopStatePath = Join-Path $env:USERPROFILE 'OpenClawPAD/antigravity_loop_state.json'
$cleanInstruction = ''
if (Test-Path -LiteralPath $loopStatePath) {
    $loopState = Get-Content -LiteralPath $loopStatePath -Raw | ConvertFrom-Json
    if ($loopState.next_instruction) {
        $cleanInstruction = ($loopState.next_instruction -replace "^Writing\r?\n", "").Trim()
    }
}
if ([string]::IsNullOrWhiteSpace($cleanInstruction) -and $existing.next_instruction) {
    $cleanInstruction = ($existing.next_instruction -replace "^Writing\r?\n", "").Trim()
}

# 7. Reconcile checkpoint
# Scientific accounting: Turn 12 completed cleanly; Turn 13 was interrupted in flight without durable scientific deliverables.
# Retain turn=12 as the completed baseline so that on resume StartTurn = turn + 1 = 13.
$reconciled = $existing
$reconciled.state = 'COMPLETED'
$reconciled.turn = 12
$reconciled.stop_reason = 'RECONCILED'
$reconciled.block_reason = ''
$reconciled.conversation_id = ''  # Invalidate tainted conversation
$reconciled.next_safe_action = $NextAction
if (-not [string]::IsNullOrWhiteSpace($cleanInstruction)) {
    if ($reconciled.PSObject.Properties['next_instruction']) {
        $reconciled.next_instruction = $cleanInstruction
    } else {
        $reconciled | Add-Member -NotePropertyName next_instruction -NotePropertyValue $cleanInstruction -Force
    }
}

$reconciliationRecord = [ordered]@{
    status = $Status
    original_checkpoint = $archivePath
    original_sha256 = $archiveHash
    run_id = $RunId
    task_id = $existing.task_id
    session_report = $sessionReportRel
    session_report_sha256 = $sessionReportHash
    bootstrap_record = $bootstrapRecordRel
    bootstrap_record_sha256 = $bootstrapRecordHash
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
if (Test-Path -LiteralPath $loopStatePath) {
    $loopState = Get-Content -LiteralPath $loopStatePath -Raw | ConvertFrom-Json
    $loopState.completed_turn = 12
    $loopState.conversation_id = ''  # Fresh conversation on next dispatch
    $loopState.loop_status = 'PENDING_NEXT_TURN'
    $loopState.last_updated = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $loopState.action = 'INTERRUPTED_TURN_RECONCILED'
    $loopState.tier = 'CONTROLLER'
    if (-not [string]::IsNullOrWhiteSpace($cleanInstruction)) {
        $loopState.next_instruction = $cleanInstruction
    }
    $loopJson = $loopState | ConvertTo-Json -Depth 6
    [IO.File]::WriteAllText($loopStatePath, $loopJson, [Text.UTF8Encoding]::new($false))
    Write-Host "Updated loop state: completed_turn=12, conversation_id cleared, loop_status=PENDING_NEXT_TURN." -ForegroundColor Green
}

# 9. Validate with Assert-ControllerDispatchCheckpoint
$checkRead = Read-ControllerCheckpoint $checkpointPath
Assert-ControllerDispatchCheckpoint $Workspace $checkRead

Write-Host "Checkpoint $RunId reconciled successfully." -ForegroundColor Green
Write-Host "Archive: $archivePath (SHA: $archiveHash)"
Write-Host "Reconciliation Status: $($checkRead.reconciliation.status)"
Write-Host "Verified Next Turn: $([int]$checkRead.turn + 1)"

