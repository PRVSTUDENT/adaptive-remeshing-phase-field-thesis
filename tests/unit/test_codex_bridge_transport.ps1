$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $repo '.agents/scripts/Invoke-ChatGPTBridge.ps1')
$root=Join-Path $env:TEMP ('codex-bridge-'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($root)
$count=0
foreach($case in @('valid','correlation','status','freshness','length','raw')) {
    $dir=Join-Path $root $case;[void][IO.Directory]::CreateDirectory($dir)
    $id='HND-OFFLINE-'+$case
    $job=Start-Job -ArgumentList $dir,$id,$case -ScriptBlock {
        param($dir,$id,$case)
        $deadline=[DateTime]::UtcNow.AddSeconds(20)
        while(-not(Test-Path (Join-Path $dir 'bridge_request.ready'))){
            if([DateTime]::UtcNow -gt $deadline){throw 'Fixture request not published'}
            Start-Sleep -Milliseconds 100
        }
        $v=@{bridge_handoff_id=$id;status='OK';copied_at=[DateTimeOffset]::UtcNow.ToString('o');response_chars=8;response='Finished'}
        switch($case){
            correlation{$v.bridge_handoff_id='WRONG'}
            status{$v.status='FAILED'}
            freshness{$v.copied_at=[DateTimeOffset]::UtcNow.AddHours(-1).ToString('o')}
            length{$v.response_chars=999}
        }
        $body=if($case -eq 'raw'){'untrusted raw text'}else{$v|ConvertTo-Json}
        $tmp=Join-Path $dir 'bridge_response.tmp';[IO.File]::WriteAllText($tmp,$body)
        [IO.File]::Move($tmp,(Join-Path $dir 'bridge_response.ready'))
    }
    $failure='';$reply=''
    try{$reply=Invoke-ChatGPTBridge -PromptText 'OFFLINE FIXTURE ONLY. Finished' -HandoffId $id -BridgeDir $dir -TimeoutMinutes 1}
    catch{$failure=$_.Exception.Message}
    $null=Wait-Job $job -Timeout 5
    if($job.State -ne 'Completed'){throw "Fixture failed: $case"}
    if($case -eq 'valid'){
        if($failure -or $reply -cne 'Finished' -or (Test-Path (Join-Path $dir 'bridge_response.ready'))){throw "Valid transaction failed: $failure"}
    }else{
        $expected=@{correlation='CORRELATION_MISMATCH';status='STATUS_NOT_OK';freshness='NOT_FRESH';length='LENGTH_MISMATCH';raw='INVALID_JSON'}[$case]
        if($failure -notmatch $expected -or -not(Test-Path (Join-Path $dir 'bridge_response.ready')) -or -not(Test-Path (Join-Path $dir 'bridge_request.ready'))){throw "Invalid response not safely preserved: $case $failure"}
    }
    Remove-Job $job
    $count++;Write-Output "PASS $case"
}
$dir=Join-Path $root 'dryrun';[void][IO.Directory]::CreateDirectory($dir)
$dry=Invoke-ChatGPTBridge -PromptText 'Dry run. Finished' -BridgeDir $dir -DryRun
if(-not $dry.Contains('JOB-FIRST / REPORT-AFTER POLICY') -or (Test-Path (Join-Path $dir 'bridge_request.ready'))){throw 'Dry run mutated transport'}
$count++;Write-Output "PASS dryrun; $count checks; isolated fixtures retained at $root; no live PAD/HPC calls"
$receipt=Join-Path $root 'receipt.json';$tmp=$receipt+'.tmp'
[IO.File]::WriteAllText($receipt,'{"status":"RESERVED_ONCE"}')
[IO.File]::WriteAllText($tmp,'{"status":"RECEIVED_VALIDATED"}')
[IO.File]::Replace($tmp,$receipt,($receipt+'.reservation.bak'))
if((Get-Content $receipt -Raw|ConvertFrom-Json).status -ne 'RECEIVED_VALIDATED' -or
   (Get-Content ($receipt+'.reservation.bak') -Raw|ConvertFrom-Json).status -ne 'RESERVED_ONCE'){throw 'Durable receipt replacement failed'}
Write-Output 'PASS atomic receipt replacement preserves original reservation; 8 checks total'
