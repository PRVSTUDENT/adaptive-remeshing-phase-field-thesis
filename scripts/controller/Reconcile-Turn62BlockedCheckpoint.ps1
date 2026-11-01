[CmdletBinding()]
param(
    [string]$Workspace = "D:\Master thesis\Adaptive remeshing",
    [string]$RunId = "a0d95a00-70dc-459b-925f-a76b0865e723",
    [string]$Status = "INTERRUPTED_TURN_PROGRESS_WATCHDOG_RECONCILED",
    [string]$NextAction = "Dispatch Turn 62 in fresh AGY conversation: reconcile Package 96-R3 dual-job evidence and diagnose Step 4 forward healing; never duplicate PBS submissions"
)

$ErrorActionPreference = 'Stop'
. (Join-Path $Workspace 'scripts/controller/Controller-Recovery.ps1')

$checkpointPath = Join-Path $env:USERPROFILE 'OpenClawPAD/controller_turn_checkpoint.json'
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

# 2. Archive original blocked checkpoint and loop state
$backupsDir = Join-Path $env:USERPROFILE 'OpenClawPAD/backups'
if (-not (Test-Path -LiteralPath $backupsDir)) {
    $null = New-Item -ItemType Directory -Path $backupsDir -Force
}

$archivePath = Join-Path $backupsDir "checkpoint-$RunId-interrupted.json"
Copy-Item -LiteralPath $checkpointPath -Destination $archivePath -Force
$archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash

$loopStatePath = Join-Path $env:USERPROFILE 'OpenClawPAD/antigravity_loop_state.json'
$loopArchive = Join-Path $backupsDir "antigravity_loop_state-$RunId.json"
if (Test-Path -LiteralPath $loopStatePath) {
    Copy-Item -LiteralPath $loopStatePath -Destination $loopArchive -Force
    $loopArchiveHash = (Get-FileHash -LiteralPath $loopArchive -Algorithm SHA256).Hash
} else {
    $loopArchiveHash = ''
}

$activityLogPath = Join-Path $env:USERPROFILE 'OpenClawPAD/controller_activity.log'
$activityArchive = Join-Path $backupsDir "controller_activity-$RunId.log"
if (Test-Path -LiteralPath $activityLogPath) {
    Copy-Item -LiteralPath $activityLogPath -Destination $activityArchive -Force
    $activityArchiveHash = (Get-FileHash -LiteralPath $activityArchive -Algorithm SHA256).Hash
} else {
    $activityArchiveHash = ''
}

# 3. Verify session report
$sessionReportRel = if ($existing.session_report) {
    [string]$existing.session_report
} else {
    "project_coordination/sessions/2026-10-23_gemini-antigravity_F1597_$RunId.md"
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

# 6. Formulate clean next instruction for Turn 62
$turn62Instruction = @"
TURN 62 — METHOD C: PACKAGE 96-R3 DUAL-JOB RECONCILIATION AND HEALING DIAGNOSIS

Continue F1597-CORRECT-PACKAGE72-STATE-TRANSFER.

ONE BOUNDED OBJECTIVE: Complete the scientific reconciliation of the two Package 96-R3 executions (Jobs 1416910.mmaster02 and 1416912.mmaster02), audit the physical origin of the 84 healing points observed during Step 4 forward continuation, and formulate the minimal repair without replaying completed simulations.

1. Bootstrap
Read AGENTS.md, START_HERE.md, authoritative task/session/checkpoint, HPC and execution ledgers. Acquire session lock and reconcile live scheduler once.
Verified predecessors:
- Package 96-R3 Job 1416910.mmaster02: input hash 24b8ed917d57cc02ccb4e06bf530ebd64ff2c22c96754ad86143df8d8340ceb5, completed Exit 0.
- Package 96-R3 Job 1416912.mmaster02: input hash b1afc638d2be6889a1733606e2ae12711db7d973c04740be050078a49a8f0611, completed Exit 0.
- Current on-disk solver evaluation pkg96_r3_solver_evaluation.json reflects Job 1416912 (overwrote scratch outputs): Gate 1 (force) PASS (1.15%), Gate 2 (energy) PASS (0.41%), Gate 3 (bounds) PASS (0 overshoots), Gate 5 (history) PASS, Gate 6 (softening) PASS, Gate 4 (irreversibility) FAIL (0 healing in Step 3, 84 healing points in Step 4 forward continuation).

2. Reconcile Dual-Job Evidence
Formally document in project coordination that Job 1416912's execution overwrote Job 1416910's scratch files, and update ledger accounting to reflect both completed Exit 0 runs with their respective input hashes.

3. Diagnose 84 Step 4 Healing Points
Investigate the physical and discrete origin of the 84 healing Gauss points in Step 4. Check whether these points reside in elements adjacent to the 56 free nodes in the advancing crack corridor A, and determine whether a modified active-set formulation or continuation incrementation eliminates flank relaxation while allowing genuine crack advancement.

4. Closeout
Record verified findings in the session report, update coordination ledgers, run unit tests, and cleanly release the session lock.
End with: Finished
"@

# 7. Reconcile checkpoint
# Scientific accounting: Turn 61 was the substantive turn; Turn 62 was interrupted at step 29 without deliverables.
# Retain turn=61 as the completed baseline so that on resume StartTurn = turn + 1 = 62.
$reconciled = $existing
$reconciled.state = 'COMPLETED'
$reconciled.turn = 61
$reconciled.recovery_count = 0
$reconciled.stop_reason = 'RECONCILED'
$reconciled.block_reason = ''
$reconciled.conversation_id = ''  # Invalidate tainted conversation
$reconciled.next_safe_action = $NextAction
if ($reconciled.PSObject.Properties['next_instruction']) {
    $reconciled.next_instruction = $turn62Instruction
} else {
    $reconciled | Add-Member -NotePropertyName next_instruction -NotePropertyValue $turn62Instruction -Force
}

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
Write-ControllerCheckpoint $checkpointPath $reconciled

# 8. Reconcile antigravity_loop_state.json
if (Test-Path -LiteralPath $loopStatePath) {
    $loopState = Get-Content -LiteralPath $loopStatePath -Raw | ConvertFrom-Json
    $loopState.completed_turn = 61
    $loopState.conversation_id = ''  # Fresh conversation on next dispatch
    $loopState.loop_status = 'PENDING_NEXT_TURN'
    $loopState.last_updated = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $loopState.action = 'INTERRUPTED_TURN_RECONCILED'
    $loopState.tier = 'CONTROLLER'
    $loopState.next_instruction = $turn62Instruction
    $loopJson = $loopState | ConvertTo-Json -Depth 6
    [IO.File]::WriteAllText($loopStatePath, $loopJson, [Text.UTF8Encoding]::new($false))
    Write-Host "Updated loop state: completed_turn=61, conversation_id cleared, loop_status=PENDING_NEXT_TURN." -ForegroundColor Green
}

# 9. Validate with Assert-ControllerDispatchCheckpoint
$checkRead = Read-ControllerCheckpoint $checkpointPath
Assert-ControllerDispatchCheckpoint $Workspace $checkRead

Write-Host "Checkpoint $RunId reconciled successfully." -ForegroundColor Green
Write-Host "Archive: $archivePath (SHA: $archiveHash)"
Write-Host "Loop Archive: $loopArchive (SHA: $loopArchiveHash)"
Write-Host "Activity Archive: $activityArchive (SHA: $activityArchiveHash)"
Write-Host "Reconciliation Status: $($checkRead.reconciliation.status)"
Write-Host "Verified Next Turn: $([int]$checkRead.turn + 1)"
