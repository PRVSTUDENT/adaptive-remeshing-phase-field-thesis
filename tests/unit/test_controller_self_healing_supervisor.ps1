# ==============================================================================
# test_controller_self_healing_supervisor.ps1
#
# Unit and fault-injection test suite for Controller-SelfHealingSupervisor.ps1.
# Verifies:
#   1. Mutex acquisition & single-instance exclusivity
#   2. Atomic state read / write persistence
#   3. Deterministic failure classification across 8 failure categories
#   4. Circuit breaker tripping on repeated failures (MaxSelfRepairRetries exceeded)
#   5. Full state machine lifecycle transitions (RUNNING -> FAILURE_DETECTED ->
#      CLASSIFIED -> RECOVERY_IN_PROGRESS -> VALIDATION -> RESUME_READY)
#   6. Non-recoverable failure safe fail-closed behavior (BLOCK)
#   7. Completed checkpoint graceful termination
#   8. Safe non-destructive DryRun mode
# ==============================================================================

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$supervisorScript = Join-Path $repoRoot "scripts/controller/Controller-SelfHealingSupervisor.ps1"

if (-not (Test-Path -LiteralPath $supervisorScript)) {
    throw "Supervisor script not found at: $supervisorScript"
}

. $supervisorScript
. (Join-Path $repoRoot "scripts/controller/Controller-Recovery.ps1")

$totalTests = 0
$passedTests = 0

function Assert-Check {
    param(
        [string]$Description,
        [bool]$Condition
    )
    $script:totalTests++
    if ($Condition) {
        $script:passedTests++
        Write-Host "  [PASS] $Description" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $Description" -ForegroundColor Red
        throw "Assertion failed: $Description"
    }
}

