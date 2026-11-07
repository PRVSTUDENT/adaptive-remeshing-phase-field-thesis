<# Read saved profiles independently. Never switch, save, or modify global credentials. #>
[CmdletBinding()]
param([ValidateRange(1,100)][int]$First=1,
      [ValidateRange(1,100)][int]$Last=5,
      [switch]$AuditOnly,
      [string]$GroupRegex='.*',
      [switch]$PassThru,
      [string]$DashboardDirectory = '',
      [switch]$NoDashboard)
$ErrorActionPreference='Stop'
if ($First -gt $Last) { throw 'First must be <= Last.' }
Add-Type -AssemblyName System.Security
$python=Join-Path $env:APPDATA 'uv\tools\ai-limit-checker\Scripts\python.exe'
# Also find the existing read-only worker when this script is run from the thesis repo,
# while the worker itself remains installed in the OpenClawPAD folder.
$workerCandidates = @(
    (Join-Path $PSScriptRoot 'agy_profile_quota.py'),
    (Join-Path $PSScriptRoot 'agy_saved_profile_quota.py'),
    (Join-Path $env:USERPROFILE 'OpenClawPAD\agy_profile_quota.py'),
    (Join-Path $env:USERPROFILE 'OpenClawPAD\agy_saved_profile_quota.py')
)
$worker = $null
foreach ($candidate in $workerCandidates) {
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        $worker = $candidate
        break
    }
}
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Missing Python dependency: $python"
}
if (-not $worker) {
    throw 'Quota worker not found alongside the script or in OpenClawPAD.'
}

function New-AgyQuotaRow {
    param([string]$Profile,[string]$Account,[string]$ModelGroup='',[string]$Status='')
    [pscustomobject][ordered]@{Profile=$Profile;Account=$Account;ModelGroup=$ModelGroup;Status=$Status;
        WeeklyRemaining='N/A';WeeklyReset='N/A';FiveHourRemain='N/A';FiveHourReset='N/A'}
}

function ConvertTo-AgyQuotaRows {
    param([string]$Profile,[string]$Account,$Quota,[string]$GroupRegex='.*')
    # Preserve provider model-group names. Never relabel Claude capacity as Gemini.
    $groups=@($Quota.groups | Where-Object { $_ -and [string]$_.name -match $GroupRegex })
    if(-not $groups.Count) {
        New-AgyQuotaRow -Profile $Profile -Account $Account -ModelGroup $GroupRegex -Status 'GROUP_NOT_REPORTED'
        return
    }
    foreach($group in $groups) {
        $row=New-AgyQuotaRow -Profile $Profile -Account $Account -ModelGroup $group.name -Status 'OK'
        $weekly=@($group.buckets|Where-Object { $_.window -match '^(weekly|week|7d|five_day|five-day|5d|120h)$' })
        $short=@($group.buckets|Where-Object { $_.window -match '^(5h|five_hour|five-hour|five hour)$' })
        if(-not $weekly.Count -or -not $short.Count) { $row.Status='INCOMPLETE_QUOTA' }
        foreach($item in @(@{Buckets=$weekly;Value='WeeklyRemaining';Reset='WeeklyReset'},
                           @{Buckets=$short;Value='FiveHourRemain';Reset='FiveHourReset'})) {
            $buckets=@($item.Buckets)
            if(-not $buckets.Count) { continue }
            # Multiple same-window buckets: report the most constrained real value.
            $valid=@($buckets|Where-Object {
                $number=0.0
                $null -ne $_.remaining_pct -and
                [double]::TryParse([string]$_.remaining_pct,[Globalization.NumberStyles]::Float,
                    [Globalization.CultureInfo]::InvariantCulture,[ref]$number) -and
                $number -ge 0 -and $number -le 100
            })
            if($valid.Count -ne $buckets.Count) { $row.Status='INVALID_QUOTA';continue }
            $bucket=$valid|Sort-Object {[double]$_.remaining_pct}|Select-Object -First 1
            $row.($item.Value)=([double]$bucket.remaining_pct).ToString('0.00',[Globalization.CultureInfo]::InvariantCulture)+'%'
            if($bucket.remaining_fraction -eq 1) { $row.($item.Reset)='Available now' }
            elseif($bucket.resets_at) {$row.($item.Reset)=$bucket.resets_at}
        }
        $row
    }
}

