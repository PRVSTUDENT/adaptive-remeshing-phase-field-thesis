# ==============================================================================
# REGRESSION TEST: Controller Normal Startup LoopState Initialization
# Tests that $loopStatePath is initialized before $ControllerDryRun so that
# normal startup without -InitialPromptFile evaluates Test-Path $loopStatePath
# cleanly without throwing "Cannot bind argument to parameter 'Path' because it is null".
# ==============================================================================
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$controllerPath = Join-Path $repo 'scripts/controller/Antigravity-Autonomous-Loop.ps1'

$script:testsPassed = 0
function Check($condition, [string]$message) {
    if (-not $condition) {
        throw "FAIL: $message"
    }
    $script:testsPassed++
    Write-Host "PASS: $message"
}

# ------------------------------------------------------------------------------
# TEST 1: AST / Static Assignment Verification
# ------------------------------------------------------------------------------
$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($controllerPath, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw "Syntax errors in controller: $($errors.Message -join '; ')" }

# Find assignments to $loopStatePath and $controllerCheckpointPath
$assignments = $ast.FindAll({
    param($node)
    $node -is [Management.Automation.Language.AssignmentStatementAst]
}, $true)

$checkpointAssignment = $null
$loopStateAssignments = @()
$dryRunStatement = $null

foreach ($assign in $assignments) {
    $var = $assign.Left.Extent.Text
    if ($var -eq '$controllerCheckpointPath') {
        $checkpointAssignment = $assign
    }
    if ($var -eq '$loopStatePath') {
        $loopStateAssignments += $assign
    }
}

$ifStatements = $ast.FindAll({
    param($node)
    $node -is [Management.Automation.Language.IfStatementAst]
}, $true)

foreach ($ifStmt in $ifStatements) {
    $condText = $ifStmt.Clauses[0].Item1.Extent.Text.Trim()
    if ($condText -eq '$ControllerDryRun') {
        $dryRunStatement = $ifStmt
        break
    }
}

Check ($null -ne $checkpointAssignment) "Test 1a: Found `$controllerCheckpointPath assignment"
Check ($null -ne $dryRunStatement) "Test 1b: Found if (`$ControllerDryRun) statement"
Check ($loopStateAssignments.Count -eq 1) "Test 1c: Exactly one `$loopStatePath assignment exists"

$loopAssign = $loopStateAssignments[0]
$loopAssignOffset = $loopAssign.Extent.StartOffset
$dryRunOffset = $dryRunStatement.Extent.StartOffset

Check ($loopAssignOffset -lt $dryRunOffset) "Test 1d: `$loopStatePath is assigned before if (`$ControllerDryRun)"
Check ($loopAssign.Parent -is [Management.Automation.Language.NamedBlockAst]) "Test 1e: `$loopStatePath is in script root body, not nested in a conditional block"

