<# Compatibility entrypoint. Per-job authorization has been removed by the user.
   Normal calls qualify and submit ready jobs. VerifyOnly and DryRun remain read-only. #>
[CmdletBinding()]
param([switch]$EnrollStandingGrant,[switch]$UpgradeStandingGrant,[switch]$VerifyOnly,[switch]$DryRun,[switch]$SubmitReady,[string]$ManifestPath='')
$ErrorActionPreference='Stop'
Write-Output 'COMPATIBILITY: human authorization and issuer trust activation are retired; using technical execution workflow'
& "$PSScriptRoot/Invoke-Mode1Execution.ps1" -ManifestPath $ManifestPath -VerifyOnly:$VerifyOnly -DryRun:$DryRun
