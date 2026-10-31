# Explicit reviewed-definition -> technical qualification -> execution transition.
# Missing definitions produce one durable event, never a model preparation loop.
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
    if(Test-Path -LiteralPath $path){$fingerprint=(Get-FileHash -LiteralPath $path).Hash}
    if(-not(Test-Path -LiteralPath $path)){
        return [pscustomobject]@{status='DEFINITION_REVIEW_REQUIRED';dispatch_ready=$false;task_type='CONTROLLER_MAINTENANCE';operation_id=$id;path='';recipe='review-operation-definition';blocked_on=@('Reviewed operation definition missing');event_fingerprint=$id+':'+$fingerprint;receipt=$relative}
    }
    $definition=Get-Content -LiteralPath $path -Raw|ConvertFrom-Json
    if($definition.schema -ne 1 -or $definition.operation_id -cne $id -or
       $definition.registration_status -ne 'REVIEWED_FOR_TECHNICAL_QUALIFICATION' -or
       -not $definition.reviewed_by -or -not $definition.evidence_sources){throw 'Unreviewed operation definition'}
    $root=[IO.Path]::GetFullPath($Workspace).TrimEnd('\')+'\'
    foreach($source in $definition.evidence_sources.PSObject.Properties){
        $full=[IO.Path]::GetFullPath((Join-Path $Workspace $source.Name))
        if(-not $full.StartsWith($root,[StringComparison]::OrdinalIgnoreCase) -or
           -not(Test-Path -LiteralPath $full) -or (Get-FileHash -LiteralPath $full).Hash -cne $source.Value){
            throw 'Registered scientific evidence changed; review required'
        }
    }
    $q=Get-ControllerDynamicQualification -Workspace $Workspace -Path $definition.execution_script -ArtifactId $id
    if($q){return [pscustomobject]@{status='READY';dispatch_ready=$true;task_type='QUALIFIED_EXECUTION';operation_id=$id;path=$definition.execution_script;recipe='qualified-execution';blocked_on=@();receipt=$relative}}
    return [pscustomobject]@{status='REGISTERED_TECHNICAL_QUALIFICATION_REQUIRED';dispatch_ready=$true;task_type='RESEARCH_PREPARATION';operation_id=$id;path=$definition.preparation_script;recipe='registered-technical-qualification';blocked_on=@('Build exact reviewed package and complete real technical gates before qualification');receipt=$relative}
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
    [IO.File]::WriteAllText($path,($event|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
}
