# Bridge text is a proposal, never code or an execution permission.
function Get-ControllerPreparationPlan([string]$Workspace,[string]$Instruction) {
    $task=Get-Content -LiteralPath (Join-Path $Workspace 'project_coordination/ACTIVE_TASK.json') -Raw -Encoding UTF8|ConvertFrom-Json
    if(-not $task.scientific_checkpoint_required){
        return [pscustomobject]@{status='READY';dispatch_ready=$true;task_type='GENERAL_RESEARCH';operation_id='';path='';blocked_on=@();recipe=''}
    }
    if($task.scientific_operation){
        try{
            $op=Resolve-ControllerOperation $task $Workspace
            return [pscustomobject]@{status='READY';dispatch_ready=$true;task_type='QUALIFIED_EXECUTION';operation_id=$op.id;path=$op.path;blocked_on=@();recipe='qualified-execution'}
        }catch{
            return [pscustomobject]@{status='DEFINITION_REJECTED';dispatch_ready=$false;task_type='REJECTED';operation_id='';path='';blocked_on=@($_.Exception.Message);recipe=''}
        }
    }
    # Unsafe proposal rejection
    if($Instruction -match '(?i)(change formulation and execute arbitrary|arbitrary commands|destructive|bypass qualification|qdel|qmove|rm -rf)'){
        return [pscustomobject]@{status='DEFINITION_REJECTED';dispatch_ready=$false;task_type='REJECTED';operation_id='';path='';blocked_on=@('Unreviewed proposal rejected; safety guard enforced');recipe=''}
    }
    # Replay rejection: check if instruction attempts to replay a completed task
    if($task.completed_operations){
        foreach($comp in $task.completed_operations){
            if($Instruction -match ('\b'+[regex]::Escape($comp)+'\b') -and $Instruction -match '(?i)(run|execute|replay|repeat)'){
                return [pscustomobject]@{status='DEFINITION_REJECTED';dispatch_ready=$false;task_type='REJECTED';operation_id='';path='';blocked_on=@('COMPLETED_OPERATION_REJECTED: completed operation will not replay');recipe=''}
            }
        }
    }
    # Check for historical specific F1597 trace recipe
    $knownNext='Review the measured mechanical/history discrepancy and obtain an authentic UEL call trace before choosing a coupled transfer correction.'
    $matchesHistoricalF1597=([string]::IsNullOrWhiteSpace($Instruction) -or $Instruction -match '(?is)(UEL.{0,100}(call.?trace|call.?order)|authentic.{0,80}trace|OPERATION_ID:\s*authentic_uel_history_call_trace)')
    if($task.next_safe_action -ceq $knownNext -and @($task.completed_operations) -contains 'mapped_mechanical_history_call_order_probe' -and $matchesHistoricalF1597){
        $relative='models/pandey_kumar_mode1/73_method_c_history_call_trace/PREPARATION.json'
        $receiptPath=Join-Path $Workspace $relative
        $status='PREPARATION_REQUIRED';$block=@('Run the fixed trace-instrumentation preparation recipe and tests; never replay either completed probe.')
        if(Test-Path -LiteralPath $receiptPath){
            $r=Get-Content -LiteralPath $receiptPath -Raw|ConvertFrom-Json
            if($r.operation -ne 'authentic_uel_history_call_trace' -or $r.basis_sha256 -ne $task.scientific_checkpoint.sha256){throw 'Preparation receipt is stale or mismatched'}
            foreach($entry in $r.sources.PSObject.Properties){
                if($entry.Name -notmatch '^(models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/[^/]+|scripts/validation/probe_mode1_f1597_uel_call_trace.py|tests/unit/test_mode1_f1597_uel_call_trace.py)$'){throw 'Unsafe preparation source path'}
                $p=Join-Path $Workspace $entry.Name
                if(-not(Test-Path -LiteralPath $p) -or (Get-FileHash -LiteralPath $p).Hash -ne $entry.Value){throw 'Preparation source changed; requalification required'}
            }
            if($r.instrumented_source -ne 'models/pandey_kumar_mode1/73_method_c_history_call_trace/f42_history_trace_uel.for' -or
                -not(Test-Path -LiteralPath (Join-Path $Workspace $r.instrumented_source)) -or (Get-FileHash -LiteralPath (Join-Path $Workspace $r.instrumented_source)).Hash -ne $r.instrumented_source_sha256){throw 'Instrumentation candidate changed'}
            $status=$r.preparation_status;$block=@($r.blocked_on)
        }
        return [pscustomobject]@{status=$status;dispatch_ready=$false;task_type='RESEARCH_PREPARATION';operation_id='authentic_uel_history_call_trace';path='scripts/validation/probe_mode1_f1597_uel_call_trace.py';blocked_on=$block;recipe='f1597-trace-instrumentation-v1';receipt=$relative}
    }
    # General continuous research preparation path for new scientific tasks from ChatGPT
    return [pscustomobject]@{status='READY';dispatch_ready=$true;task_type='RESEARCH_PREPARATION';operation_id='research_preparation';path='';blocked_on=@();recipe='autonomous-research-preparation';receipt=''}
}

