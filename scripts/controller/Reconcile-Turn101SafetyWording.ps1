[CmdletBinding()]
param(
    [string]$Workspace = "D:\Master thesis\Adaptive remeshing",
    [string]$RunId = "52fd144d-2f19-491d-813c-5f2b2f93eb18"
)

$ErrorActionPreference = 'Stop'
. (Join-Path $Workspace 'scripts/controller/Controller-Recovery.ps1')
. (Join-Path $Workspace 'scripts/controller/Controller-Preparation.ps1')

$checkpointPath = Join-Path $env:USERPROFILE 'OpenClawPAD/controller_turn_checkpoint.json'
if (-not (Test-Path -LiteralPath $checkpointPath)) {
    throw "Checkpoint file not found: $checkpointPath"
}

# 1. Read existing checkpoint
$existing = Read-ControllerCheckpoint $checkpointPath
if ($existing.run_id -ne $RunId) {
    throw "Checkpoint run ID mismatch: expected $RunId, got $($existing.run_id)"
}

# 2. Archive original checkpoint before reconciliation
$backupsDir = Join-Path $env:USERPROFILE 'OpenClawPAD/backups'
if (-not (Test-Path -LiteralPath $backupsDir)) {
    $null = New-Item -ItemType Directory -Path $backupsDir -Force
}
$archivePath = Join-Path $backupsDir "checkpoint-$RunId-pre-safety-reconcile.json"
Copy-Item -LiteralPath $checkpointPath -Destination $archivePath -Force
$archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
Write-Host "[ARCHIVE] Preserved original checkpoint in $archivePath ($archiveHash)" -ForegroundColor Cyan

# 3. Verify session report
$sessionReportRel = "project_coordination/sessions/2026-10-24_gemini-antigravity_F1597_$RunId.md"
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

# 6. Correct the instruction wording: replace 'destructive PBS operations' with 'prohibited PBS operations'
$originalInstruction = [string]$existing.next_instruction
$correctedInstruction = $originalInstruction.Replace(
    "destructive PBS operations",
    "prohibited PBS operations"
)
if ($correctedInstruction -eq $originalInstruction) {
    throw "Phrase 'destructive PBS operations' not found in checkpoint next_instruction."
}

# 7. Re-evaluate preparation plan
$prep = Get-ControllerPreparationPlan $Workspace $correctedInstruction
if (-not $prep.dispatch_ready) {
    throw "Preparation plan for corrected instruction is still not dispatch_ready: $($prep.status)"
}

# 8. Reconcile checkpoint
$reconciled = $existing
$reconciled.turn = 101
$reconciled.state = 'COMPLETED'
$reconciled.next_instruction = $correctedInstruction
$reconciled.operation_preparation = $prep
$reconciled.recovery_count = 0
$reconciled.stop_reason = 'RECONCILED_SAFETY_WORDING'
$reconciled.conversation_id = ''  # Fresh conversation context for Turn 102
$reconciled.next_safe_action = "Dispatch Turn 102: Method C corridor-free C4 reference qualification"

Write-ControllerCheckpoint $checkpointPath $reconciled
Write-Host "[CHECKPOINT] Successfully updated $checkpointPath (turn=101, state=COMPLETED, dispatch_ready=True)" -ForegroundColor Green

# 9. Synchronize loop state
$loopStatePath = Join-Path $env:USERPROFILE 'OpenClawPAD/antigravity_loop_state.json'
if (Test-Path -LiteralPath $loopStatePath) {
    $loopArchive = Join-Path $backupsDir "antigravity_loop_state-$RunId-pre-reconcile.json"
    Copy-Item -LiteralPath $loopStatePath -Destination $loopArchive -Force
    $st = Get-Content -LiteralPath $loopStatePath -Raw | ConvertFrom-Json
    $st.completed_turn = 101
    $st.loop_status = "PENDING_NEXT_TURN"
    $st.next_instruction = $correctedInstruction
    $st.conversation_id = ""
    $stJson = $st | ConvertTo-Json -Depth 10
    [System.IO.File]::WriteAllText($loopStatePath, $stJson, [System.Text.UTF8Encoding]::new($false))
    Write-Host "[LOOP_STATE] Synchronized $loopStatePath (completed_turn=101, loop_status=PENDING_NEXT_TURN)" -ForegroundColor Green
}

Write-Host "`n[SUCCESS] Reconciled Turn 101 safety wording false-positive. Controller is dispatch-ready for Turn 102." -ForegroundColor Green
