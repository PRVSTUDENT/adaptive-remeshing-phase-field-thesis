# Script to apply profile parameter override & pre-AGY drift guard patch
$ErrorActionPreference = "Stop"

$filePath = "$env:USERPROFILE\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"
if (-not (Test-Path -LiteralPath $filePath)) {
    throw "Target file not found: $filePath"
}

$content = [System.IO.File]::ReadAllText($filePath, [System.Text.Encoding]::UTF8)
$content = $content -replace "`r`n", "`n"

function Clean-Replace([string]$target, [string]$oldBlock, [string]$newBlock) {
    $cleanOld = $oldBlock -replace "`r`n", "`n"
    $cleanNew = $newBlock -replace "`r`n", "`n"
    if (-not $target.Contains($cleanOld)) {
        throw "Target block not found: $($cleanOld.Substring(0, [Math]::Min(60, $cleanOld.Length)))"
    }
    return $target.Replace($cleanOld, $cleanNew)
}

# 1. Replace parameter declaration
$oldParam = @'
    # Authoritative manual AGY profile. Enforced every turn. Default: "account1"
    [string]$AuthoritativeAgyProfile = "account1",
'@

$newParam = @'
    # Authoritative manual AGY profile. Explicit caller selection always wins.
    [ValidatePattern('^account[1-5]$')]
    [string]$AuthoritativeAgyProfile = '',
'@

$content = Clean-Replace $content $oldParam $newParam

# 2. Replace post-param initialization and profile functions
$oldPostParam = @'
    [string]$ActiveProductionJobId = "",

    [switch]$AllowSkipPermissions = $true
)

if (Test-Path "C:\Program Files\Git\usr\bin") {
    if ($env:PATH -notlike "*C:\Program Files\Git\usr\bin*") {
        $env:PATH = "C:\Program Files\Git\usr\bin;$env:PATH"
    }
}
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$PadDir = "$env:USERPROFILE\OpenClawPAD"
if (-not (Test-Path $PadDir)) { New-Item -ItemType Directory -Path $PadDir -Force | Out-Null }

$LogFile    = Join-Path $PadDir "controller_activity.log"
$StatusFile = Join-Path $PadDir "controller_latest_status.json"
$StateFile  = Join-Path $PadDir "antigravity_loop_state.json"
$SelectionFile = Join-Path $PadDir "agy_selected_profile.json"

$script:AuthoritativeAgyProfile = if (-not [string]::IsNullOrWhiteSpace($AuthoritativeAgyProfile)) { $AuthoritativeAgyProfile } else { "account1" }

function Get-ManuallySelectedAgyProfile {
    if (Test-Path -LiteralPath $SelectionFile) {
        try {
            $sel = Get-Content -LiteralPath $SelectionFile -Raw | ConvertFrom-Json
            if (-not [string]::IsNullOrWhiteSpace([string]$sel.selected_profile)) {
                return [string]$sel.selected_profile
            }
        } catch { }
    }
    if (-not [string]::IsNullOrWhiteSpace($script:AuthoritativeAgyProfile)) {
        return $script:AuthoritativeAgyProfile
    }
    return "account1"
}

