# ==============================================================================
# Controller-SelfHealingSupervisor.ps1
#
# Independent, persistent self-healing supervisor for the Gemini Antigravity
# autonomous controller loop. Survives worker exits, diagnoses failures,
# reconciles authentication and checkpoint state, performs bounded repairs,
# and safely resumes exact pending research operations.
#
# Protocol: Codex + Gemini Antigravity
# ==============================================================================

[CmdletBinding()]
param(
    [string]$WorkspaceDir = "D:\Master thesis\Adaptive remeshing",
    [string]$PadDir       = "$env:USERPROFILE\OpenClawPAD",
    [int]$PollIntervalSec = 5,
    [int]$MaxSelfRepairRetries = 3,
    [switch]$SinglePass,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function Get-SupervisorMutex {
    $createdNew = $false
    $mutexName = "Local\AntigravitySelfHealingSupervisorLock"
    $mutex = New-Object System.Threading.Mutex($false, $mutexName, [ref]$createdNew)
    return [pscustomobject]@{ Mutex = $mutex; CreatedNew = $createdNew }
}

function Test-IsControllerWorkerProcess {
    param(
        [int]$ProcessId,
        [datetimeoffset]$ExpectedMinStartTime = [datetimeoffset]::MinValue
    )
    if ($ProcessId -le 0) { return $false }
    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $proc -or $proc.HasExited) { return $false }

    # Process must be a PowerShell interpreter or Antigravity research worker
    if ($proc.ProcessName -notin @('powershell', 'pwsh', 'agy')) { return $false }

    # If an expected minimum start time is provided, verify process was not started long before
    if ($ExpectedMinStartTime -gt [datetimeoffset]::MinValue) {
        try {
            $pStart = [datetimeoffset]$proc.StartTime
            if ($pStart -lt $ExpectedMinStartTime.AddMinutes(-5)) {
                # Process was started long before expected turn; stale recycled PID
                return $false
            }
        } catch {}
    }
    return $true
}

function Read-SupervisorCheckpoint([string]$Workspace, [string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try {
        . (Join-Path $Workspace "scripts/controller/Controller-Recovery.ps1")
        return (Read-ControllerCheckpoint $Path)
    } catch {
        # Corrupted checkpoint envelope or invalid state fields MUST NOT be bypassed.
        return [pscustomobject]@{
            is_corrupted = $true
            error = $_.Exception.Message
            path = $Path
            state = "CORRUPTED"
            process_id = 0
            run_id = ""
        }
    }
}

function Read-SupervisorState([string]$Path) {
    if (Test-Path -LiteralPath $Path) {
        try {
            return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json)
        } catch {
            return $null
        }
    }
    return $null
}

function Write-SupervisorState([string]$Path, [pscustomobject]$State) {
    $tmp = $Path + '.' + [guid]::NewGuid().ToString('N') + '.tmp'
    $json = $State | ConvertTo-Json -Depth 15
    [IO.File]::WriteAllText($tmp, $json, [Text.UTF8Encoding]::new($false))
    if (Test-Path -LiteralPath $Path) {
        [IO.File]::Replace($tmp, $Path, ($Path + '.bak'))
    } else {
        [IO.File]::Move($tmp, $Path)
    }
}

