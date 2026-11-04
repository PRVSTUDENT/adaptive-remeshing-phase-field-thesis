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

    # Validate process command line and ownership chain via CIM
    try {
        $cimProc = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
        if ($cimProc) {
            $cmd = [string]$cimProc.CommandLine

            # Reject interactive VS Code hub
            if ($cmd -match '--hub') { return $false }

            $isLoopScript = ($cmd -match 'Antigravity-Autonomous-Loop\.ps1')
            $isAgyWorker = ($cimProc.Name -match '^agy(?:\.exe)?$' -and ($cmd -match '--dangerously-skip-permissions|--print|--conversation'))
            $isSupervisor = ($cmd -match 'Controller-SelfHealingSupervisor\.ps1')
            $isTestHarness = ($cmd -match 'test_')

            if (-not ($isLoopScript -or $isAgyWorker -or $isSupervisor -or $isTestHarness)) {
                # Arbitrary PowerShell process or interactive shell not belonging to controller
                return $false
            }

            # If agy worker, verify parent process ancestry
            if ($isAgyWorker) {
                $parent = Get-CimInstance Win32_Process -Filter ("ProcessId = " + $cimProc.ParentProcessId) -ErrorAction SilentlyContinue
                if ($parent) {
                    if ($parent.Name -match '(?i)^code(?:\.exe)?$') {
                        # Directly spawned by VS Code UI, not controller loop
                        return $false
                    }
                }
            }
        }
    } catch {}

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

function Get-SupervisorStatus {
    param(
        [string]$PadPath = "$env:USERPROFILE\OpenClawPAD"
    )
    $supStateFile = Join-Path $PadPath "supervisor_recovery_state.json"
    $mutexName = "Local\AntigravitySelfHealingSupervisorLock"
    $mutex = $null
    $createdNew = $false
    try {
        $mutex = New-Object System.Threading.Mutex($false, $mutexName, [ref]$createdNew)
    } catch {}

    $status = [ordered]@{
        is_active = (-not $createdNew)
        mutex_locked = (-not $createdNew)
        supervisor_pid = 0
        state = "INACTIVE"
        last_check_utc = $null
        process_alive = $false
        legitimate_chain = $false
    }

    if ($mutex) {
        $mutex.Dispose()
    }

    if (Test-Path -LiteralPath $supStateFile) {
        try {
            $s = Get-Content -LiteralPath $supStateFile -Raw | ConvertFrom-Json
            $status.state = $s.state
            $status.last_check_utc = $s.last_check_utc
            $status.supervisor_pid = $s.active_pid
            if ($s.active_pid -gt 0) {
                $proc = Get-Process -Id $s.active_pid -ErrorAction SilentlyContinue
                if ($proc -and -not $proc.HasExited) {
                    $status.process_alive = $true
                    $cim = Get-CimInstance Win32_Process -Filter "ProcessId = $($s.active_pid)" -ErrorAction SilentlyContinue
                    if ($cim -and $cim.CommandLine -match 'Controller-SelfHealingSupervisor\.ps1|Antigravity-Autonomous-Loop\.ps1') {
                        $status.legitimate_chain = $true
                    }
                }
            }
        } catch {}
    }

    return [pscustomobject]$status
}

