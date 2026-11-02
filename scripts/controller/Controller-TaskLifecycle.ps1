# Parent tasks and bounded preparation checkpoints have separate lifecycles.
function Test-ControllerTaskTerminalStatus([string]$Status) {
    if($Status -in @('PREPARATION_COMPLETE','RESEARCH_PREPARATION_COMPLETE','bounded_step_complete')){return $false}
    return $Status -match '(?i)(^complete$|completed|classified|closed|^done$)'
}

function Get-ControllerTaskLifecycle([string]$Workspace) {
    $path=Join-Path $Workspace 'project_coordination/ACTIVE_TASK.json'
    $task=Get-Content -LiteralPath $path -Raw|ConvertFrom-Json
    $ledger=Join-Path $Workspace 'project_coordination/TASK_LEDGER.csv'
    $rows=if(Test-Path -LiteralPath $ledger){@(Import-Csv -LiteralPath $ledger)}else{@()}
    $exact=@($rows|Where-Object {$_.task_id -ceq $task.task_id})
    $closed=@($exact|Where-Object {$_.status -match '^(?i:complete|completed|closed|done)$'})
    # Any historical exact closure is irreversible. A later active row cannot reopen it.
    $terminal=(Test-ControllerTaskTerminalStatus $task.status) -or $closed.Count -gt 0 -or $task.lifecycle.state -eq 'COMPLETED_AWAITING_SUCCESSOR'
    $successor='';$reason=''
    if($terminal){
        $links=@($task.successor_task_id)+@($closed|ForEach-Object next_task)
        $valid=@()
        foreach($link in ($links|Where-Object {$_}|Select-Object -Unique)){
            # Only exact existing task IDs qualify; prose and prefix matches do not.
            if($link -ceq $task.task_id){continue}
            $candidate=@($rows|Where-Object {$_.task_id -ceq $link})
            if(-not $candidate.Count){continue}
            if(@($candidate|Where-Object {$_.status -match '^(?i:complete|completed|closed|done)$'}).Count){continue}
            $last=$candidate[-1]
            if(Test-ControllerTaskTerminalStatus $last.status){continue}
            if($last.status -notmatch '^(?i:ready(?:_|$)|active$|in_progress$|pending$|queued$|blocked(?:_|$))'){continue}
            $valid+=$link
        }
        $valid=@($valid|Select-Object -Unique)
        if($valid.Count -eq 1){$successor=$valid[0]}elseif($valid.Count -gt 1){$reason='Conflicting recorded successors; reconciliation required'}
        else{$reason='No exact existing open successor task is recorded; never synthesize one from next-action prose'}
    }
    [pscustomobject]@{task_id=$task.task_id;task_status=$task.status;terminal=[bool]$terminal;
        preparation_is_terminal=$false;ledger_available=(Test-Path -LiteralPath $ledger);
        state=$(if($terminal){'COMPLETED_AWAITING_SUCCESSOR'}else{'ACTIVE'});
        next_authoritative_task=$(if($terminal){if($successor){$successor}else{$null}}else{$task.task_id});
        dispatch_ready=(!$terminal -and (Test-Path -LiteralPath $ledger));
        transition=$(if($terminal -and $successor){'SELECT_RECORDED_SUCCESSOR'}elseif($terminal){'SUCCESSOR_REQUIRED'}else{'CONTINUE_ACTIVE_TASK'});
        reason=$reason;task_sha256=(Get-FileHash -LiteralPath $path).Hash;
        ledger_sha256=$(if(Test-Path -LiteralPath $ledger){(Get-FileHash -LiteralPath $ledger).Hash})}
}

function Assert-ControllerTaskLifecycle([string]$Workspace) {
    $life=Get-ControllerTaskLifecycle $Workspace
    if($life.terminal){throw ('COMPLETED_TASK_REJECTED: '+$life.task_id+'; '+$life.transition+'; '+$life.reason)}
    if(-not $life.ledger_available){throw 'TASK_LIFECYCLE_LEDGER_MISSING'}
    $registration=Get-ControllerTaskRegistrationPlan $Workspace
    if(-not $registration.dispatch_ready){throw ('TASK_REGISTRATION_REJECTED: '+$registration.reason)}
}

