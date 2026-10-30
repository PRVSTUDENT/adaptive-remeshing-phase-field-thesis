# Non-submitting dispatcher test proving the next turn resolves to QUALIFIED_EXECUTION
$ErrorActionPreference = 'Stop'
$ws = Resolve-Path "$PSScriptRoot\..\.." | Select-Object -ExpandProperty Path

. "$ws\scripts\controller\Controller-Qualification.ps1"
. "$ws\scripts\controller\Controller-Operations.ps1"
. "$ws\scripts\controller\Controller-Recovery.ps1"
. "$ws\scripts\controller\Controller-Preparation.ps1"

$nextInstruction = @"
CONTROLLER TURN 344 — PACKAGE 148 R3: QUALIFIED EXECUTION AND HPC SUBMISSION

OPERATION_ID: evaluate_mode1_package148_state_transfer_r3

TASK_ID: F1597-CORRECT-PACKAGE72-STATE-TRANSFER

TASK_TYPE: QUALIFIED_EXECUTION

ONE OBJECTIVE: Execute the independently reviewed and registered Package 148 R3 operation. Stage candidate, perform authentic Abaqus 2023 datachecks and submit exactly once if all gates pass.
"@

Write-Host "=== DISPATCHER TEST: Verifying Next Turn Handoff ==="

# 1. Preparation plan check
$plan = Get-ControllerPreparationPlan $ws $nextInstruction
Write-Host "Preparation Plan Status: $($plan.status)"
Write-Host "Preparation Plan Dispatch Ready: $($plan.dispatch_ready)"
Write-Host "Preparation Plan Task Type: $($plan.task_type)"
Write-Host "Preparation Plan Operation ID: $($plan.operation_id)"
Write-Host "Preparation Plan Path: $($plan.path)"

if ($plan.task_type -ne 'QUALIFIED_EXECUTION') {
    throw "DISPATCHER CHECK FAILED: Expected plan.task_type 'QUALIFIED_EXECUTION', got '$($plan.task_type)'"
}
if (-not $plan.dispatch_ready) {
    throw "DISPATCHER CHECK FAILED: Expected plan.dispatch_ready `$true"
}
if ($plan.operation_id -ne 'evaluate_mode1_package148_state_transfer_r3') {
    throw "DISPATCHER CHECK FAILED: Expected plan.operation_id 'evaluate_mode1_package148_state_transfer_r3', got '$($plan.operation_id)'"
}

# 2. Instruction resolution check
$resolved = Resolve-ControllerInstruction $ws $nextInstruction
Write-Host "`nResolved Task Type: $($resolved.task_type)"
Write-Host "Resolved Operation ID: $($resolved.operation.id)"
Write-Host "Resolved Canonical Path: $($resolved.operation.path)"

if ($resolved.task_type -ne 'QUALIFIED_EXECUTION') {
    throw "DISPATCHER CHECK FAILED: Expected resolved.task_type 'QUALIFIED_EXECUTION', got '$($resolved.task_type)'"
}
if ($resolved.operation.id -ne 'evaluate_mode1_package148_state_transfer_r3') {
    throw "DISPATCHER CHECK FAILED: Expected resolved.operation.id 'evaluate_mode1_package148_state_transfer_r3', got '$($resolved.operation.id)'"
}

# 3. Turn state generation check
$turnState = New-ControllerTurnState $resolved.evidence 344 $nextInstruction 0
Write-Host "`nTurn State Task Type: $($turnState.task_type)"
Write-Host "Turn State Operation ID: $($turnState.operation_id)"
Write-Host "Turn State Scientific Operation: $($turnState.scientific_operation)"

if ($turnState.task_type -ne 'QUALIFIED_EXECUTION') {
    throw "DISPATCHER CHECK FAILED: Expected turnState.task_type 'QUALIFIED_EXECUTION', got '$($turnState.task_type)'"
}
if ($turnState.operation_id -ne 'evaluate_mode1_package148_state_transfer_r3') {
    throw "DISPATCHER CHECK FAILED: Expected turnState.operation_id 'evaluate_mode1_package148_state_transfer_r3', got '$($turnState.operation_id)'"
}
if ($turnState.scientific_operation -ne 'scripts/validation/execute_package148_state_transfer.py') {
    throw "DISPATCHER CHECK FAILED: Expected turnState.scientific_operation 'scripts/validation/execute_package148_state_transfer.py', got '$($turnState.scientific_operation)'"
}

Write-Host "`nDISPATCHER HANDOFF VERIFICATION PASSED: Next session successfully resolves to QUALIFIED_EXECUTION with operation evaluate_mode1_package148_state_transfer_r3!"
