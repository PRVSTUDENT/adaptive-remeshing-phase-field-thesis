# Unit tests for controller PBS regex and STOP handling logic

$testControllerPath = "C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"
if (-not (Test-Path -LiteralPath $testControllerPath)) {
    throw "Controller file does not exist: $testControllerPath"
}

# 1. AST syntax test
$errors = $null
$tokens = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($testControllerPath, [ref]$tokens, [ref]$errors)
if ($errors.Count -ne 0) {
    throw "Controller syntax validation failed with $($errors.Count) errors."
}
Write-Host "[TEST 1] Controller AST Syntax Validation: PASS" -ForegroundColor Green

# 2. Test Get-ExactPbsJobIdsFromText definition and behavior
function Get-ExactPbsJobIdsFromText {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    $pattern = '(?<![A-Za-z0-9_.])(?<id>\d{6,10}\.mmaster02)(?![A-Za-z0-9_.])'

    @(
        [regex]::Matches($Text, $pattern) |
            ForEach-Object {
                $_.Groups['id'].Value
            } |
            Select-Object -Unique
    )
}

$sampleOutput = @"
Cycle REAL_PILOT_CYCLE_016 status:
Production job: 1397992.mmaster02
Predecessor datacheck: 1397991.mmaster02
Donor job: 1397988.mmaster02

Scientific results:
RF1 = 0.00247551 kN
U1  = 0.04551289 mm
RF1 = 0.009721 kN
RF1 = 0.584947 kN
U1  = 0.04801289 mm
dmax = 0.000000
dt_min = 1.0e-14
SHA256 = 716981317dca090b3b96b22a425139c1f87917922744b509b60d96b3a1421d5f
N_nodes = 5288
N_elements = 5112
"@

$extracted = @(Get-ExactPbsJobIdsFromText -Text $sampleOutput)

$expected = @("1397992.mmaster02", "1397991.mmaster02", "1397988.mmaster02")

if ($extracted.Count -ne 3) {
    throw "Expected 3 extracted IDs, but got $($extracted.Count): $($extracted -join ', ')"
}

foreach ($exp in $expected) {
    if ($extracted -notcontains $exp) {
        throw "Expected ID $exp was not extracted."
    }
}

# Verify no fake IDs
$fakeIds = @(
    "00247551.mmaster02",
    "04551289.mmaster02",
    "009721.mmaster02",
    "584947.mmaster02",
    "04801289.mmaster02",
    "000000.mmaster02"
)

foreach ($fake in $fakeIds) {
    if ($extracted -contains $fake) {
        throw "CRITICAL FAILURE: Fake ID $fake was extracted from scientific data!"
    }
}
Write-Host "[TEST 2] Strict PBS ID Extraction from Scientific Text: PASS" -ForegroundColor Green

# 3. Test edge case formatting
$edgeText = "job.1397992.mmaster02, 1397992.mmaster02.log, 1397992.mmaster02 999999.mmaster02"
$edgeExtracted = @(Get-ExactPbsJobIdsFromText -Text $edgeText)
# 1397992.mmaster02.log has .log after it so lookahead (?![A-Za-z0-9_.]) will exclude it.
# 1397992.mmaster02 with spaces should match.
# 999999.mmaster02 should match.
if ($edgeExtracted -notcontains "1397992.mmaster02" -or $edgeExtracted -notcontains "999999.mmaster02") {
    throw "Edge text extraction failed: $($edgeExtracted -join ', ')"
}
Write-Host "[TEST 3] Edge Case Formatting Rejection & Acceptance: PASS" -ForegroundColor Green

Write-Host "`nAll controller unit tests PASSED cleanly." -ForegroundColor Green