function Get-ControllerTaskRegistrationPlan([string]$Workspace) {
    $task=Get-Content -LiteralPath (Join-Path $Workspace 'project_coordination/ACTIVE_TASK.json') -Raw|ConvertFrom-Json
    if(-not $task.registration){
        $ledger=Join-Path $Workspace 'project_coordination/TASK_LEDGER.csv'
        if(Test-Path -LiteralPath $ledger){
            $registered=@(Import-Csv -LiteralPath $ledger|Where-Object {$_.task_id -ceq $task.task_id -and $_.classification -eq 'REGISTERED_NOT_EXECUTED'})
            if($registered.Count){return [pscustomobject]@{status='TASK_REGISTRATION_BLOCKED';dispatch_ready=$false;reason='Registered successor cannot become legacy by removing its definition binding'}}
        }
        return [pscustomobject]@{status='LEGACY_TASK';dispatch_ready=$true;reason='Existing task has no successor registration'}
    }
    try {
        $rel=[string]$task.registration.definition
        if($rel -notmatch '^project_coordination/task_definitions/[A-Za-z0-9_-]+\.json$'){throw 'Unsafe task definition path'}
        $path=Join-Path $Workspace $rel
        if(-not(Test-Path -LiteralPath $path) -or (Get-FileHash -LiteralPath $path).Hash -cne $task.registration.sha256){throw 'Task definition missing or changed'}
        $d=Get-Content -LiteralPath $path -Raw|ConvertFrom-Json
        if($d.schema -ne 1 -or $d.task_id -cne $task.task_id -or $d.predecessor.task_id -cne $task.predecessor_task.task_id){throw 'Task/predecessor definition mismatch'}
        $rows=@(Import-Csv -LiteralPath (Join-Path $Workspace 'project_coordination/TASK_LEDGER.csv'))
        if(@($rows|Where-Object {$_.task_id -ceq $d.task_id}).Count -ne 1){throw 'Duplicate or missing task registration'}
        if(-not @($rows|Where-Object {$_.task_id -ceq $d.predecessor.task_id -and $_.status -match '^(?i:complete|completed|closed|done)$'}).Count){throw 'Predecessor is not closed'}
        if($d.operation.id -cne 'research_preparation' -or $d.operation.mode -cne 'READ_ONLY_SCIENTIFIC_EVALUATION' -or $d.max_new_pbs_submissions -ne 0 -or $task.scientific_operation -or $task.scientific_operation_id -cne 'research_preparation' -or -not $task.scientific_checkpoint_required){throw 'Successor definition is not the bounded evidence-evaluation operation'}
        foreach($op in $d.inherited_completed_operations){if($op -cnotin @($task.completed_operations)){throw 'Completed-operation accounting was lost'}}
        foreach($pin in $d.evidence_sources.PSObject.Properties){
            if($pin.Name -match '(?:^[/\\]|\.\.)'){throw 'Unsafe evidence path'}
            $p=Join-Path $Workspace $pin.Name
            if(-not(Test-Path -LiteralPath $p) -or (Get-FileHash -LiteralPath $p).Hash -cne $pin.Value){throw ('Task evidence changed: '+$pin.Name)}
        }
        return [pscustomobject]@{status='REGISTERED_READ_ONLY_EVALUATION';dispatch_ready=$true;reason='No numerical execution qualification conferred';definition=$d}
    }catch{return [pscustomobject]@{status='TASK_REGISTRATION_BLOCKED';dispatch_ready=$false;reason=$_.Exception.Message}}
}

function Get-ControllerSuccessorCheckpointPlan([string]$Workspace,[string]$CheckpointPath,$State) {
    $task=Get-Content -LiteralPath (Join-Path $Workspace 'project_coordination/ACTIVE_TASK.json') -Raw|ConvertFrom-Json
    if(-not $State -or $State.task_id -ceq $task.task_id){return [pscustomobject]@{fresh_successor=$false}}
    if($State.state -cne 'COMPLETED'){throw 'SUCCESSOR_CHECKPOINT_BLOCKED: foreign nonterminal checkpoint requires reconciliation'}
    Assert-ControllerTaskLifecycle $Workspace
    $r=Get-ControllerTaskRegistrationPlan $Workspace
    if(-not $r.definition -or $r.definition.predecessor.task_id -cne $State.task_id -or
        $r.definition.predecessor.run_id -cne $State.run_id -or
        (Get-FileHash -LiteralPath $CheckpointPath).Hash -cne $r.definition.predecessor.checkpoint_sha256){throw 'SUCCESSOR_CHECKPOINT_BLOCKED: completed predecessor binding missing or changed'}
    return [pscustomobject]@{fresh_successor=$true;instruction=$r.definition.initial_instruction;predecessor_run_id=$State.run_id}
}

function Set-ControllerPreparationStepStatus($Task,[string]$Status) {
    # An artifact's PASSED/PREPARATION_COMPLETE is not a parent-task transition.
    if(Test-ControllerTaskTerminalStatus $Task.status){throw ('COMPLETED_TASK_REJECTED: '+$Task.task_id)}
    $Task|Add-Member -NotePropertyName last_step_status -NotePropertyValue $Status -Force
    if($Task.status -in @('PREPARATION_COMPLETE','RESEARCH_PREPARATION_COMPLETE')){$Task.status='ACTIVE'}
    return $Task
}
