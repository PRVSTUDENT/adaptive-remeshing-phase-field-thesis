# ==============================================================================
# REGRESSION TEST: Controller Startup Fix & Historical Recovery Boundary
# Tests that completed historical recoveries do not block new research turns,
# while genuine checkpoint integrity, session ownership, and HPC safety remain enforced.
# ==============================================================================
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')
. (Join-Path $repo 'scripts/controller/Controller-Preparation.ps1')
. (Join-Path $repo 'scripts/controller/Controller-Operations.ps1')
. (Join-Path $repo 'scripts/controller/Controller-TaskLifecycle.ps1')

$fixture = Join-Path $env:TEMP ('controller-startup-fix-test-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path (Join-Path $fixture 'project_coordination/sessions'),
                                   (Join-Path $fixture 'project_coordination/task_definitions'),
                                   (Join-Path $fixture 'project_coordination/controller'),
                                   (Join-Path $fixture 'results/validation'),
                                   (Join-Path $fixture 'backups') -Force | Out-Null

$script:testsPassed = 0
function Check($condition, [string]$message) {
    if (-not $condition) {
        throw "FAIL: $message"
    }
    $script:testsPassed++
    Write-Host "PASS: $message"
}

function Put([string]$relPath, [string]$content) {
    $p = Join-Path $fixture $relPath
    $dir = Split-Path $p
    if (-not (Test-Path -LiteralPath $dir)) { [void][IO.Directory]::CreateDirectory($dir) }
    [IO.File]::WriteAllText($p, $content, [Text.Encoding]::UTF8)
}

try {
    # -------------------------------------------------------------------------
    # Setup base fixture files
    # -------------------------------------------------------------------------
    Put 'project_coordination/ACTIVE_SESSION.json' '{"active":false,"agent":"gemini-antigravity"}'
    Put 'project_coordination/HPC_JOB_LEDGER.csv' "Job_ID,Job_Name,Remote_Dir,Host,Queue,Submitted_At,Status,Exit_Code,Classification,Verification_Hash`n1419873.mmaster02,M1_C6_P171_R7_C3_0,/scratch9,mnode105,normal_imfdfkmq,2026-11-03T20:16:49+00:00,FAILED,1,FAILED_COUPLED_NONCONVERGENCE_OUTER100,d86c2798164efd9a9896b37c2e5d32081863a7e7ed89f323b13e164015f04780"
    Put 'project_coordination/MODE1_EXECUTION_LEDGER.json' '{"reserved":1}'
    Put 'project_coordination/ARTIFACT_REGISTRY.csv' "artifact_id,canonical_path`n"
    Put 'project_coordination/CURRENT_STATE.md' "Scientific state retained."
    Put 'AGENTS.md' "Bootstrap rules fixture"
    Put 'project_coordination/START_HERE.md' "Start here fixture"
    Put 'docs/project/PROJECT_PHASE_CHECKLIST.md' "Checklist fixture"

    # Git init
    $git = (Get-Command git.exe).Source
    & $git -C $fixture init -q
    & $git -C $fixture config user.name 'TestRunner'
    & $git -C $fixture config user.email 'test@fixture.invalid'
    & $git -C $fixture add AGENTS.md
    & $git -C $fixture commit -q -m 'initial'

    # Register task F1605 (completed) and F1606 (ready)
    Put 'project_coordination/TASK_LEDGER.csv' @"
task_id,stage,title,status,agent,base_commit,result_commit,write_scope,job_id,classification,next_task,updated_at
F1604-OLD,Mode-I,Preparation,completed,gemini-antigravity,commit0,,scope,none,EVALUATED,F1605-PRED,2026-11-03T21:10:00+01:00
F1605-PRED,Mode-I,Execution,completed,gemini-antigravity,commit1,,scope,1419873.mmaster02,EVALUATED_FAILED_COUPLED_NONCONVERGENCE,F1606-NEW,2026-11-04T06:25:00+01:00
F1606-NEW,Mode-I,Diagnosis,ready,gemini-antigravity,commit1,,scope,none,REGISTERED_NOT_EXECUTED,,2026-11-04T06:25:00+01:00
"@

    $f1606Def = @{
        schema = 1
        task_id = "F1606-NEW"
        title = "Diagnosis"
        predecessor = @{
            run_id = "06642f83-a72a-48d0-962e-953f109183bb"
            status = "COMPLETED"
            task_id = "F1605-PRED"
            checkpoint_artifact = "results/validation/preparation-06642f83.json"
        }
        operation = @{
            checkpoint_kind = "PREPARATION_CHECKPOINT"
            id = "research_preparation"
            mode = "READ_ONLY_SCIENTIFIC_EVALUATION"
            registration = "Diagnosis only"
        }
        max_new_pbs_submissions = 0
        evidence_sources = @{
            "results/validation/preparation-06642f83.json" = "59C179A2EBD4C9B65E472B08C291EB6A936D1A9B6E04658D9272C267DF6BC270"
        }
        initial_instruction = "TASK: F1606-NEW"
    }
    Put 'project_coordination/task_definitions/F1606-NEW.json' ($f1606Def | ConvertTo-Json -Depth 10)
    Put 'results/validation/preparation-06642f83.json' '{"status":"ok"}'
    # Ensure hash matches evidence_sources pin
    $artHash = (Get-FileHash -LiteralPath (Join-Path $fixture 'results/validation/preparation-06642f83.json')).Hash
    $f1606Def.evidence_sources["results/validation/preparation-06642f83.json"] = $artHash
    Put 'project_coordination/task_definitions/F1606-NEW.json' ($f1606Def | ConvertTo-Json -Depth 10)

    $defHash = (Get-FileHash -LiteralPath (Join-Path $fixture 'project_coordination/task_definitions/F1606-NEW.json')).Hash
    $f1606Task = @{
        task_id = "F1606-NEW"
        status = "READY_FOR_EXECUTION"
        scientific_checkpoint_required = $true
        scientific_operation = ""
        scientific_operation_id = "research_preparation"
        registration = @{
            sha256 = $defHash
            schema = 1
            definition = "project_coordination/task_definitions/F1606-NEW.json"
        }
        predecessor_task = @{
            run_id = "06642f83-a72a-48d0-962e-953f109183bb"
            status = "COMPLETED"
            task_id = "F1605-PRED"
            source_commit = (& $git -C $fixture rev-parse HEAD).Trim()
            checkpoint_sha256 = $artHash
        }
        completed_pbs_job_ids = @("1419873.mmaster02")
        max_new_pbs_submissions = 0
    }
    Put 'project_coordination/ACTIVE_TASK.json' ($f1606Task | ConvertTo-Json -Depth 10)

    # -------------------------------------------------------------------------
    # TEST 1: Legitimately completed historical recovery followed by new task starts successfully
    # -------------------------------------------------------------------------
    $historicalArchive = Join-Path $fixture 'backups/checkpoint-old-interrupted.json'
    $oldOriginal = [pscustomobject]@{
        schema = 1
        run_id = "old-run-id-1234"
        state = "PENDING"
        task_id = "F1604-OLD"
        recovery_count = 0
        updated_at = [DateTimeOffset]::UtcNow.ToString('o')
    }
    Write-ControllerCheckpoint $historicalArchive $oldOriginal
    $oldArchiveHash = (Get-FileHash -LiteralPath $historicalArchive).Hash

    # Completed checkpoint from F1604 sitting at controller_turn_checkpoint.json
    $oldCheckpoint = [pscustomobject]@{
        schema = 1
        run_id = "old-run-id-1234"
        state = "COMPLETED"
        task_id = "F1604-OLD"
        recovery_count = 0
        updated_at = [DateTimeOffset]::UtcNow.ToString('o')
        reconciliation = [pscustomobject]@{
            status = "INTERRUPTED_TURN_PROGRESS_WATCHDOG_RECONCILED"
            run_id = "old-run-id-1234"
            original_checkpoint = $historicalArchive
            original_sha256 = $oldArchiveHash
            bootstrap_record = "project_coordination/controller/turn-old.json"
            bootstrap_record_sha256 = "OLD_BOOTSTRAP_HASH_DOES_NOT_MATCH_CURRENT_DISK"
            session_report = "project_coordination/sessions/old_session.md"
            session_report_sha256 = "OLD_SESSION_HASH"
        }
    }
    $cpPath = Join-Path $fixture 'controller_turn_checkpoint.json'
    Write-ControllerCheckpoint $cpPath $oldCheckpoint

    $t1Passed = $false
    try {
        Assert-ControllerStartupCheckpoint $fixture $oldCheckpoint
        $t1Passed = $true
    } catch {
        Write-Host "Test 1 failed with: $($_.Exception.Message)"
        $t1Passed = $false
    }
    Check $t1Passed "Test 1: Completed historical recovery does not block new task startup"

    # Also verify Assert-ControllerDispatchCheckpoint honors the completed historical task boundary
    $t1DispatchPassed = $false
    try {
        Assert-ControllerDispatchCheckpoint $fixture $oldCheckpoint
        $t1DispatchPassed = $true
    } catch {
        Write-Host "Test 1 dispatch check failed with: $($_.Exception.Message)"
        $t1DispatchPassed = $false
    }
    Check $t1DispatchPassed "Test 1b: Assert-ControllerDispatchCheckpoint returns clean for completed historical task"

    # -------------------------------------------------------------------------
    # TEST 2: Incomplete recovery still blocks
    # -------------------------------------------------------------------------
    $blockedCheckpoint = [pscustomobject]@{
        schema = 1
        run_id = "blocked-run-id"
        state = "BLOCKED"
        task_id = "F1606-NEW"
        block_reason = "Unresolved numerical divergence in crack step"
    }
    $t2Blocked = $false
    try {
        Assert-ControllerStartupCheckpoint $fixture $blockedCheckpoint
    } catch {
        $t2Blocked = $_.Exception.Message -match "BLOCKED: historical checkpoint requires evidence-based reconciliation"
    }
    Check $t2Blocked "Test 2: Incomplete/BLOCKED checkpoint still blocks startup"

    # -------------------------------------------------------------------------
    # TEST 3: Tampered historical evidence is rejected during recovery validation
    # -------------------------------------------------------------------------
    # Active recovery checkpoint for F1606
    $activeArchive = Join-Path $fixture 'backups/checkpoint-active-interrupted.json'
    $activeOriginal = [pscustomobject]@{
        schema = 1
        run_id = "active-run-id-5678"
        state = "PENDING"
        task_id = "F1606-NEW"
        recovery_count = 0
    }
    Write-ControllerCheckpoint $activeArchive $activeOriginal
    $activeArchHash = (Get-FileHash -LiteralPath $activeArchive).Hash
    $sessionReportPath = 'project_coordination/sessions/active_report.md'
    Put $sessionReportPath "Active report content"
    $repHash = (Get-FileHash -LiteralPath (Join-Path $fixture $sessionReportPath)).Hash

    $reconciledState = [pscustomobject]@{
        schema = 1
        run_id = "active-run-id-5678"
        state = "COMPLETED"
        task_id = "F1606-NEW"
        recovery_count = 0
        reconciliation = [pscustomobject]@{
            status = "INTERRUPTED_TURN_PROGRESS_WATCHDOG_RECONCILED"
            run_id = "active-run-id-5678"
            original_checkpoint = $activeArchive
            original_sha256 = $activeArchHash
            session_report = $sessionReportPath
            session_report_sha256 = $repHash
        }
    }
    # Clean check passes
    $t3CleanPassed = $false
    try {
        Assert-ControllerDispatchCheckpoint $fixture $reconciledState
        $t3CleanPassed = $true
    } catch {
        Write-Host "Test 3 clean check failed: $($_.Exception.Message)"
        $t3CleanPassed = $false
    }
    Check $t3CleanPassed "Test 3a: Valid active reconciliation passes recovery validation"

    # Tampered original archive hash fails closed
    $tamperedState1 = $reconciledState | ConvertTo-Json -Depth 10 | ConvertFrom-Json
    $tamperedState1.reconciliation.original_sha256 = "CORRUPTED_HASH_VALUE_1234567890"
    $t3Tamper1Blocked = $false
    try {
        Assert-ControllerDispatchCheckpoint $fixture $tamperedState1
    } catch {
        $t3Tamper1Blocked = $_.Exception.Message -match "reconciled historical evidence missing or changed"
    }
    Check $t3Tamper1Blocked "Test 3b: Tampered historical archive hash fails closed during recovery validation"

    # Tampered session report hash fails closed
    $tamperedState2 = $reconciledState | ConvertTo-Json -Depth 10 | ConvertFrom-Json
    $tamperedState2.reconciliation.session_report_sha256 = "CORRUPTED_REPORT_HASH"
    $t3Tamper2Blocked = $false
    try {
        Assert-ControllerDispatchCheckpoint $fixture $tamperedState2
    } catch {
        $t3Tamper2Blocked = $_.Exception.Message -match "session report evidence changed"
    }
    Check $t3Tamper2Blocked "Test 3c: Tampered session report fails closed during recovery validation"

    # Mismatched run ID fails closed
    $tamperedState3 = $reconciledState | ConvertTo-Json -Depth 10 | ConvertFrom-Json
    $tamperedState3.reconciliation.run_id = "mismatched-run-id"
    $t3Tamper3Blocked = $false
    try {
        Assert-ControllerDispatchCheckpoint $fixture $tamperedState3
    } catch {
        $t3Tamper3Blocked = $_.Exception.Message -match "BLOCKED: original historical checkpoint identity mismatch"
    }
    Check $t3Tamper3Blocked "Test 3d: Mismatched recovery run ID fails closed during recovery validation"

    # -------------------------------------------------------------------------
    # TEST 4: Foreign session ownership still blocks
    # -------------------------------------------------------------------------
    Put 'project_coordination/ACTIVE_SESSION.json' '{"active":true,"agent":"foreign-agent","task_id":"F1606-NEW"}'
    $t4Blocked = $false
    try {
        Assert-ControllerStartupCheckpoint $fixture $oldCheckpoint
    } catch {
        $t4Blocked = $_.Exception.Message -match "BLOCKED: repository session active; no profile selection or AGY execution"
    }
    Check $t4Blocked "Test 4: Foreign active session blocks controller startup"
    Put 'project_coordination/ACTIVE_SESSION.json' '{"active":false,"agent":"gemini-antigravity"}'

    # -------------------------------------------------------------------------
    # TEST 5: Duplicate PBS submissions still block
    # -------------------------------------------------------------------------
    # 5a: Zero-submission task with pbs_job_id in checkpoint
    $zeroSubViolationCheckpoint = [pscustomobject]@{
        schema = 1
        run_id = "run-zero-sub"
        state = "COMPLETED"
        task_id = "F1606-NEW"
        pbs_job_id = "1419999.mmaster02"
    }
    $t5aBlocked = $false
    try {
        Assert-ControllerStartupCheckpoint $fixture $zeroSubViolationCheckpoint
    } catch {
        $t5aBlocked = $_.Exception.Message -match "permits zero PBS submissions but checkpoint contains job"
    }
    Check $t5aBlocked "Test 5a: Zero-submission task blocks checkpoint containing PBS job"

    # 5b: Duplicate submission of an already completed job
    $dupSubCheckpoint = [pscustomobject]@{
        schema = 1
        run_id = "run-dup-sub"
        state = "COMPLETED"
        task_id = "F1606-NEW"
        submitted_job_id = "1419873.mmaster02"
    }
    $t5bBlocked = $false
    try {
        Assert-ControllerStartupCheckpoint $fixture $dupSubCheckpoint
    } catch {
        $t5bBlocked = $_.Exception.Message -match "duplicate PBS submission detected for completed job"
    }
    Check $t5bBlocked "Test 5b: Duplicate PBS submission for completed job is blocked"

    # -------------------------------------------------------------------------
    # TEST 6: Existing completed task records remain immutable
    # -------------------------------------------------------------------------
    # Attempting to set ACTIVE_TASK to an already completed task (F1605-PRED) fails lifecycle assertion
    $closedTask = @{
        task_id = "F1605-PRED"
        status = "COMPLETED"
        scientific_checkpoint_required = $true
        scientific_operation = ""
    }
    Put 'project_coordination/ACTIVE_TASK.json' ($closedTask | ConvertTo-Json -Depth 5)
    $t6Blocked = $false
    try {
        Assert-ControllerTaskLifecycle $fixture
    } catch {
        $t6Blocked = $_.Exception.Message -match "COMPLETED_TASK_REJECTED"
    }
    Check $t6Blocked "Test 6: Completed task in ACTIVE_TASK is rejected as immutable"

    Write-Host "`nALL $script:testsPassed CONTROLLER STARTUP FIX REGRESSION TESTS PASSED."
} finally {
    Remove-Item -LiteralPath $fixture -Recurse -Force -ErrorAction SilentlyContinue
}
