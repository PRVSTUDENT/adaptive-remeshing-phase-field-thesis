<# Read saved profiles independently. Never switch, save, or modify global credentials. #>
[CmdletBinding()]
param([ValidateRange(1,100)][int]$First=1,
      [ValidateRange(1,100)][int]$Last=5,
      [switch]$AuditOnly,
      [string]$GroupRegex='.*',
      [switch]$PassThru)
$ErrorActionPreference='Stop'
if ($First -gt $Last) { throw 'First must be <= Last.' }
Add-Type -AssemblyName System.Security
$python=Join-Path $env:APPDATA 'uv\tools\ai-limit-checker\Scripts\python.exe'
$worker=Join-Path $PSScriptRoot 'agy_profile_quota.py'
if(-not (Test-Path -LiteralPath $worker)){$worker=Join-Path $PSScriptRoot 'agy_saved_profile_quota.py'}
foreach($required in @($python,$worker)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Missing dependency: $required" }
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
if($PassThru) { $results }
else {
    $results | Select-Object Profile,Account,ModelGroup,Status,@{n='Weekly';e={$_.WeeklyRemaining}},WeeklyReset,@{n='5h';e={$_.FiveHourRemain}},@{n='5hReset';e={$_.FiveHourReset}} | Format-Table -AutoSize | Out-String -Width 260 | Write-Host
    Write-Host 'Read-only refresh: no switching or saving required. Missing groups are unavailable. Fully available buckets have no active reset countdown.'
}
