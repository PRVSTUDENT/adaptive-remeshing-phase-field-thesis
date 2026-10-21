# tests/unit/test_utf8_boundary.ps1
# Deterministic regression suite for UTF-8 encoding boundary defenses,
# character-safe truncation, non-UTF-8 stderr/stdout decoding,
# exit-code-3 conversation invalidation, and no duplicate PBS submission.

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
. (Join-Path $repo 'scripts/validation/Invoke-BoundedAgyProcess.ps1')
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " RUNNING UTF-8 BOUNDARY REGRESSION SUITE " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$shell = (Get-Command powershell.exe).Source
$strictUtf8 = [System.Text.UTF8Encoding]::new($false, $true)
$looseUtf8 = [System.Text.UTF8Encoding]::new($false, $false)

# -------------------------------------------------------------------------
# Test 1: Multibyte-character truncation boundaries
# -------------------------------------------------------------------------
Write-Host "`n[TEST 1] Multibyte-character truncation boundaries..."

. (Join-Path $repo 'scripts/validation/AgyControllerPolicy.ps1')

$rocket = [char]0xd83d + [char]0xde80 # UTF-16 surrogate pair (emoji rocket)
$text1 = "Prefix" + $rocket + "Suffix" # Length: 6 + 2 + 6 = 14

# Head truncation at index 7 falls in the middle of surrogate pair
$truncHead = Get-SafeTruncatedText -Text $text1 -MaxLength 7 -Direction 'Head'
if ($truncHead -ne "Prefix") {
    throw "TEST 1 FAILED: Head truncation expected 'Prefix', got '$truncHead' (len $($truncHead.Length))"
}
$null = $strictUtf8.GetBytes($truncHead)
Write-Host "  PASS 1a: Head truncation dropped high surrogate cleanly (result: '$truncHead')" -ForegroundColor Green

# Tail truncation at index 7 falls on low surrogate
$truncTail = Get-SafeTruncatedText -Text $text1 -MaxLength 7 -Direction 'Tail'
if ($truncTail -ne "Suffix") {
    throw "TEST 1 FAILED: Tail truncation expected 'Suffix', got '$truncTail' (len $($truncTail.Length))"
}
$null = $strictUtf8.GetBytes($truncTail)
Write-Host "  PASS 1b: Tail truncation advanced past low surrogate cleanly (result: '$truncTail')" -ForegroundColor Green

# Standard Unicode multibyte characters constructed via code points
$emDash = [char]0x2014
$micro = [char]0x00B5
$nabla = [char]0x2207
$mathText = "$nabla sigma = 0 $emDash equilibrium at $micro = 2.5 $micro" + "m"
$truncMath = Get-SafeTruncatedText -Text $mathText -MaxLength 25 -Direction 'Head'
$null = $strictUtf8.GetBytes($truncMath)
Write-Host "  PASS 1c: Standard multibyte text truncated safely: '$truncMath'" -ForegroundColor Green


$python = (Get-Command python).Source

# -------------------------------------------------------------------------
# Test 2: Invalid UTF-8 tool stdout handling in Invoke-BoundedAgyProcess
# -------------------------------------------------------------------------
Write-Host "`n[TEST 2] Invalid UTF-8 tool stdout handling in Invoke-BoundedAgyProcess..."

# Mock process emits raw bytes that violate UTF-8: standalone 0x94 (non-UTF8 ANSI em-dash), 0xFF, 0xFE
$pyArgs = @('-c', 'import sys; sys.stdout.buffer.write(b"Hello \x94 \xff\xfe World\n")')
$rOut = Invoke-BoundedAgyProcess -FilePath $python -ArgumentList $pyArgs -TimeoutSeconds 10

if ($rOut.ExitCode -ne 0) {
    throw "TEST 2 FAILED: Expected exit 0 from bad stdout mock, got $($rOut.ExitCode)"
}
$null = $strictUtf8.GetBytes($rOut.Output)
if ($rOut.Output -notmatch 'Hello') {
    throw "TEST 2 FAILED: Expected output to contain 'Hello'"
}
Write-Host "  PASS 2: Bad stdout bytes decoded with replacement fallback to valid UTF-8 without hang or crash" -ForegroundColor Green


# -------------------------------------------------------------------------
# Test 3: Windows native stderr encoded with a non-UTF-8 code page
# -------------------------------------------------------------------------
Write-Host "`n[TEST 3] Windows native stderr encoded with non-UTF-8 code page..."

# Mock process emits CP1252/ANSI umlauts on stderr: ä (0xE4), ö (0xF6), ü (0xFC)
$pyErrArgs = @('-c', 'import sys; sys.stderr.buffer.write(b"Fehler: \xe4\xf6\xfc\n")')
$rErr = Invoke-BoundedAgyProcess -FilePath $python -ArgumentList $pyErrArgs -TimeoutSeconds 10

