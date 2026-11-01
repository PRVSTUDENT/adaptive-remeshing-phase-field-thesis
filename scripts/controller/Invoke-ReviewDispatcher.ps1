[CmdletBinding()]
param(
    [string]$Workspace = '',
    [string]$OperationId = '',
    [switch]$Once,
    [switch]$DryRun,
    [ValidateRange(5,60)][int]$IntervalSeconds = 30
)

$ErrorActionPreference = 'Stop'
if (-not $Workspace) {
    $Workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
}
$sessionPath = Join-Path $Workspace 'project_coordination/ACTIVE_SESSION.json'
$controllerDir = Join-Path $Workspace 'project_coordination/controller'

do {
    try {
        if (Test-Path -LiteralPath $sessionPath) {
            $session = Get-Content -LiteralPath $sessionPath -Raw | ConvertFrom-Json
            if (-not $session.active) {
                $targetOps = @()
                if ($OperationId) {
                    $targetOps += $OperationId
                } else {
                    if (Test-Path -LiteralPath $controllerDir) {
                        $events = @(Get-ChildItem -LiteralPath $controllerDir -Filter 'definition-review-*.json')
                        foreach ($file in $events) {
                            try {
                                $event = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
                                if ($event.status -eq 'DEFINITION_REVIEW_REQUIRED' -and $event.operation_id) {
                                    $targetOps += $event.operation_id
                                }
                            } catch {}
                        }
                    }
                }

                foreach ($op in $targetOps) {
                    try {
                        $arguments = @('-3', (Join-Path $PSScriptRoot 'review_dispatcher.py'), '--workspace', $Workspace, '--operation-id', $op)
                        if ($DryRun) { $arguments += '--dry-run' }
                        & py @arguments
                        if ($LASTEXITCODE -ne 0) {
                            Write-Warning "Review dispatcher exited with code $LASTEXITCODE for $op"
                        }
                    } catch {
                        Write-Warning "Failed processing operation $op : $_"
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
