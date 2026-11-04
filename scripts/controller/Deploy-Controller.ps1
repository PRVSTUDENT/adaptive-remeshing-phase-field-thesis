[CmdletBinding()]
param(
    [string]$Destination = "$env:USERPROFILE/OpenClawPAD"
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Destination -PathType Container)) {
    throw "Install directory must already exist: $Destination"
}

$filesToDeploy = @(
    'Antigravity-Autonomous-Loop.ps1',
    'Invoke-ReviewDispatcher.ps1',
    'review_dispatcher.py',
    'attest_review.py',
    'Controller-Registration.ps1',
    'Controller-Preparation.ps1',
    'Controller-Operations.ps1',
    'Controller-Recovery.ps1',
    'Controller-Qualification.ps1',
    'Controller-TaskLifecycle.ps1',
    'Controller-AuthRecovery.ps1',
    'Controller-Supervisor.ps1',
    'Controller-FailureHandoff.ps1',
    'Test-IndependentReviewQualification.ps1',
    'Invoke-IndependentReviewBridge.ps1'
)

$backupsDir = Join-Path $Destination 'backups'
if (-not (Test-Path -LiteralPath $backupsDir)) {
    $null = New-Item -ItemType Directory -Path $backupsDir -Force
}

$deployResults = @()

foreach ($fileName in $filesToDeploy) {
    $source = Join-Path $PSScriptRoot $fileName
    if (-not (Test-Path -LiteralPath $source)) {
        Write-Warning "Source file not found: $source"
        continue
    }

    # Validate PowerShell syntax if ps1
    if ($fileName.EndsWith('.ps1', [StringComparison]::OrdinalIgnoreCase)) {
        $tokens = $null; $errors = $null
        [Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$errors) | Out-Null
        if ($errors.Count) { throw "Syntax error in $fileName : $($errors.Message -join '; ')" }
    }

    $target = Join-Path $Destination $fileName
    if (Test-Path -LiteralPath $target) {
        $backup = Join-Path $backupsDir ($fileName + '.bak-' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss-fff'))
        Copy-Item -LiteralPath $target -Destination $backup -Force
    }

    Copy-Item -LiteralPath $source -Destination $target -Force
    $expected = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    $actual = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    if ($actual -ne $expected) {
        throw "Deployment verification failed for $fileName : expected $expected, got $actual"
    }

    $deployResults += [pscustomobject]@{
        file = $fileName
        sha256 = $actual
        target = $target
    }
    Write-Host "DEPLOYED $fileName SHA256=$actual" -ForegroundColor Green
}

return $deployResults
