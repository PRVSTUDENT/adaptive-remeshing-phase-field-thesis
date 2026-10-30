. (Join-Path $PSScriptRoot 'Controller-Qualification.ps1')
function Test-ControllerOperationBinding($Operation,$Record,$State) {
    return ($Operation.id -ceq $Record.operation_id -and
        $State.operation_id -ceq $Operation.id -and $State.task_type -ceq 'QUALIFIED_EXECUTION' -and
        $Record.operation_path -cin @($Operation.path,$Operation.id) -and
        $State.scientific_operation -cin @($Operation.path,$Operation.id))
}
function Get-ControllerPinnedOperationHash($Operation,$State,[string]$Workspace) {
    $pin=$State.sources.($Operation.path)
    if($pin){return $pin}
    # Legacy ID-form checkpoints may omit the path, but must still pin the
    # exact qualification artifact. Never accept the current file as its own pin.
    $q=$Operation.qualification
    if($q -and $q.script_sha256 -and $q.qualification_artifact){
        $recordPin=$State.sources.($q.qualification_artifact)
        if($recordPin -and (Get-FileHash -LiteralPath (Join-Path $Workspace $q.qualification_artifact)).Hash -ceq $recordPin){return $q.script_sha256}
    }
    throw 'Scientific verifier source was not pinned before dispatch'
}
# Closed operation registry with dynamic qualified operation support. Retired KKT artifacts remain verifiable, never executable.
function Get-ControllerOperation([string]$Path,[string]$ArtifactId,[switch]$Historical,[switch]$Proposed,[string]$Workspace='') {
    if(($Path -cin @('evaluate_mode1_package148_state_transfer','evaluate_mode1_package148_state_transfer_r2','evaluate_mode1_package148_state_transfer_r3','evaluate_mode1_package148_state_transfer_r4','evaluate_mode1_package148_state_transfer_r5','evaluate_mode1_package148_state_transfer_r6')) -or (-not $Path -and $ArtifactId -cin @('evaluate_mode1_package148_state_transfer','evaluate_mode1_package148_state_transfer_r2','evaluate_mode1_package148_state_transfer_r3','evaluate_mode1_package148_state_transfer_r4','evaluate_mode1_package148_state_transfer_r5','evaluate_mode1_package148_state_transfer_r6'))){
        if(-not $ArtifactId){ $ArtifactId = $Path }
        $Path='scripts/validation/execute_package148_state_transfer.py'
    }
    $new=[pscustomobject]@{path='scripts/validation/probe_mode1_f1597_mechanical_history.py';id='mapped_mechanical_history_call_order_probe';status='F1597_MECHANICAL_HISTORY_DIAGNOSTIC_VERIFIED_CORRECTION_PENDING';title='Mechanical equilibrium and transactional history call-order diagnostic';executable=$true}
    $old=[pscustomobject]@{path='scripts/validation/probe_mode1_f1597_kkt.py';id='mapped_frozen_history_lower_bound_kkt_probe';status='F1597_KKT_DIAGNOSTIC_VERIFIED_CORRECTION_PENDING';title='Completed frozen-history KKT diagnostic';executable=$false}
    $trace=[pscustomobject]@{path='scripts/validation/probe_mode1_f1597_uel_call_trace.py';id='authentic_uel_history_call_trace';status='F1597_AUTHENTIC_TRACE_VERIFIED_CORRECTION_PENDING';title='Authentic Abaqus UEL history call trace';executable=$true}
    if($Proposed -and ($Path -ceq $trace.path -or $ArtifactId -ceq $trace.id)){$trace.executable=$false;return $trace}
    if($Path -ceq $old.path -or $ArtifactId -ceq $old.id){
        if($Historical){return $old}
        throw 'UNQUALIFIED_OR_RETIRED_OPERATION: completed KKT probe cannot execute'
    }
    $op=if($Path -ceq $trace.path -or $ArtifactId -ceq $trace.id){$trace}elseif($Path -ceq $new.path -or $ArtifactId -ceq $new.id){$new}else{$null}
    if($op){
        if(-not $Historical -and -not $op.executable){throw 'UNQUALIFIED_OR_RETIRED_OPERATION: completed KKT probe cannot execute'}
        return $op
    }
    # Dynamic operation support for newly qualified research operations
    if(($Path -or $ArtifactId) -and $Workspace){
        $dynQual = Get-ControllerDynamicQualification -Workspace $Workspace -Path $Path -ArtifactId $ArtifactId
        if($dynQual){
            return [pscustomobject]@{
                path = $dynQual.canonical_path
                id = $dynQual.operation
                status = 'QUALIFIED_OPERATION_EXECUTION'
                title = "Qualified operation: $($dynQual.operation)"
                executable = $true
                qualification = $dynQual
            }
        }
    }
    if($Historical){return $null}
    throw "UNQUALIFIED_OR_RETIRED_OPERATION: operation lacks validated qualification record: $(if($Path){$Path}else{$ArtifactId})"
}
function Resolve-ControllerOperation($Task,[string]$Workspace='') {
    if(-not $Task.scientific_operation){throw ('NEXT_OPERATION_REQUIRES_DEFINITION: completed operation will not replay; '+$Task.next_safe_action)}
    $op=Get-ControllerOperation -Path $Task.scientific_operation -ArtifactId $Task.scientific_operation_id -Workspace $Workspace
    if(@($Task.completed_operations) -contains $op.id){throw 'COMPLETED_OPERATION_REJECTED: operation already completed'}
    if($op.id -eq 'authentic_uel_history_call_trace'){if(-not $Workspace){throw 'Trace qualification requires workspace evidence'};$null=Get-ControllerTraceQualification $Workspace}
    return $op
}
function Resolve-ControllerTaskType($Task,[string]$Workspace='',[string]$RequestedOperationId='') {
    if(-not $Task.scientific_checkpoint_required){
        return [pscustomobject]@{task_type='GENERAL_RESEARCH';dispatch_ready=$true;operation=$null;reason='No checkpoint required'}
    }
    $effectiveOp = if($Task.scientific_operation){ [string]$Task.scientific_operation } elseif($RequestedOperationId -and $RequestedOperationId -ne 'research_preparation'){ $RequestedOperationId } else { '' }
    $effectiveOpId = if($Task.scientific_operation_id){ [string]$Task.scientific_operation_id } elseif($RequestedOperationId -and $RequestedOperationId -ne 'research_preparation'){ $RequestedOperationId } else { '' }
    if($effectiveOp){
        try{
            $opTask = [pscustomobject]@{
                scientific_operation = $effectiveOp
                scientific_operation_id = $effectiveOpId
                completed_operations = $Task.completed_operations
                next_safe_action = $Task.next_safe_action
            }
            $op=Resolve-ControllerOperation $opTask $Workspace
            return [pscustomobject]@{task_type='QUALIFIED_EXECUTION';dispatch_ready=$true;operation=$op;reason='Qualified executable operation ready'}
        }catch{
            if($_.Exception.Message -match '(COMPLETED_OPERATION_REJECTED|completed KKT probe)'){throw}
            return [pscustomobject]@{task_type='RESEARCH_PREPARATION';dispatch_ready=$true;operation=$null;reason=$_.Exception.Message}
        }
    }
    return [pscustomobject]@{task_type='RESEARCH_PREPARATION';dispatch_ready=$true;operation=$null;reason='New research objective requires preparation'}
}
