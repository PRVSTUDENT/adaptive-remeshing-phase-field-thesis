function Restore-OperatorAuthorizedF1598Session {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Path,[Parameter(Mandatory)][string]$ExpectedHash,
          [Parameter(Mandatory)][string]$Archive,[Parameter(Mandatory)][scriptblock]$AssertNoOwner,
          [switch]$OperatorAuthorized)
    if(-not $OperatorAuthorized){throw 'OPERATOR_EXCEPTION_REQUIRED'}
    $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $mutex=[Threading.Mutex]::new($false,('Global\AdaptiveRemeshing.AgyController.'+$sid))
    $locked=$false; $handle=$null
    try {
        try{$locked=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$locked=$true}
        if(-not $locked){throw 'LIVE_CONTROLLER_MUTEX'}
        & $AssertNoOwner
        $handle=[IO.File]::Open($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read -bor [IO.FileShare]::Delete)
        if((Get-FileHash -LiteralPath $Path).Hash -cne $ExpectedHash){throw 'SESSION_CHANGED'}
        $s=Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json
        if(-not $s.active -or $s.agent -cne 'gemini-antigravity' -or $s.task_id -cne 'F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE' -or $s.controller_run_id -cne 'live_monitoring_1419488' -or $s.claimed_at -cne '2026-11-02T05:16:00.0000000+01:00'){throw 'EXACT_ORPHAN_CLAIM_REQUIRED'}
        $backup=Join-Path $Archive 'ACTIVE_SESSION.json'
        if(-not(Test-Path $backup) -or (Get-FileHash $backup).Hash -cne $ExpectedHash){throw 'VERIFIED_BACKUP_REQUIRED'}
        $event=Join-Path $Archive 'recovery-event.json'
        if(Test-Path $event){throw 'RECOVERY_ALREADY_RECORDED'}
        $s.active=$false
        $s | Add-Member recovery ([pscustomobject]@{reason='OPERATOR_AUTHORIZED_ORPHAN_RECOVERY';original_sha256=$ExpectedHash;original_claim=$backup;recovered_at=[DateTimeOffset]::Now.ToString('o');monitoring_closeout_verified=$false})
        $temp=$Path+'.operator-recovery.tmp'
        if(Test-Path $temp){throw 'RECOVERY_TEMP_EXISTS'}
        [IO.File]::WriteAllText($temp,($s|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
        & $AssertNoOwner
        if((Get-FileHash $Path).Hash -cne $ExpectedHash){throw 'SESSION_CHANGED'}
        # Atomic replacement; open handle denies in-place writers during comparison.
        $receipt=$Path+'.operator-replaced-original.json'
        if(Test-Path $receipt){throw 'REPLACEMENT_RECEIPT_EXISTS'}
        [IO.File]::Replace($temp,$Path,$receipt)
        [IO.File]::WriteAllText($event,(@{original_sha256=$ExpectedHash;result_sha256=(Get-FileHash $Path).Hash;operator_exception='2026-11-02 exact F1598 orphan only';monitoring_completed=$false}|ConvertTo-Json))
        (Get-Item $event).IsReadOnly=$true
    } finally {if($handle){$handle.Dispose()};if($locked){$mutex.ReleaseMutex()};$mutex.Dispose()}
}