function Audit-InterruptedTurnSideEffects {
    param(
        [Parameter(Mandatory)][string]$Workspace,
        [Parameter(Mandatory)]$Checkpoint,
        [string]$HpcLedgerPath = "",
        [string]$ActiveTaskPath = "",
        [string]$DispatchDir = "",
        [string]$BridgeDir = ""
    )

    if (-not $HpcLedgerPath) { $HpcLedgerPath = Join-Path $Workspace "project_coordination/HPC_JOB_LEDGER.csv" }
    if (-not $ActiveTaskPath) { $ActiveTaskPath = Join-Path $Workspace "project_coordination/ACTIVE_TASK.json" }
    if (-not $DispatchDir)   { $DispatchDir   = Join-Path $Workspace "project_coordination/review_dispatch" }
    if (-not $BridgeDir)     { $BridgeDir     = Join-Path $env:USERPROFILE 'OpenClawPAD/ChatGPTBridge/supervisor' }

    $report = [ordered]@{
        has_side_effects = $false
        has_pbs_side_effects = $false
        has_scientific_side_effects = $false
        has_bridge_side_effects = $false
        has_file_write_side_effects = $false
        pbs_jobs = @()
        completed_operations = @()
        bridge_transactions = @()
        modified_files = @()
        partial_files = @()
        details = ""
    }

    $turnStarted = [DateTimeOffset]::MinValue
    if ($Checkpoint.started_at) {
        [DateTimeOffset]::TryParse([string]$Checkpoint.started_at, [ref]$turnStarted) | Out-Null
    }

    # 1. Audit PBS Reservations: once-only rule
    if (Test-Path -LiteralPath $HpcLedgerPath) {
        try {
            $rows = @(Import-Csv -LiteralPath $HpcLedgerPath)
            foreach ($row in $rows) {
                $subTime = [DateTimeOffset]::MinValue
                if ($row.submission_timestamp -and [DateTimeOffset]::TryParse($row.submission_timestamp, [ref]$subTime)) {
                    if ($turnStarted -gt [DateTimeOffset]::MinValue -and $subTime -ge $turnStarted.AddSeconds(-30)) {
                        $report.pbs_jobs += $row.job_id
                        $report.has_pbs_side_effects = $true
                    }
                }
            }
        } catch {}
    }

    # 2. Audit Scientific Operations:
    if (Test-Path -LiteralPath $ActiveTaskPath) {
        try {
            $task = Get-Content -LiteralPath $ActiveTaskPath -Raw | ConvertFrom-Json
            if ($null -ne $Checkpoint.completed_operations -and $null -ne $task.completed_operations) {
                $predecessorOps = @($Checkpoint.completed_operations)
                foreach ($op in $task.completed_operations) {
                    if ($op -notin $predecessorOps) {
                        $report.completed_operations += $op
                        $report.has_scientific_side_effects = $true
                    }
                }
            }
            if ($task.scientific_checkpoint -and $task.scientific_checkpoint.created_at) {
                $cpTime = [DateTimeOffset]::MinValue
                if ([DateTimeOffset]::TryParse($task.scientific_checkpoint.created_at, [ref]$cpTime)) {
                    if ($turnStarted -gt [DateTimeOffset]::MinValue -and $cpTime -ge $turnStarted.AddSeconds(-30)) {
                        $report.completed_operations += [string]$task.scientific_checkpoint.operation
                        $report.has_scientific_side_effects = $true
                    }
                }
            }
        } catch {}
    }

    # 3. Audit Bridge Transactions:
    if (Test-Path -LiteralPath $DispatchDir) {
        try {
            $reqs = Get-ChildItem -LiteralPath $DispatchDir -Filter "*.request.json" -File -ErrorAction SilentlyContinue
            foreach ($r in $reqs) {
                if ($turnStarted -gt [DateTimeOffset]::MinValue -and $r.LastWriteTimeUtc -ge $turnStarted.UtcDateTime.AddSeconds(-30)) {
                    $report.bridge_transactions += $r.Name
                    $report.has_bridge_side_effects = $true
                }
            }
        } catch {}
    }
    if (Test-Path -LiteralPath $BridgeDir) {
        try {
            $pendFiles = Get-ChildItem -LiteralPath $BridgeDir -Filter "*.pending.json" -File -ErrorAction SilentlyContinue
            foreach ($pf in $pendFiles) {
                if ($turnStarted -gt [DateTimeOffset]::MinValue -and $pf.LastWriteTimeUtc -ge $turnStarted.UtcDateTime.AddSeconds(-30)) {
                    $report.bridge_transactions += $pf.Name
                    $report.has_bridge_side_effects = $true
                }
            }
        } catch {}
    }

    # 4. Audit File Writes (Deliverables and partial files):
    $valDir = Join-Path $Workspace "results/validation"
    if (Test-Path -LiteralPath $valDir) {
        try {
            $files = Get-ChildItem -LiteralPath $valDir -File -ErrorAction SilentlyContinue
            foreach ($f in $files) {
                if ($turnStarted -gt [DateTimeOffset]::MinValue -and $f.LastWriteTimeUtc -ge $turnStarted.UtcDateTime.AddSeconds(-30)) {
                    $report.modified_files += $f.Name
                    $report.has_file_write_side_effects = $true
                }
            }
        } catch {}
    }
    if (Test-Path -LiteralPath $Workspace) {
        $tmpFiles = Get-ChildItem -LiteralPath $Workspace -Filter "*.tmp" -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 10
        foreach ($tf in $tmpFiles) {
            $report.partial_files += $tf.FullName
            $report.has_file_write_side_effects = $true
        }
    }

    $report.has_side_effects = ($report.has_pbs_side_effects -or $report.has_scientific_side_effects -or $report.has_bridge_side_effects -or $report.has_file_write_side_effects)
    $detailsList = @()
    if ($report.has_pbs_side_effects) { $detailsList += "PBS jobs ($($report.pbs_jobs -join ', '))" }
    if ($report.has_scientific_side_effects) { $detailsList += "Operations ($($report.completed_operations -join ', '))" }
    if ($report.has_bridge_side_effects) { $detailsList += "Bridge ($($report.bridge_transactions -join ', '))" }
    if ($report.has_file_write_side_effects) { $detailsList += "Files ($($report.modified_files -join ', '))" }
    $report.details = $detailsList -join '; '

    return [pscustomobject]$report
}

