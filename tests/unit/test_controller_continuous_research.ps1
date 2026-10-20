$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. "$repo/scripts/controller/Controller-Recovery.ps1"
. "$repo/scripts/controller/Controller-Preparation.ps1"
. "$repo/scripts/controller/Controller-Operations.ps1"
. "$repo/scripts/validation/Invoke-BoundedAgyProcess.ps1"

$fixture = Join-Path $env:TEMP ('agy-continuous-research-test-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$fixture/project_coordination/sessions", "$fixture/scripts/controller", "$fixture/scripts/validation", "$fixture/docs/project", "$fixture/results/validation" -Force | Out-Null

function Put($Name, $Text) {
    $target = Join-Path $fixture $Name
    $dir = Split-Path $target
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [IO.File]::WriteAllText($target, $Text)
}

$script:checks = 0
function Assert($Value, $Message) {
    if (-not $Value) { throw "FAIL: $Message" }
    $script:checks++
    "PASS $script:checks`: $Message"
}

try {
    # Copy essential controller and validation scripts
    foreach ($relative in @('scripts/controller/Controller-Recovery.ps1', 'scripts/controller/Controller-Operations.ps1', 'scripts/controller/Controller-Preparation.ps1', 'scripts/controller/Controller-Qualification.ps1', 'scripts/validation/probe_mode1_f1597_mechanical_history.py', 'scripts/validation/Invoke-BoundedAgyProcess.ps1', 'scripts/validation/probe_mode1_f1597_kkt.py')) {
        Copy-Item -LiteralPath (Join-Path $repo $relative) -Destination (Join-Path $fixture $relative) -Force
    }

    # Setup base project coordination prerequisites
    foreach ($relative in @('AGENTS.md', 'project_coordination/START_HERE.md', 'project_coordination/CURRENT_STATE.md', 'docs/project/PROJECT_PHASE_CHECKLIST.md')) {
        Put $relative 'Prerequisite fixture for autonomous controller test.'
    }
    Put 'project_coordination/ACTIVE_SESSION.json' '{"active":false,"agent":"codex","task_id":"prior"}'
    Put 'project_coordination/ACTIVE_TASK.json' '{"task_id":"F1597-AUTONOMOUS-RESEARCH","status":"READY_OFFLINE_MECHANICAL_HISTORY_PROBE","scientific_checkpoint_required":true,"scientific_operation":"scripts/validation/probe_mode1_f1597_mechanical_history.py","completed_operations":["mapped_frozen_history_lower_bound_kkt_probe"],"phase":"Measure mapped-state history call order"}'
    Put 'project_coordination/TASK_LEDGER.csv' "task_id,stage,title,status,agent,base_commit,result_commit,write_scope,job_id,classification,next_task,updated_at`nF1596-AUDIT,Mode-I,Audit,complete,gemini,commit1,commit2,scope,job1,class,next,2026-10-20`n"
    Put 'project_coordination/HPC_JOB_LEDGER.csv' "job_id,status`n1415199.mmaster02,completed"
    Put 'project_coordination/MODE1_EXECUTION_LEDGER.json' '{"reserved":1}'
    Put 'project_coordination/ARTIFACT_REGISTRY.csv' 'artifact_id,canonical_path'

    # Git repository initialization with origin remote
    $git = (Get-Command git.exe).Source
    $remote = Join-Path $fixture 'remote.git'
    foreach ($gitArgs in @(
        @('init', $fixture),
        @('-C', $fixture, 'config', 'user.name', 'ContinuousFixture'),
        @('-C', $fixture, 'config', 'user.email', 'continuous@fixture.invalid'),
        @('-C', $fixture, 'add', 'AGENTS.md'),
        @('-C', $fixture, 'commit', '-m', 'fixture: initial root commit'),
        @('init', '--bare', $remote),
        @('-C', $fixture, 'remote', 'add', 'origin', $remote)
    )) {
        $r = Invoke-BoundedAgyProcess -FilePath $git -ArgumentList $gitArgs -WorkingDirectory $fixture -TimeoutSeconds 15
        if ($r.ExitCode -ne 0) { throw $r.Output }
    }

    # Setup solver inputs and basis artifact for Turn 1
    $inputs = @(
        'models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for',
        'models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/M1_EXP_COUPLED_TRANSFER_650.inp',
        'models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/offset_state_table.csv',
        'models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/f42_experimental_offset_uel.for'
    )
    foreach ($relative in $inputs) { Put $relative 'Synthetic validator input fixture' }
    Copy-Item -LiteralPath "$repo/models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for" -Destination "$fixture/models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for" -Force
    Copy-Item -LiteralPath "$repo/models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/f42_experimental_offset_uel.for" -Destination "$fixture/models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/f42_experimental_offset_uel.for" -Force
    Put 'models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/M1_EXP_COUPLED_TRANSFER_650.inp' "*Node`n1,0,0`n2,1,0`n3,1,1`n4,0,1`n*Element,type=U1,elset=PHASE_QUADS`n1,1,2,3,4`n*UEL PROPERTY,ELSET=PHASE_QUADS`n0.1,0.2,210,0.3,1e-7,1`n*Nset,nset=N_BOTTOM`n1,2`n*Nset,nset=N_PIN`n1`n*Nset,nset=N_TOP`n3,4`n*Nset,nset=N_RP`n999999`n*EQUATION`n2`n3,2,1.0,999999,2,-1.0`n*EQUATION`n2`n4,2,1.0,999999,2,-1.0`n*Boundary`nN_BOTTOM,2,2,0.0`nN_PIN,1,1,0.0`nN_TOP,1,1,0.0`nN_RP,2,2,0.0`n"
    Put 'models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/offset_state_table.csv' "1,0,0,0,0,0,0,0,0,0.1,0.1,0.1,0.1,0.3,0.3,0.3,0.3`n"

    $basis = 'results/validation/mode1_f1597/00000000-0000-0000-0000-000000000000.json'
    $basisSources = [ordered]@{}
    foreach ($relative in ($inputs + @('scripts/validation/probe_mode1_f1597_kkt.py'))) {
        $basisSources[$relative] = (Get-FileHash -LiteralPath (Join-Path $fixture $relative)).Hash
    }
    Put $basis (@{task_id = 'F1597'; operation = 'mapped_frozen_history_lower_bound_kkt_probe'; verification_passed = $true; measurements = @{phase_residual_inf_kN = 0.085}; sources = $basisSources } | ConvertTo-Json -Depth 10)

    $taskObj = Get-Content -LiteralPath "$fixture/project_coordination/ACTIVE_TASK.json" -Raw | ConvertFrom-Json
    $taskObj | Add-Member scientific_checkpoint ([pscustomobject]@{artifact = $basis; sha256 = (Get-FileHash -LiteralPath (Join-Path $fixture $basis)).Hash }) -Force
    Put 'project_coordination/ACTIVE_TASK.json' ($taskObj | ConvertTo-Json -Depth 10)

    # -------------------------------------------------------------------------
    # TURN 1: Complete an already-registered qualified operation
    # -------------------------------------------------------------------------
    $state1 = New-ControllerTurnState (Get-ControllerEvidence $fixture) 1 'Turn 1: Registered mechanical history probe'
    $state1.state = 'RUNNING'; $state1.process_id = $PID
    $state1.scientific_basis_artifact = $basis
    $checkpoint1 = Join-Path $fixture 'runtime-1.json'; Write-ControllerCheckpoint $checkpoint1 $state1
    $turnEntry = Join-Path $repo 'scripts/controller/Invoke-ControllerTurn.ps1'

    # Stage Bootstrap
    $args1_boot = @('-NoProfile', '-NonInteractive', '-File', $turnEntry, '-Stage', 'Bootstrap', '-Workspace', $fixture, '-RunId', $state1.run_id, '-TaskId', $state1.task_id, '-RuntimeCheckpoint', $checkpoint1)
    $r = Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList $args1_boot -WorkingDirectory $fixture -TimeoutSeconds 30
    Assert ($r.ExitCode -eq 0 -and $r.Output -match 'BOOTSTRAP_COMPLETE') 'Turn 1 Bootstrap claims session and completes'

    # Stage Scientific
    $args1_sci = @('-NoProfile', '-NonInteractive', '-File', $turnEntry, '-Stage', 'Scientific', '-Workspace', $fixture, '-RunId', $state1.run_id, '-TaskId', $state1.task_id, '-RuntimeCheckpoint', $checkpoint1)
    $r = Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList $args1_sci -WorkingDirectory $fixture -TimeoutSeconds 30
    Assert ($r.ExitCode -eq 0 -and $r.Output -match 'mapped_mechanical_history_call_order_probe') 'Turn 1 Scientific executes mechanical history probe'

    # Stage Complete
    $args1_comp = @('-NoProfile', '-NonInteractive', '-File', $turnEntry, '-Stage', 'Complete', '-Workspace', $fixture, '-RunId', $state1.run_id, '-TaskId', $state1.task_id, '-RuntimeCheckpoint', $checkpoint1)
    $r = Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList $args1_comp -WorkingDirectory $fixture -TimeoutSeconds 30
    Assert ($r.ExitCode -eq 0 -and $r.Output -match 'SCIENTIFIC_STEP_COMPLETE') 'Turn 1 Complete commits, pushes, and clears scientific_operation'

    $taskAfterTurn1 = Get-Content -LiteralPath "$fixture/project_coordination/ACTIVE_TASK.json" -Raw | ConvertFrom-Json
    Assert ([string]::IsNullOrEmpty($taskAfterTurn1.scientific_operation)) 'Turn 1 leaves scientific_operation empty for continuous transition'
    Assert (@($taskAfterTurn1.completed_operations) -contains 'mapped_mechanical_history_call_order_probe') 'Turn 1 registers mapped_mechanical_history_call_order_probe as completed'

    # -------------------------------------------------------------------------
    # TURN 2: Receive unknown scientific task from ChatGPT - NO FATAL DEAD END
    # -------------------------------------------------------------------------
    $chatGptPrompt2 = "# ChatGPT Research Task: Investigate transactional call order discrepancy and formulate history update correction"
    $taskType2 = Resolve-ControllerTaskType $taskAfterTurn1 $fixture
    Assert ($taskType2.task_type -eq 'RESEARCH_PREPARATION' -and $taskType2.dispatch_ready) 'Turn 2 automatically resolves unknown task as RESEARCH_PREPARATION'

    $prepPlan2 = Get-ControllerPreparationPlan $fixture $chatGptPrompt2
    Assert ($prepPlan2.status -eq 'READY' -and $prepPlan2.dispatch_ready -and $prepPlan2.task_type -eq 'RESEARCH_PREPARATION') 'Turn 2 preparation plan is dispatch_ready without fatal dead end'

    $resolved2 = Resolve-ControllerInstruction $fixture $chatGptPrompt2
    Assert ($resolved2.task_type -eq 'RESEARCH_PREPARATION' -and -not $resolved2.operation) 'Resolve-ControllerInstruction does not throw NEXT_OPERATION_REQUIRES_DEFINITION'

    # -------------------------------------------------------------------------
    # TURN 3: Automatically enter research preparation turn & produce finding
    # -------------------------------------------------------------------------
    $state3 = New-ControllerTurnState (Get-ControllerEvidence $fixture) 2 'Turn 3: Autonomous research preparation'
    $state3.state = 'RUNNING'; $state3.process_id = $PID
    Assert ($state3.task_type -eq 'RESEARCH_PREPARATION') 'Turn 3 turn state reflects RESEARCH_PREPARATION'

    $checkpoint3 = Join-Path $fixture 'runtime-3.json'; Write-ControllerCheckpoint $checkpoint3 $state3

    # Turn 3 Bootstrap
    $args3_boot = @('-NoProfile', '-NonInteractive', '-File', $turnEntry, '-Stage', 'Bootstrap', '-Workspace', $fixture, '-RunId', $state3.run_id, '-TaskId', $state3.task_id, '-RuntimeCheckpoint', $checkpoint3)
    $r = Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList $args3_boot -WorkingDirectory $fixture -TimeoutSeconds 30
    Assert ($r.ExitCode -eq 0 -and $r.Output -match '"next_stage":\s*"Preparation"') 'Turn 3 Bootstrap completes and advances to Preparation'

    # Write genuine preparation finding artifact
    $prepArtifactRel3 = "results/validation/preparation-$($state3.run_id).json"
    $prepArtifactPath3 = Join-Path $fixture $prepArtifactRel3
    $prepFindingData = @{
        schema = 1
        task_id = $state3.task_id
        status = 'PREPARATION_COMPLETE'
        finding = 'Observed that displacement mapping precedes damage projection; history variable must update monotonically'
        operation = 'research_preparation'
        verification_passed = $true
        next_operation = 'Implement and qualify discrete transfer operator'
    }
    Put $prepArtifactRel3 ($prepFindingData | ConvertTo-Json -Depth 8)

    # Stage Preparation
    $args3_prep = @('-NoProfile', '-NonInteractive', '-File', $turnEntry, '-Stage', 'Preparation', '-Workspace', $fixture, '-RunId', $state3.run_id, '-TaskId', $state3.task_id, '-RuntimeCheckpoint', $checkpoint3, '-CheckpointArtifact', $prepArtifactRel3)
    $r = Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList $args3_prep -WorkingDirectory $fixture -TimeoutSeconds 30
    Assert ($r.ExitCode -eq 0 -and $r.Output -match 'PREPARATION_COMPLETE') 'Turn 3 Preparation verifies preparation checkpoint artifact'
    Assert (Test-ControllerScientificCheckpoint $fixture $state3) 'Test-ControllerScientificCheckpoint passes for PREPARATION_CHECKPOINT'

    # Stage Complete
    $args3_comp = @('-NoProfile', '-NonInteractive', '-File', $turnEntry, '-Stage', 'Complete', '-Workspace', $fixture, '-RunId', $state3.run_id, '-TaskId', $state3.task_id, '-RuntimeCheckpoint', $checkpoint3)
    $r = Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList $args3_comp -WorkingDirectory $fixture -TimeoutSeconds 30
    Assert ($r.ExitCode -eq 0 -and $r.Output -match 'SCIENTIFIC_STEP_COMPLETE') 'Turn 3 Complete releases session and logs preparation finding'

    # -------------------------------------------------------------------------
    # TURN 4: Produce and qualify a new operation, then advance without restart
    # -------------------------------------------------------------------------
    # Create a newly qualified python probe script in workspace
    $newOpRel = 'scripts/validation/probe_mode1_f1597_coupled_correction.py'
    $newOpPath = Join-Path $fixture $newOpRel
    Put $newOpRel @"
import sys, json
# Verified offline coupled correction probe
output_path = sys.argv[sys.argv.index('--output') + 1] if '--output' in sys.argv else 'out.json'
with open(output_path, 'w') as f:
    json.dump({'schema': 1, 'task_id': 'F1597', 'operation': 'probe_mode1_f1597_coupled_correction', 'verification_passed': True, 'measurements': {'phase_elements': 1, 'phase_nodes': 4, 'residual': 0.0}, 'next_operation': 'Advance to full verification'}, f)
sys.exit(0)
"@
    # Set the newly qualified operation in ACTIVE_TASK
    $taskObj4 = Get-Content -LiteralPath "$fixture/project_coordination/ACTIVE_TASK.json" -Raw | ConvertFrom-Json
    $taskObj4.scientific_operation = $newOpRel
    Put 'project_coordination/ACTIVE_TASK.json' ($taskObj4 | ConvertTo-Json -Depth 10)

    $taskType4 = Resolve-ControllerTaskType $taskObj4 $fixture
    Assert ($taskType4.task_type -eq 'QUALIFIED_EXECUTION' -and $taskType4.operation.path -eq $newOpRel) 'Newly created and qualified operation resolved as QUALIFIED_EXECUTION'

    $state4 = New-ControllerTurnState (Get-ControllerEvidence $fixture) 3 'Turn 4: Executing newly qualified operation'
    $state4.state = 'RUNNING'; $state4.process_id = $PID
    Assert ($state4.task_type -eq 'QUALIFIED_EXECUTION') 'Turn 4 turn state reflects QUALIFIED_EXECUTION'

    # -------------------------------------------------------------------------
    # TURN 5: Receive another unknown objective and continue again
    # -------------------------------------------------------------------------
    $taskObj5 = Get-Content -LiteralPath "$fixture/project_coordination/ACTIVE_TASK.json" -Raw | ConvertFrom-Json
    $taskObj5.scientific_operation = '' # Completed op cleared
    Put 'project_coordination/ACTIVE_TASK.json' ($taskObj5 | ConvertTo-Json -Depth 10)

    $chatGptPrompt5 = "# ChatGPT Next Task: Formulate adaptive evolving threshold criterion"
    $taskType5 = Resolve-ControllerTaskType $taskObj5 $fixture
    Assert ($taskType5.task_type -eq 'RESEARCH_PREPARATION' -and $taskType5.dispatch_ready) 'Turn 5 automatically handles second unknown objective as RESEARCH_PREPARATION'

    # -------------------------------------------------------------------------
    # SAFETY TESTS & FAILURE CASES
    # -------------------------------------------------------------------------
    # 1. Unsafe candidate rejection (e.g. arbitrary commands or rm -rf)
    $unsafePlan = Get-ControllerPreparationPlan $fixture 'Please rm -rf / and bypass qualification'
    Assert ($unsafePlan.status -eq 'DEFINITION_REJECTED' -and -not $unsafePlan.dispatch_ready) 'Unsafe candidate with rm -rf and bypass rejected'

    # 2. Duplicate completed operation replay rejection
    $replayPlan = Get-ControllerPreparationPlan $fixture 'Execute mapped_mechanical_history_call_order_probe again'
    Assert ($replayPlan.status -eq 'DEFINITION_REJECTED' -and -not $replayPlan.dispatch_ready) 'Replay of completed operation rejected'

    # 3. Completed task ID rejection
    $taskClosedRejected = $false
    try {
        $null = Resolve-ControllerInstruction $fixture '# F1596: repeat audit task'
    } catch {
        $taskClosedRejected = ($_.Exception.Message -match 'COMPLETED_TASK_REJECTED')
    }
    Assert $taskClosedRejected 'Closed predecessor task F1596 rejected by Resolve-ControllerInstruction'

    # 4. Retired KKT probe rejection
    $taskObjRetired = Get-Content -LiteralPath "$fixture/project_coordination/ACTIVE_TASK.json" -Raw | ConvertFrom-Json
    $taskObjRetired.scientific_operation = 'scripts/validation/probe_mode1_f1597_kkt.py'
    $retiredRejected = $false
    try {
        $null = Resolve-ControllerTaskType $taskObjRetired $fixture
    } catch {
        $retiredRejected = ($_.Exception.Message -match 'UNQUALIFIED_OR_RETIRED_OPERATION')
    }
    Assert $retiredRejected 'Retired KKT probe strictly rejected by Resolve-ControllerTaskType'

    # 5. Invalid / tampered preparation checkpoint rejection
    $corruptState = New-ControllerTurnState (Get-ControllerEvidence $fixture) 5 'Corrupt test'
    $corruptState.state = 'RUNNING'; $corruptState.process_id = $PID
    $corruptRecord = [pscustomobject]@{
        schema = 1
        controller_run_id = $corruptState.run_id
        task_id = $corruptState.task_id
        bootstrap_status = 'COMPLETE'
        scientific_checkpoint = [pscustomobject]@{
            kind = 'PREPARATION_CHECKPOINT'
            exit_code = 0
            artifact = $prepArtifactRel3
            sha256 = '0000000000000000000000000000000000000000000000000000000000000000' # Wrong hash
        }
    }
    Put ('project_coordination/controller/turn-' + $corruptState.run_id + '.json') ($corruptRecord | ConvertTo-Json -Depth 10)
    Assert (-not (Test-ControllerScientificCheckpoint $fixture $corruptState)) 'Corrupted preparation artifact hash rejected'

    # 6. Foreign active session rejection
    Put 'project_coordination/ACTIVE_SESSION.json' '{"active":true,"agent":"codex","task_id":"foreign-job"}'
    $foreignState = New-ControllerTurnState (Get-ControllerEvidence $fixture) 6 'Foreign'
    $foreignState.state = 'RUNNING'; $foreignState.process_id = $PID
    $foreignCheckpoint = Join-Path $fixture 'runtime-foreign.json'
    Write-ControllerCheckpoint $foreignCheckpoint $foreignState
    $argsForeign = @('-NoProfile', '-NonInteractive', '-File', $turnEntry, '-Stage', 'Bootstrap', '-Workspace', $fixture, '-RunId', $foreignState.run_id, '-TaskId', $foreignState.task_id, '-RuntimeCheckpoint', $foreignCheckpoint)
    $r = Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList $argsForeign -WorkingDirectory $fixture -TimeoutSeconds 15
    Assert ($r.ExitCode -ne 0 -and $r.Output -match 'Another agent owns the project session') 'Foreign active session correctly blocks new turn bootstrap'

    "ALL $script:checks CONTINUOUS RESEARCH & SAFETY CHECKS PASSED"
} finally {
    if (Test-Path -LiteralPath $fixture) {
        Remove-Item -LiteralPath $fixture -Recurse -Force -ErrorAction SilentlyContinue
    }
}