function Ensure-AuthoritativeAgyProfile {
    param(
        [string]$Context = "unknown"
    )

    $target = Get-ManuallySelectedAgyProfile
    if ([string]::IsNullOrWhiteSpace($target)) {
        $target = if (-not [string]::IsNullOrWhiteSpace($script:AuthoritativeAgyProfile)) { $script:AuthoritativeAgyProfile } else { "account1" }
    }
    $script:AuthoritativeAgyProfile = $target

    $savedInfoPref = $InformationPreference
    $InformationPreference = 'Continue'
    $current = ""
    $global:LASTEXITCODE = 0
    try {
        $current = (& agy-profile current 6>&1 2>&1 3>&1 | Out-String).Trim()
    }
    catch {
        $current = "ERROR: $($_.Exception.Message)"
    }
    finally {
        $InformationPreference = $savedInfoPref
    }

    $activeFile = Join-Path "$env:USERPROFILE\.gemini\agy-profiles" "_active.txt"
    $activeFileProfile = if (Test-Path -LiteralPath $activeFile) { (Get-Content -LiteralPath $activeFile -Raw).Trim() } else { "" }

    $isTargetActive = (
        (-not [string]::IsNullOrWhiteSpace($current)) -and
        ($current -match "(?i)\b$([regex]::Escape($target))\b") -and
        ($current -notmatch "(?i)matches NO saved profile") -and
        ($current -notmatch "(?i)^ERROR:") -and
        ([string]::IsNullOrWhiteSpace($activeFileProfile) -or $activeFileProfile -eq $target)
    )

    if (-not $isTargetActive) {
        Write-Host ""
        Write-Host "==========================================================" -ForegroundColor Yellow
        Write-Host " AGY PROFILE DRIFT DETECTED [$Context]" -ForegroundColor Yellow
        Write-Host " Required: $target" -ForegroundColor Yellow
        Write-Host " Current:  $current (active file: $activeFileProfile)" -ForegroundColor Yellow
        Write-Host " Restoring authoritative profile..." -ForegroundColor Yellow
        Write-Host "==========================================================" -ForegroundColor Yellow

        $global:LASTEXITCODE = 0
        try {
            $null = & agy-profile switch $target -Force 6>&1 2>&1 3>&1
        }
        catch {
            $err = "FATAL: Exception while restoring AGY profile '$target' in context '$Context': $($_.Exception.Message)"
            if (Get-Command Write-LoopLog -ErrorAction SilentlyContinue) {
                Write-LoopLog -Turn $CurrentTurn -Tier "CONTROLLER" -Action "PROFILE_RESTORE_FAILED" -Message $err
            }
            throw $err
        }

        # Verify against active profile
        $verify = ""
        $savedInfoPref = $InformationPreference
        $InformationPreference = 'Continue'
        $global:LASTEXITCODE = 0
        try {
            $verify = (& agy-profile current 6>&1 2>&1 3>&1 | Out-String).Trim()
        }
        catch {
            $verify = "ERROR: $($_.Exception.Message)"
        }
        finally {
            $InformationPreference = $savedInfoPref
        }

        $activeFileProfileAfter = if (Test-Path -LiteralPath $activeFile) { (Get-Content -LiteralPath $activeFile -Raw).Trim() } else { "" }

        $verifiedOk = (
            (-not [string]::IsNullOrWhiteSpace($verify)) -and
            ($verify -match "(?i)\b$([regex]::Escape($target))\b") -and
            ($verify -notmatch "(?i)matches NO saved profile") -and
            ($verify -notmatch "(?i)^ERROR:") -and
            ([string]::IsNullOrWhiteSpace($activeFileProfileAfter) -or $activeFileProfileAfter -eq $target)
        )

        if (-not $verifiedOk) {
            $err = "FATAL: AGY profile restoration verification failed in context '$Context'. Current='$verify' (active file: '$activeFileProfileAfter')"
            if (Get-Command Write-LoopLog -ErrorAction SilentlyContinue) {
                Write-LoopLog -Turn $CurrentTurn -Tier "CONTROLLER" -Action "PROFILE_VERIFY_FAILED" -Message $err
            }
            throw $err
        }

        Write-Host "[PROFILE-GUARD] Restored and verified '$target' [$Context]." -ForegroundColor Green
        if (Get-Command Write-LoopLog -ErrorAction SilentlyContinue) {
            Write-LoopLog -Turn $CurrentTurn -Tier "CONTROLLER" -Action "PROFILE_RESTORED" -Message "Restored and verified authoritative profile '$target' in context '$Context'."
        }
    }
}
'@

$newPostParam = @'
    [string]$ActiveProductionJobId = "",

    [switch]$AllowSkipPermissions = $true
)

Write-Host " DEBUG PROFILE PARAMETER"
Write-Host " Raw parameter value: '$AuthoritativeAgyProfile'"
Write-Host " Was explicitly bound: $($PSBoundParameters.ContainsKey('AuthoritativeAgyProfile'))"

$script:RequestedAgyProfile = $AuthoritativeAgyProfile

if (Test-Path "C:\Program Files\Git\usr\bin") {
    if ($env:PATH -notlike "*C:\Program Files\Git\usr\bin*") {
        $env:PATH = "C:\Program Files\Git\usr\bin;$env:PATH"
    }
}
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$PadDir = "$env:USERPROFILE\OpenClawPAD"
if (-not (Test-Path $PadDir)) { New-Item -ItemType Directory -Path $PadDir -Force | Out-Null }

$LogFile       = Join-Path $PadDir "controller_activity.log"
$StatusFile    = Join-Path $PadDir "controller_latest_status.json"
$StateFile     = Join-Path $PadDir "antigravity_loop_state.json"
$SelectionFile = Join-Path $PadDir "agy_selected_profile.json"