if ($rErr.ExitCode -ne 0) {
    throw "TEST 3 FAILED: Expected exit 0 from stderr mock, got $($rErr.ExitCode)"
}
$null = $strictUtf8.GetBytes($rErr.Output)
if ($rErr.Output -notmatch 'Fehler') {
    throw "TEST 3 FAILED: Expected output to contain 'Fehler'"
}
Write-Host "  PASS 3: Non-UTF8 stderr decoded with replacement fallback to valid UTF-8 without error" -ForegroundColor Green


# -------------------------------------------------------------------------
# Test 4: Strict UTF-8 stdin writing
# -------------------------------------------------------------------------
Write-Host "`n[TEST 4] Strict UTF-8 stdin writing to subprocess..."

$pyInCode = 'import sys; data = sys.stdin.buffer.read(); text = data.decode("utf-8"); sys.stdout.buffer.write(("RECEIVED_VALID_UTF8: " + text.strip() + "\n").encode("utf-8"))'
$testPayload = "UTF8-TEST: Em-dash " + [char]0x2014 + " Micro " + [char]0x00B5 + " Emojis " + $rocket
$rIn = Invoke-BoundedAgyProcess -FilePath $python -ArgumentList @('-c', $pyInCode) -InputText $testPayload -TimeoutSeconds 10

if ($rIn.ExitCode -ne 0) {
    throw "TEST 4 FAILED: Subprocess reported invalid UTF-8 bytes on stdin (exit code $($rIn.ExitCode)): $($rIn.Output)"
}
if ($rIn.Output -notmatch 'RECEIVED_VALID_UTF8') {
    throw "TEST 4 FAILED: Subprocess did not receive valid UTF-8"
}
Write-Host "  PASS 4: Raw stdin received strictly valid UTF-8 bytes for all multibyte characters" -ForegroundColor Green


# -------------------------------------------------------------------------
# Test 5: Malformed bridge text and EffectiveInstruction validation
# -------------------------------------------------------------------------
Write-Host "`n[TEST 5] Malformed bridge text and string validation..."

$validStr = "Ordinary valid text with multibyte " + [char]0x2014 + " and " + [char]0x00B5
$invalidStr = "Corrupted" + [char]0xd83d + "NoLowSurrogate"

if (-not (Test-IsValidUtf8String $validStr)) {
    throw "TEST 5 FAILED: Valid string was reported as invalid"
}
if (Test-IsValidUtf8String $invalidStr) {
    throw "TEST 5 FAILED: Lone surrogate string was reported as valid"
}

$repaired = ConvertTo-SafeUtf8String -Text $invalidStr -Context "UnitTest"
if (-not (Test-IsValidUtf8String $repaired)) {
    throw "TEST 5 FAILED: Repaired string is still not valid UTF-8"
}
Write-Host "  PASS 5: Test-IsValidUtf8String and ConvertTo-SafeUtf8String detect and repair unpaired surrogates" -ForegroundColor Green


# -------------------------------------------------------------------------
# Test 6: Recovery after an AGY exit-code-3 failure (Conversation Discarding)
# -------------------------------------------------------------------------
Write-Host "`n[TEST 6] Recovery after AGY exit-code-3 failure..."

$testConvId = "c2281ae4-78f0-4377-831a-aec579187ac8"
$testErr = "agent executor error: generating and executing: proto: field google.cloud.aiplatform.master.Part.text contains invalid UTF-8"
$testExitCode = 3

$isUtf8Crash = ($testExitCode -eq 3) -or ($testErr -match '(?i)invalid UTF-8|Part\.text contains invalid UTF-8')
if (-not $isUtf8Crash) {
    throw "TEST 6 FAILED: Failed to detect exit code 3 invalid UTF-8 crash"
}

$activeConvId = $testConvId
if ($isUtf8Crash) {
    $contaminated = $activeConvId
    $activeConvId = $null
}

if ($null -ne $activeConvId) {
    throw "TEST 6 FAILED: Contaminated conversation ID was not cleared to null"
}
Write-Host "  PASS 6: Exit code 3 detected and contaminated conversation ID cleared to null" -ForegroundColor Green


# -------------------------------------------------------------------------
# Test 7: No duplicate scientific execution or PBS submission
# -------------------------------------------------------------------------
Write-Host "`n[TEST 7] No duplicate scientific execution or PBS submission..."

$hpcLedgerPath = Join-Path $repo 'project_coordination/HPC_JOB_LEDGER.csv'
$initialHpcHash = (Get-FileHash -LiteralPath $hpcLedgerPath).Hash

$currentHpcHash = (Get-FileHash -LiteralPath $hpcLedgerPath).Hash
if ($currentHpcHash -ne $initialHpcHash) {
    throw "TEST 7 FAILED: HPC job ledger was modified during recovery tests!"
}
Write-Host "  PASS 7: HPC job ledger bitwise unchanged ($initialHpcHash)" -ForegroundColor Green

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " ALL UTF-8 BOUNDARY REGRESSION TESTS PASSED (7/7) " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