$seen=@{}
$results=@(foreach($i in $First..$Last) {
    $profile="account$i"
    $row=New-AgyQuotaRow -Profile $profile -Status 'PROFILE_CHECK_FAILED'
    $stage='PROFILE_READ_FAILED'
    try {
        $file=Join-Path $env:USERPROFILE ".gemini\agy-profiles\$profile\credential.dpapi"
        if (-not (Test-Path -LiteralPath $file)) { $row.Status='PROFILE_MISSING';$row;continue }
        $plain=[Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($file),$null,'CurrentUser')
        $credential=[Text.Encoding]::UTF8.GetString($plain)|ConvertFrom-Json
        # Tokens go through stdin only; raw worker output/errors are never displayed.
        $stage='IDENTITY_CHECK_FAILED'
        $request=@{credential=$credential;audit_only=$true}|ConvertTo-Json -Depth 10 -Compress
        $output=$request | & $python $worker 2>$null
        if ($LASTEXITCODE -ne 0) { throw 'Identity inspection failed' }
        $info=$output|ConvertFrom-Json
        if (-not $info.identity) { throw 'Missing identity' }
        $row.Account=$info.email
        if ($seen.ContainsKey($info.identity)) {
            $row.Status="DUPLICATE_OF_$($seen[$info.identity])";$row
        } else {
            $seen[$info.identity]=$profile
            if($AuditOnly) { $row.Status='AUDIT_ONLY';$row }
            else {
                $stage='QUOTA_CHECK_FAILED'
                $request=@{credential=$credential;audit_only=$false}|ConvertTo-Json -Depth 10 -Compress
                $output=$request | & $python $worker 2>$null
                if ($LASTEXITCODE -ne 0) { throw 'Quota worker failed' }
                $q=($output|ConvertFrom-Json).antigravity
                if($q.status -ne 'ok') {
                    $row.Status=if($q.error_code -eq 'AUTHENTICATION_FAILED') {'AUTH_ERROR: saved grant rejected'} elseif($q.error_code) {$q.error_code} else {'QUOTA_CHECK_FAILED'}
                    $row
                } else {
                    ConvertTo-AgyQuotaRows -Profile $profile -Account $info.email -Quota $q -GroupRegex $GroupRegex
                }
            }
        }
    } catch { $row.Status=$stage;$row }
    finally { $plain=$null;$credential=$null;$request=$null;$output=$null }
})


# Quota-dashboard outputs are display-only. Nothing below this point reads,
# switches, exports, or modifies credentials or account profiles.
function ConvertTo-AgyHtml {
    param([AllowNull()][string]$Value)
    if ($null -eq $Value) { return '' }
    return [System.Net.WebUtility]::HtmlEncode($Value)
}

function Get-AgyResetDisplay {
    param(
        [AllowNull()][string]$Reset,
        [ValidateSet('Weekly','FiveHour')][string]$Window,
        [datetimeoffset]$AsOf
    )
    if ([string]::IsNullOrWhiteSpace($Reset) -or $Reset -eq 'N/A') {
        return 'Not reported'
    }
    if ($Reset -eq 'Available now') {
        return 'Available now (no active reset countdown)'
    }

    $utc = [datetimeoffset]::MinValue
    $style = [Globalization.DateTimeStyles]::AssumeUniversal
    $culture = [Globalization.CultureInfo]::InvariantCulture
    if (-not [datetimeoffset]::TryParse($Reset, $culture, $style, [ref]$utc)) {
        return 'Reset time unavailable'
    }
    $local = $utc.ToLocalTime()
    $remaining = $utc - $AsOf
    if ($remaining.TotalSeconds -le 0) {
        $relative = 'reset time reached; refresh to confirm'
    } else {
        $totalMinutes = [math]::Ceiling($remaining.TotalMinutes)
        $days = [math]::Floor($totalMinutes / 1440)
        $hours = [math]::Floor(($totalMinutes % 1440) / 60)
        $minutes = $totalMinutes % 60
        if ($days -gt 0) {
            $relative = "in ${days}d ${hours}h"
        } elseif ($hours -gt 0) {
            $relative = "in ${hours}h ${minutes}m"
        } else {
            $relative = "in ${minutes}m"
        }
    }

    # Local offset is explicit, so DST transitions cannot silently shift resets.
    if ($Window -eq 'Weekly') {
        $when = $local.ToString('ddd, dd MMM yyyy HH:mm:ss', $culture)
        return "$when (UTC$($local.ToString('zzz'))) - $relative"
    }
    $clock = $local.ToString('HH:mm:ss', $culture)
    $date = $local.ToString('ddd, dd MMM yyyy', $culture)
    return "$clock ($date, UTC$($local.ToString('zzz'))) - $relative"
}

