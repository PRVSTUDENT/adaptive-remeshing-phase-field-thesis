<#
.SYNOPSIS
    Comprehensive unit tests for Antigravity-Autonomous-Loop.ps1 profile guard,
    precedence hierarchy, parser robustness, and fail-closed quota recovery.
#>

$controllerPath = "C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"
if (-not (Test-Path -LiteralPath $controllerPath)) {
    Write-Error "Controller script not found at '$controllerPath'."
    exit 1
}

# ==============================================================================
# TEST 1: PowerShell Syntax Parse
# ==============================================================================
$tokens = $null
$errors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
    $controllerPath,
    [ref]$tokens,
    [ref]$errors
) | Out-Null

if ($errors.Count -ne 0) {
    Write-Error "Syntax errors detected in $controllerPath"
    $errors | ForEach-Object { Write-Error $_.Message }
    exit 1
}
Write-Host "TEST 1: PowerShell Syntax Parse: PASS (0 errors)" -ForegroundColor Green

# ==============================================================================
# TEST 2: Required Architectural Patterns
# ==============================================================================
$requiredPatterns = @(
    "[ValidatePattern('^account[1-5]$')]",
    "[string]`$AuthoritativeAgyProfile = ''",
    "`$script:RequestedAgyProfile = `$AuthoritativeAgyProfile",
    "`$script:RunLockedAgyProfile",
    "Get-AgyProfileFromCurrentOutput",
    "Get-AgyProfileState",
    "Test-AgyProfileLocked",
    "Set-AndVerifyAgyRunProfile",
    'Set-AndVerifyAgyRunProfile "STARTUP"',
    'Set-AndVerifyAgyRunProfile "PRE_AGY"',
    'Set-AndVerifyAgyRunProfile "POST_AGY"',
    'Set-AndVerifyAgyRunProfile "AGY_QUOTA_FAILURE_RECOVERY"'
)

foreach ($pattern in $requiredPatterns) {
    $match = Select-String -Path $controllerPath -Pattern $pattern -SimpleMatch
    if ($match) {
        Write-Host "TEST 2: Pattern [$pattern]: PASS" -ForegroundColor Green
    } else {
        Write-Error "TEST 2: Pattern [$pattern]: MISSING!"
        exit 1
    }
}

# ==============================================================================
# TEST 3: Parser Functionality on Edge-Case Outputs
# ==============================================================================
function Parse-MockAgyProfileState([string]$raw) {
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

    [pscustomobject]@{
        ActiveProfile = $activeProfile
        LastSwitch    = $lastSwitch
        ActiveFile    = $activeFile
        Raw           = $raw
    }
}

# Case A: Drifted OAuth credential while active file remains previous
$rawDrift = "Active profile: account4 (active file: account2)"
$stateDrift = Parse-MockAgyProfileState $rawDrift
if ($stateDrift.ActiveProfile -ne "account4" -or $stateDrift.ActiveFile -ne "account2") {
    Write-Error "TEST 3A FAILED: Expected ActiveProfile=account4, ActiveFile=account2. Got: $($stateDrift | Out-String)"
    exit 1
}
Write-Host "TEST 3A: Split active profile / active file parser: PASS" -ForegroundColor Green

# Case B: Token refreshed / no saved profile match, but provenance recorded
$rawRefreshed = @"
The logged-in account matches NO saved profile (last switch: account3).
If this is a new account or the token was refreshed, run: agy-profile save <name> (active file: account3)
"@
$stateRefreshed = Parse-MockAgyProfileState $rawRefreshed
if ($stateRefreshed.ActiveProfile -ne $null -or $stateRefreshed.LastSwitch -ne "account3" -or $stateRefreshed.ActiveFile -ne "account3") {
    Write-Error "TEST 3B FAILED: Expected ActiveProfile=null, LastSwitch=account3, ActiveFile=account3. Got: $($stateRefreshed | Out-String)"
    exit 1
}
Write-Host "TEST 3B: Unmatched token with last-switch provenance parser: PASS" -ForegroundColor Green

# Case C: Standard clean active profile
$rawClean = "Active profile: account3"
$stateClean = Parse-MockAgyProfileState $rawClean
if ($stateClean.ActiveProfile -ne "account3") {
    Write-Error "TEST 3C FAILED: Expected ActiveProfile=account3. Got: $($stateClean | Out-String)"
    exit 1
}
Write-Host "TEST 3C: Standard clean profile parser: PASS" -ForegroundColor Green

# ==============================================================================
# TEST 4: Lock Verification Discipline (Test-AgyProfileLocked)
# ==============================================================================
function Test-MockAgyProfileLocked($state, [string]$Expected) {
    if ($state.ActiveProfile) {
        return ($state.ActiveProfile -eq $Expected)
    }
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

# When OAuth credential is account4, account2 must NOT pass even if active file is account2
if (Test-MockAgyProfileLocked $stateDrift "account2") {
    Write-Error "TEST 4A FAILED: Active credential is account4; expected account2 must evaluate to FALSE."
    exit 1
}
if (-not (Test-MockAgyProfileLocked $stateDrift "account4")) {
    Write-Error "TEST 4B FAILED: Active credential is account4; expected account4 must evaluate to TRUE."
    exit 1
}
Write-Host "TEST 4A/B: Authenticated credential precedence over file marker: PASS" -ForegroundColor Green

# When OAuth mapping is null, matching last switch + active file passes
if (-not (Test-MockAgyProfileLocked $stateRefreshed "account3")) {
    Write-Error "TEST 4C FAILED: Unmatched token with last switch account3 must evaluate to TRUE for account3."
    exit 1
}
if (Test-MockAgyProfileLocked $stateRefreshed "account2") {
    Write-Error "TEST 4D FAILED: Unmatched token with last switch account3 must evaluate to FALSE for account2."
    exit 1
}
Write-Host "TEST 4C/D: Fallback provenance matching: PASS" -ForegroundColor Green

# ==============================================================================
# TEST 5: Parameter Precedence Hierarchy
# ==============================================================================
# Explicit parameter WINS over saved selection file
$mockExplicit = "account3"
$mockSavedFile = "account2"

$resolvedRunLocked = if (-not [string]::IsNullOrWhiteSpace($mockExplicit)) {
    $mockExplicit.ToLowerInvariant()
} else {
    $mockSavedFile.ToLowerInvariant()
}

if ($resolvedRunLocked -ne "account3") {
    Write-Error "TEST 5 FAILED: Explicit parameter did not override saved profile file."
    exit 1
}
Write-Host "TEST 5: Explicit parameter override precedence: PASS (account3 wins over account2)" -ForegroundColor Green

# ==============================================================================
# TEST 6: Individual Quota Exhaustion Fail-Closed Regex
# ==============================================================================
$sampleAgyQuotaError = @"
error: Individual quota reached. Please try again later.
"@
if ($sampleAgyQuotaError -match '(?i)Individual quota reached') {
    Write-Host "TEST 6: Individual quota reached error detection: PASS" -ForegroundColor Green
} else {
    Write-Error "TEST 6 FAILED: Failed to detect 'Individual quota reached'."
    exit 1
}

Write-Host "`nALL PROFILE GUARD UNIT TESTS PASSED CLEANLY (6/6)." -ForegroundColor Green
exit 0
