function Get-AgyCompactRules {
    return @'
Mode-I research only. Current user instructions and repository AGENTS.md govern. Dynamic state is in project_coordination, not historical handoffs. Follow mandatory bootstrap, single-agent lock, exact allowed scope, selective Git staging and forward-only synchronization. Preserve unrelated dirty work.
JOB-FIRST / REPORT-AFTER: immediately execute independently ready, technically qualified jobs through scripts/hpc/Invoke-Mode1Execution.ps1. No human permits or credential approvals. Reconcile exact PBS IDs, live scheduler, once-only reservations, input/UEL hashes, datachecks, real dual notifications and scientific predecessor review. Current serial Mode-I limits apply. No duplicate submissions, blind retries, qdel/qmove, production UEL changes, or invented acceptance. Empty queue is not scientific completion.
Advance Method B evaluation -> same-mesh reconstruction -> genuine continuation -> nonmatching transfer -> sequential cycles, as supported by current quantitative evidence. A failed scientific threshold needs a reviewed numerical hypothesis. Use authentic checkpoints and results. Guard remote commands and generated-file existence. Check current artifacts and ledger before recovering work; never replay an experiment because of account or conversation changes.
Each turn: one bounded scientific investigation or one independently qualified batch and its immediate accounting. Return promptly after submission or evidence evaluation; do not poll/wait for solver completion or chain the whole research programme. Record partial progress, exact receipts, failure evidence and the next dependent action. Meetings are reporting milestones.
'@
}

function Test-AgyQuotaHeadroom {
    param($Record, [double]$ShortThreshold = 20, [double]$LongThreshold = 20)
    if ($null -eq $Record -or $null -eq $Record.long_remaining_pct -or $null -eq $Record.five_h_remaining_pct) { return $false }
    $long = [double]$Record.long_remaining_pct; $short = [double]$Record.five_h_remaining_pct
    return ($long -gt $LongThreshold -and $long -le 100 -and $short -gt $ShortThreshold -and $short -le 100)
}

function Get-AgyQuotaCooldownDeadline {
    param([string]$Message, [datetimeoffset]$Now = [datetimeoffset]::UtcNow, [string]$ExistingUntil = '', [string]$TelemetryReset = '')
    $until = $Now.AddHours(24) # Unknown individual-quota reset is not a one-hour retry invitation.
    $match = [regex]::Match($Message, '(?i)resets?\s+in\s+(?:(\d+)d\s*)?(?:(\d+)h\s*)?(?:(\d+)m\s*)?(?:(\d+)s)?')
    if ($match.Success -and ($match.Groups[1].Success -or $match.Groups[2].Success -or $match.Groups[3].Success -or $match.Groups[4].Success)) {
        $seconds = 0.0
        $units = @(86400,3600,60,1)
        for ($i=1; $i -le 4; $i++) { if ($match.Groups[$i].Success) { $seconds += [double]$match.Groups[$i].Value * $units[$i-1] } }
        $until = $Now.AddSeconds($seconds + 60) # Provider reset plus clock margin.
    } elseif ($TelemetryReset) {
        $parsed = [datetimeoffset]::MinValue
        if ([datetimeoffset]::TryParse($TelemetryReset, [ref]$parsed) -and $parsed -gt $Now) { $until = $parsed.AddMinutes(1) }
    }
    if ($ExistingUntil) {
        $previous = [datetimeoffset]::MinValue
        if ([datetimeoffset]::TryParse($ExistingUntil, [ref]$previous) -and $previous -gt $until) { $until = $previous }
    }
    return $until.ToUniversalTime().ToString('o')
}