function Get-AgyQuotaDisplay {
    param(
        [AllowNull()][string]$Remaining,
        [AllowNull()][string]$Reset,
        [ValidateSet('Weekly','FiveHour')][string]$Window,
        [datetimeoffset]$AsOf
    )
    $number = 0.0
    $valid = $false
    if ($Remaining -match '^([0-9]+(?:\.[0-9]+)?)%$') {
        $valid = [double]::TryParse(
            $Matches[1],
            [Globalization.NumberStyles]::Float,
            [Globalization.CultureInfo]::InvariantCulture,
            [ref]$number
        ) -and $number -ge 0 -and $number -le 100
    }
    if (-not $valid) {
        return [pscustomobject]@{
            Available = $false
            Percentage = 0.0
            PercentageText = 'N/A'
            Bar = ('░' * 32)
            Level = 'unavailable'
            ResetText = (Get-AgyResetDisplay -Reset $Reset -Window $Window -AsOf $AsOf)
        }
    }
    $blocks = [math]::Max(0, [math]::Min(32,
        [int][math]::Round($number * 32 / 100, 0, [MidpointRounding]::AwayFromZero)))
    $level = if ($number -le 5) { 'critical' } elseif ($number -le 20) { 'low' } else { 'normal' }
    return [pscustomobject]@{
        Available = $true
        Percentage = $number
        PercentageText = $number.ToString('0.00',[Globalization.CultureInfo]::InvariantCulture) + '%'
        Bar = ('█' * $blocks) + ('░' * (32 - $blocks))
        Level = $level
        ResetText = (Get-AgyResetDisplay -Reset $Reset -Window $Window -AsOf $AsOf)
    }
}

