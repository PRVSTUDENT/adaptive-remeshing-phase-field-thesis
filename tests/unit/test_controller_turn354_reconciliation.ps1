# Unit regression test: Turn 354 historical checkpoint evidence-based reconciliation
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')

$root = Join-Path ([IO.Path]::GetTempPath()) ('turn354-reconcile-test-' + [guid]::NewGuid().ToString('N'))
foreach ($folder in @('project_coordination', 'project_coordination/sessions', 'project_coordination/controller', 'results/validation', 'openclawpad', 'openclawpad/backups')) {
    [void](New-Item -ItemType Directory -Path (Join-Path $root $folder) -Force)
}

function Put([string]$Rel, [string]$Text) {
    [IO.File]::WriteAllText((Join-Path $root $Rel), $Text, [Text.UTF8Encoding]::new($false))
}
function Check([bool]$Okay, [string]$Message) {
    if (-not $Okay) { throw "FAIL: $Message" }
    Write-Host "PASS: $Message"
}

$runId = '8beba6cd-fad9-4b50-b7b1-c62258b7b3e7'
$sessionReportRel = "project_coordination/sessions/2026-10-30_gemini-antigravity_F1597_$runId.md"
$bootstrapRecordRel = "project_coordination/controller/turn-$runId.json"

# Copy or create identical test fixtures from repository
$realSessionReport = Get-Content -LiteralPath (Join-Path $repo $sessionReportRel) -Raw
Put $sessionReportRel $realSessionReport

$realBootstrapRecord = Get-Content -LiteralPath (Join-Path $repo $bootstrapRecordRel) -Raw
Put $bootstrapRecordRel $realBootstrapRecord

$realHpcLedger = Get-Content -LiteralPath (Join-Path $repo 'project_coordination/HPC_JOB_LEDGER.csv') -Raw
Put 'project_coordination/HPC_JOB_LEDGER.csv' $realHpcLedger

Put 'project_coordination/ACTIVE_TASK.json' '{"task_id":"F1597-CORRECT-PACKAGE72-STATE-TRANSFER","status":"BLOCKED_SCIENTIFIC_REVIEW","completed_operations":["evaluate_mode1_package148_state_transfer_r4"]}'
Put 'project_coordination/CURRENT_STATE.md' 'Turn 354 test state.'
Put 'project_coordination/ACTIVE_SESSION.json' '{"active":false,"agent":"codex","task_id":"PACKAGE148-R4-KKT-INDEPENDENT-DIAGNOSIS"}'

$testCheckpointPath = Join-Path $root 'openclawpad/controller_turn_checkpoint.json'
$testLoopStatePath = Join-Path $root 'openclawpad/antigravity_loop_state.json'
$testBackupsDir = Join-Path $root 'openclawpad/backups'

# Create blocked checkpoint replicating Turn 354
$blockedState = [ordered]@{
    schema = 1
    run_id = $runId
    turn = 354
    state = 'BLOCKED'
    block_reason = 'Response incomplete, explicitly blocked, or repository session not released'
    stop_reason = 'BLOCKED'
    task_id = 'F1597-CORRECT-PACKAGE72-STATE-TRANSFER'
    operation_id = 'evaluate_mode1_package148_state_transfer_r4'
    task_type = 'RESEARCH_PREPARATION'
    session_report = $sessionReportRel
    bootstrap_record_path = Join-Path $root $bootstrapRecordRel
    initial_session_active = $false
    repository_commit = '2da5376aea1dfd8cb684f1eaf9d242648a913030'
    recovery_count = 0
    process_id = 23324
    started_at = '2026-10-30T15:08:55.8272364+00:00'
    updated_at = '2026-10-30T15:20:54.7782944+00:00'
    sources = @{}
    pbs_receipts = @()
    execution_accounting = @{ attempts = 1; max_attempts = 1 }
    session = @{ active = $false }
    conversation_id = '35b03c9f-15c9-4521-8a6c-c63313223e36'
}
Write-ControllerCheckpoint $testCheckpointPath ([pscustomobject]$blockedState)

# Create loop state replicating Turn 353
$loopState = [ordered]@{
    completed_turn = 353
    conversation_id = '35b03c9f-15c9-4521-8a6c-c63313223e36'
    loop_status = 'PENDING_NEXT_TURN'
    workspace = $root
    last_updated = '2026-10-30 16:08:55'
}
Put 'openclawpad/antigravity_loop_state.json' ($loopState | ConvertTo-Json -Depth 5)

# Test 1: Prior to reconciliation, Assert-ControllerDispatchCheckpoint throws BLOCKED
$initialBlocked = $false
try {
    $cp = Read-ControllerCheckpoint $testCheckpointPath
    Assert-ControllerDispatchCheckpoint $root $cp
} catch {
    $initialBlocked = $_.Exception.Message -match 'Response incomplete, explicitly blocked, or repository session not released'
}
Check $initialBlocked 'Historical BLOCKED checkpoint fails dispatch closed prior to reconciliation'

