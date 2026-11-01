[CmdletBinding()]
param(
    [string]$Workspace = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent),
    [switch]$Once,
    [switch]$DryRun,
    [ValidateRange(5,60)][int]$IntervalSeconds = 30
)

$ErrorActionPreference = 'Stop'
$sessionPath = Join-Path $Workspace 'project_coordination/ACTIVE_SESSION.json'
$controllerDir = Join-Path $Workspace 'project_coordination/controller'

do {
    try {
        if (Test-Path -LiteralPath $sessionPath) {
            $session = Get-Content -LiteralPath $sessionPath -Raw | ConvertFrom-Json
            if (-not $session.active) {
                if (Test-Path -LiteralPath $controllerDir) {
                    $events = @(Get-ChildItem -LiteralPath $controllerDir -Filter 'definition-review-*.json')
                    foreach ($file in $events) {
                        try {
                            $event = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
                            if ($event.status -ne 'DEFINITION_REVIEW_REQUIRED') { continue }
                            $arguments = @('-3', (Join-Path $PSScriptRoot 'review_dispatcher.py'), '--workspace', $Workspace, '--operation-id', $event.operation_id)
                            if ($DryRun) { $arguments += '--dry-run' }
                            & py @arguments
                            if ($LASTEXITCODE -ne 0) {
                                Write-Warning "Review dispatcher exited with code $LASTEXITCODE for $($event.operation_id)"
                            }
                        } catch {
                            Write-Warning "Failed processing event file $($file.Name): $_"
                        }
                    }
                }
            }
        }
    } catch {
        Write-Warning "Dispatcher poll error: $_"
    }

    if ($Once -or $DryRun) { break }
    Start-Sleep -Seconds $IntervalSeconds
} while ($true)
