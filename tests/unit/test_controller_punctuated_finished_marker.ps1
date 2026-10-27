# Unit regression test: punctuated Finished marker handling and recovery invariant validation
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')

$root = Join-Path ([IO.Path]::GetTempPath()) ('punctuated-marker-test-' + [guid]::NewGuid().ToString('N'))
foreach ($folder in @('project_coordination', 'project_coordination/sessions', 'project_coordination/controller', 'results/validation')) {
    [void](New-Item -ItemType Directory -Path (Join-Path $root $folder) -Force)
}

function Put([string]$Rel, [string]$Text) {
    [IO.File]::WriteAllText((Join-Path $root $Rel), $Text, [Text.UTF8Encoding]::new($false))
}
function Check([bool]$Okay, [string]$Message) {
    if (-not $Okay) { throw "FAIL: $Message" }
    Write-Host "PASS: $Message"
}

$run = [guid]::NewGuid().ToString()
$reportRel = "project_coordination/sessions/2026_test_$run.md"
$bootRel = "project_coordination/controller/turn-$run.json"
$prepRel = "results/validation/preparation-$run.json"

Put 'project_coordination/ACTIVE_TASK.json' '{"task_id":"F1597-CORRECT-PACKAGE72-STATE-TRANSFER","status":"PREPARATION_COMPLETE"}'
Put 'project_coordination/CURRENT_STATE.md' 'Punctuated marker test fixture.'
Put 'project_coordination/TASK_LEDGER.csv' "task_id,status`nF1597-CORRECT-PACKAGE72-STATE-TRANSFER,preparation_complete"
Put 'project_coordination/HPC_JOB_LEDGER.csv' "pbs_id,status`n1417751.mmaster02,SUBMITTED"
Put 'project_coordination/MODE1_EXECUTION_LEDGER.json' '{"jobs":["1417751.mmaster02"]}'
Put 'project_coordination/ACTIVE_SESSION.json' (@{active = $false; task_id = 'F1597-CORRECT-PACKAGE72-STATE-TRANSFER'; agent = 'gemini-antigravity'; controller_run_id = $run; session_report = $reportRel } | ConvertTo-Json)
Put $reportRel "Scientific report for $run`nFinished`n"

$h = (Get-FileHash (Join-Path $root 'project_coordination/HPC_JOB_LEDGER.csv')).Hash
$prep = @{schema = 1; status = 'PREPARATION_COMPLETE'; finding = 'Verified test deliverable for punctuated marker check.'; verification_passed = $true; evidence_sources = @{ 'project_coordination/HPC_JOB_LEDGER.csv' = $h } }
Put $prepRel ($prep | ConvertTo-Json -Depth 7)
$pHash = (Get-FileHash (Join-Path $root $prepRel)).Hash
$record = @{controller_run_id = $run; task_id = 'F1597-CORRECT-PACKAGE72-STATE-TRANSFER'; bootstrap_status = 'COMPLETE'; stage = 'COMPLETE'; session_report = $reportRel; scientific_checkpoint = @{kind = 'PREPARATION_CHECKPOINT'; operation = 'research_preparation'; exit_code = 0; artifact = $prepRel; sha256 = $pHash } }
Put $bootRel ($record | ConvertTo-Json -Depth 8)

$path = Join-Path $root 'controller_checkpoint.json'

function New-State {
    $e = Get-ControllerEvidence $root
    $s = New-ControllerTurnState $e 215 'test turn'
    $s.run_id = $run
    $s.bootstrap_record_path = Join-Path $root $bootRel
    return $s
}

# 1. Punctuated Finished marker 'Finished.' is accepted
$s = New-State
$res1 = Complete-ControllerTurn $root $path $s "Research narrative completed cleanly.`nFinished.`n"
Check ($res1 -eq 'COMPLETED') 'Finished. with period is accepted as normal completion'

# 2. Finished without punctuation is accepted
$s = New-State
$res2 = Complete-ControllerTurn $root $path $s "Research narrative completed cleanly.`nFinished`n"
Check ($res2 -eq 'COMPLETED') 'Standard Finished is accepted as normal completion'

# 3. Finished with multiple trailing whitespace/newlines is accepted
$s = New-State
$res3 = Complete-ControllerTurn $root $path $s "Research narrative completed cleanly.`nFinished.`r`n"
Check ($res3 -eq 'COMPLETED') 'Finished. with carriage return is accepted'

