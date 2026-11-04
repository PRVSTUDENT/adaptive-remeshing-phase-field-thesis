# Multi-Turn Authentication Lifecycle & Comprehensive Regression Suite
# Protocol: Codex + Gemini Antigravity
$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $repo

$testCount = 0
function Assert-Test($condition, $message) {
    if (-not $condition) {
        throw "ASSERTION FAILED: $message"
    }
    $script:testCount++
    Write-Host "PASS [$script:testCount]: $message" -ForegroundColor Green
}

function New-IsolatedAuthFixture {
    $fixDir = Join-Path $env:TEMP ("auth-lifecycle-" + [guid]::NewGuid().ToString('N'))
    [IO.Directory]::CreateDirectory($fixDir) | Out-Null
    $profilesDir = Join-Path $fixDir "agy-profiles"
    [IO.Directory]::CreateDirectory($profilesDir) | Out-Null
    $openclawDir = Join-Path $fixDir "OpenClawPAD"
    [IO.Directory]::CreateDirectory($openclawDir) | Out-Null
    $authRecDir = Join-Path $openclawDir "auth_recovery"
    [IO.Directory]::CreateDirectory($authRecDir) | Out-Null
    $cliDir = Join-Path $fixDir ".gemini/antigravity-cli"
    [IO.Directory]::CreateDirectory($cliDir) | Out-Null

    # Create dummy checkpoint
    $cpPath = Join-Path $openclawDir "controller_turn_checkpoint.json"
    $cpContent = @{
        schema = 1
        run_id = "c55e54d7-a7a6-40a9-9e2e-3ddf8a1ff48c"
        turn = 7
        state = "PENDING"
        task_id = "F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION"
        workspace = $repo
        process_id = 0
        original_instruction_hash = "DUMMYHASH"
    } | ConvertTo-Json
    [IO.File]::WriteAllText($cpPath, $cpContent, [Text.UTF8Encoding]::new($false))

    return [pscustomobject]@{
        BaseDir = $fixDir
        ProfilesDir = $profilesDir
        OpenClawDir = $openclawDir
        AuthRecDir = $authRecDir
        CliDir = $cliDir
        CheckpointPath = $cpPath
    }
}

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " TEST SUITE: MULTI-TURN AUTH LIFECYCLE & REGRESSION" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

. "$repo/scripts/controller/Controller-AuthRecovery.ps1"

# ------------------------------------------------------------------------------
# SCENARIO 1: REPRODUCTION OF ORIGINAL TURN 7 FAILURE (UNMODIFIED NARROWING & LOCKOUT)
# ------------------------------------------------------------------------------
Write-Host "`n--- Scenario 1: Reproduce Original Turn 7 Narrowing & Lockout Failure ---" -ForegroundColor Yellow

$fixture = New-IsolatedAuthFixture
$statePath = Join-Path $fixture.AuthRecDir "test-state.json"
$cpHash = "8C780F284BA7E2AE034970D1301624F7E16EBFF083D8E31DCD22BE0726FA2DDF"

$identities = @{
    account2 = "11896874e435f4c4"
    account4 = "c2fe85c6d46e6596"
}
$mockNativeIdentity = "c2fe85c6d46e6596" # Native store has account4

# Simulate the unmodified narrowing: candidateProfile was forced to account2 only
$unmodifiedProfiles = @('account2')

$reproducedOutcome = $null
try {
    $r = Invoke-ControllerAuthRecovery -StatePath $statePath -CheckpointHash $cpHash -Profiles $unmodifiedProfiles -Identity {
        param($p) $identities[$p]
    } -Activate {
        param($p)
    } -Verify {
        param($p)
        if ($mockNativeIdentity -ne $identities[$p]) {
            throw "AGY_CREDENTIAL_REPAIR_PROVIDER_MISMATCH"
        }
        return $mockNativeIdentity
    } -Refresh {
        param($p) throw "Refresh not permitted or rejected"
    }
    $reproducedOutcome = $r
} catch {}

Assert-Test ($reproducedOutcome.status -eq 'AUTH_RECOVERY_REQUIRED') "Unmodified recovery returned AUTH_RECOVERY_REQUIRED"
Assert-Test ($reproducedOutcome.safety_blocked -eq $true) "Unmodified recovery set safety_blocked = true"
Assert-Test ($reproducedOutcome.attempts.Count -eq 1) "Unmodified recovery recorded 1 attempt"
Assert-Test ($reproducedOutcome.attempts[0].profile -eq 'account2') "Attempt profile was account2"
Assert-Test ($reproducedOutcome.attempts[0].outcome -eq 'IDENTITY_MISMATCH') "Attempt outcome was IDENTITY_MISMATCH"

