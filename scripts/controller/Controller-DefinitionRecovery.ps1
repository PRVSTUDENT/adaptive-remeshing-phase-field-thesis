# Durable outbox for rejected proposals. This module never executes an operation.
function Get-DefinitionProposalHash([string]$Text) {
    Get-ControllerTextHash (($Text.Trim() -replace '\s+',' ').ToLowerInvariant())
}

function Get-DefinitionRecoveryCatalog([string]$Workspace,$Task) {
    $items=@([pscustomobject]@{id='research_preparation';path='';allowed=(-not $Task.scientific_operation);scope='Existing evidence/definition preparation workflow only; no scientific execution qualification'})
    $paths=@('scripts/validation/probe_mode1_f1597_mechanical_history.py','scripts/validation/probe_mode1_f1597_kkt.py','scripts/validation/probe_mode1_f1597_uel_call_trace.py')
    if($Task.scientific_operation){$paths += [string]$Task.scientific_operation}
    if($Task.operation_preparation.path){$paths += [string]$Task.operation_preparation.path}
    $qualDir=Join-Path $Workspace 'project_coordination/qualifications'
    if(Test-Path -LiteralPath $qualDir){
        foreach($file in Get-ChildItem -LiteralPath $qualDir -File -Filter '*.json'){
            if($file.Length -gt 1048576){continue}
            try{$q=Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8|ConvertFrom-Json;if($q.canonical_path){$paths += [string]$q.canonical_path}}catch{}
        }
    }
    foreach($path in ($paths|Select-Object -Unique)){
        $id=$path;$allowed=$false;$reason=''
        try{
            $op=Get-ControllerOperation -Path $path -Workspace $Workspace -Historical
            if($op){$id=$op.id}else{throw 'No registered operation'}
            $null=Resolve-ControllerOperation ([pscustomobject]@{scientific_operation=$path;completed_operations=@($Task.completed_operations)}) $Workspace
            $allowed=$true;$reason='Normal qualification and scientific dependency gates still apply'
        }catch{$reason=$_.Exception.Message}
        $items += [pscustomobject]@{id=$id;path=$path;allowed=$allowed;scope=$reason}
    }
    return $items
}

function Read-DefinitionRecoveryState([string]$Path) {
    if(-not(Test-Path -LiteralPath $Path)){return [pscustomobject]@{schema=1;chains=@()}}
    $envelope=Get-Content -LiteralPath $Path -Raw -Encoding UTF8|ConvertFrom-Json
    if($envelope.schema -ne 1 -or (Get-ControllerTextHash $envelope.payload) -cne $envelope.sha256){throw 'DEFINITION_RECOVERY_STATE_CORRUPT: preserve state; no bridge replay'}
    $s=$envelope.payload|ConvertFrom-Json
    if($s.schema -ne 1 -or $null -eq $s.chains){throw 'DEFINITION_RECOVERY_STATE_CORRUPT: invalid schema'}
    return $s
}

function Write-DefinitionRecoveryState([string]$Path,$State) {
    $payload=$State|ConvertTo-Json -Depth 35 -Compress
    $text=@{schema=1;payload=$payload;sha256=(Get-ControllerTextHash $payload)}|ConvertTo-Json -Compress
    $tmp=$Path+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
    try{[IO.File]::WriteAllText($tmp,$text,[Text.UTF8Encoding]::new($false));Set-ControllerFileAtomic $tmp $Path ($Path+'.previous')}
    finally{if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp}}
}

