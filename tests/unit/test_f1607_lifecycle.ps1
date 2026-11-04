param([string]$Workspace = (Get-Location).Path)
. (Join-Path $Workspace 'scripts/controller/Controller-TaskLifecycle.ps1')
$life = Get-ControllerTaskLifecycle $Workspace
$reg = Get-ControllerTaskRegistrationPlan $Workspace
Write-Output "Lifecycle state: $($life.state)"
Write-Output "Lifecycle terminal: $($life.terminal)"
Write-Output "Lifecycle task: $($life.next_authoritative_task)"
Write-Output "Registration status: $($reg.status)"
Write-Output "Registration dispatch_ready: $($reg.dispatch_ready)"
if(-not $reg.dispatch_ready){
    throw "Registration plan not dispatch_ready: $($reg.reason)"
}
if($life.terminal){
    throw "Lifecycle is unexpectedly terminal"
}
Write-Output "CONTROLLER_LIFECYCLE_VERIFIED"