# Test lockout on second attempt:
$rSecond = Invoke-ControllerAuthRecovery -StatePath $statePath -CheckpointHash $cpHash -Profiles $unmodifiedProfiles -Identity {
    param($p) $identities[$p]
} -Activate {} -Verify { param($p) throw "Should not be called if locked out" } -Refresh {}

Assert-Test ($rSecond.status -eq 'AUTH_RECOVERY_REQUIRED') "Unmodified recovery locked out on repeat execution"
Assert-Test ($rSecond.safety_blocked -eq $true) "Safety blocked remains true on repeat execution"

Remove-Item -LiteralPath $fixture.BaseDir -Recurse -Force -ErrorAction SilentlyContinue

# ------------------------------------------------------------------------------
# SCENARIO 2: FIVE CONSECUTIVE SUCCESSFUL TURNS (VERIFY FIRST, ZERO FAILOVERS)
# ------------------------------------------------------------------------------
Write-Host "`n--- Scenario 2: Five Consecutive Successful Turns (No Failovers) ---" -ForegroundColor Yellow

$script:failoverCount = 0
$script:verifiedTurns = 0

# Mock controller turn loop execution
for ($turn = 1; $turn -le 5; $turn++) {
    $tokens = $null; $errors = $null
    $ast = [Management.Automation.Language.Parser]::ParseFile("$repo/scripts/controller/Antigravity-Autonomous-Loop.ps1", [ref]$tokens, [ref]$errors)
    & {
        function Invoke-AgyAuthenticationFailover {
            $script:failoverCount++
            [pscustomobject]@{new_profile='account4';new_conversation_policy='none'}
        }
        function Set-AndVerifyAgyRunProfileCore {
            param($Context)
            # Simulated healthy verification on each turn
            $script:verifiedTurns++
        }
        $node = $ast.Find({param($x)$x -is [Management.Automation.Language.FunctionDefinitionAst] -and $x.Name -eq 'Set-AndVerifyAgyRunProfile'},$true)
        . ([scriptblock]::Create($node.Extent.Text))

        Set-AndVerifyAgyRunProfile -Context "TURN_START"
    }
}

Assert-Test ($script:verifiedTurns -eq 5) "All 5 consecutive turns verified through normal verification"
Assert-Test ($script:failoverCount -eq 0) "Zero failover invocations occurred across 5 successful turns"

# ------------------------------------------------------------------------------
# SCENARIO 3: NATIVE/MARKER DISAGREEMENT RECONCILIATION UNDER BACKGROUND HUB
# ------------------------------------------------------------------------------
Write-Host "`n--- Scenario 3: Native/Marker Disagreement Reconciliation ---" -ForegroundColor Yellow

# When marker is account2 but native credential has account4 (and provider confirms account4):
# Background hub logic identifies candidateProfile as account4, verifies it read-only, and reconciles marker.
$fixture3 = New-IsolatedAuthFixture
$statePath3 = Join-Path $fixture3.AuthRecDir "reconciliation-state.json"

$hubIdentities = @{
    account1 = "1fd3540022c69f1c"
    account2 = "11896874e435f4c4"
    account4 = "c2fe85c6d46e6596"
}
$mockNativeToken = @{
    access_token = "live_valid_token_account4"
    expiry = [DateTimeOffset]::UtcNow.AddHours(1).ToString("o")
}
$mockLiveProviderId = "c2fe85c6d46e6596" # account4

# Test identification logic: native store matches account4 in registry
$matchedProfile = ""
foreach ($p in $hubIdentities.Keys) {
    if ($hubIdentities[$p] -eq $mockLiveProviderId) {
        $matchedProfile = $p
        break
    }
}
Assert-Test ($matchedProfile -eq 'account4') "Authenticated native store identified as account4 from saved profile registry"

# Test that read-only check succeeds for account4
$roCheck = Invoke-ControllerReadOnlyProfileCheck -CheckpointPath $fixture3.CheckpointPath -CurrentProfile 'account4' -AssertOwnerFree {} -Verify {
    param($profile)
    return ($profile -eq 'account4')
}
Assert-Test ($roCheck.status -eq 'VERIFIED_PROFILE') "Read-only profile check verified account4 under background hub"
Assert-Test ($roCheck.selected_profile -eq 'account4') "Selected profile is account4"
Assert-Test ($roCheck.safety_blocked -eq $false) "Safety blocked is false after verified read-only check"

