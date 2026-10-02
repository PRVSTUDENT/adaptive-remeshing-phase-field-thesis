import os

target_path = r"C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"

with open(target_path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

has_crlf = "\r\n" in content
content = content.replace("\r\n", "\n")

# 1. Update Get-LivePbsJobs to use qstat -x -u and flexible column parsing
old_live_fn = '''function Get-LivePbsJobs {
    [CmdletBinding()]
    param(
        [string]$User = "pr21vyci",
        [string]$HostAlias = "tu_freiberg",
        [string]$ConfigPath = "$env:USERPROFILE\\.ssh\\codex_config"
    )

    $sshCommand = Get-Command ssh.exe -ErrorAction Stop
    $sshPath = $sshCommand.Source

    $remoteCommand = "qstat -u $User"

    $savedErrorActionPreference = $ErrorActionPreference
    $hadNativePreference = $null -ne (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue)
    if ($hadNativePreference) {
        $savedNativePreference = $PSNativeCommandUseErrorActionPreference
    }

    try {
        $ErrorActionPreference = "Continue"
        if ($hadNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $false
        }

        $raw = & $sshPath -F $ConfigPath $HostAlias $remoteCommand 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedErrorActionPreference
        if ($hadNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $savedNativePreference
        }
    }

    $cleanRaw = @(
        $raw |
        ForEach-Object {
            $_.ToString()
        } |
        Where-Object {
            $_ -notmatch "post-quantum key exchange algorithm"
        }
    )

    $text = ($cleanRaw | Out-String).Trim()

    if ($exitCode -ne 0) {
        throw "Failed to query live scheduler ($remoteCommand):`n$text"
    }

    $lines = $text -split "`r?`n"

    $liveJobs = @()
    $runningJobs = @()
    $queuedJobs = @()
    $otherJobs = @()

    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("Job id") -or $trimmed.StartsWith("---")) {
            continue
        }

        $parts = ($trimmed -split '\\s+') | Where-Object { $_ -ne '' }
        if ($parts.Count -ge 5) {
            $jobId = $parts[0]
            # In TU Freiberg PBS: Job ID (0), Name (1), User (2), Time Use (3), S (4), Queue (5)
            $state = $parts[4].ToUpper()

            if ($jobId -match '^\\d+(\\.\\w+)?$') {
                $jobObj = [PSCustomObject]@{
                    JobId = $jobId
                    State = $state
                    Line  = $trimmed
                }
                $liveJobs += $jobObj

                if ($state -eq 'R') {
                    $runningJobs += $jobId
                }
                elseif ($state -in @('Q', 'H', 'W')) {
                    $queuedJobs += $jobId
                }
                else {
                    $otherJobs += $jobId
                }
            }
        }
    }

    return [PSCustomObject]@{
        LiveJobs     = $liveJobs
        RunningJobs  = $runningJobs
        QueuedJobs   = $queuedJobs
        WaitableJobs = @($runningJobs + $queuedJobs)
        OtherJobs    = $otherJobs
        RawOutput    = $text
    }
}'''

new_live_fn = '''function Get-LivePbsJobs {
    [CmdletBinding()]
    param(
        [string]$User = "pr21vyci",
        [string]$HostAlias = "tu_freiberg",
        [string]$ConfigPath = "$env:USERPROFILE\\.ssh\\codex_config"
    )

    $sshCommand = Get-Command ssh.exe -ErrorAction Stop
    $sshPath = $sshCommand.Source

    $remoteCommand = "qstat -x -u $User"

    $savedErrorActionPreference = $ErrorActionPreference
    $hadNativePreference = $null -ne (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue)
    if ($hadNativePreference) {
        $savedNativePreference = $PSNativeCommandUseErrorActionPreference
    }

    try {
        $ErrorActionPreference = "Continue"
        if ($hadNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $false
        }

        $raw = & $sshPath -F $ConfigPath $HostAlias $remoteCommand 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedErrorActionPreference
        if ($hadNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $savedNativePreference
        }
    }

    $cleanRaw = @(
        $raw |
        ForEach-Object {
            $_.ToString()
        } |
        Where-Object {
            $_ -notmatch "post-quantum key exchange algorithm"
        }
    )

    $text = ($cleanRaw | Out-String).Trim()

    if ($exitCode -ne 0) {
        throw "Failed to query live scheduler ($remoteCommand):`n$text"
    }

    $lines = $text -split "`r?`n"

    $liveJobs = @()
    $runningJobs = @()
    $queuedJobs = @()
    $finishedJobs = @()
    $otherJobs = @()

    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("Job id") -or $trimmed.StartsWith("Job ID") -or $trimmed.StartsWith("---") -or $trimmed.StartsWith("mmaster02:")) {
            continue
        }

        $parts = ($trimmed -split '\\s+') | Where-Object { $_ -ne '' }
        if ($parts.Count -ge 5) {
            $rawJobId = $parts[0] -replace '\\*$', ''
            
            # State determination:
            # In 6-col format (qstat -x <id>): [JobId, Name, User, TimeUse, S, Queue] -> S is index 4
            # In 11-col format (qstat -u <user>): [JobId, Username, Queue, Jobname, SessID, NDS, TSK, Memory, ReqTime, S, ElapTime] -> S is index 9
            $state = $null
            if ($parts.Count -ge 10 -and $parts[9] -match '^[RQHWFCEBT]$') {
                $state = $parts[9].ToUpper()
            }
            elseif ($parts.Count -ge 5 -and $parts[4] -match '^[RQHWFCEBT]$') {
                $state = $parts[4].ToUpper()
            }
            else {
                for ($i = 1; $i -lt $parts.Count; $i++) {
                    if ($parts[$i] -match '^[RQHWFCEBT]$') {
                        $state = $parts[$i].ToUpper()
                        break
                    }
                }
            }

            if ($rawJobId -match '^\\d+(\\.\\w+)?$') {
                $jobObj = [PSCustomObject]@{
                    JobId = $rawJobId
                    State = $state
                    Line  = $trimmed
                }
                $liveJobs += $jobObj

                if ($state -eq 'R') {
                    $runningJobs += $rawJobId
                }
                elseif ($state -in @('Q', 'H', 'W')) {
                    $queuedJobs += $rawJobId
                }
                elseif ($state -in @('F', 'C', 'E')) {
                    $finishedJobs += $rawJobId
                }
                else {
                    $otherJobs += $rawJobId
                }
            }
        }
    }

    return [PSCustomObject]@{
        LiveJobs     = $liveJobs
        RunningJobs  = $runningJobs
        QueuedJobs   = $queuedJobs
        WaitableJobs = @($runningJobs + $queuedJobs)
        FinishedJobs = $finishedJobs
        OtherJobs    = $otherJobs
        RawOutput    = $text
    }
}'''

assert old_live_fn in content, "old_live_fn not found"
content = content.replace(old_live_fn, new_live_fn, 1)
print("Get-LivePbsJobs successfully updated.")

# 2. Update STOP handler block in Section 5
old_stop_block = '''    if ($isStop) {

        Write-LoopLog `
            -Turn $CurrentTurn `
            -Tier "CONTROLLER" `
            -Action "CHATGPT_STOP_RECEIVED" `
            -Message "ChatGPT STOP received. Entering scheduler-controlled wait logic."

        try {
            $liveScheduler = Get-LivePbsJobs
            $waitableJobs = @($liveScheduler.WaitableJobs)
            $trackedActive = @(Get-ActivePbsJobIds)

            # A 900s scheduler wait is justified ONLY for genuine Q/R jobs.
            # Intersect tracked jobs with live Q/R jobs, or use live Q/R jobs directly.
            $activeJobsToWait = @()
            if ($waitableJobs.Count -gt 0) {
                if ($trackedActive.Count -gt 0) {
                    $activeJobsToWait = @($trackedActive | Where-Object { $_ -in $waitableJobs })
                    if ($activeJobsToWait.Count -eq 0) {
                        $activeJobsToWait = $waitableJobs
                    }
                } else {
                    $activeJobsToWait = $waitableJobs
                }
            }
        }
        catch {

            Write-LoopLog `
                -Turn $CurrentTurn `
                -Tier "CONTROLLER" `
                -Action "ACTIVE_JOB_STATE_CHECK_RETRY" `
                -Message "Initial qstat check failed. Retrying after preserving STOP state. Error: $_"

            Write-Host ""
            Write-Host "[SCHEDULER] Initial qstat check failed." -ForegroundColor Yellow
            Write-Host "[SCHEDULER] Retaining STOP state and retrying scheduler query." -ForegroundColor Yellow

            Start-Sleep -Seconds 30

            try {
                $activeJobsToWait = @(Get-ActivePbsJobIds)
            }
            catch {

                Save-LoopStatus `
                    -Turn $CurrentTurn `
                    -Status "FAILED" `
                    -Tier "CONTROLLER" `
                    -Action "ACTIVE_JOB_STATE_CHECK_FAILED_AFTER_RETRY" `
                    -Details $_.Exception.Message

                break MainLoop
            }
        }

        if ($activeJobsToWait.Count -gt 0) {

            $pollingActive = $true
            $consecutiveQstatFailures = 0
            while ($pollingActive) {
                Write-Host ""
                Write-Host "[SCHEDULER] ChatGPT returned STOP while live PBS job(s) remain in Q/R state." `
                    -ForegroundColor Yellow

                Write-Host "[SCHEDULER] Active Q/R job(s): $($activeJobsToWait -join ', ')" `
                    -ForegroundColor Yellow

                Write-Host "[SCHEDULER] Entering WAITING_FOR_SCHEDULER: waiting 900 seconds before fresh scheduler review..." `
                    -ForegroundColor Cyan

                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "CONTROLLER" `
                    -Action "WAITING_FOR_SCHEDULER" `
                    -Message "Waiting 900 seconds for active Q/R PBS job(s): $($activeJobsToWait -join ', ')"

                Start-Sleep -Seconds 900

                try {
                    $qstatText = Invoke-DirectPbsQuery -JobIds $activeJobsToWait
                }
                catch {
                    $consecutiveQstatFailures++

                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "CONTROLLER" `
                        -Action "QSTAT_DIRECT_ERROR" `
                        -Message "Attempt $consecutiveQstatFailures failed for exact job(s) $($activeJobsToWait -join ', '): $_"

                    if ($consecutiveQstatFailures -lt 2) {
                        Write-Host "[SCHEDULER] Direct qstat review failed once." -ForegroundColor Yellow
                        Write-Host "[SCHEDULER] Retaining exact PBS job ID(s) and retrying after normal 900-second wait." -ForegroundColor Yellow

                        Write-LoopLog `
                            -Turn $CurrentTurn `
                            -Tier "CONTROLLER" `
                            -Action "QSTAT_DIRECT_RETRY_SAME_IDS" `
                            -Message "First direct qstat failure; exact job IDs retained for one additional normal polling cycle: $($activeJobsToWait -join ', ')"

                        continue
                    }

                    Save-LoopStatus `
                        -Turn $CurrentTurn `
                        -Status "FAILED" `
                        -Tier "CONTROLLER" `
                        -Action "QSTAT_DIRECT_ERROR_AFTER_RETRY" `
                        -Details "Two consecutive direct qstat failures for exact job(s) $($activeJobsToWait -join ', '): $($_.Exception.Message)"

                    break MainLoop
                }

                $consecutiveQstatFailures = 0

                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "CONTROLLER" `
                    -Action "POST_WAIT_QSTAT_RESULT" `
                    -Message $qstatText

                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "tier3_chatgpt" `
                    -Action "ESCALATE_SCHEDULER_REVIEW" `
                    -Message "Sending fresh direct scheduler result to ChatGPT bridge..."

                try {
                    $schedulerInstruction = Invoke-SchedulerReviewChatGPT -QstatText $qstatText
                }
                catch {
                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "tier3_chatgpt" `
                        -Action "CHATGPT_FAILURE_STOP" `
                        -Message "Error during scheduler review: $_"

                    Save-LoopStatus `
                        -Turn $CurrentTurn `
                        -Status "FAILED" `
                        -Tier "tier3_chatgpt" `
                        -Action "CHATGPT_ERROR" `
                        -Details $_.Exception.Message

                    break MainLoop
                }

                if ($schedulerInstruction -match '^(?i:stop)\s*$') {
                    # Check if jobs have transitioned away from Q/R (e.g. to F/C/E)
                    try {
                        $freshLive = Get-LivePbsJobs
                        if ($freshLive.WaitableJobs.Count -eq 0) {
                            Write-LoopLog `
                                -Turn $CurrentTurn `
                                -Tier "CONTROLLER" `
                                -Action "SCHEDULER_JOB_TERMINAL_NO_REWAIT" `
                                -Message "Job(s) transitioned to terminal state; exiting scheduler wait loop."
                            $pollingActive = $false
                            break
                        }
                    } catch {}

                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "CONTROLLER" `
                        -Action "SCHEDULER_STOP_REPOLL_SAME_IDS" `
                        -Message "ChatGPT replied stop on scheduler result; retaining active job(s) and repolling after wait: $($activeJobsToWait -join ', ')"
                }
                else {
                    $pollingActive = $false
                    $NextInstruction = $schedulerInstruction
                    $gptPreview = if ($NextInstruction.Length -gt 80) { $NextInstruction.Substring(0, 80) } else { $NextInstruction }
                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "tier3_chatgpt" `
                        -Action "CHATGPT_SCHEDULER_DISPATCH" `
                        -Message "ChatGPT post-qstat instruction received: ${gptPreview}..."
                }
            }
        }
        else {
            # ChatGPT STOP and no live Q/R PBS work remains -> genuine clean termination.
            Write-Host "`n==========================================================" -ForegroundColor Green
            Write-Host " AUTONOMOUS LOOP COMPLETED SAFELY (STOP SIGNAL RECEIVED) " -ForegroundColor Green
            Write-Host "==========================================================" -ForegroundColor Green

            Write-LoopLog `
                -Turn $CurrentTurn `
                -Tier "CONTROLLER" `
                -Action "LOOP_TERMINATED_SAFE" `
                -Message "ChatGPT stop received and zero live Q/R PBS jobs remain on scheduler."

            Save-LoopStatus `
                -Turn $CurrentTurn `
                -Status "STOPPED_CLEAN" `
                -Tier "CONTROLLER" `
                -Action "NORMAL_TERMINATION" `
                -Details "Zero live Q/R PBS jobs remain."

            break MainLoop
        }
    }'''

new_stop_block = '''    if ($isStop) {

        Write-LoopLog `
            -Turn $CurrentTurn `
            -Tier "CONTROLLER" `
            -Action "CHATGPT_STOP_RECEIVED" `
            -Message "ChatGPT STOP received. Entering scheduler-controlled wait/evaluation logic."

        # --------------------------------------------------------
        # Collect candidate PBS job IDs from:
        # 1. Latest agent response (e.g. submitted job ID)
        # 2. ACTIVE_TASK.json
        # 3. controller-state.json (tracked active jobs)
        # 4. Live scheduler (qstat -x -u)
        # --------------------------------------------------------
        $candidateJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

        # 1. From agent response
        if (-not [string]::IsNullOrWhiteSpace($agentResponse)) {
            $mMatches = [regex]::Matches($agentResponse, '\\b(\\d{6,8}(\\.mmaster02)?)\\b')
            foreach ($m in $mMatches) {
                $val = $m.Value
                if ($val -notmatch '\\.mmaster02$') { $val = "$val.mmaster02" }
                [void]$candidateJobIds.Add($val)
            }
        }

        # 2. From ACTIVE_TASK.json
        $activeTaskFile = Join-Path $WorkspaceDir "project_coordination\\ACTIVE_TASK.json"
        if (Test-Path -LiteralPath $activeTaskFile) {
            try {
                $taskData = Get-Content -LiteralPath $activeTaskFile -Raw | ConvertFrom-Json
                if ($taskData.active_job_id -and [string]$taskData.active_job_id -match '^\\d+(\\.\\w+)?$') {
                    $j = [string]$taskData.active_job_id
                    if ($j -notmatch '\\.mmaster02$') { $j = "$j.mmaster02" }
                    [void]$candidateJobIds.Add($j)
                }
            } catch {}
        }

        # 3. From controller-state.json
        try {
            $tracked = @(Get-ActivePbsJobIds)
            foreach ($j in $tracked) {
                if ($j) {
                    $jFull = if ($j -notmatch '\\.mmaster02$') { "$j.mmaster02" } else { $j }
                    [void]$candidateJobIds.Add($jFull)
                }
            }
        } catch {}

        # 4. From live scheduler
        try {
            $liveScheduler = Get-LivePbsJobs
            foreach ($j in @($liveScheduler.LiveJobs)) {
                if ($j.JobId) {
                    $jFull = if ($j.JobId -notmatch '\\.mmaster02$') { "$($j.JobId).mmaster02" } else { $j.JobId }
                    [void]$candidateJobIds.Add($jFull)
                }
            }
        } catch {}

        $activeJobsToQuery = @($candidateJobIds)

        if ($activeJobsToQuery.Count -gt 0) {

            # Perform direct qstat -x query on exact candidate job IDs
            $qstatText = $null
            try {
                $qstatText = Invoke-DirectPbsQuery -JobIds $activeJobsToQuery
            }
            catch {
                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "CONTROLLER" `
                    -Action "ACTIVE_JOB_STATE_CHECK_RETRY" `
                    -Message "Initial direct qstat check failed. Retrying in 30s. Error: $_"

                Write-Host ""
                Write-Host "[SCHEDULER] Initial direct qstat check failed." -ForegroundColor Yellow
                Write-Host "[SCHEDULER] Retrying in 30 seconds..." -ForegroundColor Yellow

                Start-Sleep -Seconds 30

                try {
                    $qstatText = Invoke-DirectPbsQuery -JobIds $activeJobsToQuery
                }
                catch {
                    Save-LoopStatus `
                        -Turn $CurrentTurn `
                        -Status "FAILED" `
                        -Tier "CONTROLLER" `
                        -Action "ACTIVE_JOB_STATE_CHECK_FAILED_AFTER_RETRY" `
                        -Details $_.Exception.Message

                    break MainLoop
                }
            }

            # Check if any candidate job is currently Running (R) or Queued (Q, H, W)
            $hasRunningOrQueuedJob = $false
            $qstatLines = $qstatText -split "`r?`n"
            foreach ($qLine in $qstatLines) {
                $qTrim = $qLine.Trim()
                if (-not $qTrim -or $qTrim.StartsWith("Job id") -or $qTrim.StartsWith("Job ID") -or $qTrim.StartsWith("---") -or $qTrim.StartsWith("mmaster02:")) {
                    continue
                }
                $qParts = ($qTrim -split '\\s+') | Where-Object { $_ -ne '' }
                if ($qParts.Count -ge 5) {
                    $qState = $null
                    if ($qParts.Count -ge 10 -and $qParts[9] -match '^[RQHWFCEBT]$') {
                        $qState = $qParts[9].ToUpper()
                    }
                    elseif ($qParts.Count -ge 5 -and $qParts[4] -match '^[RQHWFCEBT]$') {
                        $qState = $qParts[4].ToUpper()
                    }
                    if ($qState -in @('R', 'Q', 'H', 'W')) {
                        $hasRunningOrQueuedJob = $true
                        break
                    }
                }
            }

            if ($hasRunningOrQueuedJob) {
                # Case A: Live Q/R job -> wait 900s polling loop
                $pollingActive = $true
                $consecutiveQstatFailures = 0
                while ($pollingActive) {
                    Write-Host ""
                    Write-Host "[SCHEDULER] Active PBS job(s) remain in Q/R state: $($activeJobsToQuery -join ', ')" `
                        -ForegroundColor Yellow
                    Write-Host "[SCHEDULER] Entering WAITING_FOR_SCHEDULER: waiting 900 seconds before fresh scheduler review..." `
                        -ForegroundColor Cyan

                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "CONTROLLER" `
                        -Action "WAITING_FOR_SCHEDULER" `
                        -Message "Waiting 900 seconds for active Q/R PBS job(s): $($activeJobsToQuery -join ', ')"

                    Start-Sleep -Seconds 900

                    try {
                        $qstatText = Invoke-DirectPbsQuery -JobIds $activeJobsToQuery
                    }
                    catch {
                        $consecutiveQstatFailures++
                        Write-LoopLog `
                            -Turn $CurrentTurn `
                            -Tier "CONTROLLER" `
                            -Action "QSTAT_DIRECT_ERROR" `
                            -Message "Attempt $consecutiveQstatFailures failed for exact job(s) $($activeJobsToQuery -join ', '): $_"

                        if ($consecutiveQstatFailures -lt 2) {
                            Write-Host "[SCHEDULER] Direct qstat review failed once." -ForegroundColor Yellow
                            Write-Host "[SCHEDULER] Retrying after normal 900-second wait." -ForegroundColor Yellow
                            continue
                        }

                        Save-LoopStatus `
                            -Turn $CurrentTurn `
                            -Status "FAILED" `
                            -Tier "CONTROLLER" `
                            -Action "QSTAT_DIRECT_ERROR_AFTER_RETRY" `
                            -Details "Two consecutive direct qstat failures for exact job(s) $($activeJobsToQuery -join ', '): $($_.Exception.Message)"

                        break MainLoop
                    }

                    $consecutiveQstatFailures = 0

                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "CONTROLLER" `
                        -Action "POST_WAIT_QSTAT_RESULT" `
                        -Message $qstatText

                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "tier3_chatgpt" `
                        -Action "ESCALATE_SCHEDULER_REVIEW" `
                        -Message "Sending fresh direct scheduler result to ChatGPT bridge..."

                    try {
                        $schedulerInstruction = Invoke-SchedulerReviewChatGPT -QstatText $qstatText
                    }
                    catch {
                        Write-LoopLog `
                            -Turn $CurrentTurn `
                            -Tier "tier3_chatgpt" `
                            -Action "CHATGPT_FAILURE_STOP" `
                            -Message "Error during scheduler review: $_"

                        Save-LoopStatus `
                            -Turn $CurrentTurn `
                            -Status "FAILED" `
                            -Tier "tier3_chatgpt" `
                            -Action "CHATGPT_ERROR" `
                            -Details $_.Exception.Message

                        break MainLoop
                    }

                    if ($schedulerInstruction -match '^(?i:stop)\s*$') {
                        # Re-check if jobs have transitioned away from Q/R
                        $freshDirect = Invoke-DirectPbsQuery -JobIds $activeJobsToQuery
                        $freshLines = $freshDirect -split "`r?`n"
                        $anyStillRunning = $false
                        foreach ($fl in $freshLines) {
                            $flParts = ($fl.Trim() -split '\\s+') | Where-Object { $_ -ne '' }
                            if ($flParts.Count -ge 5) {
                                $flState = if ($flParts.Count -ge 10 -and $flParts[9] -match '^[RQHWFCEBT]$') { $flParts[9] } elseif ($flParts[4] -match '^[RQHWFCEBT]$') { $flParts[4] } else { $null }
                                if ($flState -in @('R', 'Q', 'H', 'W')) { $anyStillRunning = $true; break }
                            }
                        }
                        if (-not $anyStillRunning) {
                            Write-LoopLog `
                                -Turn $CurrentTurn `
                                -Tier "CONTROLLER" `
                                -Action "SCHEDULER_JOB_TERMINAL_NO_REWAIT" `
                                -Message "Job(s) transitioned to terminal state; exiting wait loop."
                            $pollingActive = $false
                            # Immediate escalation to ChatGPT with terminal state
                            $terminalInstruction = Invoke-SchedulerReviewChatGPT -QstatText $freshDirect
                            if ($terminalInstruction -notmatch '^(?i:stop)\s*$') {
                                $NextInstruction = $terminalInstruction
                            }
                            break
                        }

                        Write-LoopLog `
                            -Turn $CurrentTurn `
                            -Tier "CONTROLLER" `
                            -Action "SCHEDULER_STOP_REPOLL_SAME_IDS" `
                            -Message "ChatGPT replied stop on scheduler result; retaining active job(s) and repolling after wait: $($activeJobsToQuery -join ', ')"
                    }
                    else {
                        $pollingActive = $false
                        $NextInstruction = $schedulerInstruction
                        $gptPreview = if ($NextInstruction.Length -gt 80) { $NextInstruction.Substring(0, 80) } else { $NextInstruction }
                        Write-LoopLog `
                            -Turn $CurrentTurn `
                            -Tier "tier3_chatgpt" `
                            -Action "CHATGPT_SCHEDULER_DISPATCH" `
                            -Message "ChatGPT post-qstat instruction received: ${gptPreview}..."
                    }
                }
            }
            else {
                # Case B: Terminal state (F/C/E) reached immediately -> Do NOT wait 15 min; escalate to ChatGPT immediately!
                Write-Host ""
                Write-Host "[SCHEDULER] Job(s) are in terminal state (F/C/E): $($activeJobsToQuery -join ', ')" -ForegroundColor Cyan
                Write-Host "[SCHEDULER] Immediately sending terminal scheduler result to ChatGPT for evaluation..." -ForegroundColor Cyan

                Write-LoopLog `
                    -Turn $CurrentTurn `
                    -Tier "CONTROLLER" `
                    -Action "SCHEDULER_TERMINAL_JOB_EVALUATION" `
                    -Message "Job(s) in terminal state ($($activeJobsToQuery -join ', ')); escalating immediately to ChatGPT without 15m wait: $qstatText"

                try {
                    $schedulerInstruction = Invoke-SchedulerReviewChatGPT -QstatText $qstatText
                }
                catch {
                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "tier3_chatgpt" `
                        -Action "CHATGPT_FAILURE_STOP" `
                        -Message "Error during scheduler review: $_"

                    Save-LoopStatus `
                        -Turn $CurrentTurn `
                        -Status "FAILED" `
                        -Tier "tier3_chatgpt" `
                        -Action "CHATGPT_ERROR" `
                        -Details $_.Exception.Message

                    break MainLoop
                }

                if ($schedulerInstruction -notmatch '^(?i:stop)\s*$') {
                    $NextInstruction = $schedulerInstruction
                    $gptPreview = if ($NextInstruction.Length -gt 80) { $NextInstruction.Substring(0, 80) } else { $NextInstruction }
                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "tier3_chatgpt" `
                        -Action "CHATGPT_SCHEDULER_DISPATCH" `
                        -Message "ChatGPT post-qstat instruction received: ${gptPreview}..."
                }
                else {
                    # ChatGPT reviewed terminal evidence and explicitly stopped -> genuine completion
                    Write-Host "`n==========================================================" -ForegroundColor Green
                    Write-Host " AUTONOMOUS LOOP COMPLETED SAFELY (STOP SIGNAL RECEIVED) " -ForegroundColor Green
                    Write-Host "==========================================================" -ForegroundColor Green

                    Write-LoopLog `
                        -Turn $CurrentTurn `
                        -Tier "CONTROLLER" `
                        -Action "LOOP_TERMINATED_SAFE" `
                        -Message "ChatGPT stop received and terminal scheduler state was evaluated."

                    Save-LoopStatus `
                        -Turn $CurrentTurn `
                        -Status "STOPPED_CLEAN" `
                        -Tier "CONTROLLER" `
                        -Action "NORMAL_TERMINATION" `
                        -Details "Terminal scheduler state evaluated and confirmed complete."

                    break MainLoop
                }
            }
        }
        else {
            # Case C: Zero candidate PBS jobs exist -> genuine clean completion
            Write-Host "`n==========================================================" -ForegroundColor Green
            Write-Host " AUTONOMOUS LOOP COMPLETED SAFELY (STOP SIGNAL RECEIVED) " -ForegroundColor Green
            Write-Host "==========================================================" -ForegroundColor Green

            Write-LoopLog `
                -Turn $CurrentTurn `
                -Tier "CONTROLLER" `
                -Action "LOOP_TERMINATED_SAFE" `
                -Message "ChatGPT stop received and zero candidate PBS jobs exist in workflow."

            Save-LoopStatus `
                -Turn $CurrentTurn `
                -Status "STOPPED_CLEAN" `
                -Tier "CONTROLLER" `
                -Action "NORMAL_TERMINATION" `
                -Details "Zero candidate PBS jobs exist."

            break MainLoop
        }
    }'''

assert old_stop_block in content, "old_stop_block not found"
content = content.replace(old_stop_block, new_stop_block, 1)
print("STOP handler block successfully updated.")

if has_crlf:
    content = content.replace("\n", "\r\n")

with open(target_path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print(f"Target successfully updated: {target_path}")
