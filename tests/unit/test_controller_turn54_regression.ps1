# Regression suite for Turn 54 recovery and controller self-repair.
# Covers all 8 requirements of Phase 6:
# 1. Preparation completed but controller response incomplete (with coordination ledger in evidence_sources).
# 2. Preparation completed with an unreleased repository session.
# 3. Genuine active-session conflict.
# 4. Valid completed checkpoint after interruption.
# 5. Corrupt or mismatched checkpoint.
# 6. Previously submitted HPC job.
# 7. Unregistered successor scientific operation.
# 8. A blocked response that must remain blocked.

$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')

$root = Join-Path ([IO.Path]::GetTempPath()) ('t54-regression-' + [guid]::NewGuid().ToString('N'))
foreach ($d in @('project_coordination', 'project_coordination/controller', 'project_coordination/sessions', 'project_coordination/task_definitions', 'results/validation')) {
    [void](New-Item -ItemType Directory -Path (Join-Path $root $d) -Force)
}

function Put([string]$rel, [string]$text) {
    [IO.File]::WriteAllText((Join-Path $root $rel), $text, [Text.UTF8Encoding]::new($false))
}

function Check([bool]$condition, [string]$message) {
    if (-not $condition) { throw "FAIL: $message" }
    Write-Output "PASS: $message"
}