# Test 2: Run Reconcile-Turn354BlockedCheckpoint.ps1
$reconcileScript = Join-Path $repo 'scripts/controller/Reconcile-Turn354BlockedCheckpoint.ps1'
& $reconcileScript -Workspace $root -RunId $runId -CheckpointPath $testCheckpointPath -LoopStatePath $testLoopStatePath -BackupsDir $testBackupsDir

# Test 3: Reconciled checkpoint passes Assert-ControllerDispatchCheckpoint
$reconciledCp = Read-ControllerCheckpoint $testCheckpointPath
Check ($reconciledCp.state -eq 'COMPLETED') 'Reconciled checkpoint state is COMPLETED'
Check ($reconciledCp.turn -eq 354) 'Reconciled checkpoint turn is 354'
Check ($reconciledCp.stop_reason -eq 'RECONCILED') 'Reconciled checkpoint stop_reason is RECONCILED'
Check ([string]::IsNullOrEmpty($reconciledCp.block_reason)) 'Reconciled checkpoint block_reason is cleared'
Check ([string]::IsNullOrEmpty($reconciledCp.conversation_id)) 'Reconciled checkpoint conversation_id is cleared for fresh dispatch'
Check ($reconciledCp.reconciliation.status -eq 'INTERRUPTED_TURN_PROGRESS_WATCHDOG_RECONCILED') 'Reconciliation status is INTERRUPTED_TURN_PROGRESS_WATCHDOG_RECONCILED'

$dispatchPassed = $true
try {
    Assert-ControllerDispatchCheckpoint $root $reconciledCp
} catch {
    $dispatchPassed = $false
}
Check $dispatchPassed 'Reconciled checkpoint passes Assert-ControllerDispatchCheckpoint without exception'

# Test 4: Archive exists and SHA256 matches
$archiveFile = Join-Path $testBackupsDir "checkpoint-$runId-interrupted.json"
Check (Test-Path -LiteralPath $archiveFile) 'Archive backup of original checkpoint exists'
$archHash = (Get-FileHash -LiteralPath $archiveFile -Algorithm SHA256).Hash
Check ($archHash -eq $reconciledCp.reconciliation.original_sha256) 'Archived original checkpoint hash matches reconciliation record'

# Test 5: Reconciled loop state is updated to turn 354
$updatedLoopState = Get-Content -LiteralPath $testLoopStatePath -Raw | ConvertFrom-Json
Check ($updatedLoopState.completed_turn -eq 354) 'Loop state completed_turn advanced to 354'
Check ([string]::IsNullOrEmpty($updatedLoopState.conversation_id)) 'Loop state conversation_id cleared'
Check ($updatedLoopState.action -eq 'INTERRUPTED_TURN_RECONCILED') 'Loop state action recorded as INTERRUPTED_TURN_RECONCILED'

# Test 6: Invariant guard: tampering with original checkpoint archive causes Assert to fail closed
$tamperedArchive = $reconciledCp
$tamperedArchive.reconciliation.original_sha256 = 'TAMPERED_HASH_VALUE'
$tamperedPath = Join-Path $root 'tampered_checkpoint.json'
Write-ControllerCheckpoint $tamperedPath $tamperedArchive
$tamperBlocked = $false
try {
    Assert-ControllerDispatchCheckpoint $root (Read-ControllerCheckpoint $tamperedPath)
} catch {
    $tamperBlocked = $_.Exception.Message -match 'reconciled historical evidence missing or changed'
}
Check $tamperBlocked 'Tampered archive hash causes Assert-ControllerDispatchCheckpoint to fail closed'

# Test 7: Invariant guard: tampering with session report causes Assert to fail closed
$tamperedReport = $reconciledCp
$tamperedReport.reconciliation.original_sha256 = $archHash
$tamperedReport.reconciliation.session_report_sha256 = 'TAMPERED_REPORT_HASH'
Write-ControllerCheckpoint $tamperedPath $tamperedReport
$reportTamperBlocked = $false
try {
    Assert-ControllerDispatchCheckpoint $root (Read-ControllerCheckpoint $tamperedPath)
} catch {
    $reportTamperBlocked = $_.Exception.Message -match 'session report evidence changed'
}
Check $reportTamperBlocked 'Tampered session report causes Assert-ControllerDispatchCheckpoint to fail closed'

# Test 8: Invariant guard: tampering with HPC ledger causes Assert to fail closed
$tamperedHpc = $reconciledCp
$tamperedHpc.reconciliation.session_report_sha256 = (Get-FileHash -LiteralPath (Join-Path $root $sessionReportRel)).Hash
$tamperedHpc.reconciliation.hpc_ledger_sha256 = 'TAMPERED_HPC_HASH'
Write-ControllerCheckpoint $tamperedPath $tamperedHpc
$hpcTamperBlocked = $false
try {
    Assert-ControllerDispatchCheckpoint $root (Read-ControllerCheckpoint $tamperedPath)
} catch {
    $hpcTamperBlocked = $_.Exception.Message -match 'HPC job ledger changed unexpectedly'
}
Check $hpcTamperBlocked 'Tampered HPC ledger causes Assert-ControllerDispatchCheckpoint to fail closed'

Write-Host "ALL TURN 354 RECONCILIATION REGRESSION TESTS PASSED."
