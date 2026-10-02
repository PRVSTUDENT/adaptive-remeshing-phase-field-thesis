$controller = "C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"
$tokens = $null
$errors = $null

[System.Management.Automation.Language.Parser]::ParseFile(
    $controller,
    [ref]$tokens,
    [ref]$errors
) | Out-Null

if ($errors.Count -eq 0) {
    Write-Host "POWERSHELL SYNTAX: PASS"
} else {
    Write-Host "POWERSHELL SYNTAX: FAIL"
    foreach ($err in $errors) {
        Write-Host "Line $($err.Extent.StartLineNumber), Col $($err.Extent.StartColumnNumber): $($err.Message)"
    }
    exit 1
}

$patterns = @(
    "Invoke-DirectPbsQuery",
    "Invoke-SchedulerReviewChatGPT",
    "SCHEDULER_STOP_REPOLL_SAME_IDS",
    "break MainLoop",
    "AGY_STATUS_ERROR"
)

foreach ($p in $patterns) {
    $m = Select-String -Path $controller -Pattern $p -SimpleMatch
    if ($m) {
        Write-Host "PATTERN [$p]: PRESENT (matches: $($m.Count))"
    } else {
        Write-Host "PATTERN [$p]: MISSING"
        exit 1
    }
}

$warn = Select-String -Path $controller -Pattern "AGY_STATUS_WARN"
if ($warn) {
    Write-Host "PATTERN [AGY_STATUS_WARN]: STILL PRESENT (UNSAFE)"
    exit 1
} else {
    Write-Host "PATTERN [AGY_STATUS_WARN]: ABSENT (SAFE)"
}
