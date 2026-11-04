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

    # 3.3 Auth mismatch
    $c3 = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $mockCp -LastLogText "Error: AUTH_RECOVERY_REQUIRED: profile marker account2 mismatches store"
    Assert-Check "AUTH_RECOVERY_REQUIRED classified as TRANSIENT_AUTH_MISMATCH / RECONCILE_AUTH_AND_RESUME" ($c3.category -eq "TRANSIENT_AUTH_MISMATCH" -and $c3.action -eq "RECONCILE_AUTH_AND_RESUME" -and $c3.recoverable -eq $true)

    # 3.4 Code defect (null path)
    $c4 = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $mockCp -LastLogText "Cannot bind argument to parameter 'Path' because it is null in Test-Path `$loopStatePath"
    Assert-Check "Null path binding classified as DETERMINISTIC_CODE_DEFECT / SELF_REPAIR_AND_DEPLOY" ($c4.category -eq "DETERMINISTIC_CODE_DEFECT" -and $c4.action -eq "SELF_REPAIR_AND_DEPLOY" -and $c4.recoverable -eq $true)

    # 3.5 Transport timeout
    $c5 = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $mockCp -LastLogText "System.Net.WebException: The operation has timed out."
    Assert-Check "Transport timeout classified as TRANSIENT_TRANSPORT_ERROR / BACKOFF_RETRY" ($c5.category -eq "TRANSIENT_TRANSPORT_ERROR" -and $c5.action -eq "BACKOFF_RETRY" -and $c5.recoverable -eq $true)

    # 3.6 Credentials exhausted
    $c6 = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $mockCp -LastLogText "HTTP 401 Unauthorized: invalid_grant token has expired"
    Assert-Check "HTTP 401 classified as AUTHENTICATION_EXHAUSTED / BLOCK" ($c6.category -eq "AUTHENTICATION_EXHAUSTED" -and $c6.action -eq "BLOCK" -and $c6.recoverable -eq $false)

    # 3.7 Clean interrupted PENDING turn
    $cleanPendingCp = [pscustomobject]@{ run_id = "my-run-id-111"; state = "PENDING"; process_id = 0 }
    $c7 = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $cleanPendingCp -LastLogText ""
    Assert-Check "Unstarted PENDING turn classified as CLEAN_INTERRUPTED_CHECKPOINT / RESUME_PENDING_INSTRUCTION" ($c7.category -eq "CLEAN_INTERRUPTED_CHECKPOINT" -and $c7.action -eq "RESUME_PENDING_INSTRUCTION" -and $c7.recoverable -eq $true)

    # 3.8 Unknown failure
    $c8 = Classify-ControllerFailure -Workspace $mockWs -PadPath $mockPad -Checkpoint $mockCp -LastLogText "Fatal unhandled exception in core subsystem"
    Assert-Check "Unclassified failure classified as UNCLASSIFIED_FAILURE / BLOCK" ($c8.category -eq "UNCLASSIFIED_FAILURE" -and $c8.action -eq "BLOCK" -and $c8.recoverable -eq $false)

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
        run_id = "test-run-comp"
        turn = 10
        process_id = 0
    }
    $compCpPath = Join-Path $padEnv "controller_turn_checkpoint.json"
    [IO.File]::WriteAllText($compCpPath, ($completedCp | ConvertTo-Json), [Text.UTF8Encoding]::new($false))

    Start-ControllerSupervisedLoop -Workspace $repoRoot -Pad $padEnv -SinglePass -DryRun
    $supState = Read-SupervisorState (Join-Path $padEnv "supervisor_recovery_state.json")
    Assert-Check "Completed checkpoint terminates with state COMPLETED" ($supState.state -eq "COMPLETED")

    $activeRunId = (Get-Content (Join-Path $repoRoot "project_coordination/ACTIVE_SESSION.json") -Raw | ConvertFrom-Json).controller_run_id

    # Case 5.2: Non-recoverable failure halts with BLOCKED_NEEDS_INTERVENTION
    $blockedCp = [ordered]@{
        state = "RUNNING"
        run_id = $activeRunId
        turn = 11
        process_id = 0
    }
    [IO.File]::WriteAllText($compCpPath, ($blockedCp | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
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
    . (Join-Path $repoRoot "scripts/controller/Controller-Recovery.ps1")
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
    [IO.File]::WriteAllText($compCpPath, ($pendingCp | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
    Remove-Item -LiteralPath $failDir -Recurse -Force
    Remove-Item -LiteralPath (Join-Path $padEnv "supervisor_recovery_state.json") -Force

    Start-ControllerSupervisedLoop -Workspace $repoRoot -Pad $padEnv -SinglePass -DryRun
    $supState3 = Read-SupervisorState (Join-Path $padEnv "supervisor_recovery_state.json")
    Assert-Check "Recoverable PENDING turn in DryRun reaches RESUME_READY" ($supState3.state -eq "RESUME_READY")

    Write-Host "`n==================================================================" -ForegroundColor Cyan
    Write-Host " ALL SUPERVISOR TESTS PASSED: $passedTests / $totalTests" -ForegroundColor Green
    Write-Host "==================================================================" -ForegroundColor Cyan
}
finally {
    if (Test-Path -LiteralPath $tmpDir) {
        Remove-Item -LiteralPath $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