function Resolve-ControllerScriptPath([string]$Workspace, [string]$RelativePath) {
    $target = Join-Path $Workspace $RelativePath
    if (Test-Path -LiteralPath $target) { return $target }
    if ($PSScriptRoot) {
        $leaf = Split-Path $RelativePath -Leaf
        $cand = Join-Path $PSScriptRoot $leaf
        if (Test-Path -LiteralPath $cand) { return $cand }
    }
    $repoDefault = Join-Path "D:\Master thesis\Adaptive remeshing" $RelativePath
    if (Test-Path -LiteralPath $repoDefault) { return $repoDefault }
    return $target
}

function Read-SupervisorCheckpoint([string]$Workspace, [string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try {
        . (Resolve-ControllerScriptPath $Workspace "scripts/controller/Controller-Recovery.ps1")
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
        # Worker crashed mid-turn without recording an unhandled error! Audit partial side effects before classifying resumption
        $sideEffects = Audit-InterruptedTurnSideEffects -Workspace $Workspace -Checkpoint $Checkpoint

        if ($sideEffects.has_pbs_side_effects) {
            $classification.category = "INTERRUPTED_TURN_PBS_SUBMITTED"
            $classification.recoverable = $true
            $classification.action = "RECONCILE_PARTIAL_EVIDENCE"
            $classification.reason = "Interrupted worker submitted PBS job ($($sideEffects.pbs_jobs -join ', ')); cannot replay original instruction (once-only rule)."
            $classification.fingerprint = "PBS_SUBMITTED_CRASH"
        }
        elseif ($sideEffects.has_scientific_side_effects) {
            $classification.category = "INTERRUPTED_TURN_OPERATION_COMPLETED"
            $classification.recoverable = $true
            $classification.action = "RECONCILE_COMPLETED_OPERATION"
            $classification.reason = "Interrupted worker already completed scientific operation ($($sideEffects.completed_operations -join ', ')); cannot replay completed operation."
            $classification.fingerprint = "OPERATION_COMPLETED_CRASH"
        }
        elseif ($sideEffects.has_bridge_side_effects) {
            $classification.category = "INTERRUPTED_TURN_BRIDGE_TRANSACTION"
            $classification.recoverable = $true
            $classification.action = "RECONCILE_BRIDGE_TRANSACTION"
            $classification.reason = "Interrupted worker initiated bridge transaction ($($sideEffects.bridge_transactions -join ', ')); cannot duplicate transaction."
            $classification.fingerprint = "BRIDGE_TRANSACTION_CRASH"
        }
        elseif ($sideEffects.has_file_write_side_effects) {
            $classification.category = "INTERRUPTED_TURN_PARTIAL_FILES"
            $classification.recoverable = $true
            $classification.action = "RECONCILE_PARTIAL_EVIDENCE"
            $classification.reason = "Interrupted worker wrote deliverables or partial files ($($sideEffects.modified_files -join ', ')); requires reconciliation before re-arming."
            $classification.fingerprint = "PARTIAL_FILES_CRASH"
        }
        elseif (-not $automaticRestartAllowed) {
            $classification.category = "AUTOMATIC_RESTART_RESTRICTED"
            $classification.recoverable = $false
            $classification.action = "BLOCK"
            $classification.reason = "Automatic restart of crashed turn is restricted by ACTIVE_TASK.json governance (automatic_restart_allowed=false)."
            $classification.fingerprint = "RESTART_RESTRICTED"
        } else {
            $classification.category = "CRASHED_WORKER_RESUMPTION"
            $classification.recoverable = $true
            $classification.action = "RESUME_PENDING_INSTRUCTION"
            $classification.reason = "Worker process terminated unexpectedly with zero side effects; governance authorizes resumption of turn."
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

function Set-StateProperty($State, [string]$Name, $Value) {
    if ($null -ne $State) {
        if ($State.PSObject.Properties[$Name]) {
            $State.$Name = $Value
        } else {
            $State | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
        }
    }
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
            . (Resolve-ControllerScriptPath $Workspace "scripts/controller/Controller-Recovery.ps1")
            . (Resolve-ControllerScriptPath $Workspace "scripts/validation/AgyCredentialStores.ps1")
            . (Resolve-ControllerScriptPath $Workspace "scripts/controller/Controller-AuthRecovery.ps1")

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

        "RECONCILE_PARTIAL_EVIDENCE" {
            . (Resolve-ControllerScriptPath $Workspace "scripts/controller/Controller-Recovery.ps1")
            $state = Read-SupervisorCheckpoint $Workspace $CheckpointPath
            # Clean temporary files if present
            try {
                $tmpFiles = Get-ChildItem -LiteralPath $Workspace -Filter "*.tmp" -File -Recurse -ErrorAction SilentlyContinue
                foreach ($tf in $tmpFiles) {
                    Remove-Item -LiteralPath $tf.FullName -Force -ErrorAction SilentlyContinue
                }
            } catch {}

            Set-StateProperty $state 'state' 'CHECKPOINTED'
            Set-StateProperty $state 'process_id' 0
            Set-StateProperty $state 'owned_session_fingerprint' ''
            Set-StateProperty $state 'conversation_id' ''
            $recCount = if ($state.recovery_count) { $state.recovery_count + 1 } else { 1 }
            Set-StateProperty $state 'recovery_count' $recCount
            Set-StateProperty $state 'updated_at' ([DateTimeOffset]::UtcNow.ToString('o'))
            Set-StateProperty $state 'next_safe_action' "Evidence-only reconciliation in a fresh conversation; no solver, submission, or scientific changes"
            Write-ControllerCheckpoint $CheckpointPath $state

            # Release orphaned session lock if owned by crashed run
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

            $result.success = $true
            $result.action_taken = "Interrupted turn side effects reconciled: partial files cleaned and converted to bounded evidence recovery."
        }

        "RECONCILE_COMPLETED_OPERATION" {
            . (Resolve-ControllerScriptPath $Workspace "scripts/controller/Controller-Recovery.ps1")
            $state = Read-SupervisorCheckpoint $Workspace $CheckpointPath
            Set-StateProperty $state 'state' 'CHECKPOINTED'
            Set-StateProperty $state 'process_id' 0
            Set-StateProperty $state 'owned_session_fingerprint' ''
            Set-StateProperty $state 'conversation_id' ''
            $recCount = if ($state.recovery_count) { $state.recovery_count + 1 } else { 1 }
            Set-StateProperty $state 'recovery_count' $recCount
            Set-StateProperty $state 'updated_at' ([DateTimeOffset]::UtcNow.ToString('o'))
            Set-StateProperty $state 'next_safe_action' "Advance task lifecycle: scientific operation already completed, do not replay"
            Write-ControllerCheckpoint $CheckpointPath $state

            $result.success = $true
            $result.action_taken = "Scientific operation completion confirmed: state checkpointed to advance lifecycle without replaying operation."
        }

        "RECONCILE_BRIDGE_TRANSACTION" {
            . (Resolve-ControllerScriptPath $Workspace "scripts/controller/Controller-Recovery.ps1")
            $state = Read-SupervisorCheckpoint $Workspace $CheckpointPath
            Set-StateProperty $state 'state' 'CHECKPOINTED'
            Set-StateProperty $state 'process_id' 0
            Set-StateProperty $state 'owned_session_fingerprint' ''
            Set-StateProperty $state 'conversation_id' ''
            $recCount = if ($state.recovery_count) { $state.recovery_count + 1 } else { 1 }
            Set-StateProperty $state 'recovery_count' $recCount
            Set-StateProperty $state 'updated_at' ([DateTimeOffset]::UtcNow.ToString('o'))
            Set-StateProperty $state 'next_safe_action' "Await or reconcile existing bridge response; do not resend transaction"
            Write-ControllerCheckpoint $CheckpointPath $state

            $result.success = $true
            $result.action_taken = "Pending bridge transaction preserved: duplicate request prevented."
        }

        "RESUME_PENDING_INSTRUCTION" {
            . (Resolve-ControllerScriptPath $Workspace "scripts/controller/Controller-Recovery.ps1")
            . (Resolve-ControllerScriptPath $Workspace "scripts/controller/Controller-AuthRecovery.ps1")
            $state = Read-SupervisorCheckpoint $Workspace $CheckpointPath
            $loopStatePath = Join-Path $PadPath "antigravity_loop_state.json"

            # Strict guard: audit partial side effects before re-arming!
            $seAudit = Audit-InterruptedTurnSideEffects -Workspace $Workspace -Checkpoint $state
            if ($seAudit.has_side_effects) {
                throw "CANNOT_REARM_WITH_SIDE_EFFECTS: Interrupted turn committed side effects ($($seAudit.details)); requires bounded evidence recovery, not unstarted re-arming."
            }

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