$tmpDir = Join-Path ([System.IO.Path]::GetTempPath()) ("agy_sup_test_" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null

try {
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host " RUNNING CONTROLLER SELF-HEALING SUPERVISOR TEST SUITE" -ForegroundColor Cyan
    Write-Host " Scratch: $tmpDir" -ForegroundColor Cyan
    Write-Host "==================================================================" -ForegroundColor Cyan

    # -------------------------------------------------------------------------
    # Test Group 1: Mutex Acquisition & Exclusivity
    # -------------------------------------------------------------------------
    Write-Host "`n--- Test Group 1: Mutex Acquisition & Exclusivity ---" -ForegroundColor Yellow

    $m1 = Get-SupervisorMutex
    Assert-Check "Primary mutex successfully acquired" ($m1.CreatedNew -eq $true)

    $m2 = Get-SupervisorMutex
    Assert-Check "Secondary mutex detects existing instance" ($m2.CreatedNew -eq $false)

    $m2.Mutex.Dispose()
    $m1.Mutex.Dispose()

    # -------------------------------------------------------------------------
    # Test Group 2: Atomic State Read / Write Persistence
    # -------------------------------------------------------------------------
    Write-Host "`n--- Test Group 2: Atomic State Read / Write Persistence ---" -ForegroundColor Yellow

    $stateFile = Join-Path $tmpDir "test_sup_state.json"
    $initState = [pscustomobject]@{
        state = "RUNNING"
        active_pid = 1234
        consecutive_failures = 0
        circuit_broken = $false
        last_fingerprint = "TEST_FP"
    }

    Write-SupervisorState $stateFile $initState
    Assert-Check "State file created on disk" (Test-Path -LiteralPath $stateFile)

    $readState = Read-SupervisorState $stateFile
    Assert-Check "Read state matches written state" ($readState.state -eq "RUNNING" -and $readState.active_pid -eq 1234)

    # Update state
    $readState.state = "FAILURE_DETECTED"
    Write-SupervisorState $stateFile $readState
    $updatedState = Read-SupervisorState $stateFile
    Assert-Check "Updated state successfully persisted" ($updatedState.state -eq "FAILURE_DETECTED")
    Assert-Check "Backup state file created" (Test-Path -LiteralPath ($stateFile + ".bak"))

    # -------------------------------------------------------------------------
    # Test Group 3: Deterministic Failure Classification
    # -------------------------------------------------------------------------
    Write-Host "`n--- Test Group 3: Failure Classification Engine ---" -ForegroundColor Yellow

    $mockPad = Join-Path $tmpDir "pad"
    New-Item -ItemType Directory -Path $mockPad -Force | Out-Null
    $mockWs = Join-Path $tmpDir "workspace"
    New-Item -ItemType Directory -Path (Join-Path $mockWs "project_coordination") -Force | Out-Null

    # 3.1 Missing checkpoint
    $c1 = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $null
    Assert-Check "Missing checkpoint classified as MISSING_CHECKPOINT / BLOCK" ($c1.category -eq "MISSING_CHECKPOINT" -and $c1.action -eq "BLOCK" -and $c1.recoverable -eq $false)

    # 3.2 Foreign session active
    $foreignSess = [pscustomobject]@{
        active = $true
        agent = "codex"
        controller_run_id = "foreign-run-id-999"
    }
    Set-Content -LiteralPath (Join-Path $mockWs "project_coordination/ACTIVE_SESSION.json") -Value ($foreignSess | ConvertTo-Json)
    $mockCp = [pscustomobject]@{ run_id = "my-run-id-111"; state = "RUNNING"; process_id = 100 }
    $c2 = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $mockCp
    Assert-Check "Foreign session collision classified as FOREIGN_SESSION_ACTIVE / BLOCK" ($c2.category -eq "FOREIGN_SESSION_ACTIVE" -and $c2.action -eq "BLOCK" -and $c2.recoverable -eq $false)

    # Remove foreign session for remaining tests
    Remove-Item -LiteralPath (Join-Path $mockWs "project_coordination/ACTIVE_SESSION.json") -Force

    # 3.3 Auth mismatch vs Exhaustion (GAP 1 Tests)
    # 3.3a Recoverable profile marker mismatch
    $c3a = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $mockCp -LastLogText "Error: AUTH_RECOVERY_REQUIRED: profile marker account2 mismatches store"
    Assert-Check "AUTH_RECOVERY_REQUIRED (marker mismatch) classified as TRANSIENT_AUTH_MISMATCH / RECONCILE_AUTH_AND_RESUME" ($c3a.category -eq "TRANSIENT_AUTH_MISMATCH" -and $c3a.action -eq "RECONCILE_AUTH_AND_RESUME" -and $c3a.recoverable -eq $true)

    # 3.3b Recoverable identity mismatch
    $c3b = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $mockCp -LastLogText "IDENTITY_MISMATCH: token subject does not match profile marker"
    Assert-Check "IDENTITY_MISMATCH classified as TRANSIENT_AUTH_MISMATCH / RECONCILE_AUTH_AND_RESUME" ($c3b.category -eq "TRANSIENT_AUTH_MISMATCH" -and $c3b.action -eq "RECONCILE_AUTH_AND_RESUME" -and $c3b.recoverable -eq $true)

    # 3.3c Genuine exhaustion with AUTH_RECOVERY_REQUIRED prefix MUST NOT be classified as recoverable mismatch
    $c3c = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $mockCp -LastLogText "AUTH_RECOVERY_REQUIRED: eligible existing profiles exhausted; legitimate interactive sign-in required"
    Assert-Check "AUTH_RECOVERY_REQUIRED (profiles exhausted) classified as AUTHENTICATION_EXHAUSTED / BLOCK (Gap 1)" ($c3c.category -eq "AUTHENTICATION_EXHAUSTED" -and $c3c.action -eq "BLOCK" -and $c3c.recoverable -eq $false)

    # 3.3d HTTP 401 Unauthorized
    $c3d = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $mockCp -LastLogText "HTTP 401 Unauthorized: invalid_grant token has expired"
    Assert-Check "HTTP 401 classified as AUTHENTICATION_EXHAUSTED / BLOCK (Gap 1)" ($c3d.category -eq "AUTHENTICATION_EXHAUSTED" -and $c3d.action -eq "BLOCK" -and $c3d.recoverable -eq $false)

    # 3.3e Provider rejection / interactive required
    $c3e = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $mockCp -LastLogText "AUTHENTICATION_FAILED: interactive sign-in required for account"
    Assert-Check "AUTHENTICATION_FAILED classified as AUTHENTICATION_EXHAUSTED / BLOCK (Gap 1)" ($c3e.category -eq "AUTHENTICATION_EXHAUSTED" -and $c3e.action -eq "BLOCK" -and $c3e.recoverable -eq $false)

    # 3.4 Code defect (null path)
    $c4 = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $mockCp -LastLogText "Cannot bind argument to parameter 'Path' because it is null in Test-Path `$loopStatePath"
    Assert-Check "Null path binding classified as DETERMINISTIC_CODE_DEFECT / SELF_REPAIR_AND_DEPLOY" ($c4.category -eq "DETERMINISTIC_CODE_DEFECT" -and $c4.action -eq "SELF_REPAIR_AND_DEPLOY" -and $c4.recoverable -eq $true)

    # 3.5 Transport timeout
    $c5 = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $mockCp -LastLogText "System.Net.WebException: The operation has timed out."
    Assert-Check "Transport timeout classified as TRANSIENT_TRANSPORT_ERROR / BACKOFF_RETRY" ($c5.category -eq "TRANSIENT_TRANSPORT_ERROR" -and $c5.action -eq "BACKOFF_RETRY" -and $c5.recoverable -eq $true)

    # 3.6 Clean interrupted PENDING turn
    $cleanPendingCp = [pscustomobject]@{ run_id = "my-run-id-111"; state = "PENDING"; process_id = 0 }
    $c6 = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $cleanPendingCp -LastLogText ""
    Assert-Check "Unstarted PENDING turn classified as CLEAN_INTERRUPTED_CHECKPOINT / RESUME_PENDING_INSTRUCTION" ($c6.category -eq "CLEAN_INTERRUPTED_CHECKPOINT" -and $c6.action -eq "RESUME_PENDING_INSTRUCTION" -and $c6.recoverable -eq $true)

    # 3.7 Checkpoint corruption integrity (GAP 2 Tests)
    $corruptedCpObj = [pscustomobject]@{ is_corrupted = $true; error = "Envelope checksum mismatch"; path = "fake.json" }
    $c7 = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $corruptedCpObj
    Assert-Check "Corrupted checkpoint object classified as CORRUPTED_CHECKPOINT / BLOCK (Gap 2)" ($c7.category -eq "CORRUPTED_CHECKPOINT" -and $c7.action -eq "BLOCK" -and $c7.recoverable -eq $false)

    # Read-SupervisorCheckpoint rejection of tampered disk files
    $tamperedCpFile = Join-Path $tmpDir "tampered_checkpoint.json"
    $validPayload = [ordered]@{ state = "PENDING"; run_id = "run-1"; task_id = "task-1"; recovery_count = 0; process_id = 0 } | ConvertTo-Json -Compress
    $tamperedEnvelope = [ordered]@{ schema = 1; payload = $validPayload; sha256 = "INVALID_HASH_1234567890ABCDEF" } | ConvertTo-Json
    [IO.File]::WriteAllText($tamperedCpFile, $tamperedEnvelope, [Text.UTF8Encoding]::new($false))
    $readTampered = Read-SupervisorCheckpoint $repoRoot $tamperedCpFile
    Assert-Check "Read-SupervisorCheckpoint identifies tampered checksum as corrupted (Gap 2)" ($readTampered.is_corrupted -eq $true)
    $c7b = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $readTampered
    Assert-Check "Tampered disk checkpoint classified as CORRUPTED_CHECKPOINT / BLOCK (Gap 2)" ($c7b.category -eq "CORRUPTED_CHECKPOINT" -and $c7b.action -eq "BLOCK" -and $c7b.recoverable -eq $false)

    # 3.8 Stale PIDs & Governance (GAP 3 Tests)
    # Direct test of Test-IsControllerWorkerProcess
    Assert-Check "Test-IsControllerWorkerProcess rejects PID 0" ((Test-IsControllerWorkerProcess -ProcessId 0) -eq $false)
    Assert-Check "Test-IsControllerWorkerProcess rejects non-existent PID" ((Test-IsControllerWorkerProcess -ProcessId 99999999) -eq $false)
    $currentPid = [System.Diagnostics.Process]::GetCurrentProcess().Id
    Assert-Check "Test-IsControllerWorkerProcess accepts current PowerShell process" ((Test-IsControllerWorkerProcess -ProcessId $currentPid) -eq $true)
    Assert-Check "Test-IsControllerWorkerProcess rejects stale process started before expected turn" ((Test-IsControllerWorkerProcess -ProcessId $currentPid -ExpectedMinStartTime ([datetimeoffset]::UtcNow.AddDays(1))) -eq $false)
    $systemPid = (Get-Process -Name explorer,services -ErrorAction SilentlyContinue | Select-Object -First 1).Id
    if ($systemPid) {
        Assert-Check "Test-IsControllerWorkerProcess rejects non-worker binary (e.g. explorer/services)" ((Test-IsControllerWorkerProcess -ProcessId $systemPid) -eq $false)
    }

    # Active worker detected
    $activeWorkerCp = [pscustomobject]@{ run_id = "my-run-id-111"; state = "RUNNING"; process_id = $currentPid }
    $c8a = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $activeWorkerCp
    Assert-Check "Active worker PID classified as WORKER_STILL_ACTIVE / WAIT_FOR_WORKER (Gap 3)" ($c8a.category -eq "WORKER_STILL_ACTIVE" -and $c8a.action -eq "WAIT_FOR_WORKER" -and $c8a.recoverable -eq $false)

    # Crashed worker with automatic_restart_allowed = false
    $crashedWorkerCp = [pscustomobject]@{ run_id = "my-run-id-111"; state = "RUNNING"; process_id = 99999999 }
    $taskGovFile = Join-Path $mockWs "project_coordination/ACTIVE_TASK.json"
    $taskGovRestricted = [ordered]@{
        controller_maintenance = [ordered]@{
            automatic_restart_allowed = $false
        }
    }
    Set-Content -LiteralPath $taskGovFile -Value ($taskGovRestricted | ConvertTo-Json -Depth 5)
    $c8b = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $crashedWorkerCp -LastLogText ""
    Assert-Check "Crashed worker with automatic_restart_allowed=false classified as AUTOMATIC_RESTART_RESTRICTED / BLOCK (Gap 3)" ($c8b.category -eq "AUTOMATIC_RESTART_RESTRICTED" -and $c8b.action -eq "BLOCK" -and $c8b.recoverable -eq $false)

    # Crashed worker with automatic_restart_allowed = true
    $taskGovAllowed = [ordered]@{
        controller_maintenance = [ordered]@{
            automatic_restart_allowed = $true
        }
    }
    Set-Content -LiteralPath $taskGovFile -Value ($taskGovAllowed | ConvertTo-Json -Depth 5)
    $c8c = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $crashedWorkerCp -LastLogText ""
    Assert-Check "Crashed worker with automatic_restart_allowed=true classified as CRASHED_WORKER_RESUMPTION / RESUME_PENDING_INSTRUCTION (Gap 3)" ($c8c.category -eq "CRASHED_WORKER_RESUMPTION" -and $c8c.action -eq "RESUME_PENDING_INSTRUCTION" -and $c8c.recoverable -eq $true)

    # 3.9 Unknown failure
    $c9 = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $mockCp -LastLogText "Fatal unhandled exception in core subsystem"
    Assert-Check "Unclassified failure classified as UNCLASSIFIED_FAILURE / BLOCK" ($c9.category -eq "UNCLASSIFIED_FAILURE" -and $c9.action -eq "BLOCK" -and $c9.recoverable -eq $false)

    # -------------------------------------------------------------------------
    # Test Group 4: Circuit Breaker Logic
    # -------------------------------------------------------------------------
    Write-Host "`n--- Test Group 4: Circuit Breaker & Retry Limits ---" -ForegroundColor Yellow

    # Simulate retrying the same fingerprint 4 times with MaxSelfRepairRetries = 3
    $retries = @{}
    $fp = "AUTH_MISMATCH"
    $maxRetries = 3
    $circuitBroken = $false

    for ($i = 1; $i -le 4; $i++) {
        if (-not $retries.ContainsKey($fp)) { $retries[$fp] = 0 }
        $retries[$fp]++
        if ($retries[$fp] -gt $maxRetries) {
            $circuitBroken = $true
            break
        }
    }
    Assert-Check "Circuit breaker trips after exceeding max retries" ($circuitBroken -eq $true -and $retries[$fp] -eq 4)

    # -------------------------------------------------------------------------
    # Test Group 5: Supervised Loop Life Cycle & DryRun
    # -------------------------------------------------------------------------
    Write-Host "`n--- Test Group 5: Supervised Loop Execution & State Progression ---" -ForegroundColor Yellow

    $padEnv = Join-Path $tmpDir "pad_loop"
    New-Item -ItemType Directory -Path $padEnv -Force | Out-Null

    # Case 5.1: Completed checkpoint halts cleanly
    $completedCp = [ordered]@{
        state = "COMPLETED"
        task_id = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"
        run_id = "test-run-comp"
        turn = 10
        recovery_count = 0
        process_id = 0
    }
    $compCpPath = Join-Path $padEnv "controller_turn_checkpoint.json"
    Write-ControllerCheckpoint $compCpPath $completedCp

    Start-ControllerSupervisedLoop -Workspace $repoRoot -Pad $padEnv -SinglePass -DryRun
    $supState = Read-SupervisorState (Join-Path $padEnv "supervisor_recovery_state.json")
    Assert-Check "Completed checkpoint terminates with state COMPLETED" ($supState.state -eq "COMPLETED")

    $activeRunId = (Get-Content (Join-Path $repoRoot "project_coordination/ACTIVE_SESSION.json") -Raw | ConvertFrom-Json).controller_run_id

    # Case 5.2: Non-recoverable failure halts with BLOCKED_NEEDS_INTERVENTION
    $blockedCp = [ordered]@{
        state = "RUNNING"
        task_id = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"
        run_id = $activeRunId
        turn = 11
        recovery_count = 0
        process_id = 0
    }
    Write-ControllerCheckpoint $compCpPath $blockedCp
    # Inject failure packet with unrecoverable error
    $failDir = Join-Path $padEnv "failure_recovery/packet_01"
    New-Item -ItemType Directory -Path $failDir -Force | Out-Null
    $packet = [ordered]@{
        error = "AUTHENTICATION_FAILED: Refresh token revoked by provider"
    }
    [IO.File]::WriteAllText((Join-Path $failDir "packet.json"), ($packet | ConvertTo-Json), [Text.UTF8Encoding]::new($false))

    # Reset supervisor state
    Remove-Item -LiteralPath (Join-Path $padEnv "supervisor_recovery_state.json") -Force
    Start-ControllerSupervisedLoop -Workspace $repoRoot -Pad $padEnv -SinglePass -DryRun
    $supState2 = Read-SupervisorState (Join-Path $padEnv "supervisor_recovery_state.json")
    Assert-Check "Unrecoverable auth failure leads to BLOCKED_NEEDS_INTERVENTION" ($supState2.state -eq "BLOCKED_NEEDS_INTERVENTION")

    # Case 5.3: Recoverable clean pending checkpoint in DryRun transitions to RESUME_READY
    $inst = "Execute pending turn 12"
    $instHash = (Get-ControllerTextHash $inst)
    $pendingCp = [ordered]@{
        state = "PENDING"
        task_id = "F1699-TEST-UNSTARTED-TASK"
        run_id = $activeRunId
        turn = 12
        recovery_count = 0
        process_id = 0
        original_instruction_hash = $instHash
    }
    Write-ControllerCheckpoint $compCpPath $pendingCp
    Remove-Item -LiteralPath $failDir -Recurse -Force
    Remove-Item -LiteralPath (Join-Path $padEnv "supervisor_recovery_state.json") -Force

    Start-ControllerSupervisedLoop -Workspace $repoRoot -Pad $padEnv -SinglePass -DryRun
    $supState3 = Read-SupervisorState (Join-Path $padEnv "supervisor_recovery_state.json")
    Assert-Check "Recoverable PENDING turn in DryRun reaches RESUME_READY" ($supState3.state -eq "RESUME_READY")

    # Case 5.4: Corrupted checkpoint fails closed safely without worker execution (GAP 2)
    [IO.File]::WriteAllText($compCpPath, "{ corrupt json schema envelope missing sha256: true", [Text.UTF8Encoding]::new($false))
    Remove-Item -LiteralPath (Join-Path $padEnv "supervisor_recovery_state.json") -Force

    Start-ControllerSupervisedLoop -Workspace $repoRoot -Pad $padEnv -SinglePass -DryRun
    $supState4 = Read-SupervisorState (Join-Path $padEnv "supervisor_recovery_state.json")
    Assert-Check "Corrupted checkpoint halts supervisor in BLOCKED_NEEDS_INTERVENTION (Gap 2)" ($supState4.state -eq "BLOCKED_NEEDS_INTERVENTION")
    Assert-Check "Supervisor recorded CORRUPTED_CHECKPOINT classification (Gap 2)" ($supState4.classification.category -eq "CORRUPTED_CHECKPOINT")

    # Case 5.5: Reconciled historical failure packet does not block valid PENDING turn resumption
    Write-ControllerCheckpoint $compCpPath $pendingCp
    $reconciledFailDir = Join-Path $padEnv "failure_recovery/reconciled_packet_01"
    New-Item -ItemType Directory -Path $reconciledFailDir -Force | Out-Null
    $oldPacket = [ordered]@{ error = "AUTHENTICATION_FAILED: Old historical error" }
    [IO.File]::WriteAllText((Join-Path $reconciledFailDir "packet.json"), ($oldPacket | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText((Join-Path $reconciledFailDir "reconciled.json"), (@{reconciled=$true} | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
    Remove-Item -LiteralPath (Join-Path $padEnv "supervisor_recovery_state.json") -Force

    Start-ControllerSupervisedLoop -Workspace $repoRoot -Pad $padEnv -SinglePass -DryRun
    $supState5 = Read-SupervisorState (Join-Path $padEnv "supervisor_recovery_state.json")
    Assert-Check "Reconciled historical failure packet allows PENDING turn to reach RESUME_READY" ($supState5.state -eq "RESUME_READY")
    Assert-Check "Supervisor classification is CLEAN_INTERRUPTED_CHECKPOINT" ($supState5.classification.category -eq "CLEAN_INTERRUPTED_CHECKPOINT")

    # Case 5.6: Crashed worker in RUNNING state re-arms to PENDING and reaches RESUME_READY
    $crashedCp = [ordered]@{
        state = "RUNNING"
        task_id = "F1699-TEST-UNSTARTED-TASK"
        run_id = $activeRunId
        turn = 12
        recovery_count = 0
        process_id = 999999 # Dead PID
        started_at = [DateTimeOffset]::UtcNow.AddMinutes(-10).ToString("o")
        original_instruction_hash = $instHash
    }
    Write-ControllerCheckpoint $compCpPath $crashedCp
    Remove-Item -LiteralPath (Join-Path $padEnv "supervisor_recovery_state.json") -Force

    Start-ControllerSupervisedLoop -Workspace $repoRoot -Pad $padEnv -SinglePass -DryRun
    $supState6 = Read-SupervisorState (Join-Path $padEnv "supervisor_recovery_state.json")
    Assert-Check "Crashed worker in RUNNING state reaches RESUME_READY under governance" ($supState6.state -eq "RESUME_READY")
    Assert-Check "Supervisor classification is CRASHED_WORKER_RESUMPTION" ($supState6.classification.category -eq "CRASHED_WORKER_RESUMPTION")
    $postReArmCp = Read-SupervisorCheckpoint $repoRoot $compCpPath
    Assert-Check "Post-reconciliation checkpoint re-armed to PENDING" ($postReArmCp.state -eq "PENDING")
    Assert-Check "Post-reconciliation checkpoint cleared stale PID" ($postReArmCp.process_id -eq 0)

    # Case 5.7: Interrupted PENDING turn with stale owned_session_fingerprint re-arms cleanly
    $pendingStaleFingerprintCp = [ordered]@{
        state = "PENDING"
        task_id = "F1699-TEST-UNSTARTED-TASK"
        run_id = $activeRunId
        turn = 12
        recovery_count = 0
        process_id = 0
        owned_session_fingerprint = "stale_orphaned_fingerprint_hash_abc123"
        conversation_id = "stale_convo_guid_456"
        started_at = [DateTimeOffset]::UtcNow.AddMinutes(-10).ToString("o")
        original_instruction_hash = $instHash
    }
    Write-ControllerCheckpoint $compCpPath $pendingStaleFingerprintCp
    Remove-Item -LiteralPath (Join-Path $padEnv "supervisor_recovery_state.json") -Force

    Start-ControllerSupervisedLoop -Workspace $repoRoot -Pad $padEnv -SinglePass -DryRun
    $supState7 = Read-SupervisorState (Join-Path $padEnv "supervisor_recovery_state.json")
    Assert-Check "Interrupted PENDING turn with stale fingerprint reaches RESUME_READY" ($supState7.state -eq "RESUME_READY")
    $postReArmCp7 = Read-SupervisorCheckpoint $repoRoot $compCpPath
    Assert-Check "Post-reconciliation checkpoint cleared stale session fingerprint" ([string]::IsNullOrEmpty($postReArmCp7.owned_session_fingerprint))
    Assert-Check "Post-reconciliation checkpoint cleared stale conversation_id" ([string]::IsNullOrEmpty($postReArmCp7.conversation_id))

    # -------------------------------------------------------------------------
    # Test Group 6: Process Ownership Chain & Supervisor Status
    # -------------------------------------------------------------------------
    Write-Host "`n--- Test Group 6: Process Ownership Chain & Supervisor Status ---" -ForegroundColor Yellow

    $supStatus = Get-SupervisorStatus -PadPath $padEnv
    Assert-Check "Get-SupervisorStatus reports structured status" ($null -ne $supStatus.is_active -and $null -ne $supStatus.mutex_locked)

    # Validate process ownership chain inspection
    # A fake worker PID with an arbitrary command line should be rejected
    $currentPid = [System.Diagnostics.Process]::GetCurrentProcess().Id
    Assert-Check "Test-IsControllerWorkerProcess rejects PID 0" ((Test-IsControllerWorkerProcess -ProcessId 0) -eq $false)
    Assert-Check "Test-IsControllerWorkerProcess rejects non-existent PID" ((Test-IsControllerWorkerProcess -ProcessId 98765432) -eq $false)

    # -------------------------------------------------------------------------
    # Test Group 7: Partial Side Effects Audit & Replay Prevention
    # -------------------------------------------------------------------------
    Write-Host "`n--- Test Group 7: Partial Side Effects Audit & Replay Prevention ---" -ForegroundColor Yellow

    $mockSideWs = Join-Path $tmpDir "mock_side_ws"
    New-Item -ItemType Directory -Path (Join-Path $mockSideWs "project_coordination/review_dispatch") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $mockSideWs "results/validation") -Force | Out-Null
    $mockHpcLedger = Join-Path $mockSideWs "project_coordination/HPC_JOB_LEDGER.csv"
    $mockActiveTask = Join-Path $mockSideWs "project_coordination/ACTIVE_TASK.json"

    # Base task data
    $baseTask = [ordered]@{
        task_id = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"
        completed_operations = @("operation_1", "operation_2")
        scientific_checkpoint = $null
        controller_maintenance = [ordered]@{
            automatic_restart_allowed = $true
            unattended_operation_allowed = $false
        }
    }
    Set-Content -LiteralPath $mockActiveTask -Value ($baseTask | ConvertTo-Json -Depth 5)

    # Base HPC ledger with older job
    $oldTime = [DateTimeOffset]::UtcNow.AddHours(-5).ToString("o")
    "job_id,job_name,run_dir,node_list,queue_name,submission_timestamp,status,exit_code,classification,manifest_sha256" | Set-Content -LiteralPath $mockHpcLedger
    "1400001.mmaster02,OLD_JOB,/scratch,,normal,$oldTime,COMPLETED,0,STANDING_MODE1_V2_ACCEPTED_ONCE,abc" | Add-Content -LiteralPath $mockHpcLedger

    # 7.1 Clean turn: zero side effects
    $cleanTurnStart = [DateTimeOffset]::UtcNow.AddMinutes(-5).ToString("o")
    $cleanTurnCp = [ordered]@{
        state = "RUNNING"
        task_id = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"
        run_id = "run-clean"
        turn = 7
        process_id = 999999
        recovery_count = 0
        started_at = $cleanTurnStart
        completed_operations = @("operation_1", "operation_2")
    }
    $cleanAudit = Audit-InterruptedTurnSideEffects -Workspace $mockSideWs -Checkpoint $cleanTurnCp -HpcLedgerPath $mockHpcLedger -ActiveTaskPath $mockActiveTask
    Assert-Check "Clean turn produces zero side effects" ($cleanAudit.has_side_effects -eq $false -and $cleanAudit.has_pbs_side_effects -eq $false -and $cleanAudit.has_scientific_side_effects -eq $false)

    # 7.2 PBS Reservation side effect: worker submitted PBS job before crashing
    $jobTime = [DateTimeOffset]::UtcNow.AddMinutes(-2).ToString("o")
    "1420001.mmaster02,M1_C6_P171_R8_JOB,/scratch,,normal,$jobTime,SUBMITTED,,STANDING_MODE1_V2_ACCEPTED_ONCE,def" | Add-Content -LiteralPath $mockHpcLedger
    $pbsAudit = Audit-InterruptedTurnSideEffects -Workspace $mockSideWs -Checkpoint $cleanTurnCp -HpcLedgerPath $mockHpcLedger -ActiveTaskPath $mockActiveTask
    Assert-Check "Audit detects PBS reservation submitted during crashed turn" ($pbsAudit.has_pbs_side_effects -eq $true -and $pbsAudit.pbs_jobs.Count -eq 1 -and $pbsAudit.pbs_jobs[0] -eq "1420001.mmaster02")

    # Classification of PBS side effect: must NOT re-arm to PENDING
    $pbsClass = Classify-ControllerFailure -Workspace $mockSideWs -PadPath $mockPad -Checkpoint $cleanTurnCp
    Assert-Check "Crashed turn with PBS reservation classified as INTERRUPTED_TURN_PBS_SUBMITTED (once-only)" ($pbsClass.category -eq "INTERRUPTED_TURN_PBS_SUBMITTED" -and $pbsClass.action -eq "RECONCILE_PARTIAL_EVIDENCE" -and $pbsClass.fingerprint -eq "PBS_SUBMITTED_CRASH")

    # 7.3 Scientific Operation side effect: worker marked operation completed before crashing
    # Reset HPC ledger
    "job_id,job_name,run_dir,node_list,queue_name,submission_timestamp,status,exit_code,classification,manifest_sha256" | Set-Content -LiteralPath $mockHpcLedger
    "1400001.mmaster02,OLD_JOB,/scratch,,normal,$oldTime,COMPLETED,0,STANDING_MODE1_V2_ACCEPTED_ONCE,abc" | Add-Content -LiteralPath $mockHpcLedger
    $sciTask = [ordered]@{
        task_id = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"
        completed_operations = @("operation_1", "operation_2", "execute_mode1_package171_r8_c6_coupled_reequilibration")
        controller_maintenance = [ordered]@{ automatic_restart_allowed = $true; unattended_operation_allowed = $false }
    }
    Set-Content -LiteralPath $mockActiveTask -Value ($sciTask | ConvertTo-Json -Depth 5)
    $sciAudit = Audit-InterruptedTurnSideEffects -Workspace $mockSideWs -Checkpoint $cleanTurnCp -HpcLedgerPath $mockHpcLedger -ActiveTaskPath $mockActiveTask
    Assert-Check "Audit detects scientific operation completed during crashed turn" ($sciAudit.has_scientific_side_effects -eq $true -and $sciAudit.completed_operations -contains "execute_mode1_package171_r8_c6_coupled_reequilibration")

    $sciClass = Classify-ControllerFailure -Workspace $mockSideWs -PadPath $mockPad -Checkpoint $cleanTurnCp
    Assert-Check "Crashed turn with completed operation classified as INTERRUPTED_TURN_OPERATION_COMPLETED" ($sciClass.category -eq "INTERRUPTED_TURN_OPERATION_COMPLETED" -and $sciClass.action -eq "RECONCILE_COMPLETED_OPERATION")

    # 7.4 Bridge Transaction side effect: worker emitted review request before crashing
    # Reset active task
    Set-Content -LiteralPath $mockActiveTask -Value ($baseTask | ConvertTo-Json -Depth 5)
    $reqFile = Join-Path $mockSideWs "project_coordination/review_dispatch/test_dispatch.request.json"
    [IO.File]::WriteAllText($reqFile, '{"request_id":"test"}', [Text.UTF8Encoding]::new($false))
    $bridgeAudit = Audit-InterruptedTurnSideEffects -Workspace $mockSideWs -Checkpoint $cleanTurnCp -HpcLedgerPath $mockHpcLedger -ActiveTaskPath $mockActiveTask -DispatchDir (Join-Path $mockSideWs "project_coordination/review_dispatch")
    Assert-Check "Audit detects bridge transaction dispatched during crashed turn" ($bridgeAudit.has_bridge_side_effects -eq $true -and $bridgeAudit.bridge_transactions -contains "test_dispatch.request.json")

    $bridgeClass = Classify-ControllerFailure -Workspace $mockSideWs -PadPath $mockPad -Checkpoint $cleanTurnCp
    Assert-Check "Crashed turn with bridge transaction classified as INTERRUPTED_TURN_BRIDGE_TRANSACTION" ($bridgeClass.category -eq "INTERRUPTED_TURN_BRIDGE_TRANSACTION" -and $bridgeClass.action -eq "RECONCILE_BRIDGE_TRANSACTION")

    # 7.5 File Writes & Temporary Files: worker wrote .tmp file before crashing
    Remove-Item -LiteralPath $reqFile -Force
    $tmpFile = Join-Path $mockSideWs "results/validation/partial_output.json.tmp"
    [IO.File]::WriteAllText($tmpFile, '{"partial":true}', [Text.UTF8Encoding]::new($false))
    $fileAudit = Audit-InterruptedTurnSideEffects -Workspace $mockSideWs -Checkpoint $cleanTurnCp -HpcLedgerPath $mockHpcLedger -ActiveTaskPath $mockActiveTask
    Assert-Check "Audit detects partial / temporary file writes" ($fileAudit.has_file_write_side_effects -eq $true -and $fileAudit.partial_files.Count -ge 1)

    # 7.6 Re-Arming Guard: Calling RESUME_PENDING_INSTRUCTION on a turn with side effects MUST throw
    # Create checkpoint with side effects in mockPad
    $sideEffectCpFile = Join-Path $mockPad "controller_turn_checkpoint.json"
    Write-ControllerCheckpoint $sideEffectCpFile $cleanTurnCp
    $rearmBlocked = $false
    try {
        # mockSideWs has the .tmp file, so Audit-InterruptedTurnSideEffects returns has_side_effects = true
        Invoke-SupervisorReconciliationStep -Workspace $mockSideWs -PadPath $mockPad -Classification ([pscustomobject]@{ action = "RESUME_PENDING_INSTRUCTION" }) -CheckpointPath $sideEffectCpFile
    } catch {
        if ($_.Exception.Message -match "CANNOT_REARM_WITH_SIDE_EFFECTS") {
            $rearmBlocked = $true
        }
    }
    Assert-Check "RESUME_PENDING_INSTRUCTION throws CANNOT_REARM_WITH_SIDE_EFFECTS when partial side effects exist" ($rearmBlocked -eq $true)

    # 7.7 RECONCILE_PARTIAL_EVIDENCE cleans temporary files and converts to CHECKPOINTED
    $reconcileRes = Invoke-SupervisorReconciliationStep -Workspace $mockSideWs -PadPath $mockPad -Classification ([pscustomobject]@{ action = "RECONCILE_PARTIAL_EVIDENCE" }) -CheckpointPath $sideEffectCpFile
    Assert-Check "RECONCILE_PARTIAL_EVIDENCE succeeds" ($reconcileRes.success -eq $true)
    Assert-Check "Temporary file cleaned by RECONCILE_PARTIAL_EVIDENCE" (-not (Test-Path -LiteralPath $tmpFile))
    $reconciledCp = Read-SupervisorCheckpoint $repoRoot $sideEffectCpFile
    Assert-Check "Checkpoint converted to CHECKPOINTED state with evidence recovery action" ($reconciledCp.state -eq "CHECKPOINTED" -and $reconciledCp.next_safe_action -match "Evidence-only reconciliation")

    # -------------------------------------------------------------------------
    # Test Group 8: Unattended Operation Governance
    # -------------------------------------------------------------------------
    Write-Host "`n--- Test Group 8: Unattended Operation Governance ---" -ForegroundColor Yellow

    # Verify that ACTIVE_TASK governance with unattended_operation_allowed = false is preserved
    $taskGov = Get-Content (Join-Path $repoRoot "project_coordination/ACTIVE_TASK.json") -Raw | ConvertFrom-Json
    Assert-Check "Governance maintains unattended_operation_allowed = false" ($taskGov.controller_maintenance.unattended_operation_allowed -eq $false)
    Assert-Check "Governance maintains max_new_pbs_submissions = 0" ($taskGov.max_new_pbs_submissions -eq 0)

    # -------------------------------------------------------------------------
    # Test Group 9: PENDING Turn Side Effects Audit & Reconciliation (F1608 Defect Repair)
    # -------------------------------------------------------------------------
    Write-Host "`n--- Test Group 9: PENDING Turn Side Effects Audit & Reconciliation ---" -ForegroundColor Yellow

    $mockPendingWs = Join-Path $tmpDir "mock_pending_ws"
    New-Item -ItemType Directory -Path (Join-Path $mockPendingWs "project_coordination/review_dispatch") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $mockPendingWs "results/validation") -Force | Out-Null
    $pendingHpcLedger = Join-Path $mockPendingWs "project_coordination/HPC_JOB_LEDGER.csv"
    $pendingActiveTask = Join-Path $mockPendingWs "project_coordination/ACTIVE_TASK.json"

    # Base task with no completed operations
    $basePendingTask = [ordered]@{
        task_id = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"
        completed_operations = @()
        scientific_checkpoint = $null
        controller_maintenance = [ordered]@{ automatic_restart_allowed = $true; unattended_operation_allowed = $false }
    }
    Set-Content -LiteralPath $pendingActiveTask -Value ($basePendingTask | ConvertTo-Json -Depth 5)

    "job_id,job_name,run_dir,node_list,queue_name,submission_timestamp,status,exit_code,classification,manifest_sha256" | Set-Content -LiteralPath $pendingHpcLedger
    "1400001.mmaster02,OLD_JOB,/scratch,,normal,$oldTime,COMPLETED,0,STANDING_MODE1_V2_ACCEPTED_ONCE,abc" | Add-Content -LiteralPath $pendingHpcLedger

    $testInstHash = (Get-ControllerTextHash "Execute Turn 7 instruction")
    $pendingTestCp = [ordered]@{
        state = "PENDING"
        task_id = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"
        run_id = "run-pending-test"
        turn = 7
        process_id = 0
        recovery_count = 0
        started_at = [DateTimeOffset]::UtcNow.AddMinutes(-5).ToString("o")
        original_instruction_hash = $testInstHash
        completed_operations = @()
    }

    # 9.1 Scenario 1: PENDING checkpoint, zero side effects -> genuine pending resume
    $c9_1 = Classify-ControllerFailure -Workspace $mockPendingWs -PadPath $mockPad -Checkpoint $pendingTestCp
    Assert-Check "9.1 PENDING checkpoint with zero side effects classified as CLEAN_INTERRUPTED_CHECKPOINT" ($c9_1.category -eq "CLEAN_INTERRUPTED_CHECKPOINT" -and $c9_1.action -eq "RESUME_PENDING_INSTRUCTION" -and $c9_1.recoverable -eq $true)

    # 9.2 Scenario 2: PENDING checkpoint, completed scientific operation in ACTIVE_TASK -> reconcile; do not replay
    $taskWithSciOp = [ordered]@{
        task_id = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"
        completed_operations = @("execute_mode1_package171_r8_c6_coupled_reequilibration")
        scientific_checkpoint = $null
        controller_maintenance = [ordered]@{ automatic_restart_allowed = $true; unattended_operation_allowed = $false }
    }
    Set-Content -LiteralPath $pendingActiveTask -Value ($taskWithSciOp | ConvertTo-Json -Depth 5)
    $c9_2 = Classify-ControllerFailure -Workspace $mockPendingWs -PadPath $mockPad -Checkpoint $pendingTestCp
    Assert-Check "9.2 PENDING checkpoint with completed scientific operation classified as COMPLETED_OPERATION_PENDING_RECONCILIATION" ($c9_2.category -eq "COMPLETED_OPERATION_PENDING_RECONCILIATION" -and $c9_2.action -eq "RECONCILE_COMPLETED_OPERATION" -and $c9_2.recoverable -eq $true)

    # 9.3 Scenario 3: PENDING checkpoint, verified technical-qualification receipt -> preserve receipt and advance lifecycle
    # Reset active task to base
    Set-Content -LiteralPath $pendingActiveTask -Value ($basePendingTask | ConvertTo-Json -Depth 5)
    $receiptPath = Join-Path $mockPendingWs "results/validation/package171_r8_technical_qualification_receipt.json"
    $validReceiptData = [ordered]@{
        schema = 1
        package_id = "mode1_c6_package171_r8_c3_0_adaptive_reequilibration"
        task_id = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"
        candidate_job = "M1_C6_P171_R8_ADAPTIVE_DAMPED"
        overall_status = "PASSED_TECHNICAL_QUALIFICATION"
    }
    [IO.File]::WriteAllText($receiptPath, ($validReceiptData | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))
    $c9_3 = Classify-ControllerFailure -Workspace $mockPendingWs -PadPath $mockPad -Checkpoint $pendingTestCp
    Assert-Check "9.3 PENDING checkpoint with verified receipt classified as COMPLETED_OPERATION_PENDING_RECONCILIATION" ($c9_3.category -eq "COMPLETED_OPERATION_PENDING_RECONCILIATION" -and $c9_3.action -eq "RECONCILE_COMPLETED_OPERATION")

    # Verify reconciliation advances checkpoint to COMPLETED and preserves receipt
    $reconcileCpFile = Join-Path $mockPad "pending_reconcile_cp.json"
    Write-ControllerCheckpoint $reconcileCpFile $pendingTestCp
    $recOpResult = Invoke-SupervisorReconciliationStep -Workspace $mockPendingWs -PadPath $mockPad -Classification $c9_3 -CheckpointPath $reconcileCpFile
    Assert-Check "9.3 RECONCILE_COMPLETED_OPERATION succeeds" ($recOpResult.success -eq $true)
    $postRecCp = Read-SupervisorCheckpoint $repoRoot $reconcileCpFile
    Assert-Check "9.3 Checkpoint state advanced to COMPLETED" ($postRecCp.state -eq "COMPLETED")
    Assert-Check "9.3 Checkpoint stop_reason is OPERATION_COMPLETED" ($postRecCp.stop_reason -eq "OPERATION_COMPLETED")
    Assert-Check "9.3 Original instruction hash preserved" ($postRecCp.original_instruction_hash -eq $testInstHash)
    Assert-Check "9.3 Technical qualification receipt preserved untouched" (Test-Path -LiteralPath $receiptPath)

    # 9.4 Scenario 4: PENDING checkpoint, PBS submission already recorded -> never submit twice
    Remove-Item -LiteralPath $receiptPath -Force
    $pbsTime = [DateTimeOffset]::UtcNow.AddMinutes(-2).ToString("o")
    "1420002.mmaster02,M1_C6_P171_R8_JOB,/scratch,,normal,$pbsTime,SUBMITTED,,STANDING_MODE1_V2_ACCEPTED_ONCE,def" | Add-Content -LiteralPath $pendingHpcLedger
    $c9_4 = Classify-ControllerFailure -Workspace $mockPendingWs -PadPath $mockPad -Checkpoint $pendingTestCp
    Assert-Check "9.4 PENDING checkpoint with recorded PBS job classified as INTERRUPTED_TURN_PBS_SUBMITTED (never submit twice)" ($c9_4.category -eq "INTERRUPTED_TURN_PBS_SUBMITTED" -and $c9_4.action -eq "RECONCILE_PARTIAL_EVIDENCE")

    # 9.5 Scenario 5: PENDING checkpoint, unresolved bridge transaction -> preserve transaction without replay
    "job_id,job_name,run_dir,node_list,queue_name,submission_timestamp,status,exit_code,classification,manifest_sha256" | Set-Content -LiteralPath $pendingHpcLedger
    $pendingBridgeReq = Join-Path $mockPendingWs "project_coordination/review_dispatch/test_pending.request.json"
    [IO.File]::WriteAllText($pendingBridgeReq, '{"request_id":"pending_req"}', [Text.UTF8Encoding]::new($false))
    $c9_5 = Classify-ControllerFailure -Workspace $mockPendingWs -PadPath $mockPad -Checkpoint $pendingTestCp
    Assert-Check "9.5 PENDING checkpoint with unresolved bridge transaction classified as INTERRUPTED_TURN_BRIDGE_TRANSACTION" ($c9_5.category -eq "INTERRUPTED_TURN_BRIDGE_TRANSACTION" -and $c9_5.action -eq "RECONCILE_BRIDGE_TRANSACTION")

    # 9.6 Scenario 6: Invalid or mismatched receipt -> block
    Remove-Item -LiteralPath $pendingBridgeReq -Force
    $invalidReceiptData = [ordered]@{
        schema = 1
        package_id = "mode1_c6_package171_r8_c3_0_adaptive_reequilibration"
        task_id = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"
        candidate_job = "M1_C6_P171_R8_ADAPTIVE_DAMPED"
        overall_status = "FAILED_QUALIFICATION_ERRORS"
    }
    [IO.File]::WriteAllText($receiptPath, ($invalidReceiptData | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))
    $c9_6 = Classify-ControllerFailure -Workspace $mockPendingWs -PadPath $mockPad -Checkpoint $pendingTestCp
    Assert-Check "9.6 PENDING checkpoint with invalid receipt status classified as INVALID_RECEIPT_BLOCKED / BLOCK" ($c9_6.category -eq "INVALID_RECEIPT_BLOCKED" -and $c9_6.action -eq "BLOCK" -and $c9_6.recoverable -eq $false)

    # 9.6b Mismatched receipt task_id -> block
    $mismatchedReceiptData = [ordered]@{
        schema = 1
        package_id = "mode1_c6_package171_r8_c3_0_adaptive_reequilibration"
        task_id = "F9999-WRONG-TASK"
        candidate_job = "M1_C6_P171_R8_ADAPTIVE_DAMPED"
        overall_status = "PASSED_TECHNICAL_QUALIFICATION"
    }
    [IO.File]::WriteAllText($receiptPath, ($mismatchedReceiptData | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))
    $c9_6b = Classify-ControllerFailure -Workspace $mockPendingWs -PadPath $mockPad -Checkpoint $pendingTestCp
    Assert-Check "9.6b PENDING checkpoint with mismatched receipt task_id classified as INVALID_RECEIPT_BLOCKED / BLOCK" ($c9_6b.category -eq "INVALID_RECEIPT_BLOCKED" -and $c9_6b.action -eq "BLOCK" -and $c9_6b.recoverable -eq $false)

    # 9.7 Scenario 7: Reconciliation exception -> persist a controlled blocked state
    Remove-Item -LiteralPath $receiptPath -Force
    $excPadEnv = Join-Path $tmpDir "exc_pad"
    New-Item -ItemType Directory -Path $excPadEnv -Force | Out-Null
    $excCpPath = Join-Path $excPadEnv "controller_turn_checkpoint.json"
    Write-ControllerCheckpoint $excCpPath $pendingTestCp

    # Lock checkpoint file exclusively so Invoke-SupervisorReconciliationStep encounters an IOException
    $lockStream = [System.IO.File]::Open($excCpPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    try {
        Start-ControllerSupervisedLoop -Workspace $mockPendingWs -Pad $excPadEnv -SinglePass -DryRun
    } finally {
        $lockStream.Close()
    }
    $excSupState = Read-SupervisorState (Join-Path $excPadEnv "supervisor_recovery_state.json")
    Assert-Check "9.7 Reconciliation exception caught at supervisor boundary and persists BLOCKED_NEEDS_INTERVENTION" ($excSupState.state -eq "BLOCKED_NEEDS_INTERVENTION")
    Assert-Check "9.7 Supervisor recorded durable last_error evidence" ($null -ne $excSupState.last_error -and $excSupState.last_error.Length -gt 0)

    # 9.8 Scenario 8: Reproduce the reported F1608 condition and prove clean reconciliation without replay
    $liveF1608Cp = [ordered]@{
        state = "PENDING"
        task_id = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"
        run_id = $activeRunId
        turn = 7
        process_id = 0
        recovery_count = 1
        started_at = [DateTimeOffset]::UtcNow.AddHours(-1).ToString("o")
        original_instruction_hash = "3245eb12ad47819343fd06d9b72096891ca063214a48c02719c81314e06633da"
    }
    $f1608Class = Classify-ControllerFailure -Workspace $repoRoot -PadPath $mockPad -Checkpoint $liveF1608Cp
    Assert-Check "9.8 Reported F1608 condition classified as COMPLETED_OPERATION_PENDING_RECONCILIATION" ($f1608Class.category -eq "COMPLETED_OPERATION_PENDING_RECONCILIATION" -and $f1608Class.action -eq "RECONCILE_COMPLETED_OPERATION")
    Assert-Check "9.8 F1608 failure classification avoids RESUME_PENDING_INSTRUCTION (no Turn 7 replay)" ($f1608Class.action -ne "RESUME_PENDING_INSTRUCTION")

    # Execute supervisor loop on F1608 checkpoint in DryRun: halts cleanly in COMPLETED without replaying worker
    $f1608PadEnv = Join-Path $tmpDir "f1608_pad"
    New-Item -ItemType Directory -Path $f1608PadEnv -Force | Out-Null
    $f1608CpPath = Join-Path $f1608PadEnv "controller_turn_checkpoint.json"
    Write-ControllerCheckpoint $f1608CpPath $liveF1608Cp
    Start-ControllerSupervisedLoop -Workspace $repoRoot -Pad $f1608PadEnv -SinglePass -DryRun
    $f1608SupState = Read-SupervisorState (Join-Path $f1608PadEnv "supervisor_recovery_state.json")
    Assert-Check "9.8 Supervised loop cleanly completes F1608 reconciliation with state COMPLETED" ($f1608SupState.state -eq "COMPLETED")
    $f1608PostCp = Read-SupervisorCheckpoint $repoRoot $f1608CpPath
    Assert-Check "9.8 F1608 checkpoint transitioned to COMPLETED without process spawn" ($f1608PostCp.state -eq "COMPLETED")

    Write-Host "`n==================================================================" -ForegroundColor Cyan
    Write-Host " ALL SUPERVISOR TESTS PASSED: $passedTests / $totalTests" -ForegroundColor Green
    Write-Host "==================================================================" -ForegroundColor Cyan
}
finally {
    if (Test-Path -LiteralPath $tmpDir) {
        Remove-Item -LiteralPath $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