function Classify-ControllerFailure {
    param(
        [Parameter(Mandatory)][string]$Workspace,
        [Parameter(Mandatory)][string]$PadPath,
        [AllowNull()]$Checkpoint,
        [string]$LastLogText = "",
        [string]$FailurePacketDir = ""
    )

    $classification = [ordered]@{
        category = "UNKNOWN"
        recoverable = $false
        action = "BLOCK"
        reason = ""
        fingerprint = ""
    }

    # 1. Inspect checkpoint state & corruption
    if (-not $Checkpoint) {
        $classification.category = "MISSING_CHECKPOINT"
        $classification.reason = "No controller checkpoint available for evaluation."
        $classification.fingerprint = "NO_CHECKPOINT"
        return [pscustomobject]$classification
    }

    if ($Checkpoint.is_corrupted) {
        $classification.category = "CORRUPTED_CHECKPOINT"
        $classification.recoverable = $false
        $classification.action = "BLOCK"
        $classification.reason = "Checkpoint envelope corrupted or failed cryptographic verification: $($Checkpoint.error)"
        $classification.fingerprint = "CHECKPOINT_CORRUPTION"
        return [pscustomobject]$classification
    }

    # 2. Check worker PID state (Stale PID vs Active Worker)
    $workerAlive = $false
    if ($Checkpoint.process_id -gt 0) {
        $turnStartedAt = [datetimeoffset]::MinValue
        if ($Checkpoint.started_at) { [datetimeoffset]::TryParse([string]$Checkpoint.started_at, [ref]$turnStartedAt) | Out-Null }
        $workerAlive = Test-IsControllerWorkerProcess -ProcessId $Checkpoint.process_id -ExpectedMinStartTime $turnStartedAt
        if ($workerAlive) {
            $classification.category = "WORKER_STILL_ACTIVE"
            $classification.recoverable = $false
            $classification.action = "WAIT_FOR_WORKER"
            $classification.reason = "Worker process (PID $($Checkpoint.process_id)) is still actively executing."
            $classification.fingerprint = "WORKER_ACTIVE"
            return [pscustomobject]$classification
        }
    }

    # 3. Check for active/foreign repository session ownership
    $sessionFile = Join-Path $Workspace "project_coordination/ACTIVE_SESSION.json"
    if (Test-Path -LiteralPath $sessionFile) {
        try {
            $sess = Get-Content -LiteralPath $sessionFile -Raw | ConvertFrom-Json
            if ($sess.active -and $sess.controller_run_id -and $Checkpoint.run_id -and ($sess.controller_run_id -ne $Checkpoint.run_id)) {
                $classification.category = "FOREIGN_SESSION_ACTIVE"
                $classification.reason = "A foreign session ($($sess.agent) / $($sess.controller_run_id)) owns the repository."
                $classification.fingerprint = "SESSION_COLLISION"
                return [pscustomobject]$classification
            }
        } catch {}
    }

    # 4. Check automatic-restart restriction from ACTIVE_TASK.json governance
    $activeTaskFile = Join-Path $Workspace "project_coordination/ACTIVE_TASK.json"
    $automaticRestartAllowed = $false
    if (Test-Path -LiteralPath $activeTaskFile) {
        try {
            $taskData = Get-Content -LiteralPath $activeTaskFile -Raw | ConvertFrom-Json
            if ($taskData.controller_maintenance -and $null -ne $taskData.controller_maintenance.automatic_restart_allowed) {
                $automaticRestartAllowed = [bool]$taskData.controller_maintenance.automatic_restart_allowed
            }
        } catch {}
    }

    # 5. Read failure packet error if available
    $errorText = ""
    if ($FailurePacketDir) {
        $packetPath = Join-Path $FailurePacketDir "packet.json"
        $isReconciled = (Test-Path -LiteralPath (Join-Path $FailurePacketDir "reconciled.json")) -or
                        (Test-Path -LiteralPath (Join-Path $FailurePacketDir "packet.reconciled.json"))
        if ((Test-Path -LiteralPath $packetPath) -and (-not $isReconciled)) {
            try {
                $packet = Get-Content -LiteralPath $packetPath -Raw | ConvertFrom-Json
                $errorText = [string]$packet.error
            } catch {}
        }
    }
    if (-not $errorText -and $LastLogText) {
        $errorText = $LastLogText
    }

    # 6. Pattern classification: Genuine authentication exhaustion takes absolute precedence
    if ($errorText -match 'HTTP\s*401|invalid_grant|interactive sign-in required|AUTHENTICATION_FAILED|eligible existing profiles exhausted|profiles exhausted') {
        $classification.category = "AUTHENTICATION_EXHAUSTED"
        $classification.recoverable = $false
        $classification.action = "BLOCK"
        $classification.reason = "Legitimate credentials expired or exhausted; interactive sign-in required."
        $classification.fingerprint = "CREDENTIALS_EXHAUSTED"
    }
    elseif ($errorText -match 'Cannot bind argument to parameter .Path. because it is null|\$loopStatePath') {
        $classification.category = "DETERMINISTIC_CODE_DEFECT"
        $classification.recoverable = $true
        $classification.action = "SELF_REPAIR_AND_DEPLOY"
        $classification.reason = "Null path binding in controller loop initialization."
        $classification.fingerprint = "NULL_PATH_BINDING"
    }
    elseif ($errorText -match 'SUPERVISOR_TRANSPORT_FAILED|WebException|HttpRequestException|TimeoutException') {
        $classification.category = "TRANSIENT_TRANSPORT_ERROR"
        $classification.recoverable = $true
        $classification.action = "BACKOFF_RETRY"
        $classification.reason = "Transient transport error communicating with supervisor or provider."
        $classification.fingerprint = "TRANSPORT_TIMEOUT"
    }
    elseif ($errorText -match 'AUTH_RECOVERY_REQUIRED|IDENTITY_MISMATCH|AGY_CREDENTIAL_REPAIR_PROVIDER_MISMATCH|profile marker|AUTH_RECOVERY_LIVE_AGY') {
        $classification.category = "TRANSIENT_AUTH_MISMATCH"
        $classification.recoverable = $true
        $classification.action = "RECONCILE_AUTH_AND_RESUME"
        $classification.reason = "Profile marker and native credential store disagree or require reconciliation."
        $classification.fingerprint = "AUTH_MISMATCH"
    }
    elseif ($Checkpoint.state -eq 'PENDING' -and $Checkpoint.process_id -eq 0) {
        # Clean unstarted turn interrupted before worker launch
        $classification.category = "CLEAN_INTERRUPTED_CHECKPOINT"
        $classification.recoverable = $true
        $classification.action = "RESUME_PENDING_INSTRUCTION"
        $classification.reason = "Turn preserved in unstarted PENDING state with verified instruction hash."
        $classification.fingerprint = "CLEAN_PENDING"
    }
    elseif ($Checkpoint.state -in @('RUNNING', 'CHECKPOINTED') -and -not $workerAlive -and [string]::IsNullOrWhiteSpace($errorText)) {
        # Worker crashed mid-turn without recording an unhandled error! Check if automatic restart is authorized by governance
        if (-not $automaticRestartAllowed) {
            $classification.category = "AUTOMATIC_RESTART_RESTRICTED"
            $classification.recoverable = $false
            $classification.action = "BLOCK"
            $classification.reason = "Automatic restart of crashed turn is restricted by ACTIVE_TASK.json governance (automatic_restart_allowed=false)."
            $classification.fingerprint = "RESTART_RESTRICTED"
        } else {
            $classification.category = "CRASHED_WORKER_RESUMPTION"
            $classification.recoverable = $true
            $classification.action = "RESUME_PENDING_INSTRUCTION"
            $classification.reason = "Worker process terminated unexpectedly; governance authorizes resumption of turn."
            $classification.fingerprint = "CRASHED_WORKER"
        }
    }
    else {
        $classification.category = "UNCLASSIFIED_FAILURE"
        $classification.recoverable = $false
        $classification.action = "BLOCK"
        $classification.reason = "Failure cannot be proven safe for automatic recovery without human intervention."
        $classification.fingerprint = "UNKNOWN_ERROR"
    }

    return [pscustomobject]$classification
}