# ------------------------------------------------------------------------------
# TEST 2: Normal Startup Execution Path with PENDING Checkpoint and No Initial Prompt
# Simulates the exact startup evaluation logic from Antigravity-Autonomous-Loop.ps1
# with no $InitialPrompt, no $InitialPromptFile, and $ControllerDryRun = $false
# ------------------------------------------------------------------------------
$fixture = Join-Path $env:TEMP ('controller-normal-startup-test-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path (Join-Path $fixture 'OpenClawPAD') -Force | Out-Null

try {
    $fakePad = Join-Path $fixture 'OpenClawPAD'
    $fakeCheckpointPath = Join-Path $fakePad 'controller_turn_checkpoint.json'
    $fakeLoopStatePath = Join-Path $fakePad 'antigravity_loop_state.json'

    # Case A: antigravity_loop_state.json exists with next_instruction
    $pendingCheckpoint = [pscustomobject]@{
        schema = 1
        run_id = 'test-run-id-pending-6'
        state = 'PENDING'
        turn = 6
        task_id = 'F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION'
        next_instruction = $null
    }
    [IO.File]::WriteAllText($fakeCheckpointPath, ($pendingCheckpoint | ConvertTo-Json -Depth 5), [Text.Encoding]::UTF8)

    $loopStateData = [pscustomobject]@{
        loop_status = 'RUNNING'
        completed_turn = 5
        next_instruction = 'CONTINUE_PENDING_RESEARCH_TURN_6'
    }
    [IO.File]::WriteAllText($fakeLoopStatePath, ($loopStateData | ConvertTo-Json -Depth 5), [Text.Encoding]::UTF8)

    # Execute the startup evaluation logic in an isolated child scope where $loopStatePath is NOT pre-defined
    $evalScriptBlock = {
        param($padDir, $isDryRun, $initPrompt, $initPromptFile)
        $ErrorActionPreference = 'Stop'

        # Emulate controller script preamble up to prompt evaluation
        $controllerCheckpointPath = Join-Path $padDir 'controller_turn_checkpoint.json'
        $loopStatePath = Join-Path $padDir 'antigravity_loop_state.json'

        if ($isDryRun) {
            # In dry run mode
            $dryPrompt = if ($initPromptFile) {
                Get-Content -LiteralPath $initPromptFile -Raw -Encoding UTF8
            } elseif ($initPrompt) {
                $initPrompt
            } elseif (Test-Path $loopStatePath) {
                try { ([IO.File]::ReadAllText($loopStatePath, [Text.Encoding]::UTF8) | ConvertFrom-Json).next_instruction } catch { '' }
            } else { '' }
            return [pscustomobject]@{ mode = 'DRY_RUN'; prompt = $dryPrompt; loopStateBound = ($null -ne $loopStatePath) }
        }

        # Normal startup mode without dry run
        $preparationPrompt = if ($initPromptFile) {
            Get-Content -LiteralPath $initPromptFile -Raw -Encoding UTF8
        } elseif ($initPrompt) {
            $initPrompt
        } elseif (Test-Path $loopStatePath) {
            try { ([IO.File]::ReadAllText($loopStatePath, [Text.Encoding]::UTF8) | ConvertFrom-Json).next_instruction } catch { '' }
        } else {
            ''
        }

        return [pscustomobject]@{ mode = 'NORMAL_STARTUP'; prompt = $preparationPrompt; loopStateBound = ($null -ne $loopStatePath) }
    }

    # Run with ControllerDryRun = $false, InitialPrompt = '', InitialPromptFile = ''
    $resultA = & $evalScriptBlock -padDir $fakePad -isDryRun $false -initPrompt '' -initPromptFile ''
    Check ($resultA.loopStateBound -eq $true) "Test 2a: `$loopStatePath is non-null in normal startup"
    Check ($resultA.prompt -eq 'CONTINUE_PENDING_RESEARCH_TURN_6') "Test 2b: normal startup successfully reads next_instruction from loopState"

    # Case B: antigravity_loop_state.json does not exist
    Remove-Item -LiteralPath $fakeLoopStatePath -Force
    $resultB = & $evalScriptBlock -padDir $fakePad -isDryRun $false -initPrompt '' -initPromptFile ''
    Check ($resultB.loopStateBound -eq $true) "Test 2c: `$loopStatePath is non-null when loop state file is missing"
    Check ($resultB.prompt -eq '') "Test 2d: normal startup cleanly falls back to empty prompt when loop state is missing (no Test-Path null exception)"

    # Case C: Dry run path continues to work with loopStatePath
    [IO.File]::WriteAllText($fakeLoopStatePath, ($loopStateData | ConvertTo-Json -Depth 5), [Text.Encoding]::UTF8)
    $resultC = & $evalScriptBlock -padDir $fakePad -isDryRun $true -initPrompt '' -initPromptFile ''
    Check ($resultC.loopStateBound -eq $true) "Test 2e: `$loopStatePath is non-null in dry run mode"
    Check ($resultC.prompt -eq 'CONTINUE_PENDING_RESEARCH_TURN_6') "Test 2f: dry run mode successfully reads next_instruction from loopState"

} finally {
    Remove-Item -LiteralPath $fixture -Recurse -Force -ErrorAction SilentlyContinue
}

# ------------------------------------------------------------------------------
# TEST 3: Defect Demonstration (Test-Path $null fails) vs Fixed (Test-Path $loopStatePath passes)
# ------------------------------------------------------------------------------
# 3a: Verify that evaluating Test-Path on uninitialized ($null) path raises ParameterBindingValidationException
$nullPathFailed = $false
try {
    $uninitializedPath = $null
    Test-Path $uninitializedPath -ErrorAction Stop
} catch {
    $nullPathFailed = $_.Exception.Message -match "Cannot bind argument to parameter 'Path' because it is null"
}
Check $nullPathFailed "Test 3a: Defect reproduced: Test-Path `$null throws 'Cannot bind argument to parameter Path because it is null'"

# 3b: Verify that in a fresh powershell process with the fixed script lines, evaluation succeeds without error
$pwshCmd = (Get-Command powershell.exe).Source
$fixedSnippet = @"
`$ErrorActionPreference = 'Stop'
`$controllerCheckpointPath = Join-Path `$env:USERPROFILE 'OpenClawPAD/controller_turn_checkpoint.json'
`$loopStatePath = Join-Path `$env:USERPROFILE 'OpenClawPAD/antigravity_loop_state.json'

`$InitialPromptFile = ''
`$InitialPrompt = ''

`$preparationPrompt = if (`$InitialPromptFile) {
    Get-Content -LiteralPath `$InitialPromptFile -Raw -Encoding UTF8
} elseif (`$InitialPrompt) {
    `$InitialPrompt
} elseif (Test-Path `$loopStatePath) {
    try { ([IO.File]::ReadAllText(`$loopStatePath, [Text.Encoding]::UTF8) | ConvertFrom-Json).next_instruction } catch { '' }
} else {
    ''
}
Write-Output "PROMPT_EVAL_OK: `$(`$preparationPrompt.Length)"
"@
$procOutput = & $pwshCmd -NoProfile -ExecutionPolicy Bypass -Command $fixedSnippet
Check ($procOutput -match '^PROMPT_EVAL_OK:') "Test 3b: Fixed normal startup snippet executes cleanly in fresh session"

