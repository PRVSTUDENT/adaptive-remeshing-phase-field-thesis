[CmdletBinding()]
param(
    [string]$Workspace = "D:\Master thesis\Adaptive remeshing",
    [string]$RunId = "8beba6cd-fad9-4b50-b7b1-c62258b7b3e7",
    [string]$Status = "INTERRUPTED_TURN_PROGRESS_WATCHDOG_RECONCILED",
    [string]$NextAction = "Independently review serializer-only correction; qualify frozen-UEL one-quad nonuniform-history initialization/phase-operator parity before any corrected transfer. No new R5, C1-2, retry or autonomous restart; reconcile historical checkpoint and verify compute alerts.",
    [string]$CheckpointPath = "",
    [string]$LoopStatePath = "",
    [string]$BackupsDir = ""
)

$ErrorActionPreference = 'Stop'
$recoveryPath = Join-Path $PSScriptRoot 'Controller-Recovery.ps1'
if (-not (Test-Path -LiteralPath $recoveryPath)) {
    $recoveryPath = Join-Path $Workspace 'scripts/controller/Controller-Recovery.ps1'
}
. $recoveryPath

if ([string]::IsNullOrWhiteSpace($CheckpointPath)) {
    $CheckpointPath = Join-Path $env:USERPROFILE 'OpenClawPAD/controller_turn_checkpoint.json'
}
if (-not (Test-Path -LiteralPath $CheckpointPath)) {
    throw "Checkpoint file not found: $CheckpointPath"
}

if ([string]::IsNullOrWhiteSpace($LoopStatePath)) {
    $LoopStatePath = Join-Path $env:USERPROFILE 'OpenClawPAD/antigravity_loop_state.json'
}

if ([string]::IsNullOrWhiteSpace($BackupsDir)) {
    $BackupsDir = Join-Path $env:USERPROFILE 'OpenClawPAD/backups'
}

# 1. Read existing checkpoint
$existing = Read-ControllerCheckpoint $CheckpointPath
if ([string]::IsNullOrWhiteSpace($RunId)) {
    $RunId = [string]$existing.run_id
}
if ($existing.run_id -ne $RunId) {
    throw "Checkpoint run ID mismatch: expected $RunId, got $($existing.run_id)"
}
if ($existing.state -ne 'BLOCKED') {
    throw "Checkpoint is not in BLOCKED state: $($existing.state)"
}

# 2. Archive original blocked checkpoint and loop state
if (-not (Test-Path -LiteralPath $BackupsDir)) {
    $null = New-Item -ItemType Directory -Path $BackupsDir -Force
}

$archivePath = Join-Path $BackupsDir "checkpoint-$RunId-interrupted.json"
Copy-Item -LiteralPath $CheckpointPath -Destination $archivePath -Force
$archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash

$loopArchive = Join-Path $BackupsDir "antigravity_loop_state-$RunId.json"
if (Test-Path -LiteralPath $LoopStatePath) {
    Copy-Item -LiteralPath $LoopStatePath -Destination $loopArchive -Force
    $loopArchiveHash = (Get-FileHash -LiteralPath $loopArchive -Algorithm SHA256).Hash
} else {
    $loopArchive = ''
    $loopArchiveHash = ''
}

$activityLogPath = Join-Path (Split-Path $CheckpointPath -Parent) 'controller_activity.log'
$activityArchive = Join-Path $BackupsDir "controller_activity-$RunId.log"
if (Test-Path -LiteralPath $activityLogPath) {
    Copy-Item -LiteralPath $activityLogPath -Destination $activityArchive -Force
    $activityArchiveHash = (Get-FileHash -LiteralPath $activityArchive -Algorithm SHA256).Hash
} else {
    $activityArchive = ''
    $activityArchiveHash = ''
}