function Write-AgyQuotaDashboards {
    param([object[]]$Rows, [string]$Directory)
    $stamp = [datetimeoffset]::Now
    $htmlFile = Join-Path $Directory 'AGY_Quota_Dashboard.html'
    $mdFile = Join-Path $Directory 'AGY_Quota_Dashboard.md'
    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) {
        $null = New-Item -ItemType Directory -Path $Directory -Force
    }
    $updated = $stamp.ToString('ddd, dd MMM yyyy HH:mm:ss zzz',
        [Globalization.CultureInfo]::InvariantCulture)

    $md = New-Object System.Collections.Generic.List[string]
    $md.Add('# Antigravity account quotas')
    $md.Add('')
    $md.Add("**Last refreshed:** $updated (computer local time)")
    $md.Add('**Source:** saved profiles, read-only. Bars represent **quota remaining**, not quota used.')
    $md.Add('')

    $html = New-Object System.Text.StringBuilder
    [void]$html.AppendLine(@'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Antigravity Quota Dashboard</title>
<style>
:root { color-scheme: dark; font-family: "Segoe UI", Inter, system-ui, sans-serif; }
* { box-sizing: border-box; }
body { margin:0; background:#0e1525; color:#ebf1fb; padding:24px 22px 60px; }
main { margin:auto; max-width:1100px; }
h1 { font-size:clamp(1.5rem,2.5vw,2.2rem); letter-spacing:-.035em; margin:0 0 6px; }
.subtitle { color:#abb9ce; margin:0 0 8px; line-height:1.6; }
.updated { color:#899ab3; font-size:.85rem; margin:0 0 22px; }
.account { background:#151f32; border:1px solid #293a52; border-radius:15px; padding:18px; margin:0 0 16px; }
.account-header { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:7px; padding-bottom:13px; border-bottom:1px solid #2a3950; }
.account-header h2 { font-size:1.13rem; margin:0; color:#f2f6ff; }
.account-email { color:#a6b6cb; font-size:.9rem; overflow-wrap:anywhere; }
.groups { display:grid; grid-template-columns: repeat(auto-fit,minmax(290px,1fr)); gap:13px; margin-top:14px; }
.group { background:#101a2d; border-radius:11px; border:1px solid #2a3950; padding:15px 16px; }
.group-title { display:flex; flex-wrap:wrap; gap:8px; align-items:center; justify-content:space-between; margin:0 0 16px; }
.group-title h3 { margin:0; font-size:.94rem; font-weight:650; }
.status { font-size:.69rem; border:1px solid #32465f; padding:3px 7px; border-radius:20px; color:#aab9c9; }
.bucket { margin-top:14px; }
.bucket-head { display:flex; justify-content:space-between; gap:8px; margin-bottom:7px; font-size:.86rem; }
.bucket-head strong { font-size:.94rem; font-variant-numeric:tabular-nums; }
.track { height:13px; width:100%; overflow:hidden; background:#2b3548; border-radius:20px; border:1px solid #3c4c62; }
.fill { height:100%; border-radius:20px; background:linear-gradient(90deg,#1ab8c3,#43dbb1); transition:width .2s ease; }
.bucket.low .fill { background:linear-gradient(90deg,#e9a735,#ffd26b); }
.bucket.critical .fill { background:linear-gradient(90deg,#d95361,#ff8193); }
.bucket.unavailable .fill { background:#617187; }
.reset-label { color:#879bb3; font-size:.71rem; margin-top:7px; }
.reset { margin-top:2px; font-size:.8rem; color:#d3dded; font-variant-numeric:tabular-nums; overflow-wrap:anywhere; }
footer { color:#8394aa; line-height:1.6; font-size:.81rem; margin-top:15px; }
@media (max-width:550px) { body { padding:14px 11px 40px; } .account{padding:12px;} .groups{grid-template-columns:1fr;} }
</style>
</head>
<body><main>
<h1>Antigravity quota dashboard</h1>
<p class="subtitle">Remaining capacity for every saved account and model group. Refresh using Refresh-AgyAccounts.ps1.</p>
'@)
    [void]$html.AppendLine('<p class="updated">Last refreshed: ' + (ConvertTo-AgyHtml $updated) + ' (computer local time)</p>')

    foreach ($account in @($Rows | Group-Object -Property Profile)) {
        $accountName = [string]$account.Name
        $firstRow = @($account.Group)[0]
        $email = if ([string]::IsNullOrWhiteSpace($firstRow.Account)) { 'Identity unavailable' } else { [string]$firstRow.Account }

        $md.Add("## $accountName - $email")
        $md.Add('')
        [void]$html.AppendLine('<section class="account"><div class="account-header"><h2>' +
            (ConvertTo-AgyHtml $accountName) + '</h2><span class="account-email">' +
            (ConvertTo-AgyHtml $email) + '</span></div><div class="groups">')

        foreach ($r in @($account.Group)) {
            $groupName = if ([string]::IsNullOrWhiteSpace([string]$r.ModelGroup)) { 'Quota unavailable' } else { [string]$r.ModelGroup }
            $weekly = Get-AgyQuotaDisplay -Remaining $r.WeeklyRemaining -Reset $r.WeeklyReset -Window Weekly -AsOf $stamp
            $five = Get-AgyQuotaDisplay -Remaining $r.FiveHourRemain -Reset $r.FiveHourReset -Window FiveHour -AsOf $stamp
            $md.Add("### $groupName  [$($r.Status)]")
            $md.Add('')

            [void]$html.AppendLine('<div class="group"><div class="group-title"><h3>' +
                (ConvertTo-AgyHtml $groupName) + '</h3><span class="status">' +
                (ConvertTo-AgyHtml ([string]$r.Status)) + '</span></div>')

            foreach ($item in @(
                @{Name='Weekly'; Data=$weekly; ResetName='Next weekly reset'},
                @{Name='5-hour'; Data=$five; ResetName='Next 5-hour reset'})) {
                $d = $item.Data
                $md.Add("**$($item.Name): $($d.PercentageText) remaining**")
                $md.Add('')
                $md.Add('`' + $d.Bar + '`')
                $md.Add('')
                $md.Add("$($item.ResetName): $($d.ResetText)")
                $md.Add('')

                $widthPercent = $d.Percentage.ToString('0.00',[Globalization.CultureInfo]::InvariantCulture)
                $barHtml = if ($d.Available) {
                    '<div class="track" role="progressbar" aria-label="' +
                    (ConvertTo-AgyHtml ($item.Name + ' remaining')) +
                    '" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + $widthPercent +
                    '"><div class="fill" style="width:' + $widthPercent + '%"></div></div>'
                } else {
                    '<div class="track" aria-label="Quota not reported"><div class="fill" style="width:0%"></div></div>'
                }
                [void]$html.AppendLine('<div class="bucket ' + $d.Level + '">' +
                    '<div class="bucket-head"><span>' + (ConvertTo-AgyHtml $item.Name) +
                    ' remaining</span><strong>' + (ConvertTo-AgyHtml $d.PercentageText) +
                    '</strong></div>' + $barHtml +
                    '<div class="reset-label">' + (ConvertTo-AgyHtml $item.ResetName) + '</div>' +
                    '<div class="reset">' + (ConvertTo-AgyHtml $d.ResetText) + '</div></div>')
            }
            [void]$html.AppendLine('</div>')
        }
        $md.Add('---')
        $md.Add('')
        [void]$html.AppendLine('</div></section>')
    }
    $md.Add('Quotas are snapshots. Run the refresh script again to update the bars and reset countdowns.')
    $md.Add('Unavailable or incomplete groups are **N/A**, not zero remaining.')
    [void]$html.AppendLine('<footer>Read-only snapshot. No account switching or credential saving. ' +
        'Unavailable quotas are shown as N/A, not 0%. ' +
        'Re-run the PowerShell refresh script for updated values and reset countdowns.</footer></main></body></html>')

    # UTF-8 files are directly viewable/pinnable inside common IDEs.
    Set-Content -LiteralPath $mdFile -Value $md.ToArray() -Encoding UTF8
    Set-Content -LiteralPath $htmlFile -Value $html.ToString() -Encoding UTF8
    return [pscustomobject]@{Markdown=$mdFile;HTML=$htmlFile}
}

$dashboardFiles = $null
if (-not $NoDashboard) {
    if ([string]::IsNullOrWhiteSpace($DashboardDirectory)) {
        $DashboardDirectory = $PSScriptRoot
    }
    $dashboardFiles = Write-AgyQuotaDashboards -Rows $results -Directory $DashboardDirectory
}

if ($PassThru) {
    $results
} else {
    $results | Select-Object Profile,Account,ModelGroup,Status,
        @{n='Weekly';e={$_.WeeklyRemaining}},WeeklyReset,
        @{n='5h';e={$_.FiveHourRemain}},@{n='5hReset';e={$_.FiveHourReset}} |
        Format-Table -AutoSize | Out-String -Width 260 | Write-Host
    Write-Host 'Read-only refresh: no switching or saving required. Missing groups are unavailable. Fully available buckets have no active reset countdown.'
    if ($null -ne $dashboardFiles) {
        Write-Host "Quota dashboard (pin in IDE): $($dashboardFiles.Markdown)"
        Write-Host "Visual HTML dashboard:       $($dashboardFiles.HTML)"
    }
}
