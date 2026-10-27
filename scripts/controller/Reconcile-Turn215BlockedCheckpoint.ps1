[CmdletBinding()]
param(
    [string]$Workspace = "D:\Master thesis\Adaptive remeshing",
    [string]$RunId = "eae8fa6c-4467-4d9a-a08d-ba1dbf88b65d",
    [string]$Status = "INTERRUPTED_TURN_PROGRESS_WATCHDOG_RECONCILED",
    [string]$NextAction = "Advance F1597-CORRECT-PACKAGE72-STATE-TRANSFER: Formalize discretization-aware energy baseline and present Package 115 evidence for supervisor/governance review before next remeshing cycle"
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
    "project_coordination/sessions/2026-10-27_gemini-antigravity_F1597_$RunId.md"
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

# 6. Formulate clean next instruction for Turn 216
$turn216Instruction = @"
TURN 216 — METHOD C: GOVERNANCE REVIEW OF DISCRETIZATION-AWARE ENERGY BASELINE BEFORE NEXT REMESHING CYCLE

Continue F1597-CORRECT-PACKAGE72-STATE-TRANSFER.

ONE BOUNDED SCIENTIFIC INVESTIGATION: Synthesize the quantitative Package 115 state-transfer and Package 113/114 energy deconstruction evidence for supervisor/governance review to formalize the discretization-aware energy baseline (accounting for mesh convergence of the regularized AT2 fracture energy functional) prior to initiating downstream adaptive remeshing cycles.

JOB-FIRST / REPORT-AFTER. Reconcile all existing jobs first. Preserve immutable Method C threshold discipline: retain C1_2_STEP2_ENERGY_GATE_FAILED without post-hoc relaxation. Zero duplicate PBS submissions.

1. Bootstrap and reconcile
Follow AGENTS.md; acquire the exclusive lock. Read live project_coordination task/session/ledger records, Package 113, 114, and 115 complete solver summaries, authentic Package 76 Increment-79 donor evidence and immutable source hashes.
Verified predecessors:
- Package 113 Job 1417682.mmaster02: Exit 0, RF2 = 187.39 N (+0.71%), E_tot = 0.216714 mJ (+2.008%), C1_2_STEP2_ENERGY_GATE_FAILED.
- Package 114 Job 1417689.mmaster02: Exit 0, MISESERI companion recovered (4422 elems, 284 marked, pre-peak valid).
- Package 115 Job 1417751.mmaster02: Exit 0, 7 cycles converged stationary state, RF2 = 185.79 N (-0.15%), 0 healing nodes, E_tot = 0.216760 mJ (+2.030%).

2. Formalize Discretization-Aware Energy Baseline
Structure the multi-mesh energy baseline formalization distinguishing:
- Elastic strain energy continuity (virtually identical: -0.153% difference between transferred and donor states).
- AT2 regularized fracture energy functional scaling with element size h (accounting for over 100% of the observed net energy increase from C3 h=2.5 um to C4 h_min=0.606 um).
- Document why post-hoc threshold relaxation is avoided while physical conservation holds.

3. Closeout
Record verified findings in the session report, update coordination ledgers, run unit tests, and cleanly release the session lock.
End with: Finished
"@

# 7. Reconcile checkpoint
# Scientific accounting: Turn 215 completed evidence-only recovery of interrupted Turn 214.
# Retain turn=215 as the completed baseline so that on resume StartTurn = turn + 1 = 216.
$reconciled = $existing
$reconciled.state = 'COMPLETED'
$reconciled.turn = 215
$reconciled.recovery_count = 0
$reconciled.stop_reason = 'RECONCILED'
$reconciled.block_reason = ''
$reconciled.conversation_id = ''  # Invalidate tainted conversation
$reconciled.next_safe_action = $NextAction
if ($reconciled.PSObject.Properties['next_instruction']) {
    $reconciled.next_instruction = $turn216Instruction
} else {
    $reconciled | Add-Member -NotePropertyName next_instruction -NotePropertyValue $turn216Instruction -Force
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
    $loopState.completed_turn = 215
    $loopState.conversation_id = ''  # Fresh conversation on next dispatch
    $loopState.loop_status = 'PENDING_NEXT_TURN'
    $loopState.last_updated = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $loopState.action = 'INTERRUPTED_TURN_RECONCILED'
    $loopState.tier = 'CONTROLLER'
    $loopState.next_instruction = $turn216Instruction
    $loopJson = $loopState | ConvertTo-Json -Depth 6
    [IO.File]::WriteAllText($loopStatePath, $loopJson, [Text.UTF8Encoding]::new($false))
    Write-Host "Updated loop state: completed_turn=215, conversation_id cleared, loop_status=PENDING_NEXT_TURN." -ForegroundColor Green
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