function Get-AgyProfileFromCurrentOutput {
    $raw = ""
    $global:LASTEXITCODE = 0
    try {
        $raw = (& agy-profile current *>&1 | Out-String).Trim()
    }
    catch {
        $raw = "ERROR: $($_.Exception.Message)"
    }

    if ($raw -match '(?im)^Active profile:\s*(account[1-5])\b') {
        return $Matches[1].ToLowerInvariant()
    }

    if ($raw -match '(?i)last switch:\s*(account[1-5])') {
        return $Matches[1].ToLowerInvariant()
    }

    if ($raw -match '(?i)active file:\s*(account[1-5])') {
        return $Matches[1].ToLowerInvariant()
    }

    $activeFile = Join-Path "$env:USERPROFILE\.gemini\agy-profiles" "_active.txt"
    if (Test-Path -LiteralPath $activeFile) {
        $af = (Get-Content -LiteralPath $activeFile -Raw).Trim()
        if ($af -match '(?i)^account[1-5]$') {
            return $af.ToLowerInvariant()
        }
    }

    $selectionFile = Join-Path "$env:USERPROFILE\OpenClawPAD" "agy_selected_profile.json"
    if (Test-Path -LiteralPath $selectionFile) {
        try {
            $sel = Get-Content -LiteralPath $selectionFile -Raw | ConvertFrom-Json
            if ($sel.selected_profile -match '(?i)^account[1-5]$') {
                return ([string]$sel.selected_profile).ToLowerInvariant()
            }
        } catch {}
    }

    throw "Unable to determine active AGY profile.`n$raw"
}

if (-not [string]::IsNullOrWhiteSpace($script:RequestedAgyProfile)) {
    # Explicit caller selection always wins.
    $script:RunLockedAgyProfile = $script:RequestedAgyProfile.ToLowerInvariant()
}
else {
    # Only auto-detect when caller supplied nothing.
    $script:RunLockedAgyProfile = Get-AgyProfileFromCurrentOutput
}

# Compatibility alias
$script:AuthoritativeAgyProfile = $script:RunLockedAgyProfile

Write-Host " Run-Locked Authoritative Profile: '$script:RunLockedAgyProfile'" -ForegroundColor Green

function Get-ManuallySelectedAgyProfile {
    if (-not [string]::IsNullOrWhiteSpace($script:RunLockedAgyProfile)) {
        return $script:RunLockedAgyProfile
    }
    if (-not [string]::IsNullOrWhiteSpace($script:RequestedAgyProfile)) {
        return $script:RequestedAgyProfile
    }
    return "account1"
}

function Get-AgyProfileState {
    $raw = ""
    $global:LASTEXITCODE = 0
    try {
        $raw = (& agy-profile current *>&1 | Out-String).Trim()
    }
    catch {
        $raw = "ERROR: $($_.Exception.Message)"
    }

    $activeProfile = $null
    $lastSwitch    = $null
    $activeFile    = $null

    if ($raw -match '(?im)^Active profile:\s*(account[1-5])\b') {
        $activeProfile = $Matches[1].ToLowerInvariant()
    }

    if ($raw -match '(?i)last switch:\s*(account[1-5])') {
        $lastSwitch = $Matches[1].ToLowerInvariant()
    }

    if ($raw -match '(?i)active file:\s*(account[1-5])') {
        $activeFile = $Matches[1].ToLowerInvariant()
    }

    if (-not $activeFile) {
        $afPath = Join-Path "$env:USERPROFILE\.gemini\agy-profiles" "_active.txt"
        if (Test-Path -LiteralPath $afPath) {
            $af = (Get-Content -LiteralPath $afPath -Raw).Trim().ToLowerInvariant()
            if ($af -match '^account[1-5]$') {
                $activeFile = $af
            }
        }
    }

    [pscustomobject]@{
        ActiveProfile = $activeProfile
        LastSwitch    = $lastSwitch
        ActiveFile    = $activeFile
        Raw           = $raw
    }
}

function Test-AgyProfileLocked {
    param(
        [Parameter(Mandatory)]
        [string]$Expected
    )

    $state = Get-AgyProfileState

    if ($state.ActiveProfile) {
        return ($state.ActiveProfile -eq $Expected)
    }

    # If AGY cannot map the current OAuth credential to a saved profile,
    # require at least the selected file / last-switch provenance to match.
    if (
        $state.ActiveFile -eq $Expected -and
        (
            -not $state.LastSwitch -or
            $state.LastSwitch -eq $Expected
        )
    ) {
        return $true
    }

    return $false
}

