[CmdletBinding()]
param([Parameter(Mandatory)][ValidatePattern('^[a-z][a-z0-9_]{5,140}$')][string]$OperationId,
      [Parameter(Mandatory)][string]$Acceptance)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$result=& py -3 (Join-Path $PSScriptRoot 'method_c_eligibility.py') --workspace $root --operation-id $OperationId --acceptance $Acceptance
if($LASTEXITCODE -ne 0){throw ($result|Out-String)}
$eligibility=($result|Out-String)|ConvertFrom-Json
if($eligibility.status -ne 'SCIENTIFICALLY_ELIGIBLE_PENDING_LIVE_PREFLIGHT'){throw 'Ineligible operation'}
# Never invoke definition-supplied commands. The existing executor reconciles
# live resources, notifications, exact inputs and once-only reservations.
& (Join-Path $root 'scripts/hpc/Invoke-Mode1Execution.ps1') -ManifestPath (Join-Path $root $eligibility.manifest)