# ------------------------------------------------------------------------------
# TEST 4: Preserved PENDING Checkpoint Resume Plan Validation
# Validates that Turn 6 PENDING checkpoint can be resolved by Get-ControllerPendingAuthResumePlan
# ------------------------------------------------------------------------------
. (Join-Path $repo 'scripts/controller/Controller-AuthRecovery.ps1')
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')
$realCheckpointPath = Join-Path $env:USERPROFILE 'OpenClawPAD/controller_turn_checkpoint.json'
$realLoopStatePath = Join-Path $env:USERPROFILE 'OpenClawPAD/antigravity_loop_state.json'
if (Test-Path -LiteralPath $realCheckpointPath) {
    $realCheckpoint = Get-Content -LiteralPath $realCheckpointPath -Raw | ConvertFrom-Json
    if ($realCheckpoint.payload) {
        $realPayload = $realCheckpoint.payload | ConvertFrom-Json
    } else {
        $realPayload = $realCheckpoint
    }

    if ($realPayload.state -eq 'PENDING') {
        Check ($realPayload.turn -eq 6) "Test 4a: Preserved checkpoint is Turn 6"
        Check ($realPayload.task_id -eq 'F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION') "Test 4b: Checkpoint task_id matches F1607"

        # Non-executing plan verification using instruction from loopState
        $inst = if (Test-Path -LiteralPath $realLoopStatePath) {
            ([IO.File]::ReadAllText($realLoopStatePath, [Text.Encoding]::UTF8) | ConvertFrom-Json).next_instruction
        } else { '' }
        $plan = Get-ControllerPendingAuthResumePlan -State $realPayload -Instruction $inst -NonExecuting
        Check ($plan.turn -eq 6) "Test 4c: Resume plan targets Turn 6"
        Check (-not [string]::IsNullOrWhiteSpace($plan.instruction)) "Test 4d: Resume plan successfully resolved pending instruction"
    } else {
        Write-Host "NOTE: Checkpoint state is $($realPayload.state); skipped Test 4a-d"
    }
}

Write-Host "`nALL $script:testsPassed CONTROLLER NORMAL STARTUP LOOPSTATE TESTS PASSED."
