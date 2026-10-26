# Test suite for Bridge External Authentication Blocker Guard
# Verifies idempotent suppression of ChatGPT bridge calls during active institutional SSO blockers.

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..\..")
$bridgeScript = Join-Path $repoRoot ".agents\scripts\Invoke-ChatGPTBridge.ps1"

if (-not (Test-Path -LiteralPath $bridgeScript)) {
    throw "Bridge script not found at: $bridgeScript"
}

. $bridgeScript

$testBridgeDir = Join-Path $env:TEMP ("test_bridge_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $testBridgeDir -Force | Out-Null

$passCount = 0
$failCount = 0

function Assert-Condition($condition, $message) {
    if ($condition) {
        Write-Host "  [PASS] $message" -ForegroundColor Green
        $script:passCount++
    } else {
        Write-Host "  [FAIL] $message" -ForegroundColor Red
        $script:failCount++
    }
}

try {
    Write-Host "`n=== Test 1: Unchanged SSO Blocker Returns BLOCKED_EXTERNAL_AUTHENTICATION Without Files or Locks ===" -ForegroundColor Cyan
    $blockedPrompt = @"
[BRIDGE_HANDOFF_ID=HND-test1]
Task F1597 evaluation complete.
Status: R18_OFFLINE_QUALIFIED__INTERACTIVE_SSO_REQUIRED
Package 108 Revision 18 frozen. Waiting for user workstation browser SSO.
"@
    $res1 = Invoke-ChatGPTBridge -PromptText $blockedPrompt -BridgeDir $testBridgeDir
    Assert-Condition ($res1.StartsWith("BLOCKED_EXTERNAL_AUTHENTICATION")) "Returns BLOCKED_EXTERNAL_AUTHENTICATION string"
    Assert-Condition ($res1.Contains("Status: R18_OFFLINE_QUALIFIED__INTERACTIVE_SSO_REQUIRED")) "Contains R18_OFFLINE_QUALIFIED__INTERACTIVE_SSO_REQUIRED status"
    Assert-Condition (-not (Test-Path (Join-Path $testBridgeDir "bridge.lock"))) "Lockfile was NOT created"
    Assert-Condition (-not (Test-Path (Join-Path $testBridgeDir "bridge_request.ready"))) "Request file was NOT created"
    Assert-Condition (-not (Test-Path (Join-Path $testBridgeDir "bridge_request.tmp"))) "Request tmp file was NOT created"

    Write-Host "`n=== Test 2: -Resume or RESUME_AFTER_SSO=1 Bypasses Blocker Guard ===" -ForegroundColor Cyan
    $res2a = Invoke-ChatGPTBridge -PromptText $blockedPrompt -Resume -DryRun -BridgeDir $testBridgeDir
    Assert-Condition (-not $res2a.StartsWith("BLOCKED_EXTERNAL_AUTHENTICATION")) "-Resume flag bypasses blocker"
    Assert-Condition ($res2a.Contains("BRIDGE CONTROLLER RULES")) "-Resume assembled bridge prompt with rules"

    $env:RESUME_AFTER_SSO = "1"
    try {
        $res2b = Invoke-ChatGPTBridge -PromptText $blockedPrompt -DryRun -BridgeDir $testBridgeDir
        Assert-Condition (-not $res2b.StartsWith("BLOCKED_EXTERNAL_AUTHENTICATION")) "RESUME_AFTER_SSO=1 environment variable bypasses blocker"
        Assert-Condition ($res2b.Contains("BRIDGE CONTROLLER RULES")) "RESUME_AFTER_SSO=1 assembled bridge prompt with rules"
    } finally {
        Remove-Item Env:RESUME_AFTER_SSO -ErrorAction SilentlyContinue
    }

    Write-Host "`n=== Test 3: Unrelated Independent Task Is Not Blocked ===" -ForegroundColor Cyan
    $independentPrompt = @"
[BRIDGE_HANDOFF_ID=HND-test3]
Independent Task F9999 analytical evaluation.
Computing linear-elastic benchmark comparison.
"@
    $res3 = Invoke-ChatGPTBridge -PromptText $independentPrompt -TaskId "F9999-INDEPENDENT" -DryRun -BridgeDir $testBridgeDir
    Assert-Condition (-not $res3.StartsWith("BLOCKED_EXTERNAL_AUTHENTICATION")) "Unrelated task is not blocked"
    Assert-Condition ($res3.Contains("Independent Task F9999")) "Assembled prompt contains independent task content"

    Write-Host "`n=== Test 4: Verify -DryRun Functions Properly ===" -ForegroundColor Cyan
    $dryRunPrompt = @"
Standard Mode-I benchmark calculation.
No SSO dependencies involved.
"@
    $res4 = Invoke-ChatGPTBridge -PromptText $dryRunPrompt -DryRun -BridgeDir $testBridgeDir
    Assert-Condition (-not $res4.StartsWith("BLOCKED_EXTERNAL_AUTHENTICATION")) "-DryRun returns assembled prompt"
    Assert-Condition ($res4.Contains("Standard Mode-I benchmark calculation")) "-DryRun preserved prompt text"
    Assert-Condition (-not (Test-Path (Join-Path $testBridgeDir "bridge.lock"))) "Lock was not acquired in DryRun"
    Assert-Condition (-not (Test-Path (Join-Path $testBridgeDir "bridge_request.ready"))) "Request ready file was not created in DryRun"

} finally {
    Remove-Item -LiteralPath $testBridgeDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "`n=========================================="
Write-Host "Test Results: $passCount Passed, $failCount Failed"
if ($failCount -gt 0) {
    exit 1
} else {
    exit 0
}