function Invoke-ControllerDefinitionRecovery {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Workspace,
        [Parameter(Mandatory=$true)][string]$Instruction,
        [Parameter(Mandatory=$true)][string]$RecoveryKey,
        [Parameter(Mandatory=$true)][string]$StatePath,
        [Parameter(Mandatory=$true)][scriptblock]$Consult,
        [string]$BridgeArchive = ''
    )
    $lockHash=Get-ControllerTextHash ([IO.Path]::GetFullPath($StatePath).ToLowerInvariant())
    $mutex=[Threading.Mutex]::new($false,('Local\DefinitionRecovery.'+$lockHash));$held=$false
    try{
        $held=$mutex.WaitOne(0)
        if(-not $held){throw 'DEFINITION_RECOVERY_BUSY: another recovery owns the outbox'}
        $taskPath=Join-Path $Workspace 'project_coordination/ACTIVE_TASK.json'
        $task=Get-Content -LiteralPath $taskPath -Raw -Encoding UTF8|ConvertFrom-Json
        $taskHash=(Get-FileHash -LiteralPath $taskPath).Hash
        $key=Get-ControllerTextHash ($task.task_id+'|'+$RecoveryKey)
        $s=Read-DefinitionRecoveryState $StatePath
        $chain=@($s.chains|Where-Object key -eq $key)
        if($chain.Count -gt 1){throw 'DEFINITION_RECOVERY_STATE_CORRUPT: duplicate chain'}
        if($chain.Count){$chain=$chain[0]}else{
            $chain=[pscustomobject]@{key=$key;task_id=$task.task_id;original_instruction=$Instruction;candidate=$Instruction;status='REJECTED';attempts=@();stop_reason='';accepted_hash=''}
            $s.chains=@($s.chains)+@($chain)
        }
        if($chain.status -eq 'STOPPED'){throw ('DEFINITION_RECOVERY_STOPPED: '+$chain.stop_reason+'; evidence='+$StatePath)}
        while($true){
            if((Get-FileHash -LiteralPath $taskPath).Hash -ne $taskHash){throw 'DEFINITION_RECOVERY_TASK_CHANGED: re-review active task before resumption'}
            $catalog=@(Get-DefinitionRecoveryCatalog $Workspace $task)
            # A reserved send is never sent again. Reuse only an authenticated archive identity.
            if($chain.status -eq 'DISPATCH_RESERVED'){
                $last=$chain.attempts[-1];$reply=''
                if($BridgeArchive -and (Test-Path -LiteralPath $BridgeArchive)){
                    $files=@(Get-ChildItem -LiteralPath $BridgeArchive -File -Filter ('response_*_'+$last.handoff_id+'.json'))
                    if($files.Count -eq 1){
                        $a=Get-Content -LiteralPath $files[0].FullName -Raw -Encoding UTF8|ConvertFrom-Json
                        if($a.bridge_handoff_id -eq $last.handoff_id -and $a.status -eq 'ok' -and $a.response){
                            $reply=[string]$a.response;$last.archive=$files[0].FullName;$last.archive_sha256=(Get-FileHash $files[0].FullName).Hash
                        }
                    }
                }
                if(-not $reply){throw ('DEFINITION_RECOVERY_DISPATCH_UNCERTAIN: do not resend '+$last.handoff_id+'; reconcile bridge archive; evidence='+$StatePath)}
                $last.reply=$reply;$chain.candidate=$reply;$chain.status='RESPONSE_SAVED';Write-DefinitionRecoveryState $StatePath $s
            }
            $candidate=[string]$chain.candidate
            if($candidate -match '(?im)^\s*(AUTHENTICATION_FAILED|SERVICE_UNAVAILABLE|EXPLICIT_SECURITY_RESTRICTION|CHATGPT_BRIDGE_FAIL_CLOSED)\b'){
                $chain.status='STOPPED';$chain.stop_reason=$candidate;Write-DefinitionRecoveryState $StatePath $s
                throw ('DEFINITION_RECOVERY_RESTRICTED: '+$candidate)
            }
            $plan=Get-ControllerPreparationPlan $Workspace $candidate
            # Auth/service/security states are never converted into definition consultations.
            if($plan.status -ne 'DEFINITION_REJECTED' -and -not $plan.dispatch_ready){return [pscustomobject]@{instruction=$candidate;plan=$plan;recovered=$false;attempts=@($chain.attempts).Count}}
            if($plan.dispatch_ready){
                $ref=[regex]::Match($candidate,'(?im)^\s*OPERATION_ID:\s*([a-zA-Z0-9_.-]+)\s*$').Groups[1].Value
                if($ref -and @($catalog|Where-Object {$_.id -ceq $ref -and $_.allowed}).Count -eq 1){
                    if($chain.status -ne 'ACCEPTED'){
                        $chain.status='ACCEPTED';$chain.accepted_hash=Get-DefinitionProposalHash $candidate
                        Write-DefinitionRecoveryState $StatePath $s
                    }
                    return [pscustomobject]@{instruction=$candidate;plan=$plan;recovered=$true;attempts=@($chain.attempts).Count}
                }
                $plan=[pscustomobject]@{status='DEFINITION_REJECTED';dispatch_ready=$false;blocked_on=@('RECOVERY_REFERENCE_REQUIRED: reference one existing allowed OPERATION_ID; consultation cannot authorize new operations')}
            }
            if(($plan.blocked_on -join ' ') -match '(?i)EXPLICIT_SECURITY_RESTRICTION|AUTHENTICATION_FAILED|SERVICE_UNAVAILABLE|PATH_ESCAPE_REJECTED'){
                throw ('DEFINITION_RECOVERY_RESTRICTED: '+($plan.blocked_on -join '; '))
            }
            if($candidate -match '(?im)^\s*(DEFINITION_REVIEW_REQUIRED|ESCALATION_UNRESOLVED|STOP)\b'){
                $chain.status='STOPPED';$chain.stop_reason='Review/registration required: '+$candidate
                Write-DefinitionRecoveryState $StatePath $s;throw ('DEFINITION_RECOVERY_STOPPED: '+$chain.stop_reason)
            }
            $proposalHash=Get-DefinitionProposalHash $candidate
            $fingerprint=Get-ControllerTextHash ($task.task_id+'|'+$proposalHash+'|'+($plan|ConvertTo-Json -Depth 10 -Compress))
            $seen=@($s.chains|Where-Object task_id -eq $task.task_id|ForEach-Object {$_.attempts}|Where-Object {$_.proposal_hash -eq $proposalHash -or $_.fingerprint -eq $fingerprint})
            if($seen.Count -or @($chain.attempts).Count -ge 2){
                $chain.status='STOPPED';$chain.stop_reason=if($seen.Count){'Identical rejected proposal/fingerprint; no redispatch'}else{'Two consultation attempts exhausted; missing review or registration requires diagnosis'}
                Write-DefinitionRecoveryState $StatePath $s;throw ('DEFINITION_RECOVERY_STOPPED: '+$chain.stop_reason+'; evidence='+$StatePath)
            }
            $n=@($chain.attempts).Count+1
            $handoff='HND-DEF-'+(Get-ControllerTextHash ($key+'|'+$n+'|'+$fingerprint)).Substring(0,20)
            $context=[ordered]@{
                task_id=$task.task_id;attempt=$n;maximum_attempts=2;rejection_status=$plan.status;reasons=@($plan.blocked_on)
                original_rejected_instruction=$chain.original_instruction;current_rejected_instruction=$candidate
                guard_token_matches=@([regex]::Matches($candidate,'(?i)change formulation and execute arbitrary|arbitrary commands|destructive|bypass qualification|qdel|qmove|rm -rf')|ForEach-Object {$_.Value}|Select-Object -Unique)
                registered_operations=$catalog;completed_operations=@($task.completed_operations)
            }
            $prompt="DEFINITION_REJECTION_RECOVERY`n"+($context|ConvertTo-Json -Depth 15)+@"

The original validator remains authoritative. Return ONE corrected instruction under 4000 characters with an exact OPERATION_ID line referencing an existing allowed entry above. Keep the approved task and scientific gates. research_preparation is evidence/definition preparation only, not qualification to run a solver. Do not self-authorize, register, alter scientific assumptions, bypass security, or replay completed/submitted jobs. Literal guard tokens can reject even negated prohibitions; do not repeat those tokens in the corrected instruction. If an operation needs missing scientific review/registration, reply DEFINITION_REVIEW_REQUIRED and identify the prerequisite. Authentication failures and unavailable services retain their original stop behavior.
"@
            $attempt=[pscustomobject]@{number=$n;proposal_hash=$proposalHash;fingerprint=$fingerprint;handoff_id=$handoff;instruction=$candidate;rejection=$plan;prompt=$prompt;reply='';archive='';archive_sha256='';reserved_at=[DateTimeOffset]::UtcNow.ToString('o');error=''}
            $chain.attempts=@($chain.attempts)+@($attempt);$chain.status='DISPATCH_RESERVED'
            Write-DefinitionRecoveryState $StatePath $s
            try{$reply=[string](& $Consult $prompt $handoff)}catch{
                $attempt.error=$_.Exception.Message;Write-DefinitionRecoveryState $StatePath $s;throw
            }
            if([string]::IsNullOrWhiteSpace($reply)){throw 'CHATGPT_BRIDGE_FAIL_CLOSED: empty correction; reserved dispatch will not be repeated'}
            $attempt.reply=$reply;$chain.candidate=$reply;$chain.status='RESPONSE_SAVED'
            Write-DefinitionRecoveryState $StatePath $s
        }
    }finally{if($held){$mutex.ReleaseMutex()};$mutex.Dispose()}
}