function Invoke-ControllerOperationPreparation([string]$Workspace,[string]$Instruction) {
    $plan=Get-ControllerPreparationPlan $Workspace $Instruction
    if($plan.dispatch_ready -or $plan.status -ne 'PREPARATION_REQUIRED' -or -not $plan.recipe){return $plan}
    $preparationMutex=[Threading.Mutex]::new($false,'Local\AdaptiveRemeshingOperationPreparation')
    $locked=$false
    try{
        try{$locked=$preparationMutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$locked=$true}
        if(-not $locked){throw 'Another operation preparation is active'}
        if(Get-Process agy -ErrorAction SilentlyContinue){throw 'Live AGY process; do not prepare a competing repository operation'}
        # This function is the only automatic recipe. Source and arguments are fixed.
        $sessionPath=Join-Path $Workspace 'project_coordination/ACTIVE_SESSION.json'
        $owner=Get-Content -LiteralPath $sessionPath -Raw|ConvertFrom-Json
        if($owner.active){throw 'Preparation cannot edit inside another active session'}
        $null=& git -C $Workspace status --short
        $null=& git -C $Workspace rev-parse HEAD
        $null=& git -C $Workspace log -1 --oneline
        foreach($relative in @('project_coordination/START_HERE.md','project_coordination/CURRENT_STATE.md','project_coordination/ACTIVE_SESSION.json','project_coordination/ACTIVE_TASK.json','project_coordination/TASK_LEDGER.csv','project_coordination/HPC_JOB_LEDGER.csv','project_coordination/ARTIFACT_REGISTRY.csv','docs/project/PROJECT_PHASE_CHECKLIST.md')){$null=Get-Content -LiteralPath (Join-Path $Workspace $relative) -Raw}
        if((& git -C $Workspace diff --cached --name-only)){throw 'Preserve pre-existing staged work before preparation'}
        $originalOwner=[IO.File]::ReadAllBytes($sessionPath)
        $scope=@('project_coordination/ACTIVE_TASK.json','project_coordination/ACTIVE_SESSION.json','project_coordination/ARTIFACT_REGISTRY.csv','project_coordination/TASK_LEDGER.csv','project_coordination/sessions/2026-10-20_controller_trace_preparation.md','models/pandey_kumar_mode1/73_method_c_history_call_trace/PREPARATION.json','models/pandey_kumar_mode1/73_method_c_history_call_trace/f42_history_trace_uel.for')
        $dirtyTargets=& git -C $Workspace status --porcelain -- @scope
        if($dirtyTargets){throw 'Preparation targets contain pre-existing dirty work; preserve and reconcile before generation'}
        $claim=[ordered]@{active=$true;agent='gemini-antigravity';task_id='F1597-TRACE-PREPARATION';starting_commit=(& git -C $Workspace rev-parse HEAD).Trim();claimed_at=[datetimeoffset]::Now.ToString('o');allowed_write_scope=$scope}
        [IO.File]::WriteAllText($sessionPath,($claim|ConvertTo-Json -Depth 8))
        try{
            . (Join-Path $Workspace 'scripts/validation/Invoke-BoundedAgyProcess.ps1')
            $python=(Get-Command python.exe).Source
            $tests=Invoke-BoundedAgyProcess -FilePath $python -ArgumentList @('-m','unittest','discover','-s',(Join-Path $Workspace 'tests/unit'),'-p','test_mode1_f1597_uel_call_trace.py') -WorkingDirectory $Workspace -TimeoutSeconds 45
            if($tests.ExitCode -ne 0 -or $tests.Output -notmatch 'Ran [1-9]\d* tests'){throw 'Fixed trace recipe unit qualification failed'}
            $r=Invoke-BoundedAgyProcess -FilePath $python -ArgumentList @((Join-Path $Workspace 'scripts/validation/probe_mode1_f1597_uel_call_trace.py'),'--workspace',$Workspace,'--output',(Join-Path $Workspace $plan.receipt),'--prepare') -WorkingDirectory $Workspace -TimeoutSeconds 30
            if($r.ExitCode -ne 0){throw ('Trace recipe failed: '+$r.Output)}
            $plan=Get-ControllerPreparationPlan $Workspace $Instruction
            $report=Join-Path $Workspace 'project_coordination/sessions/2026-10-20_controller_trace_preparation.md'
            [IO.File]::WriteAllText($report,("# Deterministic trace preparation`n`nNot a scientific checkpoint. Completed probes were not executed.`n`n"+($plan|ConvertTo-Json -Depth 8).Replace("`r`n","`n")+"`n"))
            $taskPath=Join-Path $Workspace 'project_coordination/ACTIVE_TASK.json'
            $task=Get-Content -LiteralPath $taskPath -Raw|ConvertFrom-Json
            $task|Add-Member -NotePropertyName operation_preparation -NotePropertyValue $plan -Force
            [IO.File]::WriteAllText($taskPath,(($task|ConvertTo-Json -Depth 30).Replace("`r`n","`n")))
            $registry=Join-Path $Workspace 'project_coordination/ARTIFACT_REGISTRY.csv'
            foreach($relative in @($plan.receipt,'models/pandey_kumar_mode1/73_method_c_history_call_trace/f42_history_trace_uel.for','project_coordination/sessions/2026-10-20_controller_trace_preparation.md')){
                $row=[pscustomobject]@{artifact_id=('F1597-PREPARATION-'+[IO.Path]::GetFileName($relative));stage='Controller';canonical_path=$relative;type='technical_preparation';status='not_executable';created_by='controller';source_commit=$claim.starting_commit;sha256=(Get-FileHash -LiteralPath (Join-Path $Workspace $relative)).Hash;supersedes='';notes='Technical qualification incomplete; no scientific result or submission'}
                $csv=$row|ConvertTo-Csv -NoTypeInformation
                [IO.File]::AppendAllText($registry,$csv[1]+"`n")
            }
            $row=[pscustomobject]@{task_id='F1597-TRACE-PREPARATION';stage='Controller';title='Bounded tracing instrumentation prepared';status='technical_qualification_required';agent='controller';base_commit=$claim.starting_commit;result_commit='';write_scope=($scope -join ';');job_id='';classification='NOT_SCIENTIFIC_PROGRESS';next_task=($plan.blocked_on -join ';');updated_at=[datetimeoffset]::Now.ToString('o')}
            $csv=$row|ConvertTo-Csv -NoTypeInformation
            [IO.File]::AppendAllText((Join-Path $Workspace 'project_coordination/TASK_LEDGER.csv'),$csv[1]+"`n")
        } finally {
            [IO.File]::WriteAllBytes($sessionPath,$originalOwner)
        }
        # Governed candidate files are synchronized without touching a dirty bridge prompt.
        if((& git -C $Workspace diff --cached --name-only)){throw 'Pre-existing staged changes preserved; preparation requires selective synchronization'}
        $generated=@('project_coordination/ACTIVE_TASK.json','project_coordination/ARTIFACT_REGISTRY.csv','project_coordination/TASK_LEDGER.csv',$plan.receipt,'models/pandey_kumar_mode1/73_method_c_history_call_trace/f42_history_trace_uel.for','project_coordination/sessions/2026-10-20_controller_trace_preparation.md')
        & git -C $Workspace add -- @generated | Out-Host
        if($LASTEXITCODE -ne 0){throw 'Preparation staging failed'}
        & git -C $Workspace diff --cached --check | Out-Host
        if($LASTEXITCODE -ne 0){throw 'Preparation staged validation failed'}
        & git -C $Workspace commit -m 'controller: preserve bounded trace preparation with unresolved technical qualification' | Out-Host
        if($LASTEXITCODE -ne 0){throw 'Preparation commit failed'}
        & git -C $Workspace push origin HEAD:main HEAD:mode2-pandey-kumar-reproduction | Out-Host
        if($LASTEXITCODE -ne 0){throw 'Preparation forward push failed'}
        return $plan
    }finally{if($locked){$preparationMutex.ReleaseMutex()};$preparationMutex.Dispose()}
}