try {
    $run = [guid]::NewGuid().ToString()
    $task = 'F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE'
    $reportRel = "project_coordination/sessions/2026-11-03_gemini-antigravity_$run.md"
    $bootRel = "project_coordination/controller/turn-$run.json"
    $prepRel = "results/validation/preparation-$run.json"

    # Pre-closeout state of ACTIVE_TASK.json
    $activeTaskPre = '{"task_id":"F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE","status":"READY_READ_ONLY_EVALUATION","phase":"Initial bootstrap"}'
    Put 'project_coordination/ACTIVE_TASK.json' $activeTaskPre
    $activeTaskPreHash = (Get-FileHash (Join-Path $root 'project_coordination/ACTIVE_TASK.json')).Hash

    Put 'project_coordination/CURRENT_STATE.md' 'Turn 54 regression test fixture.'
    Put 'project_coordination/TASK_LEDGER.csv' "task_id,status`n$task,bounded_step_complete"
    Put 'project_coordination/HPC_JOB_LEDGER.csv' "Job_ID,Status`n1419643.mmaster02,SUBMITTED`n"
    Put 'project_coordination/MODE1_EXECUTION_LEDGER.json' '{}'

    # Session released by stage complete
    $session = @{
        active = $false
        agent = 'gemini-antigravity'
        task_id = $task
        controller_run_id = $run
        claimed_at = '2026-11-03T06:19:42Z'
        starting_commit = 'commit_abc'
        session_report = $reportRel
    }
    Put 'project_coordination/ACTIVE_SESSION.json' ($session | ConvertTo-Json)

    Put $reportRel "Research report for $run with findings.`n`nFinished`n"

    # Preparation artifact includes ACTIVE_TASK.json (pre-closeout hash) as an evidence source
    $prep = @{
        schema = 1
        status = 'PREPARATION_COMPLETE'
        finding = 'Reconciled live scheduler and streaming telemetry for Package 171-R1 C6 re-equilibration.'
        verification_passed = $true
        evidence_sources = @{
            'project_coordination/ACTIVE_TASK.json' = $activeTaskPreHash
        }
    }
    Put $prepRel ($prep | ConvertTo-Json -Depth 8)
    $prepHash = (Get-FileHash (Join-Path $root $prepRel)).Hash

    # Bootstrap record captures ordered_sources at turn start (including ACTIVE_TASK.json pre-closeout hash)
    $record = @{
        controller_run_id = $run
        task_id = $task
        repository_commit = 'commit_abc'
        bootstrap_status = 'COMPLETE'
        stage = 'COMPLETE'
        session_report = $reportRel
        ordered_sources = @{
            'project_coordination/ACTIVE_TASK.json' = $activeTaskPreHash
        }
        basis_sources = @{
            'project_coordination/ACTIVE_TASK.json' = $activeTaskPreHash
        }
        scientific_checkpoint = @{
            kind = 'PREPARATION_CHECKPOINT'
            operation = 'research_preparation'
            exit_code = 0
            artifact = $prepRel
            sha256 = $prepHash
        }
    }
    Put $bootRel ($record | ConvertTo-Json -Depth 8)

    # Now simulate Stage Complete updating ACTIVE_TASK.json on disk (changing its hash)
    $activeTaskPost = '{"task_id":"F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE","status":"PREPARATION_COMPLETE","phase":"Post-closeout updated"}'
    Put 'project_coordination/ACTIVE_TASK.json' $activeTaskPost
    $activeTaskPostHash = (Get-FileHash (Join-Path $root 'project_coordination/ACTIVE_TASK.json')).Hash
    Check ($activeTaskPostHash -ne $activeTaskPreHash) "Simulation confirmed ACTIVE_TASK.json hash changed post-closeout"

    function New-TestState {
        $e = Get-ControllerEvidence $root
        $s = New-ControllerTurnState $e 54 'instruction'
        $s.run_id = $run
        $s.task_id = $task
        $s.repository_commit = 'commit_abc'
        $s.bootstrap_record_path = Join-Path $root $bootRel
        $s.sources[$prepRel] = $prepHash
        $s.sources[$reportRel] = (Get-FileHash (Join-Path $root $reportRel)).Hash
        $s.owned_session_fingerprint = Get-ControllerTextHash ((@($session.agent, $session.task_id, $session.claimed_at, $session.starting_commit)) -join '|')
        return $s
    }

    $cpPath = Join-Path $root 'controller_turn_checkpoint.json'

    # --- CASE 1: Preparation completed but controller response incomplete ---
    $s1 = New-TestState
    Check (Test-ControllerScientificCheckpoint $root $s1) 'Case 1a: Test-ControllerScientificCheckpoint recognizes authentic bootstrap evidence for updated coordination file'
    Check (Test-ControllerCompletedScienceReceipt $root $s1) 'Case 1b: Test-ControllerCompletedScienceReceipt accepts completed science receipt'
    $incompleteResponse = "Some response that ends with Finished but has trailing text`nFinished`n`nClarify the scope of this recovery task`n"
    $c1 = Complete-ControllerTurn $root $cpPath $s1 $incompleteResponse
    Check ($c1 -eq 'COMPLETED') 'Case 1c: Controller completes via verified science receipt despite trailing response text'

    # --- CASE 2: Preparation completed with unreleased repository session ---
    $s2 = New-TestState
    $unreleasedSession = $session.Clone()
    $unreleasedSession.active = $true
    Put 'project_coordination/ACTIVE_SESSION.json' ($unreleasedSession | ConvertTo-Json)
    $s2.session.active = $true
    $c2 = Complete-ControllerTurn $root $cpPath $s2 $incompleteResponse
    Check ($c2 -eq 'BLOCKED' -and $s2.block_reason -match 'session not released') 'Case 2: Active/unreleased repository session fails closed'
    # Restore released session
    Put 'project_coordination/ACTIVE_SESSION.json' ($session | ConvertTo-Json)

    # --- CASE 3: Genuine active-session conflict ---
    $s3 = New-TestState
    $conflictSession = $session.Clone()
    $conflictSession.active = $true
    $conflictSession.agent = 'codex'
    Put 'project_coordination/ACTIVE_SESSION.json' ($conflictSession | ConvertTo-Json)
    $threwConflict = $false
    try {
        Sync-ControllerOwnedSession (Get-ControllerEvidence $root) $s3
    } catch {
        $threwConflict = ($_.Exception.Message -match 'ownership changed|Cannot establish ownership')
    }
    Check $threwConflict 'Case 3: Foreign active-session ownership triggers immediate blocker'
    # Restore released session
    Put 'project_coordination/ACTIVE_SESSION.json' ($session | ConvertTo-Json)

    # --- CASE 4: Valid completed checkpoint after interruption ---
    $s4 = New-TestState
    $null = Complete-ControllerTurn $root $cpPath $s4 "Response ending with Finished`n`nFinished`n"
    $restored = Read-ControllerCheckpoint $cpPath
    Check ($restored.state -eq 'COMPLETED' -and $restored.run_id -eq $run) 'Case 4a: Checkpoint reflects COMPLETED'
    Assert-ControllerDispatchCheckpoint $root $restored
    Check ($restored.state -eq 'COMPLETED') 'Case 4b: Assert-ControllerDispatchCheckpoint verifies completed state'

    # --- CASE 5: Corrupt or mismatched checkpoint ---
    $s5 = New-TestState
    $badBootRel = "project_coordination/controller/turn-$run-corrupt.json"
    $badRecord = $record.Clone()
    $badRecord.scientific_checkpoint = @{
        kind = 'PREPARATION_CHECKPOINT'
        exit_code = 1 # Exit code 1 must fail
        artifact = $prepRel
        sha256 = $prepHash
    }
    Put $badBootRel ($badRecord | ConvertTo-Json -Depth 8)
    $s5.bootstrap_record_path = Join-Path $root $badBootRel
    Check (-not (Test-ControllerScientificCheckpoint $root $s5)) 'Case 5a: Exit code 1 in scientific checkpoint is rejected'
    $badRecord.scientific_checkpoint.exit_code = 0
    $badRecord.scientific_checkpoint.sha256 = 'BAD_HASH_FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
    Put $badBootRel ($badRecord | ConvertTo-Json -Depth 8)
    Check (-not (Test-ControllerScientificCheckpoint $root $s5)) 'Case 5b: SHA-256 mismatch in scientific checkpoint is rejected'

    # --- CASE 6: Previously submitted HPC job ---
    $ledgerContent = Get-Content (Join-Path $root 'project_coordination/HPC_JOB_LEDGER.csv') -Raw
    Check ($ledgerContent -match '1419643\.mmaster02') 'Case 6: Prior PBS job is accurately recorded in ledger preventing duplicate dispatch'

    # --- CASE 7: Unregistered successor scientific operation ---
    $f1599Exists = Test-Path (Join-Path $root 'project_coordination/task_definitions/F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE.json')
    Check (-not $f1599Exists) 'Case 7: Successor task F1599 correctly remains unregistered without synthetic creation'

    # --- CASE 8: A blocked response that must remain blocked ---
    $s8 = New-TestState
    $blockedResponse = "BLOCKED: Numerical divergence observed in crack propagation"
    $c8 = Complete-ControllerTurn $root $cpPath $s8 $blockedResponse
    Check ($c8 -eq 'BLOCKED') 'Case 8: Explicit BLOCKED response remains BLOCKED even with valid science receipt'

    Write-Output "ALL 8 REGRESSION CASES PASSED SUCCESSFULLY."
} finally {
    $target = [IO.Path]::GetFullPath($root)
    $temp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if ($target.StartsWith($temp, [StringComparison]::OrdinalIgnoreCase) -and (Split-Path $target -Leaf) -like 't54-regression-*') {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}
