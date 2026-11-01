[CmdletBinding()]
param([string]$Workspace=(Split-Path (Split-Path $PSScriptRoot -Parent) -Parent),[switch]$Once,[switch]$DryRun,[ValidateRange(5,60)][int]$IntervalSeconds=30)
$ErrorActionPreference='Stop'
do {
    $session=Get-Content -LiteralPath (Join-Path $Workspace 'project_coordination/ACTIVE_SESSION.json') -Raw|ConvertFrom-Json
    if(-not $session.active){
        $events=Get-ChildItem -LiteralPath (Join-Path $Workspace 'project_coordination/controller') -Filter 'definition-review-*.json'
        foreach($file in $events){
            $event=Get-Content -LiteralPath $file.FullName -Raw|ConvertFrom-Json
            if($event.status -ne 'DEFINITION_REVIEW_REQUIRED'){continue}
            $arguments=@('-3',(Join-Path $PSScriptRoot 'review_dispatcher.py'),'--workspace',$Workspace,'--operation-id',$event.operation_id)
            if($DryRun){$arguments+='--dry-run'}
            & py @arguments
            if($LASTEXITCODE -ne 0){Write-Warning "Review dispatcher failed closed: $($event.operation_id)"}
        }
    }
    if($Once -or $DryRun){break}
    Start-Sleep -Seconds $IntervalSeconds
} while($true)