# 4. Incomplete response without marker and without receipt is BLOCKED
Put $reportRel "Incomplete report without trailing Finished"
$s = New-State
$res4 = Complete-ControllerTurn $root $path $s "Response that stopped mid-sentence without marker"
Check ($res4 -eq 'BLOCKED') 'Incomplete response without terminal marker fails closed'

# 5. Explicit BLOCKED response fails closed even if it ends with Finished.
$s = New-State
$res5 = Complete-ControllerTurn $root $path $s "BLOCKED: technical blocker encountered.`nFinished."
Check ($res5 -eq 'BLOCKED') 'Explicit BLOCKED fails closed even with Finished.'

# 6. Active session fails closed even with Finished.
$claimTime = [DateTimeOffset]::UtcNow.AddSeconds(1).ToString('o')
Put 'project_coordination/ACTIVE_SESSION.json' (@{active = $true; task_id = 'F1597-CORRECT-PACKAGE72-STATE-TRANSFER'; agent = 'gemini-antigravity'; controller_run_id = $run; session_report = $reportRel; claimed_at = $claimTime; starting_commit = '' } | ConvertTo-Json)
$s = New-State
$s.initial_session_active = $false
$s.initial_session_hash = 'previous_inactive_hash'
$res6 = Complete-ControllerTurn $root $path $s "Research narrative completed cleanly.`nFinished."
Check ($res6 -eq 'BLOCKED') 'Active session fails closed even with Finished.'
Put 'project_coordination/ACTIVE_SESSION.json' (@{active = $false; task_id = 'F1597-CORRECT-PACKAGE72-STATE-TRANSFER'; agent = 'gemini-antigravity'; controller_run_id = $run; session_report = $reportRel } | ConvertTo-Json)

# 7. Checkpoint reconciliation: Assert-ControllerDispatchCheckpoint passes for valid reconciliation
$archPath = Join-Path $root 'archived_checkpoint.json'
$blockedState = New-State
$blockedState.state = 'BLOCKED'
$blockedState.block_reason = 'Response incomplete, explicitly blocked, or repository session not released'
Write-ControllerCheckpoint $archPath $blockedState
$archHash = (Get-FileHash -LiteralPath $archPath -Algorithm SHA256).Hash

$reconciledState = New-State
$reconciledState.state = 'COMPLETED'
$reconciledState.turn = 215
$recObj = [pscustomobject]@{
    status = 'INTERRUPTED_TURN_PROGRESS_WATCHDOG_RECONCILED'
    original_checkpoint = $archPath
    original_sha256 = $archHash
    run_id = $run
    task_id = 'F1597-CORRECT-PACKAGE72-STATE-TRANSFER'
    session_report = $reportRel
    session_report_sha256 = (Get-FileHash -LiteralPath (Join-Path $root $reportRel)).Hash
    bootstrap_record = $bootRel
    bootstrap_record_sha256 = (Get-FileHash -LiteralPath (Join-Path $root $bootRel)).Hash
    hpc_ledger_sha256 = $h
}
$reconciledState | Add-Member -NotePropertyName reconciliation -NotePropertyValue $recObj -Force
$reconciledPath = Join-Path $root 'reconciled_checkpoint.json'
Write-ControllerCheckpoint $reconciledPath $reconciledState

$readReconciled = Read-ControllerCheckpoint $reconciledPath
$passed = $true
try {
    Assert-ControllerDispatchCheckpoint $root $readReconciled
} catch {
    $passed = $false
}
Check $passed 'Valid evidence-only recovery clears historical dispatch blocker'

# 8. Checkpoint reconciliation fails closed if original checkpoint hash does not match
$tamperedReconciled = New-State
$tamperedReconciled.state = 'COMPLETED'
$tRecObj = [pscustomobject]@{
    status = 'INTERRUPTED_TURN_PROGRESS_WATCHDOG_RECONCILED'
    original_checkpoint = $archPath
    original_sha256 = 'TAMPERED_SHA256'
    run_id = $run
}
$tamperedReconciled | Add-Member -NotePropertyName reconciliation -NotePropertyValue $tRecObj -Force
$tamperedFailed = $false
try {
    Assert-ControllerDispatchCheckpoint $root $tamperedReconciled
} catch {
    $tamperedFailed = $_.Exception.Message -match '^BLOCKED:'
}
Check $tamperedFailed 'Reconciliation with tampered original hash fails closed'

Write-Host "ALL PUNCTUATED FINISHED MARKER AND RECOVERY INVARIANT TESTS PASSED."
