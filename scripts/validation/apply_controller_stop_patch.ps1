# Apply STOP handler and OpenSSH warning fixes to Antigravity-Autonomous-Loop.ps1
$controllerPath = "C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"

if (-not (Test-Path -LiteralPath $controllerPath)) {
    throw "Controller file not found at: $controllerPath"
}

$rawContent = [System.IO.File]::ReadAllText($controllerPath, [System.Text.Encoding]::UTF8)

# Backup current file
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = "$controllerPath.bak_before_stop_patch_$stamp"
[System.IO.File]::WriteAllText($backupPath, $rawContent, [System.Text.Encoding]::UTF8)
Write-Host "Backup created at: $backupPath"

# -----------------------------------------------------------------------------
# Fix 1: Replace Get-LivePbsJobs and Get-ActivePbsJobIds
# -----------------------------------------------------------------------------
$oldFunctionsPattern = @"
function Get-LivePbsJobs \{[\s\S]*?function Get-ActivePbsJobIds \{[\s\S]*?\n\}
"@

$newFunctions = @'
function Get-LivePbsJobs {
    [CmdletBinding()]
    param(
        [string]$User = "pr21vyci",
        [string]$HostAlias = "tu_freiberg",
        [string]$ConfigPath = "$env:USERPROFILE\.ssh\codex_config"
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

        $parts = ($trimmed -split '\s+') | Where-Object { $_ -ne '' }
        if ($parts.Count -ge 5) {
            $jobId = $parts[0]
            # In TU Freiberg PBS: Job ID (0), Name (1), User (2), Time Use (3), S (4), Queue (5)
            $state = $parts[4].ToUpper()

            if ($jobId -match '^\d+(\.\w+)?$') {
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
    $sshConfig = Join-Path $env:USERPROFILE ".ssh\codex_config"

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
        throw "qstat failed with exit code $exitCode:`n$text"
    }

    return @(
        $cleanResult |
        ForEach-Object {
            $line = $_.ToString().Trim()
            if ($line -match '^\d+(\.\w+)?$') {
                $line
            }
            else {
                $firstCol = ($line -split '\s+')[0]
                if ($firstCol -match '^\d+(\.\w+)?$') {
                    $firstCol
                }
            }
        } |
        Where-Object {
            $_ -match '^\d+(\.\w+)?$'
        }
    )
}
'@

if ($rawContent -match $oldFunctionsPattern) {
    $rawContent = [regex]::Replace($rawContent, $oldFunctionsPattern, $newFunctions)
    Write-Host "Fix 1 applied: Get-LivePbsJobs and Get-ActivePbsJobIds updated."
} else {
    throw "Fix 1 failed: Could not match Get-LivePbsJobs and Get-ActivePbsJobIds."
}

# -----------------------------------------------------------------------------
# Fix 4: Verify and update Invoke-DirectPbsQuery
# -----------------------------------------------------------------------------
$oldInvokePattern = @"
function Invoke-DirectPbsQuery \{[\s\S]*?\n\}
"@

$newInvokeFunction = @'
function Invoke-DirectPbsQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$JobIds
    )

    if (-not $JobIds -or $JobIds.Count -eq 0) {
        throw "Invoke-DirectPbsQuery called without PBS job IDs."
    }

    $sshConfig = Join-Path $env:USERPROFILE ".ssh\codex_config"

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
        throw "Direct qstat query failed with exit code $exitCode.`n$text"
    }

    if ([string]::IsNullOrWhiteSpace($text)) {
        throw "Direct qstat query returned exit code 0 but no scheduler payload for: $($JobIds -join ', ')"
    }

    return $text
}
'@

if ($rawContent -match $oldInvokePattern) {
    $rawContent = [regex]::Replace($rawContent, $oldInvokePattern, $newInvokeFunction)
    Write-Host "Fix 4 applied: Invoke-DirectPbsQuery updated."
} else {
    throw "Fix 4 failed: Could not match Invoke-DirectPbsQuery."
}

# -----------------------------------------------------------------------------
# Fix 2 & Fix 3: Update Stop handler with logging and retry
# -----------------------------------------------------------------------------
$oldStopBlockPattern = @"
    if \(\`$isStop\) \{[\s\S]*?catch \{[\s\S]*?break MainLoop\s*\}\s*if \(\`$activeJobsToWait\.Count -gt 0\) \{
"@

$newStopBlock = @'
    if ($isStop) {

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
'@

if ($rawContent -match $oldStopBlockPattern) {
    $rawContent = [regex]::Replace($rawContent, $oldStopBlockPattern, $newStopBlock)
    Write-Host "Fix 2 & Fix 3 applied: STOP handler logging and retry block updated."
} else {
    throw "Fix 2 & Fix 3 failed: Could not match STOP block pattern."
}

# Write modified file
[System.IO.File]::WriteAllText($controllerPath, $rawContent, [System.Text.Encoding]::UTF8)
Write-Host "Antigravity-Autonomous-Loop.ps1 successfully updated."