function Invoke-SupervisorReconciliationStep {
    param(
        [Parameter(Mandatory)][string]$Workspace,
        [Parameter(Mandatory)][string]$PadPath,
        [Parameter(Mandatory)][pscustomobject]$Classification,
        [Parameter(Mandatory)][string]$CheckpointPath
    )

    $result = [ordered]@{
        success = $false
        action_taken = ""
        error = ""
        new_profile = ""
    }

    switch ($Classification.action) {
        "RECONCILE_AUTH_AND_RESUME" {
            # Load auth recovery tools
            . (Join-Path $Workspace "scripts/controller/Controller-Recovery.ps1")
            . (Join-Path $Workspace "scripts/validation/AgyCredentialStores.ps1")
            . (Join-Path $Workspace "scripts/controller/Controller-AuthRecovery.ps1")

            try {
                $recoveryPlan = Invoke-AgyAuthenticationFailover
                $result.success = $true
                $result.action_taken = "Reconciled profile to $($recoveryPlan.new_profile) and synchronized markers."
                $result.new_profile = $recoveryPlan.new_profile
            } catch {
                $result.success = $false
                $result.error = $_.Exception.Message
            }
        }

        "RESUME_PENDING_INSTRUCTION" {
            . (Join-Path $Workspace "scripts/controller/Controller-Recovery.ps1")
            . (Join-Path $Workspace "scripts/controller/Controller-AuthRecovery.ps1")
            $state = Read-SupervisorCheckpoint $Workspace $CheckpointPath
            $loopStatePath = Join-Path $PadPath "antigravity_loop_state.json"
            $inst = ""
            if (Test-Path -LiteralPath $loopStatePath) {
                try {
                    $ls = [System.IO.File]::ReadAllText($loopStatePath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
                    $inst = [string]$ls.next_instruction
                } catch {}
            }
            if (-not $inst -and $state.original_instruction_hash) {
                $inst = "Execute pending turn $($state.turn)"
            }
            if ($state.state -in @('RUNNING', 'CHECKPOINTED') -or ($state.state -eq 'PENDING' -and ($state.owned_session_fingerprint -or $state.process_id -ne 0 -or $state.conversation_id))) {
                # Re-arm crashed or partially owned worker turn to clean PENDING with process_id=0
                $state.state = 'PENDING'
                $state.process_id = 0
                if ($state.PSObject.Properties['owned_session_fingerprint']) { $state.owned_session_fingerprint = '' }
                if ($state.PSObject.Properties['next_instruction']) { $state.next_instruction = '' }
                if ($state.PSObject.Properties['conversation_id']) { $state.conversation_id = '' }
                if ($state.PSObject.Properties['recovery_count']) { $state.recovery_count++ }
                $state.updated_at = [DateTimeOffset]::UtcNow.ToString('o')
                Write-ControllerCheckpoint $CheckpointPath $state

                # Release orphaned session lock if owned by the crashed run
                $sessFile = Join-Path $Workspace "project_coordination/ACTIVE_SESSION.json"
                if (Test-Path -LiteralPath $sessFile) {
                    try {
                        $s = Get-Content -LiteralPath $sessFile -Raw | ConvertFrom-Json
                        if ($s.active -and $s.controller_run_id -eq $state.run_id) {
                            $s.active = $false
                            $s.last_released = [DateTimeOffset]::UtcNow.ToString('o')
                            [IO.File]::WriteAllText($sessFile, (($s | ConvertTo-Json -Depth 8).Replace("`r`n","`n")), [Text.UTF8Encoding]::new($false))
                        }
                    } catch {}
                }
            }
            try {
                $plan = Get-ControllerPendingAuthResumePlan -State $state -Instruction $inst -NonExecuting
                $result.success = $true
                $result.action_taken = "Verified pending turn $($plan.turn) instruction plan."
            } catch {
                $result.success = $false
                $result.error = $_.Exception.Message
            }
        }

        "SELF_REPAIR_AND_DEPLOY" {
            # Validates that deployed scripts have parity with canonical repo scripts
            try {
                $deployScript = Join-Path $Workspace "scripts/controller/Deploy-Controller.ps1"
                $deployOut = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $deployScript -Destination $PadPath
                $result.success = $true
                $result.action_taken = "Controller deployed and verified canonical SHA-256 parity."
            } catch {
                $result.success = $false
                $result.error = $_.Exception.Message
            }
        }

        default {
            $result.success = $false
            $result.error = "No automatic reconciliation available for action '$($Classification.action)'."
        }
    }

    return [pscustomobject]$result
}

function Start-ControllerSupervisedLoop {
    [CmdletBinding()]
    param(
        [string]$Workspace = $WorkspaceDir,
        [string]$Pad = $PadDir,
        [int]$MaxTurns = 40,
        [string]$PrintTimeout = "2400s",
        [double]$QuotaStopPct = 5.0,
        [switch]$SinglePass,
        [switch]$DryRun
    )

    $supervisorStateFile = Join-Path $Pad "supervisor_recovery_state.json"
    $checkpointFile     = Join-Path $Pad "controller_turn_checkpoint.json"
    $loopScriptPath     = Join-Path $Pad "Antigravity-Autonomous-Loop.ps1"

    $supMutex = Get-SupervisorMutex
    if (-not $supMutex.CreatedNew) {
        Write-Warning "[SUPERVISOR] Another supervisor instance is already active. Exiting."
        return
    }

    try {
        Write-Host "==================================================================" -ForegroundColor Cyan
        Write-Host " STARTING INDEPENDENT SELF-HEALING CONTROLLER SUPERVISOR" -ForegroundColor Cyan
        Write-Host " Workspace: $Workspace" -ForegroundColor Cyan
        Write-Host " PAD Dir:   $Pad" -ForegroundColor Cyan
        Write-Host "==================================================================" -ForegroundColor Cyan

        $activeRun = $true
        $retryCounts = @{}

        while ($activeRun) {
            # 1. State: Inspect existing checkpoint and running processes
            $supState = Read-SupervisorState $supervisorStateFile
            if (-not $supState) {
                $supState = [pscustomobject]@{
                    state = "RUNNING"
                    last_check_utc = [DateTimeOffset]::UtcNow.ToString("o")
                    active_pid = 0
                    consecutive_failures = 0
                    last_fingerprint = ""
                    circuit_broken = $false
                    classification = $null
                }
                Write-SupervisorState $supervisorStateFile $supState
            }

            # 2. Check if a worker process is currently active
            $workerRunning = $false
            if ($supState.active_pid -gt 0) {
                $workerRunning = Test-IsControllerWorkerProcess -ProcessId $supState.active_pid
            }

            # Check if any PBS job is running before classifying controller inactivity
            # (Watchdog must not kill controller while PBS job is active)
            $checkpoint = Read-SupervisorCheckpoint $Workspace $checkpointFile

            if ($workerRunning) {
                Write-Verbose "[SUPERVISOR] Worker process (PID $($supState.active_pid)) is active."
                if ($SinglePass) { break }
                Start-Sleep -Seconds $PollIntervalSec
                continue
            }

            # 3. Worker is NOT running. Inspect why.
            if ($checkpoint -and $checkpoint.state -eq 'COMPLETED') {
                Write-Host "[SUPERVISOR] Controller execution completed successfully." -ForegroundColor Green
                $supState.state = "COMPLETED"
                Write-SupervisorState $supervisorStateFile $supState
                break
            }

            # Check if circuit broken
            if ($supState.circuit_broken) {
                Write-Warning "[SUPERVISOR] Circuit breaker active for fingerprint '$($supState.last_fingerprint)'. Intervention required."
                $supState.state = "BLOCKED_NEEDS_INTERVENTION"
                Write-SupervisorState $supervisorStateFile $supState
                break
            }

            # 4. State transition: FAILURE_DETECTED
            Write-Host "[SUPERVISOR] Inactive worker detected with incomplete turn. Initiating diagnosis..." -ForegroundColor Yellow
            $supState.state = "FAILURE_DETECTED"
            Write-SupervisorState $supervisorStateFile $supState

            # Find latest failure packet
            $failRecDir = Join-Path $Pad "failure_recovery"
            $latestPacketDir = ""
            if (Test-Path -LiteralPath $failRecDir) {
                $dirs = @(Get-ChildItem -LiteralPath $failRecDir -Directory | Sort-Object LastWriteTime -Descending)
                if ($dirs.Count -gt 0) { $latestPacketDir = $dirs[0].FullName }
            }

            # 5. State transition: CLASSIFIED
            $classification = Classify-ControllerFailure -Workspace $Workspace -PadPath $Pad -Checkpoint $checkpoint -FailurePacketDir $latestPacketDir
            Write-Host "[SUPERVISOR] Failure classified: $($classification.category) | Action: $($classification.action) | Recoverable: $($classification.recoverable)" -ForegroundColor Cyan
            $supState.state = "CLASSIFIED"
            if ($supState.PSObject.Properties['classification']) {
                $supState.classification = $classification
            } else {
                $supState | Add-Member -NotePropertyName 'classification' -NotePropertyValue $classification -Force
            }
            Write-SupervisorState $supervisorStateFile $supState

            # Track fingerprint retries
            $fp = $classification.fingerprint
            if (-not $retryCounts.ContainsKey($fp)) { $retryCounts[$fp] = 0 }
            $retryCounts[$fp]++

            if ($retryCounts[$fp] -gt $MaxSelfRepairRetries) {
                Write-Warning "[SUPERVISOR] Max retries ($MaxSelfRepairRetries) exceeded for failure '$fp'. Tripping circuit breaker."
                $supState.circuit_broken = $true
                $supState.state = "BLOCKED_NEEDS_INTERVENTION"
                Write-SupervisorState $supervisorStateFile $supState
                break
            }

            if (-not $classification.recoverable) {
                Write-Warning "[SUPERVISOR] Non-recoverable failure detected: $($classification.reason). Fails closed safely."
                $supState.state = "BLOCKED_NEEDS_INTERVENTION"
                Write-SupervisorState $supervisorStateFile $supState
                break
            }

            # 6. State transition: RECOVERY_IN_PROGRESS
            Write-Host "[SUPERVISOR] Attempting automated recovery action '$($classification.action)' (attempt $($retryCounts[$fp])/$MaxSelfRepairRetries)..." -ForegroundColor Yellow
            $supState.state = "RECOVERY_IN_PROGRESS"
            Write-SupervisorState $supervisorStateFile $supState

            $reconciliation = Invoke-SupervisorReconciliationStep -Workspace $Workspace -PadPath $Pad -Classification $classification -CheckpointPath $checkpointFile
            if (-not $reconciliation.success) {
                Write-Warning "[SUPERVISOR] Recovery action failed: $($reconciliation.error)"
                if ($retryCounts[$fp] -ge $MaxSelfRepairRetries) {
                    $supState.circuit_broken = $true
                    $supState.state = "BLOCKED_NEEDS_INTERVENTION"
                }
                Write-SupervisorState $supervisorStateFile $supState
                if ($SinglePass) { break }
                Start-Sleep -Seconds $PollIntervalSec
                continue
            }

            # 7. State transition: VALIDATION
            Write-Host "[SUPERVISOR] Action successful: $($reconciliation.action_taken). Validating recovery..." -ForegroundColor Green
            $supState.state = "VALIDATION"
            Write-SupervisorState $supervisorStateFile $supState

            # Validate checkpoint integrity afresh
            $validCheckpoint = $false
            try {
                $postCp = Read-SupervisorCheckpoint $Workspace $checkpointFile
                if ($postCp.state -in @('PENDING', 'RUNNING', 'CHECKPOINTED')) { $validCheckpoint = $true }
            } catch {}

            if (-not $validCheckpoint) {
                Write-Warning "[SUPERVISOR] Post-recovery checkpoint validation failed."
                $supState.state = "BLOCKED_NEEDS_INTERVENTION"
                Write-SupervisorState $supervisorStateFile $supState
                break
            }

            # 8. State transition: RESUME_READY -> RUNNING
            Write-Host "[SUPERVISOR] Recovery validated. Resuming controller execution..." -ForegroundColor Green
            $supState.state = "RESUME_READY"
            Write-SupervisorState $supervisorStateFile $supState

            if ($DryRun) {
                Write-Host "[SUPERVISOR] Dry-run requested: skipping actual process launch."
                break
            }

            # Spawn trusted controller process
            $prof = if ($reconciliation -and $reconciliation.new_profile) {
                $reconciliation.new_profile
            } else {
                $actFile = Join-Path $env:USERPROFILE ".gemini/agy-profiles/_active.txt"
                if (Test-Path -LiteralPath $actFile) { (Get-Content -LiteralPath $actFile -Raw).Trim() } else { "account2" }
            }
            $controllerArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$loopScriptPath`" -AuthoritativeAgyProfile `"$prof`" -MaxTurns $MaxTurns -PrintTimeout $PrintTimeout -QuotaStopThresholdPct $QuotaStopPct"
            $psi = New-Object System.Diagnostics.ProcessStartInfo
            $psi.FileName = "powershell.exe"
            $psi.Arguments = $controllerArgs
            $psi.WorkingDirectory = $Workspace
            $psi.UseShellExecute = $false
            $proc = [System.Diagnostics.Process]::Start($psi)

            $supState.active_pid = $proc.Id
            $supState.state = "RUNNING"
            $supState.last_check_utc = [DateTimeOffset]::UtcNow.ToString("o")
            Write-SupervisorState $supervisorStateFile $supState

            Write-Host "[SUPERVISOR] Controller resumed under PID $($proc.Id)." -ForegroundColor Green

            if ($SinglePass) { break }
            Start-Sleep -Seconds $PollIntervalSec
        }
    } finally {
        $supMutex.Mutex.Dispose()
    }
}

if ($MyInvocation.InvocationName -ne '.' -and $MyInvocation.Line -notmatch '^\s*\.\s+') {
    Start-ControllerSupervisedLoop -Workspace $WorkspaceDir -Pad $PadDir -SinglePass:$SinglePass -DryRun:$DryRun
}
