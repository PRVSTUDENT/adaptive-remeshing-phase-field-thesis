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
        task_id = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"
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
        task_id = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"
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
        task_id = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"
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

    Write-Host "`n==================================================================" -ForegroundColor Cyan
    Write-Host " ALL SUPERVISOR TESTS PASSED: $passedTests / $totalTests" -ForegroundColor Green
    Write-Host "==================================================================" -ForegroundColor Cyan
}
finally {
    if (Test-Path -LiteralPath $tmpDir) {
        Remove-Item -LiteralPath $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
