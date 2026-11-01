[CmdletBinding()]
param([Parameter(Mandatory)][ValidatePattern('^[a-z][a-z0-9_]{5,140}$')][string]$OperationId)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
& py -3 (Join-Path $PSScriptRoot 'review_dispatcher.py') --workspace $root --operation-id $OperationId --check-review
if($LASTEXITCODE -ne 0){throw 'Authenticated scientific review required'}
& py -3 (Join-Path $PSScriptRoot 'review_dispatcher.py') --workspace $root --operation-id $OperationId --check-package
if($LASTEXITCODE -ne 0){throw 'Package integrity or resource validation failed'}
Write-Output 'TECH_QUALIFIED'
