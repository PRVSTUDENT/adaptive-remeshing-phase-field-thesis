[CmdletBinding()]
param([string]$Destination = "$env:USERPROFILE/OpenClawPAD")
$ErrorActionPreference='Stop'
$source=Join-Path $PSScriptRoot 'Antigravity-Autonomous-Loop.ps1'
$tokens=$null; $errors=$null
[Management.Automation.Language.Parser]::ParseFile($source,[ref]$tokens,[ref]$errors)|Out-Null
if ($errors.Count) { throw ($errors.Message -join '; ') }
$target=Join-Path $Destination 'Antigravity-Autonomous-Loop.ps1'
if (-not (Test-Path -LiteralPath $Destination -PathType Container)) { throw 'Install directory must already exist' }
if (Test-Path -LiteralPath $target) {
    $backup=Join-Path $Destination ('backups/controller-' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss-fffffff') + '.ps1')
    New-Item -ItemType Directory -Path (Split-Path $backup) -Force|Out-Null
    Copy-Item -LiteralPath $target -Destination $backup
}
Copy-Item -LiteralPath $source -Destination $target
$expected=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $expected) { throw 'Deployment verification failed' }
"DEPLOYED $target SHA256=$expected"
