$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. "$repo/scripts/controller/Controller-Recovery.ps1"
. "$repo/scripts/validation/Invoke-BoundedAgyProcess.ps1"
$fixture=Join-Path $env:TEMP ('agy-bootstrap-test-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$fixture/project_coordination/sessions","$fixture/scripts/controller","$fixture/scripts/validation","$fixture/docs/project" -Force|Out-Null
function Put($Name,$Text){[IO.File]::WriteAllText((Join-Path $fixture $Name),$Text)}
$script:checks=0
function Assert($Value,$Message){if(-not $Value){throw "FAIL: $Message"};$script:checks++;"PASS $script:checks`: $Message"}
try{
    foreach($relative in @('scripts/controller/Controller-Recovery.ps1','scripts/controller/Controller-Operations.ps1','scripts/controller/Controller-Qualification.ps1','scripts/validation/probe_mode1_f1597_mechanical_history.py','scripts/validation/Invoke-BoundedAgyProcess.ps1','scripts/validation/probe_mode1_f1597_kkt.py')){
        Copy-Item -LiteralPath (Join-Path $repo $relative) -Destination (Join-Path $fixture $relative)
    }
    foreach($relative in @('AGENTS.md','project_coordination/START_HERE.md','project_coordination/CURRENT_STATE.md','docs/project/PROJECT_PHASE_CHECKLIST.md')){Put $relative 'Required prerequisite fixture, not a scientific finding.'}
    Put 'project_coordination/ACTIVE_SESSION.json' '{"active":false,"agent":"codex","task_id":"prior"}'
    Put 'project_coordination/ACTIVE_TASK.json' '{"task_id":"F1597-CORRECT-PACKAGE72-STATE-TRANSFER","status":"READY_OFFLINE_MECHANICAL_HISTORY_PROBE","scientific_checkpoint_required":true,"scientific_operation":"scripts/validation/probe_mode1_f1597_mechanical_history.py","completed_operations":["mapped_frozen_history_lower_bound_kkt_probe"],"phase":"Measure mapped-state KKT feasibility before correcting transfer"}'
    Put 'project_coordination/TASK_LEDGER.csv' "task_id,status`nF1596-AUDIT,complete"
    Put 'project_coordination/HPC_JOB_LEDGER.csv' "job_id,status`n1415199.mmaster02,completed"
    Put 'project_coordination/MODE1_EXECUTION_LEDGER.json' '{"reserved":1}'
    Put 'project_coordination/ARTIFACT_REGISTRY.csv' 'artifact_id,canonical_path'
    $git=(Get-Command git.exe).Source
    foreach($args in @(@('init'),@('config','user.name','Fixture'),@('config','user.email','fixture@example.invalid'),@('add','AGENTS.md'),@('commit','-m','fixture'))){
        $r=Invoke-BoundedAgyProcess -FilePath $git -ArgumentList (@('-C',$fixture)+$args) -WorkingDirectory $fixture -TimeoutSeconds 15
        if($r.ExitCode -ne 0){throw $r.Output}
    }
    $state=New-ControllerTurnState (Get-ControllerEvidence $fixture) 1 'F1597 controlled probe'
    $state.state='RUNNING';$state.process_id=$PID
    $checkpoint=Join-Path $fixture 'runtime.json';Write-ControllerCheckpoint $checkpoint $state
    $entry=Join-Path $repo 'scripts/controller/Invoke-ControllerTurn.ps1'
    $args=@('-NoProfile','-NonInteractive','-File',$entry,'-Stage','Bootstrap','-Workspace',$fixture,'-RunId',$state.run_id,'-TaskId',$state.task_id,'-RuntimeCheckpoint',$checkpoint)
    $originalTask=[IO.File]::ReadAllText((Join-Path $fixture 'project_coordination/ACTIVE_TASK.json'))
    Put 'project_coordination/ACTIVE_TASK.json' ($originalTask.Replace('probe_mode1_f1597_mechanical_history.py','probe_mode1_f1597_kkt.py'))
    $rejected=$false;try{$null=Resolve-ControllerInstruction $fixture '# F1597 retired operation'}catch{$rejected=$_.Exception.Message -match 'UNQUALIFIED_OR_RETIRED_OPERATION'}
    Assert $rejected 'completed KKT path rejected by pre-model instruction resolution'
    $r=Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList $args -WorkingDirectory $fixture -TimeoutSeconds 45
    Assert ($r.ExitCode -ne 0 -and $r.Output -match 'UNQUALIFIED_OR_RETIRED_OPERATION' -and -not(Test-Path -LiteralPath $state.bootstrap_record_path)) 'direct Bootstrap rejects retired KKT before claim or numerical execution'
    Put 'project_coordination/ACTIVE_TASK.json' $originalTask
    $r=Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList $args -WorkingDirectory $fixture -TimeoutSeconds 45
    Assert ($r.ExitCode -eq 0 -and $r.Output -match 'BOOTSTRAP_COMPLETE') ('canonical -File bootstrap reads prerequisites and claims session: '+$r.Output.Substring(0,[Math]::Min(120,$r.Output.Length)))
    $record=Get-Content -LiteralPath $state.bootstrap_record_path -Raw|ConvertFrom-Json
    Assert ($record.bootstrap_status -eq 'COMPLETE' -and @($record.ordered_sources.PSObject.Properties).Count -eq 9) 'ordered prerequisite receipt records nine source hashes once'
    $owner=Get-Content -LiteralPath "$fixture/project_coordination/ACTIVE_SESSION.json" -Raw|ConvertFrom-Json
    Assert ($owner.allowed_write_scope -contains ('results/validation/mode1_f1597/'+$state.run_id+'.json')) 'claimed write scope contains exact artifact paths, not split string fragments'
    $before=(Get-FileHash -LiteralPath "$fixture/project_coordination/ACTIVE_SESSION.json").Hash
    $r=Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList $args -WorkingDirectory $fixture -TimeoutSeconds 45
    Assert ($r.ExitCode -eq 0 -and $r.Output -match 'BOOTSTRAP_ALREADY_COMPLETE' -and (Get-FileHash -LiteralPath "$fixture/project_coordination/ACTIVE_SESSION.json").Hash -eq $before) 'unchanged bootstrap is idempotent and does not reclaim session'
    $r=Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList $args -WorkingDirectory $fixture -TimeoutSeconds 45
    Assert ($r.ExitCode -eq 0 -and $r.Output -match 'BOOTSTRAP_ALREADY_COMPLETE' -and (Get-FileHash -LiteralPath "$fixture/project_coordination/ACTIVE_SESSION.json").Hash -eq $before) 'repeated unchanged bootstrap remains idempotent and preserves session claim'
    Update-ControllerEvidence $fixture $checkpoint $state
    Assert (-not(Test-ControllerDurableProgress $state)) 'generic bootstrap status report does not count as scientific progress'
    # Stream output is telemetry. Normal PowerShell commands must not kill an active AGY turn.
    $state.live_buffer='';$state.stop_reason=''
    $commands=@('powershell.exe -NoProfile -NonInteractive -Command "git status --short; git log -3 --oneline"', 'powershell.exe -NoProfile -Command "Get-Content project_coordination/ACTIVE_SESSION.json"')
    foreach($command in $commands){
        $streamEvent=@{event='step_update';step_update=@{step_index=4;step_type='tool';state='ACTIVE';tool_info=@{parameters=@{CommandLine=$command}}}}|ConvertTo-Json -Depth 8 -Compress
        Write-ControllerStreamEvent $state ($streamEvent+"`n")
    }
    Assert (-not $state.stop_reason -and $state.bootstrap_repeat_reads -eq 0) 'AGY telemetry cannot reject ordinary git status or file inspection commands'
    $controllerSource=[IO.File]::ReadAllText((Join-Path $repo 'scripts/controller/Antigravity-Autonomous-Loop.ps1'))
    Assert ($controllerSource.Contains('scientific inactivity cutoff disabled') -and $controllerSource.Contains('-NoProgressSeconds $watchdogSeconds') -and $controllerSource.Contains('$hardTimeout = $controllerBudget.work')) 'scientific inactivity cutoff removed, finite hard deadline preserved'
    $failed=$false;try{$null=Resolve-ControllerInstruction $fixture '# F1596: run audit again'}catch{$failed=$_.Exception.Message -match 'COMPLETED_TASK_REJECTED'}
    Assert $failed 'closed predecessor rejected even when authoritative active task is F1597'
    Assert (-not(Test-ControllerScientificCheckpoint $fixture $state)) 'no measurement artifact means no verified checkpoint'
    $inputs=@('models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for','models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/M1_EXP_COUPLED_TRANSFER_650.inp','models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/offset_state_table.csv','models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/f42_experimental_offset_uel.for')
    foreach($relative in $inputs){New-Item -ItemType Directory -Path (Split-Path (Join-Path $fixture $relative)) -Force|Out-Null;Put $relative 'Synthetic validator fixture only; never scientific evidence'}
    New-Item -ItemType Directory -Path "$fixture/results/validation/mode1_f1597" -Force|Out-Null
    $basis='results/validation/mode1_f1597/00000000-0000-0000-0000-000000000000.json'
    Put $basis '{}'
    $state.scientific_basis_artifact=$basis
    $state.sources=(Get-ControllerEvidence $fixture).sources
    $state.sources[$basis]=(Get-FileHash -LiteralPath (Join-Path $fixture $basis)).Hash
    $sources=[ordered]@{}
    foreach($relative in ($inputs+@('scripts/validation/probe_mode1_f1597_kkt.py','scripts/validation/probe_mode1_f1597_mechanical_history.py',$basis))){$sources[$relative]=(Get-FileHash -LiteralPath (Join-Path $fixture $relative)).Hash}
    $artifact='results/validation/mode1_f1597/'+$state.run_id+'.json'
    New-Item -ItemType Directory -Path (Split-Path (Join-Path $fixture $artifact)) -Force|Out-Null
    $measurements=@{phase_elements=1;phase_nodes=4;free_mechanical_dofs=2;mechanical_free_residual_inf_kN=0;worst_mechanical_node=2;worst_mechanical_dof=1;mapped_displacement_jump_mm=0;mapped_damage_jump=0;history_increase_inf_kN_mm2=0;phase_before_mechanical_inf_kN=0;phase_after_mechanical_inf_kN=0;phase_call_order_delta_inf_kN=0;committed_before_accept_error=0;retry_restore_error=0;accepted_commit_error=0;mechanical_fd_relative_error=0;prior_kkt_residual_difference_kN=0}
    Put $artifact (@{task_id='F1597';operation='mapped_mechanical_history_call_order_probe';test_fixture_only=$true;verification_passed=$true;measurements=$measurements;tolerances=@{history_kN_mm2=1e-10;residual_kN=1e-10;fd_relative=1e-7;mapping_mm=1e-10;transaction=1e-14};first_verified_discrepancy=@{classification='NONE_ABOVE_DECLARED_TOLERANCES'};sources=$sources}|ConvertTo-Json -Depth 10)
    $record=Get-Content -LiteralPath $state.bootstrap_record_path -Raw|ConvertFrom-Json
    $record.scientific_checkpoint=[pscustomobject]@{kind='NUMERICAL_FINDING';operation='mapped_mechanical_history_call_order_probe';exit_code=0;artifact=$artifact;sha256=(Get-FileHash -LiteralPath (Join-Path $fixture $artifact)).Hash}
    Put ('project_coordination/controller/turn-'+$state.run_id+'.json') ($record|ConvertTo-Json -Depth 20)
    Assert (Test-ControllerScientificCheckpoint $fixture $state) 'typed numerical checkpoint validates all pinned source/artifact hashes'
    Assert (Test-ControllerDurableProgress $state) 'verified numerical checkpoint advances the scientific progress clock'
    $baseline=[IO.File]::ReadAllText((Join-Path $fixture $artifact))
    foreach($variant in @('missing-measurement','invalid-gradient','retired-artifact')){
        $data=$baseline|ConvertFrom-Json
        if($variant -eq 'missing-measurement'){$data.measurements.PSObject.Properties.Remove('mechanical_free_residual_inf_kN')}
        if($variant -eq 'invalid-gradient'){$data.measurements.mechanical_fd_relative_error=1.0}
        if($variant -eq 'retired-artifact'){$data.operation='mapped_frozen_history_lower_bound_kkt_probe'}
        Put $artifact ($data|ConvertTo-Json -Depth 20)
        $record.scientific_checkpoint.sha256=(Get-FileHash -LiteralPath (Join-Path $fixture $artifact)).Hash
        Put ('project_coordination/controller/turn-'+$state.run_id+'.json') ($record|ConvertTo-Json -Depth 20)
        Assert (-not(Test-ControllerScientificCheckpoint $fixture $state)) ("rehashed $variant fails scientific validation")
    }
    Put $artifact $baseline
    $record.scientific_checkpoint.sha256=(Get-FileHash -LiteralPath (Join-Path $fixture $artifact)).Hash
    Put ('project_coordination/controller/turn-'+$state.run_id+'.json') ($record|ConvertTo-Json -Depth 20)

    [IO.File]::AppendAllText((Join-Path $fixture $artifact),'tampered')
    Assert (-not(Test-ControllerScientificCheckpoint $fixture $state)) 'modified evidence cannot count as scientific progress'
    # Full canonical Bootstrap -> Scientific -> Complete contract on one manufactured
    # quad and an isolated bare Git remote. Never use actual Package72 solver results.
    Copy-Item -LiteralPath "$repo/models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for" -Destination "$fixture/models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
    Copy-Item -LiteralPath "$repo/models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/f42_experimental_offset_uel.for" -Destination "$fixture/models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/f42_experimental_offset_uel.for"
    Put 'models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/M1_EXP_COUPLED_TRANSFER_650.inp' "*Node`n1,0,0`n2,1,0`n3,1,1`n4,0,1`n*Element,type=U1,elset=PHASE_QUADS`n1,1,2,3,4`n*UEL PROPERTY,ELSET=PHASE_QUADS`n0.1,0.2,210,0.3,1e-7,1`n*Nset,nset=N_BOTTOM`n1,2`n*Nset,nset=N_PIN`n1`n*Nset,nset=N_TOP`n3,4`n*Nset,nset=N_RP`n999999`n*EQUATION`n2`n3,2,1.0,999999,2,-1.0`n*EQUATION`n2`n4,2,1.0,999999,2,-1.0`n*Boundary`nN_BOTTOM,2,2,0.0`nN_PIN,1,1,0.0`nN_TOP,1,1,0.0`nN_RP,2,2,0.0`n"
    Put 'models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/offset_state_table.csv' "1,0,0,0,0,0,0,0,0,0.1,0.1,0.1,0.1,0.3,0.3,0.3,0.3`n"
    Put 'project_coordination/ACTIVE_SESSION.json' '{"active":false,"agent":"codex","task_id":"prior"}'
    $remote=Join-Path $fixture 'remote.git'
    foreach($gitArgs in @(@('init','--bare',$remote),@('-C',$fixture,'remote','add','origin',$remote))){
        $r=Invoke-BoundedAgyProcess -FilePath $git -ArgumentList $gitArgs -WorkingDirectory $fixture -TimeoutSeconds 15
        if($r.ExitCode -ne 0){throw $r.Output}
    }
    $basisSources=[ordered]@{}
    foreach($relative in ($inputs+@('scripts/validation/probe_mode1_f1597_kkt.py'))){$basisSources[$relative]=(Get-FileHash -LiteralPath (Join-Path $fixture $relative)).Hash}
    Put $basis (@{task_id='F1597';operation='mapped_frozen_history_lower_bound_kkt_probe';verification_passed=$true;measurements=@{phase_residual_inf_kN=0.085};sources=$basisSources}|ConvertTo-Json -Depth 10)
    $t=Get-Content -LiteralPath "$fixture/project_coordination/ACTIVE_TASK.json" -Raw|ConvertFrom-Json
    $t|Add-Member scientific_checkpoint ([pscustomobject]@{artifact=$basis;sha256=(Get-FileHash -LiteralPath (Join-Path $fixture $basis)).Hash}) -Force
    Put 'project_coordination/ACTIVE_TASK.json' ($t|ConvertTo-Json -Depth 10)
    $state=New-ControllerTurnState (Get-ControllerEvidence $fixture) 1 'manufactured full contract'
    $state.state='RUNNING';$state.process_id=$PID;Write-ControllerCheckpoint $checkpoint $state
    foreach($stage in @('Bootstrap','Scientific','Complete')){
        $arguments=@('-NoProfile','-NonInteractive','-File',$entry,'-Stage',$stage,'-Workspace',$fixture,'-RunId',$state.run_id,'-TaskId',$state.task_id,'-RuntimeCheckpoint',$checkpoint)
        $r=Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList $arguments -WorkingDirectory $fixture -TimeoutSeconds 45
        Assert ($r.ExitCode -eq 0) ("canonical manufactured stage $stage exits cleanly: "+$r.Output.Substring(0,[Math]::Min(180,$r.Output.Length)))
    }
    $beforeTask=(Get-FileHash -LiteralPath "$fixture/project_coordination/ACTIVE_TASK.json").Hash
    $beforeLedger=(Get-FileHash -LiteralPath "$fixture/project_coordination/TASK_LEDGER.csv").Hash
    $r=Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList $arguments -WorkingDirectory $fixture -TimeoutSeconds 30
    Assert ($r.ExitCode -eq 0 -and $r.Output -match 'TURN_ALREADY_COMPLETE' -and (Get-FileHash -LiteralPath "$fixture/project_coordination/ACTIVE_TASK.json").Hash -eq $beforeTask -and (Get-FileHash -LiteralPath "$fixture/project_coordination/TASK_LEDGER.csv").Hash -eq $beforeLedger) 'repeated Complete is idempotent and cannot advance or append twice'
    Assert (Test-ControllerScientificCheckpoint $fixture $state) 'canonical runner creates a source-verified numerical checkpoint'
    $task=Get-Content -LiteralPath "$fixture/project_coordination/ACTIVE_TASK.json" -Raw|ConvertFrom-Json
    $owner=Get-Content -LiteralPath "$fixture/project_coordination/ACTIVE_SESSION.json" -Raw|ConvertFrom-Json
    Assert (-not $owner.active -and $task.status -eq 'F1597_MECHANICAL_HISTORY_DIAGNOSTIC_VERIFIED_CORRECTION_PENDING' -and @($task.completed_operations).Count -eq 2) 'controlled closeout releases the session and advances correction step without claiming transfer qualification'
    $r=Invoke-BoundedAgyProcess -FilePath $git -ArgumentList @('-C',$fixture,'rev-parse','HEAD','origin/main') -TimeoutSeconds 15
    $refs=@($r.Output.Trim() -split '\r?\n')
    Assert ($refs.Count -eq 2 -and $refs[0] -eq $refs[1]) 'canonical closeout selectively commits and forward-pushes to fixture origin/main'
    $advance=$false;try{$res=Resolve-ControllerInstruction $fixture '# F1597 correction';$advance=($res.task_type -eq 'RESEARCH_PREPARATION' -and -not $res.operation)}catch{$advance=$_.Exception.Message -match 'NEXT_OPERATION_REQUIRES_DEFINITION'}
    Assert $advance 'completed diagnostic cannot silently replay as the next correction task; advances to research preparation'
    'ALL '+$script:checks+' BOOTSTRAP CHECKS PASSED; fixture only'
}finally{"FIXTURE=$fixture"}