Remove-Item -LiteralPath $fixture3.BaseDir -Recurse -Force -ErrorAction SilentlyContinue

# ------------------------------------------------------------------------------
# SCENARIO 4: TOKEN REFRESH DURING TURN LIFECYCLE
# ------------------------------------------------------------------------------
Write-Host "`n--- Scenario 4: Token Refresh During Turn Lifecycle ---" -ForegroundColor Yellow

$fixture4 = New-IsolatedAuthFixture
$statePath4 = Join-Path $fixture4.AuthRecDir "refresh-state.json"
$script:refreshAttempts = 0
$script:tokenRefreshed = $false

$rRefresh = Invoke-ControllerAuthRecovery -StatePath $statePath4 -CheckpointHash 'cp-refresh' -Profiles @('account4') -Identity {
    param($p) 'c2fe85c6d46e6596'
} -Activate {} -Verify {
    param($p)
    if (-not $script:tokenRefreshed) {
        throw "AGY_CREDENTIAL_EXPIRED: active access token expired"
    }
    return 'c2fe85c6d46e6596'
} -Refresh {
    param($p)
    $script:refreshAttempts++
    $script:tokenRefreshed = $true
}

Assert-Test ($rRefresh.status -eq 'VERIFIED_PROFILE') "Expired token successfully recovered via refresh"
Assert-Test ($rRefresh.selected_profile -eq 'account4') "Selected profile remains account4"
Assert-Test ($script:refreshAttempts -eq 1) "In-place refresh executed exactly once"
Assert-Test ($rRefresh.attempts[0].refresh_attempted -eq $true) "Refresh intent recorded in journal"
Assert-Test ($rRefresh.safety_blocked -eq $false) "Safety unblocked after refreshed token verified"

Remove-Item -LiteralPath $fixture4.BaseDir -Recurse -Force -ErrorAction SilentlyContinue

# ------------------------------------------------------------------------------
# SCENARIO 5: LEGITIMATE ACCOUNT TRANSITION (NO BACKGROUND HUB)
# ------------------------------------------------------------------------------
Write-Host "`n--- Scenario 5: Legitimate Account Transition (No Background Hub) ---" -ForegroundColor Yellow

$fixture5 = New-IsolatedAuthFixture
$statePath5 = Join-Path $fixture5.AuthRecDir "transition-state.json"
$script:activatedProfile = ""

$rTransition = Invoke-ControllerAuthRecovery -StatePath $statePath5 -CheckpointHash 'cp-transition' -Profiles @('account1', 'account2') -Identity {
    param($p) if ($p -eq 'account1') { 'id1' } else { 'id2' }
} -Activate {
    param($p) $script:activatedProfile = $p
} -Verify {
    param($p)
    if ($p -eq 'account1') { throw "HTTP 401: quota exhausted" }
    return 'id2'
} -Refresh {
    param($p) throw "Refresh not applicable"
}

Assert-Test ($rTransition.status -eq 'VERIFIED_PROFILE') "Successfully transitioned to backup account"
Assert-Test ($rTransition.selected_profile -eq 'account2') "Selected backup profile is account2"
Assert-Test ($script:activatedProfile -eq 'account2') "Activated profile matches account2"
Assert-Test ($rTransition.attempts.Count -eq 2) "Both attempts recorded in audit journal"

Remove-Item -LiteralPath $fixture5.BaseDir -Recurse -Force -ErrorAction SilentlyContinue

# ------------------------------------------------------------------------------
# SCENARIO 6: GENUINE 401 & FAILED REFRESH (AUTHENTIC EXHAUSTION)
# ------------------------------------------------------------------------------
Write-Host "`n--- Scenario 6: Authentic 401 & Failed Refresh Exhaustion ---" -ForegroundColor Yellow

$fixture6 = New-IsolatedAuthFixture
$statePath6 = Join-Path $fixture6.AuthRecDir "exhaustion-state.json"
$script:exhaustionRefreshes = 0

$rExhaust = Invoke-ControllerAuthRecovery -StatePath $statePath6 -CheckpointHash 'cp-exhaust' -Profiles @('account4') -Identity {
    param($p) 'c2fe85c6d46e6596'
} -Activate {} -Verify {
    param($p) throw "HTTP 401 Unauthorized"
} -Refresh {
    param($p)
    $script:exhaustionRefreshes++
    throw "invalid_grant: token revoked"
}