function Get-SafeTruncatedText {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [string]$Text,
        [Parameter(Mandatory = $true)]
        [int]$MaxLength,
        [ValidateSet('Head', 'Tail')]
        [string]$Direction = 'Head',
        [string]$Ellipsis = ''
    )

    if ([string]::IsNullOrEmpty($Text) -or $Text.Length -le $MaxLength) {
        return $Text
    }

    if ($Direction -eq 'Head') {
        $len = $MaxLength
        if ($len -gt 0 -and $len -le $Text.Length) {
            if ([char]::IsHighSurrogate($Text[$len - 1])) {
                $len--
            }
        }
        $sub = $Text.Substring(0, $len)
        if (-not [string]::IsNullOrEmpty($Ellipsis)) {
            $sub += $Ellipsis
        }
        return $sub
    }
    else {
        $start = $Text.Length - $MaxLength
        if ($start -ge 0 -and $start -lt $Text.Length) {
            if ([char]::IsLowSurrogate($Text[$start])) {
                $start++
            }
        }
        $sub = $Text.Substring($start)
        if (-not [string]::IsNullOrEmpty($Ellipsis)) {
            $sub = $Ellipsis + $sub
        }
        return $sub
    }
}

function Test-IsValidUtf8String {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [string]$Text
    )
    if ([string]::IsNullOrEmpty($Text)) { return $true }
    try {
        $strict = [System.Text.UTF8Encoding]::new($false, $true)
        $null = $strict.GetBytes($Text)
        return $true
    } catch {
        return $false
    }
}

function ConvertTo-SafeUtf8String {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [string]$Text,
        [string]$Context = 'diagnostic'
    )
    if ([string]::IsNullOrEmpty($Text)) { return $Text }
    if (Test-IsValidUtf8String $Text) { return $Text }
    Write-Warning "[ENCODING-DEFENSE] Text in $Context contained invalid UTF-16 surrogates or encoding sequences; applying safe replacement."
    $loose = [System.Text.UTF8Encoding]::new($false, $false)
    $bytes = $loose.GetBytes($Text)
    return $loose.GetString($bytes)
}

function Get-AgyBoundedText {
    param([string]$Text, [int]$Limit = 6000)
    if ($Text.Length -le $Limit) { return $Text }
    $half = [int]($Limit / 2)
    $head = Get-SafeTruncatedText -Text $Text -MaxLength $half -Direction 'Head'
    $tail = Get-SafeTruncatedText -Text $Text -MaxLength $half -Direction 'Tail'
    return $head + "`n[abridged; full evidence remains in project artifacts]`n" + $tail
}

function Get-AgyCompletedReceipt {
    param([string]$WorkspaceDir, [datetimeoffset]$Since)
    $sessionFile = Join-Path $WorkspaceDir 'project_coordination/ACTIVE_SESSION.json'
    $registryFile = Join-Path $WorkspaceDir 'project_coordination/ARTIFACT_REGISTRY.csv'
    if (-not (Test-Path -LiteralPath $sessionFile)) { return $null }
    try {
        $session = Get-Content -LiteralPath $sessionFile -Raw | ConvertFrom-Json
        if ($session.active -ne $false -or -not $session.last_released -or [datetimeoffset]::Parse($session.last_released) -lt $Since) { return $null }
        $taskPrefix = ([string]$session.task_id -split '-')[0]
        if ($taskPrefix -notmatch '^F\d+$') { return $null }
        $candidates = @()
        if ($session.session_report) { $candidates += [string]$session.session_report }
        if (Test-Path -LiteralPath $registryFile) {
            $candidates += @(Import-Csv -LiteralPath $registryFile | Where-Object { $_.type -eq 'session_report' -and $_.canonical_path -match "(^|[_/])$([regex]::Escape($taskPrefix))[-_.]" } | Select-Object -ExpandProperty canonical_path)
        }
        $base = [IO.Path]::GetFullPath((Join-Path $WorkspaceDir 'project_coordination/sessions')) + [IO.Path]::DirectorySeparatorChar
        foreach ($relative in ($candidates | Select-Object -Unique)) {
            $path = [IO.Path]::GetFullPath((Join-Path $WorkspaceDir $relative))
            if (-not $path.StartsWith($base, [StringComparison]::OrdinalIgnoreCase) -or -not (Test-Path -LiteralPath $path)) { continue }
            $item = Get-Item -LiteralPath $path
            if ($item.LastWriteTimeUtc -lt $Since.UtcDateTime -or $item.Length -lt 100) { continue }
            return [pscustomobject]@{task_id=$session.task_id; session_report=$relative; content=(Get-Content -LiteralPath $path -Raw)}
        }
    } catch { return $null }
    return $null
}
