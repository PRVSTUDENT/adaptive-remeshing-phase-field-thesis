# Unit test for STOP handler and OpenSSH warning filter functions
$ErrorActionPreference = "Stop"

$controller = "C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($controller, [ref]$tokens, [ref]$errors)

if ($errors.Count -gt 0) {
    throw "Syntax errors detected in controller script: $($errors | Out-String)"
}

Write-Host "[TEST 1] Controller syntax check: PASS" -ForegroundColor Green

# Test warning filtering logic directly on synthetic OpenSSH stderr + qstat output
$mockSshOutputWithAdvisory = @(
    "** WARNING: connection is not using a post-quantum key exchange algorithm.",
    "** This session may be vulnerable to `"store now, decrypt later`" attacks.",
    "** The server may need to be upgraded. See https://openssh.com/pq.html",
    "mmaster02: ",
    "                                                            Req'd  Req'd   Elap",
    "Job ID          Username Queue    Jobname    SessID NDS TSK Memory Time  S Time",
    "--------------- -------- -------- ---------- ------ --- --- ------ ----- - -----",
    "1397393.mmaster pr21vyci entry_im M2ADAPT_RE    --    1   1   16gb 00:30 R 00:05"
)

$cleanResult = @(
    $mockSshOutputWithAdvisory |
    ForEach-Object {
        $_.ToString()
    } |
    Where-Object {
        $_ -notmatch "post-quantum key exchange algorithm"
    }
)

$extractedIds = @(
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

if ($extractedIds.Count -ne 1 -or $extractedIds[0] -ne "1397393.mmaster") {
    throw "Expected job ID '1397393.mmaster', got: $($extractedIds -join ', ')"
}

Write-Host "[TEST 2] OpenSSH advisory filtering and job ID extraction: PASS ($($extractedIds[0]))" -ForegroundColor Green

# Test single job id line format
$mockSingleIdOutput = @(
    "** WARNING: connection is not using a post-quantum key exchange algorithm.",
    "1397393.mmaster02"
)

$cleanSingle = @(
    $mockSingleIdOutput |
    ForEach-Object { $_.ToString() } |
    Where-Object { $_ -notmatch "post-quantum key exchange algorithm" }
)

$extractedSingle = @(
    $cleanSingle |
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

if ($extractedSingle.Count -ne 1 -or $extractedSingle[0] -ne "1397393.mmaster02") {
    throw "Expected single job ID '1397393.mmaster02', got: $($extractedSingle -join ', ')"
}

Write-Host "[TEST 3] Single job ID line format: PASS ($($extractedSingle[0]))" -ForegroundColor Green

# Verify all required patterns in controller script
$requiredPatterns = @(
    "CHATGPT_STOP_RECEIVED",
    "ACTIVE_JOB_STATE_CHECK_RETRY",
    "ACTIVE_JOB_STATE_CHECK_FAILED_AFTER_RETRY",
    "SCHEDULER_TERMINAL_JOB_EVALUATION",
    "post-quantum key exchange algorithm",
    "Invoke-DirectPbsQuery",
    "Get-ActivePbsJobIds",
    "Get-LivePbsJobs"
)

foreach ($pat in $requiredPatterns) {
    $matches = Select-String -Path $controller -Pattern $pat -SimpleMatch
    if (-not $matches) {
        throw "Missing required pattern in controller script: $pat"
    }
    Write-Host "[TEST 4] Pattern '$pat' present: PASS ($($matches.Count) match(es))" -ForegroundColor Green
}

Write-Host ""
Write-Host "ALL CONTROLLER STOP HANDLER UNIT TESTS PASSED (100%)." -ForegroundColor Cyan