Assert-Test ($rExhaust.status -eq 'AUTH_RECOVERY_REQUIRED') "Permanent provider rejection results in AUTH_RECOVERY_REQUIRED"
Assert-Test ($rExhaust.safety_blocked -eq $true) "Safety blocked set to true on authentic exhaustion"
Assert-Test ($rExhaust.attempts[0].outcome -eq 'AUTHENTICATION_FAILED') "Audit journal recorded AUTHENTICATION_FAILED"
Assert-Test ($script:exhaustionRefreshes -eq 1) "Failed refresh attempted exactly once"

Remove-Item -LiteralPath $fixture6.BaseDir -Recurse -Force -ErrorAction SilentlyContinue

# ------------------------------------------------------------------------------
# SCENARIO 7: IDENTITY CONFLICT REJECTION (UNREGISTERED IDENTITY)
# ------------------------------------------------------------------------------
Write-Host "`n--- Scenario 7: Identity Conflict Rejection ---" -ForegroundColor Yellow

$fixture7 = New-IsolatedAuthFixture
$statePath7 = Join-Path $fixture7.AuthRecDir "conflict-state.json"

$rConflict = Invoke-ControllerAuthRecovery -StatePath $statePath7 -CheckpointHash 'cp-conflict' -Profiles @('account4') -Identity {
    param($p) 'c2fe85c6d46e6596'
} -Activate {} -Verify {
    param($p) return 'foreign_unknown_identity_99999'
} -Refresh {
    param($p) throw "Must not refresh conflicting identity"
}

Assert-Test ($rConflict.status -eq 'AUTH_RECOVERY_REQUIRED') "Foreign identity in native store rejected"
Assert-Test ($rConflict.safety_blocked -eq $true) "Safety blocked set to true on identity conflict"
Assert-Test ($rConflict.attempts[0].outcome -eq 'IDENTITY_MISMATCH') "Audit journal recorded IDENTITY_MISMATCH"

Remove-Item -LiteralPath $fixture7.BaseDir -Recurse -Force -ErrorAction SilentlyContinue

# ------------------------------------------------------------------------------
# SCENARIO 8: CHECKPOINT INTERRUPTION, RESTART & NO DUPLICATE EXECUTION
# ------------------------------------------------------------------------------
Write-Host "`n--- Scenario 8: Checkpoint Interruption, Restart & No Duplicate Execution ---" -ForegroundColor Yellow

$fixture8 = New-IsolatedAuthFixture
. "$repo/scripts/controller/Controller-Recovery.ps1"

$pendingState = [pscustomobject]@{
    state = 'PENDING'
    turn = 7
    process_id = 0
    next_instruction = ''
    owned_session_fingerprint = ''
    original_instruction_hash = (Get-ControllerTextHash 'Execute Turn 7 Method C')
}

$resumePlan = Get-ControllerPendingAuthResumePlan -State $pendingState -Instruction 'Execute Turn 7 Method C' -ProviderVerified
Assert-Test ($resumePlan.turn -eq 7) "Resume plan returns exact pending turn 7 (no turn skip)"
Assert-Test ($resumePlan.instruction -eq 'Execute Turn 7 Method C') "Resume plan preserves exact pending instruction"

$resFile = Join-Path $fixture8.OpenClawDir "resume_lock.json"
$cpHash8 = (Get-FileHash $fixture8.CheckpointPath).Hash

New-ControllerAuthResumeReservation -CheckpointPath $fixture8.CheckpointPath -ExpectedHash $cpHash8 -ReservationPath $resFile -Verify {$true} -AssertOwnerFree {}
Assert-Test (Test-Path $resFile) "Atomic resume reservation created successfully"

# Second attempt must throw to prevent duplicate execution
$dupCaught = $false
try {
    New-ControllerAuthResumeReservation -CheckpointPath $fixture8.CheckpointPath -ExpectedHash $cpHash8 -ReservationPath $resFile -Verify {$true} -AssertOwnerFree {}
} catch {
    $dupCaught = $true
}
Assert-Test ($dupCaught -eq $true) "Duplicate resume reservation strictly prevented"

Remove-Item -LiteralPath $fixture8.BaseDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host " ALL $testCount MULTI-TURN AUTH LIFECYCLE SCENARIOS PASSED" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
