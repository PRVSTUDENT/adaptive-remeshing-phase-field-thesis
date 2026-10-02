$sshConfig = Join-Path $env:USERPROFILE ".ssh\codex_config"
$raw = & ssh -F $sshConfig tu_freiberg "qstat -x -u pr21vyci" 2>&1
$cleanRaw = @(
    $raw |
    ForEach-Object { $_.ToString() } |
    Where-Object { $_ -notmatch "post-quantum key exchange algorithm" }
)
$text = ($cleanRaw | Out-String).Trim()
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

    $parts = ($trimmed -split '\s+') | Where-Object { $_ -ne '' }
    if ($parts.Count -ge 5) {
        $rawJobId = $parts[0] -replace '\*$', ''
        
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
            # Find any single-character state flag in parts
            for ($i = 1; $i -lt $parts.Count; $i++) {
                if ($parts[$i] -match '^[RQHWFCEBT]$') {
                    $state = $parts[$i].ToUpper()
                    break
                }
            }
        }

        if ($rawJobId -match '^\d+(\.\w+)?$') {
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

Write-Host "Total parsed jobs: $($liveJobs.Count)"
Write-Host "Running jobs     : $($runningJobs.Count) ($($runningJobs -join ', '))"
Write-Host "Queued jobs      : $($queuedJobs.Count) ($($queuedJobs -join ', '))"
Write-Host "Finished jobs    : $($finishedJobs.Count) (Latest 5: $(($finishedJobs | Select-Object -Last 5) -join ', '))"
