function Get-ControllerTraceQualification([string]$Workspace) {
    $relative='models/pandey_kumar_mode1/74_method_c_history_call_trace_absolute_path/QUALIFICATION.json'
    $path=Join-Path $Workspace $relative
    if(-not(Test-Path -LiteralPath $path -PathType Leaf)){throw 'Trace technical qualification evidence missing'}
    $q=Get-Content -LiteralPath $path -Raw|ConvertFrom-Json
    if($q.schema -ne 1 -or $q.operation -ne 'authentic_uel_history_call_trace' -or $q.status -ne 'READY_FOR_TRACE_ANALYSIS' -or
        $q.dispatch_ready -isnot [bool] -or -not $q.dispatch_ready -or $q.pbs_job_id -notmatch '^\d+\.mmaster02$' -or
        $q.datacheck -ne 'PASS' -or $q.login_notifications -ne 'PASS' -or $q.compute_notifications -ne 'PASS' -or $q.parity -ne 'PASS'){throw 'Incomplete trace technical qualification'}
    $root=[IO.Path]::GetFullPath($Workspace).TrimEnd([char[]]'\/')+[IO.Path]::DirectorySeparatorChar
    if(@($q.sources.PSObject.Properties).Count -lt 10){throw 'Trace source/evidence binding incomplete'}
    foreach($item in $q.sources.PSObject.Properties){
        $p=[IO.Path]::GetFullPath((Join-Path $Workspace $item.Name))
        if(-not $p.StartsWith($root,[StringComparison]::OrdinalIgnoreCase) -or -not(Test-Path -LiteralPath $p -PathType Leaf) -or
            (Get-Item -LiteralPath $p).Length -gt 16777216 -or (Get-FileHash -LiteralPath $p).Hash -ne $item.Value){throw ('Trace qualification source/evidence changed: '+$item.Name)}
    }
    $receipts=Get-Content -LiteralPath (Join-Path $Workspace 'project_coordination/MODE1_BATCH_SUBMISSIONS.json') -Raw|ConvertFrom-Json
    $receipt=$receipts.PSObject.Properties[$q.manifest_sha256].Value.PSObject.Properties['M1_F1597_HISTORY_TRACE_R2'].Value
    if($receipt.pbs_job_id -ne $q.pbs_job_id){throw 'Actual governed trace PBS receipt mismatch'}
    $row=@(Import-Csv -LiteralPath (Join-Path $Workspace 'project_coordination/HPC_JOB_LEDGER.csv')|Where-Object {$_.Job_ID -eq $q.pbs_job_id -and $_.Job_Name -eq 'M1_F1597_HISTORY_TRACE_R2'})
    if($row.Count -ne 1 -or $row[0].Status -ne 'COMPLETED' -or [string]$row[0].Exit_Status -ne '0'){throw 'Independent terminal trace accounting missing'}
    $q|Add-Member -NotePropertyName qualification_artifact -NotePropertyValue $relative -Force
    return $q
}
