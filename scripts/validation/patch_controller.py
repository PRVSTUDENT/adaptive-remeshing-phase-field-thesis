import os

backup_path = r"C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1.bak_20260825_053930"
target_path = r"C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"

with open(backup_path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

# Normalize to \n for uniform multiline matching
has_crlf = "\r\n" in content
content = content.replace("\r\n", "\n")

# -----------------------------------------------------------------------------
# Fix 1: Get-LivePbsJobs and Get-ActivePbsJobIds
# -----------------------------------------------------------------------------
old_f1 = '''function Get-LivePbsJobs {
    [CmdletBinding()]
    param(
        [string]$User = "pr21vyci",
        [string]$HostAlias = "tu_freiberg",
        [string]$ConfigPath = "$env:USERPROFILE\\.ssh\\codex_config"
    )

    $sshCommand = Get-Command ssh.exe -ErrorAction Stop
    $sshPath = $sshCommand.Source

    $remoteCommand = "qstat -u $User"
    $raw = & $sshPath -F $ConfigPath $HostAlias $remoteCommand 2>&1

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to query live scheduler ($remoteCommand): $($raw | Out-String)"
    }

    $qstatText = $raw | Out-String
    $lines = $qstatText -split "`r?`n"

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

            if ($jobId -match '^\\d+\\.mmaster02$') {
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
        RawOutput    = $qstatText
    }
}

function Get-ActivePbsJobIds {
    $py = @'
import json

p = "/home/openclaw/.openclaw/workspace-antigravity-controller/controller-state.json"

with open(p, "r", encoding="utf-8") as f:
    state = json.load(f)

for jid, data in state.get("jobs", {}).items():
    if data.get("status") in ["SUBMITTED", "QUEUED", "RUNNING"]:
        print(jid)
'@

    $result = $py | wsl.exe `
        -d OpenClawGateway `
        -u openclaw `
        -- python3 -

    if ($LASTEXITCODE -ne 0) {
        throw "Unable to read active PBS jobs from controller-state.json"
    }

    return @(
        $result |
        ForEach-Object { $_.ToString().Trim() } |
        Where-Object { $_ -match '^\\d+\\.mmaster02$' }
    )
}'''

new_f1 = '''function Get-LivePbsJobs {
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
}

function Get-ActivePbsJobIds {
    $sshConfig = Join-Path $env:USERPROFILE ".ssh\\codex_config"

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

        $result = & ssh `
            -F $sshConfig `
            tu_freiberg `
            "qstat -u pr21vyci" 2>&1

        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedErrorActionPreference
        if ($hadNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $savedNativePreference
        }
    }

    # Remove harmless OpenSSH warnings from stderr/stdout mixing
    $cleanResult = @(
        $result |
        ForEach-Object {
            $_.ToString()
        } |
        Where-Object {
            $_ -notmatch "post-quantum key exchange algorithm"
        }
    )

    $text = ($cleanResult | Out-String).Trim()

    if ($exitCode -ne 0) {
        throw "qstat failed with exit code $($exitCode):`n$text"
    }

    return @(
        $cleanResult |
        ForEach-Object {
            $line = $_.ToString().Trim()
            if ($line -match '^\\d+(\\.\\w+)?$') {
                $line
            }
            else {
                $firstCol = ($line -split '\\s+')[0]
                if ($firstCol -match '^\\d+(\\.\\w+)?$') {
                    $firstCol
                }
            }
        } |
        Where-Object {
            $_ -match '^\\d+(\\.\\w+)?$'
        }
    )
}'''

assert old_f1 in content, "old_f1 block not found in content"
content = content.replace(old_f1, new_f1, 1)
print("Fix 1 successfully applied.")

# -----------------------------------------------------------------------------
# Fix 4: Invoke-DirectPbsQuery
# -----------------------------------------------------------------------------
old_f4 = '''function Invoke-DirectPbsQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$JobIds
    )

    if (-not $JobIds -or $JobIds.Count -eq 0) {
        throw "Invoke-DirectPbsQuery called without PBS job IDs."
    }

    $sshConfig = Join-Path $env:USERPROFILE ".ssh\\codex_config"

    if (-not (Test-Path -LiteralPath $sshConfig)) {
        throw "SSH config not found: $sshConfig"
    }

    $remoteCommand = "qstat -x " + ($JobIds -join " ")

    Write-Host "[SCHEDULER] Running direct PBS query:"
    Write-Host "[SCHEDULER] ssh -F $sshConfig tu_freiberg `"$remoteCommand`""

    # OpenSSH writes informational/security warnings to STDERR even when the
    # command succeeds. With global $ErrorActionPreference='Stop', PowerShell
    # can promote those STDERR records into terminating NativeCommandError
    # records before we ever inspect $LASTEXITCODE.
    #
    # For this native command only, capture stdout/stderr without terminating
    # on STDERR. The authoritative success/failure signal is ssh's exit code.
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

        $output = & ssh `
            -F $sshConfig `
            tu_freiberg `
            $remoteCommand 2>&1

        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedErrorActionPreference
        if ($hadNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $savedNativePreference
        }
    }

    $allLines = @(
        $output |
        ForEach-Object { $_.ToString() }
    )

    # Filter only the known OpenSSH post-quantum advisory from the scheduler
    # payload. Do not suppress arbitrary ssh/qstat diagnostics.
    $knownAdvisoryPatterns = @(
        '^\\*\\* WARNING: connection is not using a post-quantum key exchange algorithm\\.$',
        '^\\*\\* This session may be vulnerable to "store now, decrypt later" attacks\\.$',
        '^\\*\\* The server may need to be upgraded\\. See https://openssh\\.com/pq\\.html$'
    )

    $payloadLines = foreach ($line in $allLines) {
        $isKnownAdvisory = $false
        foreach ($pattern in $knownAdvisoryPatterns) {
            if ($line -match $pattern) {
                $isKnownAdvisory = $true
                break
            }
        }
        if (-not $isKnownAdvisory) {
            $line
        }
    }

    $payloadText = ($payloadLines | Out-String).Trim()
    $rawText = ($allLines | Out-String).Trim()

    if ($exitCode -ne 0) {
        throw "Direct qstat query failed with exit code $exitCode.`n$rawText"
    }

    if ([string]::IsNullOrWhiteSpace($payloadText)) {
        throw "Direct qstat query returned exit code 0 but no scheduler payload for: $($JobIds -join ', ')"
    }

    return $payloadText
}'''

new_f4 = '''function Invoke-DirectPbsQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$JobIds
    )

    if (-not $JobIds -or $JobIds.Count -eq 0) {
        throw "Invoke-DirectPbsQuery called without PBS job IDs."
    }

    $sshConfig = Join-Path $env:USERPROFILE ".ssh\\codex_config"

    if (-not (Test-Path -LiteralPath $sshConfig)) {
        throw "SSH config not found: $sshConfig"
    }

    $remoteCommand = "qstat -x " + ($JobIds -join " ")

    Write-Host "[SCHEDULER] Running direct PBS query:"
    Write-Host "[SCHEDULER] ssh -F $sshConfig tu_freiberg `"$remoteCommand`""

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

        $output = & ssh `
            -F $sshConfig `
            tu_freiberg `
            $remoteCommand 2>&1

        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedErrorActionPreference
        if ($hadNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $savedNativePreference
        }
    }

    $cleanLines = @(
        $output |
        ForEach-Object { $_.ToString() } |
        Where-Object {
            $_ -notmatch "post-quantum key exchange algorithm"
        }
    )

    $text = ($cleanLines | Out-String).Trim()

    if ($exitCode -ne 0) {
        throw "Direct qstat query failed with exit code $($exitCode):`n$text"
    }

    if ([string]::IsNullOrWhiteSpace($text)) {
        throw "Direct qstat query returned exit code 0 but no scheduler payload for: $($JobIds -join ', ')"
    }

    return $text
}'''

assert old_f4 in content, "old_f4 block not found in content"
content = content.replace(old_f4, new_f4, 1)
print("Fix 4 successfully applied.")

# -----------------------------------------------------------------------------
# Fix 2 & Fix 3: STOP Handler
# -----------------------------------------------------------------------------
old_stop = '''    if ($isStop) {

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
                -Action "ACTIVE_JOB_STATE_CHECK_FAILED" `
                -Message "$_"

            Save-LoopStatus `
                -Turn $CurrentTurn `
                -Status "FAILED" `
                -Tier "CONTROLLER" `
                -Action "ACTIVE_JOB_STATE_CHECK_FAILED" `
                -Details $_.Exception.Message

            break MainLoop
        }'''

new_stop = '''    if ($isStop) {

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
        }'''

assert old_stop in content, "old_stop block not found in content"
content = content.replace(old_stop, new_stop, 1)
print("Fix 2 & Fix 3 successfully applied.")

# Write back with exact CRLF line endings
if has_crlf:
    content = content.replace("\n", "\r\n")

with open(target_path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print(f"Target successfully updated: {target_path}")
