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
}

function Set-ControllerPreparationStepStatus($Task,[string]$Status) {
    # An artifact's PASSED/PREPARATION_COMPLETE is not a parent-task transition.
    if(Test-ControllerTaskTerminalStatus $Task.status){throw ('COMPLETED_TASK_REJECTED: '+$Task.task_id)}
    $Task|Add-Member -NotePropertyName last_step_status -NotePropertyValue $Status -Force
    if($Task.status -in @('PREPARATION_COMPLETE','RESEARCH_PREPARATION_COMPLETE')){$Task.status='ACTIVE'}
    return $Task
}
