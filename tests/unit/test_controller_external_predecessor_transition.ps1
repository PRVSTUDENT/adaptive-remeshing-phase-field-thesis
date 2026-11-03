# Focused regression test suite verifying the external predecessor transition:
# F1598 (controller checkpoint) -> F1599 (interactive AGY completion) -> F1601 (successor dispatch).
# Validates rejection of missing evidence, mismatched predecessors, altered hashes, active sessions, and duplicate successors.

$ErrorActionPreference = 'Stop'
$repo = (Get-Item $PSScriptRoot).Parent.Parent.FullName
. (Join-Path $repo 'scripts/controller/Controller-TaskLifecycle.ps1')

$script:testIndex = 0
function Check([bool]$Condition, [string]$Description) {
    $script:testIndex++
    if (-not $Condition) {
        Write-Error ("FAIL $script:testIndex $Description")
        exit 1
    }
    Write-Host ("PASS $script:testIndex $Description")
}

# Setup isolated sandbox fixture
$tmp = Join-Path ([IO.Path]::GetTempPath()) ("ext-pred-" + [Guid]::NewGuid().ToString('n'))
$null = New-Item -ItemType Directory -Path $tmp -Force
$null = New-Item -ItemType Directory -Path (Join-Path $tmp 'project_coordination/task_definitions') -Force
$null = New-Item -ItemType Directory -Path (Join-Path $tmp 'results/validation') -Force

