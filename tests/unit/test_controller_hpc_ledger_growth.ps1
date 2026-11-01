# Unit regression test: verified append-only HPC ledger growth and deliberate corruption guards
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')

$root = Join-Path ([IO.Path]::GetTempPath()) ('hpc-growth-test-' + [guid]::NewGuid().ToString('N'))
foreach ($folder in @('project_coordination', 'project_coordination/sessions', 'project_coordination/controller', 'openclawpad', 'openclawpad/backups')) {
    [void](New-Item -ItemType Directory -Path (Join-Path $root $folder) -Force)
}

function Put([string]$Rel, [string]$Text) {
    [IO.File]::WriteAllText((Join-Path $root $Rel), $Text, [Text.UTF8Encoding]::new($false))
}
function Check([bool]$Okay, [string]$Message) {
    if (-not $Okay) { throw "FAIL: $Message" }
    Write-Host "PASS: $Message"
}

try {
    $realHpcLedger = Get-Content -LiteralPath (Join-Path $repo 'project_coordination/HPC_JOB_LEDGER.csv') -Raw
    $realExec = Get-Content -LiteralPath (Join-Path $repo 'project_coordination/MODE1_EXECUTION_LEDGER.json') -Raw
    $realBatch = Get-Content -LiteralPath (Join-Path $repo 'project_coordination/MODE1_BATCH_SUBMISSIONS.json') -Raw

    Put 'project_coordination/HPC_JOB_LEDGER.csv' $realHpcLedger
    Put 'project_coordination/MODE1_EXECUTION_LEDGER.json' $realExec
    Put 'project_coordination/MODE1_BATCH_SUBMISSIONS.json' $realBatch

    # Package 160 prior ledger hash (before Job 1419305 was appended at line 485)
    $p160PriorHash = '75A55F79E090FA4E23D183D25DFC4923150560C1718F72EDACBF346C3E8E1CC1'

    # Test 1: Package 160 valid append-only growth passes
    $p160Passed = $true
    try {
        Assert-ControllerHpcLedgerGrowth $root $p160PriorHash $null
    } catch {
        $p160Passed = $false
        Write-Warning $_.Exception.Message
    }
    Check $p160Passed 'Package 160 valid append-only ledger growth passes verification'

    # Test 2: Checkpoint with P160 prior hash passes Assert-ControllerDispatchCheckpoint
    $runId = 'test-run-p160-growth'
    $sessionRel = "project_coordination/sessions/test_session_$runId.md"
    Put $sessionRel "# Test Session Report`n"
    $sessionReportHash = (Get-FileHash -LiteralPath (Join-Path $root $sessionRel) -Algorithm SHA256).Hash

    $archiveFile = Join-Path $root "openclawpad/backups/checkpoint-$runId-interrupted.json"
    $origState = [ordered]@{
        schema = 1
        run_id = $runId
        task_id = 'F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160'
        state = 'BLOCKED'
        recovery_count = 0
        updated_at = [DateTimeOffset]::UtcNow.ToString('o')
    }
    Write-ControllerCheckpoint $archiveFile ([pscustomobject]$origState)
    $archiveHash = (Get-FileHash -LiteralPath $archiveFile -Algorithm SHA256).Hash

    $reconciledState = [ordered]@{
        schema = 1
        run_id = $runId
        task_id = 'F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160'
        turn = 448
        state = 'COMPLETED'
        stop_reason = 'RECONCILED'
        recovery_count = 0
        updated_at = [DateTimeOffset]::UtcNow.ToString('o')
        reconciliation = [ordered]@{
            status = 'INTERRUPTED_TURN_PROGRESS_WATCHDOG_RECONCILED'
            original_checkpoint = $archiveFile
            original_sha256 = $archiveHash
            session_report = $sessionRel
            session_report_sha256 = $sessionReportHash
            hpc_ledger_sha256 = $p160PriorHash
        }
    }
    $cpDispatchPassed = $true
    try {
        Assert-ControllerDispatchCheckpoint $root ([pscustomobject]$reconciledState)
    } catch {
        $cpDispatchPassed = $false
        Write-Warning $_.Exception.Message
    }
    Check $cpDispatchPassed 'Reconciled checkpoint with Package 160 growth passes Assert-ControllerDispatchCheckpoint'

    # Test 3: Deliberate corruption - deleted historical row is blocked
    $lines = [IO.File]::ReadAllLines((Join-Path $root 'project_coordination/HPC_JOB_LEDGER.csv'))
    $deletedLines = @($lines[0..5] + $lines[7..($lines.Count - 1)])
    [IO.File]::WriteAllLines((Join-Path $root 'project_coordination/HPC_JOB_LEDGER.csv'), $deletedLines)
    $delBlocked = $false
    try {
        Assert-ControllerHpcLedgerGrowth $root $p160PriorHash $null
    } catch {
        $delBlocked = $_.Exception.Message -match 'BLOCKED: HPC job ledger changed unexpectedly'
    }
    Check $delBlocked 'Deliberate corruption (deleted historical row) fails closed'

    # Test 4: Deliberate corruption - altered historical row is blocked
    [IO.File]::WriteAllText((Join-Path $root 'project_coordination/HPC_JOB_LEDGER.csv'), $realHpcLedger)
    $alteredText = $realHpcLedger.Replace('M1_MB_DONOR', 'M1_CORRUPTED_DONOR')
    [IO.File]::WriteAllText((Join-Path $root 'project_coordination/HPC_JOB_LEDGER.csv'), $alteredText)
    $altBlocked = $false
    try {
        Assert-ControllerHpcLedgerGrowth $root $p160PriorHash $null
    } catch {
        $altBlocked = $_.Exception.Message -match 'BLOCKED: HPC job ledger changed unexpectedly'
    }
    Check $altBlocked 'Deliberate corruption (altered historical row) fails closed'

    # Test 5: Deliberate corruption - reordered historical rows are blocked
    [IO.File]::WriteAllText((Join-Path $root 'project_coordination/HPC_JOB_LEDGER.csv'), $realHpcLedger)
    $lines = [IO.File]::ReadAllLines((Join-Path $root 'project_coordination/HPC_JOB_LEDGER.csv'))
    $tmp = $lines[10]
    $lines[10] = $lines[11]
    $lines[11] = $tmp
    [IO.File]::WriteAllLines((Join-Path $root 'project_coordination/HPC_JOB_LEDGER.csv'), $lines)
    $reorderBlocked = $false
    try {
        Assert-ControllerHpcLedgerGrowth $root $p160PriorHash $null
    } catch {
        $reorderBlocked = $_.Exception.Message -match 'BLOCKED: HPC job ledger changed unexpectedly'
    }
    Check $reorderBlocked 'Deliberate corruption (reordered historical rows) fails closed'

    # Test 6: Deliberate corruption - unverifiable new job receipt is blocked
    [IO.File]::WriteAllText((Join-Path $root 'project_coordination/HPC_JOB_LEDGER.csv'), $realHpcLedger)
    $unverifiableLine = "9999999.mmaster02,M1_UNVERIFIED_JOB,/scratch9/unverified,,entry_imfdfkmq,2026-11-01T12:00:00.0000000+00:00,SUBMITTED,,STANDING_MODE1_V2_ACCEPTED_ONCE,unverifiedhash`r`n"
    [IO.File]::AppendAllText((Join-Path $root 'project_coordination/HPC_JOB_LEDGER.csv'), $unverifiableLine)
    $unverifiedBlocked = $false
    try {
        Assert-ControllerHpcLedgerGrowth $root $p160PriorHash $null
    } catch {
        $unverifiedBlocked = $_.Exception.Message -match 'unverifiable historical job receipt'
    }
    Check $unverifiedBlocked 'Deliberate corruption (unverifiable new job receipt) fails closed'

    # Test 7: Deliberate corruption - invalid job ID format in appended receipt is blocked
    [IO.File]::WriteAllText((Join-Path $root 'project_coordination/HPC_JOB_LEDGER.csv'), $realHpcLedger)
    $badIdLine = "not_a_valid_job_id,M1_BAD_ID,/scratch9/bad,,entry_imfdfkmq,2026-11-01T12:00:00.0000000+00:00,SUBMITTED,,STANDING_MODE1_V2_ACCEPTED_ONCE,badhash`r`n"
    [IO.File]::AppendAllText((Join-Path $root 'project_coordination/HPC_JOB_LEDGER.csv'), $badIdLine)
    $badIdBlocked = $false
    try {
        Assert-ControllerHpcLedgerGrowth $root $p160PriorHash $null
    } catch {
        $badIdBlocked = $_.Exception.Message -match 'invalid job receipt'
    }
    Check $badIdBlocked 'Deliberate corruption (invalid job ID format in appended receipt) fails closed'

    [IO.File]::WriteAllText((Join-Path $root 'project_coordination/HPC_JOB_LEDGER.csv'), $alteredText)
    $remembered=[pscustomobject]@{sources=[pscustomobject]@{'project_coordination/HPC_JOB_LEDGER.csv'=$p160PriorHash}}
    $blocked=$false;try { Assert-ControllerHpcLedgerGrowth $root $p160PriorHash $remembered } catch { $blocked=$true }
    Check $blocked 'Remembered historical hash cannot bypass altered historical receipts'
    Write-Host "ALL HPC LEDGER GROWTH REGRESSION TESTS PASSED."
} finally {
    $target=[IO.Path]::GetFullPath($root)
    if(-not $target.StartsWith([IO.Path]::GetFullPath([IO.Path]::GetTempPath()),[StringComparison]::OrdinalIgnoreCase) -or (Split-Path $target -Leaf) -notlike 'hpc-growth-test-*'){throw 'Unsafe test cleanup'}
    Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction SilentlyContinue
}
