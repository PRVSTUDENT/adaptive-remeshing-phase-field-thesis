. (Join-Path $PSScriptRoot 'Controller-Qualification.ps1')
# Closed operation registry. Retired KKT artifacts remain verifiable, never executable.
function Get-ControllerOperation([string]$Path,[string]$ArtifactId,[switch]$Historical,[switch]$Proposed) {
    $new=[pscustomobject]@{path='scripts/validation/probe_mode1_f1597_mechanical_history.py';id='mapped_mechanical_history_call_order_probe';status='F1597_MECHANICAL_HISTORY_DIAGNOSTIC_VERIFIED_CORRECTION_PENDING';title='Mechanical equilibrium and transactional history call-order diagnostic';executable=$true}
    $old=[pscustomobject]@{path='scripts/validation/probe_mode1_f1597_kkt.py';id='mapped_frozen_history_lower_bound_kkt_probe';status='F1597_KKT_DIAGNOSTIC_VERIFIED_CORRECTION_PENDING';title='Completed frozen-history KKT diagnostic';executable=$false}
    $trace=[pscustomobject]@{path='scripts/validation/probe_mode1_f1597_uel_call_trace.py';id='authentic_uel_history_call_trace';status='F1597_AUTHENTIC_TRACE_VERIFIED_CORRECTION_PENDING';title='Authentic Abaqus UEL history call trace';executable=$true}
    if($Proposed -and ($Path -ceq $trace.path -or $ArtifactId -ceq $trace.id)){$trace.executable=$false;return $trace}
    $op=if($Path -ceq $trace.path -or $ArtifactId -ceq $trace.id){$trace}elseif($Path -ceq $new.path -or $ArtifactId -ceq $new.id){$new}elseif($Historical -and $ArtifactId -ceq $old.id){$old}else{$null}
    if(-not $op -or (-not $Historical -and -not $op.executable)){throw 'UNQUALIFIED_OR_RETIRED_OPERATION: completed KKT probe cannot execute'}
    return $op
}
function Resolve-ControllerOperation($Task,[string]$Workspace='') {
    if(-not $Task.scientific_operation){throw ('NEXT_OPERATION_REQUIRES_DEFINITION: completed operation will not replay; '+$Task.next_safe_action)}
    $op=Get-ControllerOperation -Path $Task.scientific_operation
    if(@($Task.completed_operations) -contains $op.id){throw 'COMPLETED_OPERATION_REJECTED: operation already completed'}
    if($op.id -eq 'authentic_uel_history_call_trace'){if(-not $Workspace){throw 'Trace qualification requires workspace evidence'};$null=Get-ControllerTraceQualification $Workspace}
    return $op
}