try {
    # 1. Create simulated F1598 controller checkpoint on disk
    $cpPath = Join-Path $tmp 'controller_turn_checkpoint.json'
    $cpState = [pscustomobject]@{
        task_id = 'F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE'
        run_id = 'ae8660dc-363a-4847-854c-93f9e08c0212'
        state = 'COMPLETED'
        turn = 62
    }
    $cpEnvelope = [pscustomobject]@{
        schema = 1
        payload = ($cpState | ConvertTo-Json -Compress)
        sha256 = '8F2ACED072C91BB69FF238AB167795230EDA73DA91714C559B7421E94B59B2F6'
    }
    [IO.File]::WriteAllText($cpPath, ($cpEnvelope | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))
    $cpHash = (Get-FileHash -LiteralPath $cpPath).Hash

    # 2. Create authentic F1599 task definition linking back to F1598
    $predDefPath = Join-Path $tmp 'project_coordination/task_definitions/F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE.json'
    $predDef = [pscustomobject]@{
        schema = 1
        task_id = 'F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE'
        title = 'Evaluate authentic Package 171-R1 C6 evidence'
        predecessor = [pscustomobject]@{
            task_id = 'F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE'
            run_id = 'ae8660dc-363a-4847-854c-93f9e08c0212'
            status = 'COMPLETED'
            checkpoint_sha256 = $cpHash
        }
        operation = [pscustomobject]@{
            id = 'research_preparation'
            mode = 'READ_ONLY_SCIENTIFIC_EVALUATION'
        }
        max_new_pbs_submissions = 0
    }
    [IO.File]::WriteAllText($predDefPath, ($predDef | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))

    # 3. Create simulated F1599 evaluation receipt artifact
    $receiptPath = Join-Path $tmp 'results/validation/f1599_receipt.json'
    [IO.File]::WriteAllText($receiptPath, '{"physical_acceptance":"FAIL_COUPLED_NONCONVERGENCE"}', [Text.UTF8Encoding]::new($false))
    $receiptHash = (Get-FileHash -LiteralPath $receiptPath).Hash

    # 4. Create authentic F1601 definition linking to F1599
    $succDefPath = Join-Path $tmp 'project_coordination/task_definitions/F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION.json'
    $gitHead = (& git -C $repo rev-parse HEAD).Trim()
    $succDef = [pscustomobject]@{
        schema = 1
        task_id = 'F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION'
        title = 'Bounded Mode-I C6/R2 numerical diagnosis'
        predecessor = [pscustomobject]@{
            task_id = 'F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE'
            run_id = 'ae8660dc-363a-4847-854c-93f9e08c0212'
            status = 'COMPLETED'
            source_commit = $gitHead
            checkpoint_sha256 = $receiptHash
        }
        operation = [pscustomobject]@{
            id = 'research_preparation'
            mode = 'READ_ONLY_SCIENTIFIC_EVALUATION'
        }
        max_new_pbs_submissions = 0
        inherited_completed_operations = @('op1')
        evidence_sources = [pscustomobject]@{
            'results/validation/f1599_receipt.json' = $receiptHash
        }
        initial_instruction = 'TASK: F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION'
    }
    [IO.File]::WriteAllText($succDefPath, ($succDef | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
    $succDefHash = (Get-FileHash -LiteralPath $succDefPath).Hash

    # 5. Create TASK_LEDGER.csv
    $ledgerPath = Join-Path $tmp 'project_coordination/TASK_LEDGER.csv'
    $ledgerContent = @"
task_id,category,description,status,agent,commit,pbs_job_id,session_report,active_pbs_job_ids,classification,next_task,last_updated
F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE,Mode-I,Evaluate F1598,completed,gemini-antigravity,$gitHead,,report1,,EVALUATED,F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE,2026-11-03T08:38:00
F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE,Mode-I,Evaluate F1599,completed,gemini-antigravity,$gitHead,,report2,,EVALUATED_FAILED_COUPLED_NONCONVERGENCE,F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION,2026-11-03T09:25:00
F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION,Mode-I,Diagnose C6/R2,ready,gemini-antigravity,$gitHead,,report3,,REGISTERED_NOT_EXECUTED,,2026-11-03T10:15:00
"@
    [IO.File]::WriteAllText($ledgerPath, $ledgerContent, [Text.UTF8Encoding]::new($false))

    # 6. Create ACTIVE_TASK.json
    $activeTaskPath = Join-Path $tmp 'project_coordination/ACTIVE_TASK.json'
    $activeTask = [pscustomobject]@{
        task_id = 'F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION'
        status = 'READY_READ_ONLY_EVALUATION'
        predecessor_task = [pscustomobject]@{
            task_id = 'F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE'
        }
        registration = [pscustomobject]@{
            schema = 1
            definition = 'project_coordination/task_definitions/F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION.json'
            sha256 = $succDefHash
        }
        completed_operations = @('op1')
        scientific_checkpoint_required = $true
        scientific_operation = ''
        scientific_operation_id = 'research_preparation'
        max_new_pbs_submissions = 0
    }
    [IO.File]::WriteAllText($activeTaskPath, ($activeTask | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))

    # 7. Create ACTIVE_SESSION.json (inactive)
    $sessionPath = Join-Path $tmp 'project_coordination/ACTIVE_SESSION.json'
    $session = [pscustomobject]@{
        active = $false
        agent = 'gemini-antigravity'
        task_id = 'F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION'
    }
    [IO.File]::WriteAllText($sessionPath, ($session | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))

    # TEST 1: Valid external predecessor transition produces fresh successor
    $plan = Get-ControllerSuccessorCheckpointPlan $tmp $cpPath $cpState
    Check ($plan.fresh_successor -and $plan.instruction -eq 'TASK: F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION' -and $plan.external_predecessor -eq 'F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE') 'Authentic external predecessor transition resolves cleanly'

    # TEST 2: Active session rejection
    $session.active = $true
    [IO.File]::WriteAllText($sessionPath, ($session | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))
    try {
        $null = Get-ControllerSuccessorCheckpointPlan $tmp $cpPath $cpState
        throw 'Expected active session rejection'
    } catch {
        Check ($_.Exception.Message -match 'active session exists') 'Active session rejected'
    }
    $session.active = $false
    [IO.File]::WriteAllText($sessionPath, ($session | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))

    # TEST 3: Missing predecessor task definition rejection
    Remove-Item -LiteralPath $predDefPath -Force
    try {
        $null = Get-ControllerSuccessorCheckpointPlan $tmp $cpPath $cpState
        throw 'Expected missing predecessor definition rejection'
    } catch {
        Check ($_.Exception.Message -match 'completed predecessor binding missing or changed') 'Missing predecessor definition rejected'
    }
    [IO.File]::WriteAllText($predDefPath, ($predDef | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))

    # TEST 4: Mismatched predecessor chain (predDef points to wrong run_id)
    $predDef.predecessor.run_id = 'wrong-run-id'
    [IO.File]::WriteAllText($predDefPath, ($predDef | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
    try {
        $null = Get-ControllerSuccessorCheckpointPlan $tmp $cpPath $cpState
        throw 'Expected mismatched predecessor run rejection'
    } catch {
        Check ($_.Exception.Message -match 'completed predecessor binding missing or changed') 'Mismatched predecessor run rejected'
    }
    $predDef.predecessor.run_id = 'ae8660dc-363a-4847-854c-93f9e08c0212'
    [IO.File]::WriteAllText($predDefPath, ($predDef | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))

    # TEST 5: Altered receipt hash rejection
    [IO.File]::WriteAllText($receiptPath, '{"physical_acceptance":"ALTERED_CONTENT"}', [Text.UTF8Encoding]::new($false))
    try {
        $null = Get-ControllerSuccessorCheckpointPlan $tmp $cpPath $cpState
        throw 'Expected altered receipt rejection'
    } catch {
        Check ($_.Exception.Message -match '(completed predecessor receipt missing or altered|Task evidence changed)') 'Altered receipt hash rejected'
    }
    [IO.File]::WriteAllText($receiptPath, '{"physical_acceptance":"FAIL_COUPLED_NONCONVERGENCE"}', [Text.UTF8Encoding]::new($false))

    # TEST 6: Unclosed predecessor in ledger rejection
    $unclosedLedger = $ledgerContent.Replace('completed,gemini-antigravity', 'ready,gemini-antigravity')
    [IO.File]::WriteAllText($ledgerPath, $unclosedLedger, [Text.UTF8Encoding]::new($false))
    try {
        $null = Get-ControllerSuccessorCheckpointPlan $tmp $cpPath $cpState
        throw 'Expected unclosed predecessor rejection'
    } catch {
        Check ($_.Exception.Message -match 'predecessor is not closed') 'Unclosed predecessor in ledger rejected'
    }
    [IO.File]::WriteAllText($ledgerPath, $ledgerContent, [Text.UTF8Encoding]::new($false))

    # TEST 7: Predecessor does not link to successor in ledger
    $brokenLinkLedger = $ledgerContent.Replace('F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION', 'WRONG-SUCCESSOR')
    # Keep F1601 row in place
    $brokenLinkLedger = $ledgerContent.Replace(',F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION,2026-11-03T09:25:00', ',WRONG-SUCCESSOR,2026-11-03T09:25:00')
    [IO.File]::WriteAllText($ledgerPath, $brokenLinkLedger, [Text.UTF8Encoding]::new($false))
    try {
        $null = Get-ControllerSuccessorCheckpointPlan $tmp $cpPath $cpState
        throw 'Expected broken linkage rejection'
    } catch {
        Check ($_.Exception.Message -match 'predecessor does not link to successor') 'Broken predecessor-successor link rejected'
    }
    [IO.File]::WriteAllText($ledgerPath, $ledgerContent, [Text.UTF8Encoding]::new($false))

    # TEST 8: Duplicate successor in ledger rejection
    $dupLedger = $ledgerContent + "`nF1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION,Mode-I,Duplicate,ready,gemini-antigravity,$gitHead,,report4,,REGISTERED_NOT_EXECUTED,,2026-11-03T10:16:00"
    [IO.File]::WriteAllText($ledgerPath, $dupLedger, [Text.UTF8Encoding]::new($false))
    try {
        $null = Get-ControllerSuccessorCheckpointPlan $tmp $cpPath $cpState
        throw 'Expected duplicate successor rejection'
    } catch {
        Check ($_.Exception.Message -match '(duplicate or missing successor|Duplicate or missing task registration)') 'Duplicate successor in ledger rejected'
    }
    [IO.File]::WriteAllText($ledgerPath, $ledgerContent, [Text.UTF8Encoding]::new($false))

    # TEST 9: Invalid git commit rejection
    $succDef.predecessor.source_commit = '0000000000000000000000000000000000000000'
    [IO.File]::WriteAllText($succDefPath, ($succDef | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
    $activeTask.registration.sha256 = (Get-FileHash -LiteralPath $succDefPath).Hash
    [IO.File]::WriteAllText($activeTaskPath, ($activeTask | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
    try {
        $null = Get-ControllerSuccessorCheckpointPlan $tmp $cpPath $cpState
        throw 'Expected invalid git commit rejection'
    } catch {
        Check ($_.Exception.Message -match 'predecessor source commit not found') 'Invalid git commit rejected'
    }
    $succDef.predecessor.source_commit = $gitHead
    [IO.File]::WriteAllText($succDefPath, ($succDef | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
    $activeTask.registration.sha256 = (Get-FileHash -LiteralPath $succDefPath).Hash
    [IO.File]::WriteAllText($activeTaskPath, ($activeTask | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))

    Write-Host ("ALL $script:testIndex EXTERNAL PREDECESSOR REGRESSION CHECKS PASS")
} finally {
    if (Test-Path -LiteralPath $tmp) {
        Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
}
