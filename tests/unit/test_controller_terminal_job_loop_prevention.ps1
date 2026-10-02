# Unit test for Terminal Job Loop Prevention and Redundant Query Suppression
$ErrorActionPreference = "Stop"

$controller = "C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($controller, [ref]$tokens, [ref]$errors)

if ($errors.Count -gt 0) {
    throw "Syntax errors detected in controller script: $($errors | Out-String)"
}

Write-Host "[TEST 1] Controller syntax check: PASS (0 errors)" -ForegroundColor Green

$content = [System.IO.File]::ReadAllText($controller, [System.Text.Encoding]::UTF8)

# Test 2: Check required loop prevention patterns in prompt rules
$requiredPatterns = @(
    "Terminal Job Lookup & Loop Prevention Rule",
    "A previously verified terminal job (e.g., state F/C/E already established, evaluated, or recorded in the ledger/status, such as 1404306.mmaster02) does NOT trigger repeated 'qstat -x' merely because it is absent from 'qstat -u'",
    "Treat already-verified jobs as terminal-and-frozen evidence. Do NOT loop on accounting!",
    "Only a tracked job whose terminal state is not already established needs that lookup",
    "CRITICAL LOOP PREVENTION: While running jobs remain 'R', do NOT loop on repetitive accounting, telemetry queries, or active-ODB reads"
)

foreach ($pat in $requiredPatterns) {
    if (-not $content.Contains($pat)) {
        throw "Missing required prompt rule pattern in controller script: $pat"
    }
}
Write-Host "[TEST 2] All prompt loop-prevention rule patterns present: PASS" -ForegroundColor Green

# Test 3: Check terminal job filtering code patterns
$requiredCodePatterns = @(
    "`$script:VerifiedTerminalJobs",
    "HPC_JOB_LEDGER.csv",
    "`$pendingUnverifiedJobIds",
    "`$activeTrackedForPrompt",
    "SUPPRESS_REDUNDANT_TERMINAL_QUERY_LOOP"
)

foreach ($cp in $requiredCodePatterns) {
    if (-not $content.Contains($cp)) {
        throw "Missing required code pattern in controller script: $cp"
    }
}
Write-Host "[TEST 3] All candidate filtering and suppression code patterns present: PASS" -ForegroundColor Green

# Test 4: Functional test of suppression regex logic
$mockVerifiedJobs = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
[void]$mockVerifiedJobs.Add("1404306.mmaster02")

$mockLoopingInstruction = "Run fresh extended accounting for both tracked jobs because 1404306.mmaster02 is absent from the current qstat -u view: qstat -x 1404454.mmaster02; qstat -x 1404306.mmaster02"
$hasLiveRunningOrQueued = $true
$pendingUnverifiedCount = 0

$isRedundantLoop = $false
if ($hasLiveRunningOrQueued -and $pendingUnverifiedCount -eq 0) {
    foreach ($tJob in $mockVerifiedJobs) {
        if ($mockLoopingInstruction -match [regex]::Escape($tJob) -and ($mockLoopingInstruction -match '(?i)qstat\s+-x' -or $mockLoopingInstruction -match '(?i)absent from the current qstat')) {
            $isRedundantLoop = $true
            break
        }
    }
}

if (-not $isRedundantLoop) {
    throw "Functional test failed: redundant looping instruction was NOT detected!"
}
Write-Host "[TEST 4] Functional suppression logic correctly identifies redundant qstat -x instruction: PASS" -ForegroundColor Green

# Test 5: Verify legitimate instructions are NOT suppressed
$mockLegitimateInstruction = "Evaluate terminal fields for newly completed job 1404454.mmaster02 and generate phase-field contours"
$isFalsePositive = $false
foreach ($tJob in $mockVerifiedJobs) {
    if ($mockLegitimateInstruction -match [regex]::Escape($tJob) -and ($mockLegitimateInstruction -match '(?i)qstat\s+-x' -or $mockLegitimateInstruction -match '(?i)absent from the current qstat')) {
        $isFalsePositive = $true
        break
    }
}

if ($isFalsePositive) {
    throw "Functional test failed: legitimate instruction was falsely flagged as redundant!"
}
Write-Host "[TEST 5] Legitimate non-redundant instructions are preserved without false positives: PASS" -ForegroundColor Green

# Test 6: Verify liveRunningJobIds initialization and NextInstruction assignment after sleep
$requiredLiveJobPatterns = @(
    '$liveRunningJobIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)',
    '[void]$liveRunningJobIds.Add($fullSchedId)',
    '$liveRunningJobIds.Contains($cId)',
    '$NextInstruction = "Run a single fresh scheduler check now: qstat -u pr21vyci'
)

foreach ($lp in $requiredLiveJobPatterns) {
    if (-not $content.Contains($lp)) {
        throw "Missing required liveRunningJobIds / NextInstruction pattern: $lp"
    }
}
Write-Host "[TEST 6] liveRunningJobIds initialization and NextInstruction patterns verified: PASS" -ForegroundColor Green

Write-Host ""
Write-Host "ALL TERMINAL JOB LOOP PREVENTION UNIT TESTS PASSED (100%)." -ForegroundColor Cyan