# 3. Verify session report
$sessionReportRel = if ($existing.session_report) {
    [string]$existing.session_report
} else {
    "project_coordination/sessions/2026-10-30_gemini-antigravity_F1597_$RunId.md"
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

# 6. Formulate clean next instruction for Turn 355
$turn355Instruction = @"
CONTROLLER TURN 355 — PACKAGE 148: INDEPENDENT INITIAL-STATE SERIALIZER CORRECTION & PARITY QUALIFICATION

TASK_ID: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
TASK_TYPE: RESEARCH_PREPARATION
OPERATION_ID: research_preparation

ONE OBJECTIVE: Independently verify the 7+8+3 TYPE=SOLUTION card serializer correction against the verified R4 history-slot shift, and qualify frozen-UEL one-quad nonuniform-history initialization and phase-operator parity before any corrected transfer.

JOB-FIRST / REPORT-AFTER. Reconcile existing evidence first. Preserve all predecessor receipts:
- Package 148 R1 (1418787.mmaster02): Exit 1 (Python compatibility).
- Package 148 R2 (1418843.mmaster02): Exit 1 (Extraction failure).
- Package 148 R3 (1418872.mmaster02): Exit 1 (Driver precision mismatch; mechanical solve Exit 0 RF2 0.19% PASS, E_tot 0.14% PASS).
- Package 148 R4 (1418902.mmaster02): Exit 1 (Terminal phase KKT iteration limit 20 reached; no physical acceptance, no blind retry).

1. Bootstrap and reconcile
Follow AGENTS.md; acquire exclusive lock. Read live project_coordination task, session, ledger, and artifact records.
Confirm HEAD at cd1b1ce3 and verify offline R4 diagnostic evidence in results/validation/package148_r4_kkt/ and tests/unit/test_package148_r4_state_card_diagnosis.py.

2. Verify Serializer Correction
Confirm that the 9-field TYPE=SOLUTION encoding in R4 incorrectly shifted committed history H9..H12 into slots H2..H4 and zeroed all others, inducing an unphysical 20-phase oscillation.
Verify that the corrected 7+8+3 card format restores exact history-to-slot mapping and matches the frozen UEL initial condition requirements.

3. Offline Parity Verification & Bounds
Perform falsifiable unit checks ensuring:
- Bitwise frozen UEL f42_mixed_uel.for (CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6) remains strictly unmodified.
- No new R5 submission, no Stage C1-2 advancement, and no loop restart until serializer and phase-operator parity are verified.

4. Closeout
Record verified findings in the session report, update ledgers, run unit tests, and cleanly release the session lock.
End with: Finished
"@

# 7. Reconcile checkpoint
# Scientific accounting: Turn 354 completed research preparation / blocker diagnosis cleanly.
# Retain turn=354 as the completed baseline so that on resume StartTurn = turn + 1 = 355.
$reconciled = $existing
$reconciled.state = 'COMPLETED'
$reconciled.turn = 354
$reconciled.recovery_count = 0

function Set-Prop($obj, [string]$name, $val) {
    if ($obj.PSObject.Properties[$name]) {
        $obj.$name = $val
    } else {
        $obj | Add-Member -NotePropertyName $name -NotePropertyValue $val -Force
    }
}

Set-Prop $reconciled 'stop_reason' 'RECONCILED'
Set-Prop $reconciled 'block_reason' ''
Set-Prop $reconciled 'conversation_id' ''  # Invalidate tainted conversation
Set-Prop $reconciled 'next_safe_action' $NextAction
Set-Prop $reconciled 'next_instruction' $turn355Instruction

$reconciliationRecord = [ordered]@{
    status = $Status
    original_checkpoint = $archivePath
    original_sha256 = $archiveHash
    loop_archive = $loopArchive
    loop_archive_sha256 = $loopArchiveHash
    activity_archive = $activityArchive
    activity_archive_sha256 = $activityArchiveHash
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
Write-ControllerCheckpoint $CheckpointPath $reconciled

# 8. Reconcile antigravity_loop_state.json
if (Test-Path -LiteralPath $LoopStatePath) {
    $loopState = Get-Content -LiteralPath $LoopStatePath -Raw | ConvertFrom-Json
    Set-Prop $loopState 'completed_turn' 354
    Set-Prop $loopState 'conversation_id' ''  # Fresh conversation on next dispatch
    Set-Prop $loopState 'loop_status' 'PENDING_NEXT_TURN'
    Set-Prop $loopState 'last_updated' (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    Set-Prop $loopState 'action' 'INTERRUPTED_TURN_RECONCILED'
    Set-Prop $loopState 'tier' 'CONTROLLER'
    Set-Prop $loopState 'next_instruction' $turn355Instruction
    $loopJson = $loopState | ConvertTo-Json -Depth 6
    [IO.File]::WriteAllText($LoopStatePath, $loopJson, [Text.UTF8Encoding]::new($false))
    Write-Host "Updated loop state: completed_turn=354, conversation_id cleared, loop_status=PENDING_NEXT_TURN." -ForegroundColor Green
}

# 9. Validate with Assert-ControllerDispatchCheckpoint
$checkRead = Read-ControllerCheckpoint $CheckpointPath
Assert-ControllerDispatchCheckpoint $Workspace $checkRead

Write-Host "Checkpoint $RunId reconciled successfully." -ForegroundColor Green
Write-Host "Archive: $archivePath (SHA: $archiveHash)"
Write-Host "Loop Archive: $loopArchive (SHA: $loopArchiveHash)"
Write-Host "Activity Archive: $activityArchive (SHA: $activityArchiveHash)"
Write-Host "Reconciliation Status: $($checkRead.reconciliation.status)"
Write-Host "Verified Next Turn: $([int]$checkRead.turn + 1)"