function Set-AndVerifyAgyRunProfile {
    param(
        [Parameter(Mandatory)]
        [string]$Context
    )

    $expected = $script:RunLockedAgyProfile

    $state = Get-AgyProfileState

    $mustRestore = $false

    if ($state.ActiveProfile) {
        $mustRestore = ($state.ActiveProfile -ne $expected)
    }
    else {
        $mustRestore = (
            $state.ActiveFile -ne $expected -or
            (
                $state.LastSwitch -and
                $state.LastSwitch -ne $expected
            )
        )
    }

    if ($mustRestore) {
        Write-Host ""
        Write-Host "==========================================================" -ForegroundColor Yellow
        Write-Host " AGY PROFILE DRIFT DETECTED [$Context]" -ForegroundColor Yellow
        Write-Host " Required: $expected" -ForegroundColor Yellow
        Write-Host " Current state:" -ForegroundColor Yellow
        Write-Host $state.Raw -ForegroundColor Yellow
        Write-Host " Restoring authoritative run profile..." -ForegroundColor Yellow
        Write-Host "==========================================================" -ForegroundColor Yellow

        $global:LASTEXITCODE = 0
        try {
            $null = & agy-profile switch $expected -Force *>&1
        }
        catch {
            $err = "FATAL: Could not restore AGY profile '$expected' in context '$Context': $($_.Exception.Message)"
            if (Get-Command Write-LoopLog -ErrorAction SilentlyContinue) {
                Write-LoopLog -Turn $CurrentTurn -Tier "CONTROLLER" -Action "PROFILE_RESTORE_FAILED" -Message $err
            }
            throw $err
        }

        # Keep agy_selected_profile.json synchronized with the active restored profile
        if (Test-Path $PadDir) {
            try {
                $selObj = [ordered]@{
                    selected_profile = $expected
                    source           = "controller_run_lock"
                    switched_at_utc  = [DateTime]::UtcNow.ToString("o")
                    switched_by      = "Set-AndVerifyAgyRunProfile"
                }
                [System.IO.File]::WriteAllText(
                    $SelectionFile,
                    ($selObj | ConvertTo-Json -Depth 5),
                    [System.Text.UTF8Encoding]::new($false)
                )
            } catch {}
        }
    }

    $verify = Get-AgyProfileState

    if (
        $verify.ActiveProfile -and
        $verify.ActiveProfile -ne $expected
    ) {
        $err = @"
AGY profile verification failed [$Context].
Expected authenticated profile: $expected
Detected authenticated profile: $($verify.ActiveProfile)
Active file: $($verify.ActiveFile)
"@
        if (Get-Command Write-LoopLog -ErrorAction SilentlyContinue) {
            Write-LoopLog -Turn $CurrentTurn -Tier "CONTROLLER" -Action "PROFILE_VERIFY_FAILED" -Message $err
        }
        throw $err
    }

    if (
        -not $verify.ActiveProfile -and
        $verify.ActiveFile -ne $expected
    ) {
        $err = @"
AGY profile verification failed [$Context].
Expected active file: $expected
Detected active file: $($verify.ActiveFile)
Raw:
$($verify.Raw)
"@
        if (Get-Command Write-LoopLog -ErrorAction SilentlyContinue) {
            Write-LoopLog -Turn $CurrentTurn -Tier "CONTROLLER" -Action "PROFILE_VERIFY_FAILED" -Message $err
        }
        throw $err
    }

    Write-Host "[PROFILE-GUARD] Verified '$expected' [$Context]." -ForegroundColor Green
}

function Ensure-AuthoritativeAgyProfile {
    param([string]$Context = "unknown")
    Set-AndVerifyAgyRunProfile -Context $Context
}
'@

$content = Clean-Replace $content $oldPostParam $newPostParam

# 3. Replace Get-CurrentAgyProfileName function
$oldGetCurrent = @'
function Get-CurrentAgyProfileName {

    $cmd = Get-Command agy-profile -ErrorAction SilentlyContinue

    if (-not $cmd) {
        throw "agy-profile command is unavailable."
    }

    $savedEap = $ErrorActionPreference

    try {
        $ErrorActionPreference = "Continue"
        $rawCurrent = & agy-profile current *>&1
    }
    finally {
        $ErrorActionPreference = $savedEap
    }

    $currentText = ($rawCurrent | Out-String).Trim()

    foreach ($profile in $AgyProfileRotationOrder) {

        $escaped = [regex]::Escape($profile)

        if (
            $currentText -match "(?im)(^|[\s:])$escaped([\s]|$)"
        ) {
            return $profile
        }
    }


    # Fallback: agy-profile list marks the matching account with '*'.
    try {

        $savedEap = $ErrorActionPreference

        try {
            $ErrorActionPreference = "Continue"
            $rawList = & agy-profile list *>&1
        }
        finally {
            $ErrorActionPreference = $savedEap
        }

        foreach ($line in @($rawList)) {

            $text = [string]$line

            if ($text -match '^\s*\*\s*([^\s]+)') {

                $candidate = $Matches[1]

                if ($AgyProfileRotationOrder -contains $candidate) {
                    return $candidate
                }
            }
        }
    }
    catch {}


    if (
        -not [string]::IsNullOrWhiteSpace(
            [string]$script:LastAutoRotatedAgyProfile
        )
    ) {
        return $script:LastAutoRotatedAgyProfile
    }

    return $null
}
'@

