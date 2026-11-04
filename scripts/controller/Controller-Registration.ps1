# Explicit reviewed-definition -> technical qualification -> execution transition.
# Missing definitions produce one durable event, never a model preparation loop.
. (Join-Path $PSScriptRoot 'Controller-Qualification.ps1')
function Get-ControllerRegistrationPlan([string]$Workspace,[string]$Instruction,$Task) {
    $id = [string]$Task.operation_transition.operation_id
    if (-not $id) { $id = [string]$Task.requested_operation_id }
    if (-not $id) {
        $m=[regex]::Match($Instruction,'(?im)^\s*(?:REQUESTED_)?OPERATION_ID\s*:\s*([a-z][a-z0-9_]+)')
        if($m.Success){$id=$m.Groups[1].Value}
    }
    if(-not $id){return $null}
    if($id -notmatch '^[a-z][a-z0-9_]{5,140}$'){throw 'Invalid operation registration request'}
    if($Task.operation_transition.status -eq 'SUBMITTED'){return $null}
    $relative='project_coordination/operation_definitions/'+$id+'.json'
    $path=Join-Path $Workspace $relative
    $fingerprint='MISSING'
    if(Test-Path -LiteralPath $path){
        $fingerprint=(Get-FileHash -LiteralPath $path).Hash
    } else {
        $candRel='project_coordination/candidate_definitions/'+$id+'.json'
        $candPath=Join-Path $Workspace $candRel
        if(Test-Path -LiteralPath $candPath){
            $relative=$candRel
            $path=$candPath
            $fingerprint=(Get-FileHash -LiteralPath $path).Hash
        } else {
            return [pscustomobject]@{status='DEFINITION_REVIEW_REQUIRED';dispatch_ready=$false;task_type='CONTROLLER_MAINTENANCE';operation_id=$id;path='';recipe='review-operation-definition';blocked_on=@('Reviewed operation definition missing');event_fingerprint=$id+':'+$fingerprint;receipt=$relative}
        }
    }
    $definition=Get-Content -LiteralPath $path -Raw|ConvertFrom-Json
    if($definition.schema -ne 1 -or $definition.operation_id -cne $id){throw 'Invalid operation definition identity'}

    # Check for external review dispatch record
    $manifestRel = [string]$definition.manifest
    $manifestPath = if($manifestRel){Join-Path $Workspace $manifestRel}else{''}
    $manifestKey = if($manifestPath -and (Test-Path -LiteralPath $manifestPath)){(Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()}else{'no-manifest'}
    $dispatchRecord = if($manifestKey){Join-Path $Workspace ("project_coordination/review_dispatch/" + $id + "-" + $manifestKey + ".json")}else{''}
    $disp = $null
    if($dispatchRecord -and (Test-Path -LiteralPath $dispatchRecord)){
        try{$disp = Get-Content -LiteralPath $dispatchRecord -Raw | ConvertFrom-Json}catch{}
    }

    # If rejected by independent review, fail closed
    if($disp -and ($disp.status -eq 'REJECTED' -or ($disp.review -and $disp.review.decision -and $disp.review.decision.decision -eq 'REJECT'))){
        $reason = if($disp.review.decision.rationale){$disp.review.decision.rationale}else{'Independent review rejected operation'}
        return [pscustomobject]@{status='DEFINITION_REJECTED';dispatch_ready=$false;task_type='REJECTED';operation_id=$id;path='';recipe='';blocked_on=@($reason);event_fingerprint=$id+':'+$fingerprint;receipt=$relative}
    }

    # Determine if operation has passed authenticated independent review
    # Every transition to REVIEWED / QUALIFIED MUST cryptographically verify signature & file hashes
    $hasApprovedReview = $false
    $checkReviewCmd = & py -3 (Join-Path $PSScriptRoot 'review_dispatcher.py') --workspace $Workspace --operation-id $id --check-review 2>&1
    if ($LASTEXITCODE -eq 0 -and ($checkReviewCmd | Out-String) -match 'AUTHENTICATED_INDEPENDENT_REVIEW') {
        $hasApprovedReview = $true
    }

    if(-not $hasApprovedReview){
        # Operation is pending independent review
        $blockedReason = 'External authenticated scientific review/qualification pipeline'
        if($disp -and $disp.reason -eq 'INSUFFICIENT_EVIDENCE'){
            $blockedReason = "Independent review requested additional evidence: $($disp.detail)"
        } elseif($disp -and $disp.reason){
            $blockedReason = "Review dispatch status: $($disp.reason) - $($disp.detail)"
        }
        return [pscustomobject]@{status='DEFINITION_REVIEW_REQUIRED';dispatch_ready=$false;task_type='EXTERNAL_REVIEW_DISPATCH';operation_id=$id;path='';recipe='authenticated-chatgpt-review';blocked_on=@($blockedReason);event_fingerprint=$id+':'+$fingerprint;receipt=$relative}
    }

    # Clear pending review event since operation has been approved
    Clear-ControllerDefinitionReviewEvent $Workspace $id

    $root=[IO.Path]::GetFullPath($Workspace).TrimEnd('\')+'\'
    if($definition.evidence_sources){
        foreach($source in $definition.evidence_sources.PSObject.Properties){
            $full=[IO.Path]::GetFullPath((Join-Path $Workspace $source.Name))
            if(-not $full.StartsWith($root,[StringComparison]::OrdinalIgnoreCase) -or
               -not(Test-Path -LiteralPath $full) -or (Get-FileHash -LiteralPath $full).Hash -cne $source.Value){
                throw 'Registered scientific evidence changed; review required'
            }
        }
    }
    $q=Get-ControllerDynamicQualification -Workspace $Workspace -Path $definition.execution_script -ArtifactId $id
    $techQualified = ($null -ne $q) -or ($disp -and $disp.status -in @('TECH_QUALIFIED','SUBMITTING','SUBMITTED','RUNNING','TERMINAL','EVALUATED'))
    if($techQualified){
        return [pscustomobject]@{status='READY';dispatch_ready=$true;task_type='QUALIFIED_EXECUTION';operation_id=$id;path=$definition.execution_script;recipe='qualified-execution';blocked_on=@();receipt=$relative}
    }
    return [pscustomobject]@{status='REGISTERED_TECHNICAL_QUALIFICATION_REQUIRED';dispatch_ready=$true;task_type='RESEARCH_PREPARATION';operation_id=$id;path=$definition.preparation_script;recipe='registered-technical-qualification';blocked_on=@('Build exact reviewed package and complete real technical gates before qualification');receipt=$relative}
}

function Clear-ControllerDefinitionReviewEvent([string]$Workspace,[string]$OperationId) {
    $path = Join-Path $Workspace "project_coordination/controller/definition-review-$OperationId.json"
    if(Test-Path -LiteralPath $path){
        try{
            $event = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
            if($event.status -eq 'DEFINITION_REVIEW_REQUIRED'){
                $event.status = 'REVIEW_RESOLVED'
                $event | Add-Member -NotePropertyName resolved_at -NotePropertyValue ([DateTimeOffset]::UtcNow.ToString('o')) -Force
                [IO.File]::WriteAllText($path, ($event | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
            }
        }catch{}
    }
}

function Write-ControllerDefinitionReviewEvent([string]$Workspace,$Plan) {
    if($Plan.status -ne 'DEFINITION_REVIEW_REQUIRED'){return}
    $directory=Join-Path $Workspace 'project_coordination/controller'
    $path=Join-Path $directory ('definition-review-'+$Plan.operation_id+'.json')
    if(Test-Path -LiteralPath $path){
        $previous=Get-Content -LiteralPath $path -Raw|ConvertFrom-Json
        if($previous.event_fingerprint -ceq $Plan.event_fingerprint){return}
    }
    $null=New-Item -ItemType Directory -Path $directory -Force
    $event=[ordered]@{schema=1;status='DEFINITION_REVIEW_REQUIRED';operation_id=$Plan.operation_id;event_fingerprint=$Plan.event_fingerprint;next_action='Maintainer review/registration; resume only on registry or scientific-evidence change';model_dispatches=0;created_at=[DateTimeOffset]::UtcNow.ToString('o')}
    $tmp=$path+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
    [IO.File]::WriteAllText($tmp,($event|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $tmp -Destination $path -Force
}
