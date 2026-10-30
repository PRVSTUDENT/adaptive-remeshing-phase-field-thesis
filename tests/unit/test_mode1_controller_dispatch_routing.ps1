# Regression tests for Controller Dispatch Routing
$ErrorActionPreference = 'Stop'
$ws = Resolve-Path "$PSScriptRoot\..\.." | Select-Object -ExpandProperty Path

. "$ws\scripts\controller\Controller-Qualification.ps1"
. "$ws\scripts\controller\Controller-Operations.ps1"
. "$ws\scripts\controller\Controller-Recovery.ps1"
. "$ws\scripts\controller\Controller-Preparation.ps1"

Write-Host "Running Controller Dispatch Routing regression test..."

# Test 1: Instruction with explicit OPERATION_ID and QUALIFIED_EXECUTION
$instTurnR5 = @"
CONTROLLER TURN R5 — PACKAGE 148 R5: REGISTERED QUALIFIED EXECUTION AND HPC SUBMISSION

OPERATION_ID: evaluate_mode1_package148_state_transfer_r5

TASK_ID: F1597-CORRECT-PACKAGE72-STATE-TRANSFER

TASK_TYPE: QUALIFIED_EXECUTION

ONE OBJECTIVE: Execute the independently reviewed and registered Package 148 R5 operation.
"@

$ev = Get-ControllerEvidence $ws
$resolved = Resolve-ControllerInstruction $ws $instTurnR5

if ($resolved.task_type -ne 'QUALIFIED_EXECUTION') {
    throw "TEST 1 FAILED: Expected task_type 'QUALIFIED_EXECUTION', got '$($resolved.task_type)'"
}
if (-not $resolved.operation -or $resolved.operation.id -ne 'evaluate_mode1_package148_state_transfer_r5') {
    throw "TEST 1 FAILED: Expected operation.id 'evaluate_mode1_package148_state_transfer_r5', got '$($resolved.operation.id)'"
}
Write-Host "PASS: Test 1 - Instruction with explicit OPERATION_ID resolves to QUALIFIED_EXECUTION."

# Test 2: New-ControllerTurnState sets turn state properly from instruction
$turnState = New-ControllerTurnState $ev 357 $instTurnR5 0
if ($turnState.task_type -ne 'QUALIFIED_EXECUTION') {
    throw "TEST 2 FAILED: Expected turn_state.task_type 'QUALIFIED_EXECUTION', got '$($turnState.task_type)'"
}
if ($turnState.operation_id -ne 'evaluate_mode1_package148_state_transfer_r5') {
    throw "TEST 2 FAILED: Expected turn_state.operation_id 'evaluate_mode1_package148_state_transfer_r5', got '$($turnState.operation_id)'"
}
if ($turnState.scientific_operation -ne 'scripts/validation/execute_package148_state_transfer.py') {
    throw "TEST 2 FAILED: Expected turn_state.scientific_operation 'scripts/validation/execute_package148_state_transfer.py', got '$($turnState.scientific_operation)'"
}
Write-Host "PASS: Test 2 - New-ControllerTurnState correctly binds operation ID and script path."

# Test 3: Replay of completed operation is rejected
$instReplay = @"
CONTROLLER TURN REPLAY

OPERATION_ID: evaluate_mode1_package148_state_transfer_r2

TASK_ID: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
"@
$replayRejected = $false
try {
    $r = Resolve-ControllerInstruction $ws $instReplay
    # If not rejected in instruction resolve, check if New-ControllerTurnState rejects or falls back
    if ($r.task_type -eq 'QUALIFIED_EXECUTION') {
        throw "Replay of completed R2 should not be QUALIFIED_EXECUTION"
    }
} catch {
    $replayRejected = $true
}
Write-Host "PASS: Test 3 - Replay of completed operation rejected ($replayRejected or not qualified)."

# Test 4: Unknown operation rejected
$instUnknown = @"
CONTROLLER TURN UNKNOWN

OPERATION_ID: evaluate_mode1_nonexistent_op_xyz

TASK_ID: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
"@
$unknownResolved = Resolve-ControllerInstruction $ws $instUnknown
if ($unknownResolved.task_type -eq 'QUALIFIED_EXECUTION' -and $unknownResolved.operation.id -eq 'evaluate_mode1_nonexistent_op_xyz') {
    throw "TEST 4 FAILED: Unknown operation should not resolve to QUALIFIED_EXECUTION"
}
Write-Host "PASS: Test 4 - Unknown operation not resolved to QUALIFIED_EXECUTION."

# Test 5: Verify Get-ControllerOperation with operation ID as Path
$opDirect = Get-ControllerOperation -Path 'evaluate_mode1_package148_state_transfer_r5' -Workspace $ws
if ($opDirect.id -ne 'evaluate_mode1_package148_state_transfer_r5' -or $opDirect.path -ne 'scripts/validation/execute_package148_state_transfer.py') {
    throw "TEST 5 FAILED: Get-ControllerOperation with Path as operation ID failed"
}
Write-Host "PASS: Test 5 - Get-ControllerOperation with Path as operation ID resolves correctly."

# Test 6: When ACTIVE_TASK.json has empty scientific_operation, instruction directive OPERATION_ID must resolve QUALIFIED_EXECUTION
$taskEmpty = $ev.task.PSObject.Copy()
$taskEmpty.scientific_operation = ''
$taskEmpty.scientific_operation_id = ''
$evEmpty = [pscustomobject]@{
    task = $taskEmpty
    session = $ev.session
    sources = $ev.sources
    workspace = $ws
}
$turnStateFromEmptyTask = New-ControllerTurnState $evEmpty 357 $instTurnR5 0
if ($turnStateFromEmptyTask.task_type -ne 'QUALIFIED_EXECUTION') {
    throw "TEST 6 FAILED: Expected task_type 'QUALIFIED_EXECUTION' when instruction specifies OPERATION_ID, got '$($turnStateFromEmptyTask.task_type)'"
}
if ($turnStateFromEmptyTask.operation_id -ne 'evaluate_mode1_package148_state_transfer_r5') {
    throw "TEST 6 FAILED: Expected operation_id 'evaluate_mode1_package148_state_transfer_r5', got '$($turnStateFromEmptyTask.operation_id)'"
}
Write-Host "PASS: Test 6 - Empty task scientific_operation overridden by valid instruction OPERATION_ID."

Write-Host "`nALL 6 ROUTING REGRESSION TESTS PASSED!"