$newGetCurrent = @'
function Get-CurrentAgyProfileName {
    $state = Get-AgyProfileState
    if ($state.ActiveProfile) {
        return $state.ActiveProfile
    }
    if ($state.ActiveFile) {
        return $state.ActiveFile
    }
    if ($state.LastSwitch) {
        return $state.LastSwitch
    }
    return $null
}
'@

$content = Clean-Replace $content $oldGetCurrent $newGetCurrent

# 4. Replace Startup profile initialization
$oldStartup = @'
Ensure-AuthoritativeAgyProfile "STARTUP"
$script:SelectedAgyProfile = Get-ManuallySelectedAgyProfile
$script:PinnedAgyProfile = $script:SelectedAgyProfile
Write-Host " Authoritative Manual Profile: $($script:SelectedAgyProfile)" -ForegroundColor Green
'@

$newStartup = @'
Set-AndVerifyAgyRunProfile "STARTUP"
$script:SelectedAgyProfile = $script:RunLockedAgyProfile
$script:PinnedAgyProfile = $script:RunLockedAgyProfile
Write-Host " Authoritative Manual Profile: $($script:RunLockedAgyProfile)" -ForegroundColor Green
'@

$content = Clean-Replace $content $oldStartup $newStartup

# 5. Replace AGY execution and quota fail-closed block
$oldAgyExec = @'
    Ensure-AuthoritativeAgyProfile "PRE_AGY"

    $turnStartTime = [DateTimeOffset]::UtcNow
    $agyRawOutput = $EffectiveInstruction | & $AgyPath @agyArgs 2>&1
    $agyExitCode  = $LASTEXITCODE
    $turnDurationSeconds = ([DateTimeOffset]::UtcNow - $turnStartTime).TotalSeconds
    $ErrorActionPreference = $prevEAP

    Ensure-AuthoritativeAgyProfile "POST_AGY"

    if ($agyExitCode -ne 0) {

        $errText = $agyRawOutput | Out-String

        $isQuotaFailure = Test-IsAgyQuotaLimitError `
            -Message $errText
'@

$newAgyExec = @'
    Set-AndVerifyAgyRunProfile "PRE_AGY"

    $turnStartTime = [DateTimeOffset]::UtcNow
    $agyRawOutput = $EffectiveInstruction | & $AgyPath @agyArgs 2>&1
    $agyExitCode  = $LASTEXITCODE
    $turnDurationSeconds = ([DateTimeOffset]::UtcNow - $turnStartTime).TotalSeconds
    $ErrorActionPreference = $prevEAP

    $agyText = ($agyRawOutput | Out-String)

    if (
        $agyExitCode -ne 0 -and
        $agyText -match '(?i)Individual quota reached'
    ) {
        Set-AndVerifyAgyRunProfile "AGY_QUOTA_FAILURE_RECOVERY"

        Write-LoopLog `
            -Turn $CurrentTurn `
            -Tier "CONTROLLER" `
            -Action "AGY_INDIVIDUAL_QUOTA_REACHED" `
            -Message "The run-locked profile '$script:RunLockedAgyProfile' reached its individual quota. Failing closed without account rotation."

        Save-LoopStatus `
            -Turn $CurrentTurn `
            -Status "FAILED" `
            -Tier "CONTROLLER" `
            -Action "AGY_INDIVIDUAL_QUOTA_EXHAUSTED" `
            -Details "The run-locked Antigravity profile '$script:RunLockedAgyProfile' has reached its individual quota. Automatic profile substitution is disabled."

        throw @"
The run-locked Antigravity profile '$script:RunLockedAgyProfile'
has reached its individual quota.

Automatic profile substitution is disabled.
The controller will not continue using another account.
"@
    }

    Set-AndVerifyAgyRunProfile "POST_AGY"

    if ($agyExitCode -ne 0) {

        $errText = $agyText

        $isQuotaFailure = Test-IsAgyQuotaLimitError `
            -Message $errText
'@

$content = Clean-Replace $content $oldAgyExec $newAgyExec

# Convert back to Windows CRLF
$content = $content -replace "`n", "`r`n"

# Write patched file
[System.IO.File]::WriteAllText($filePath, $content, [System.Text.Encoding]::UTF8)
Write-Host "Successfully patched $filePath" -ForegroundColor Green

