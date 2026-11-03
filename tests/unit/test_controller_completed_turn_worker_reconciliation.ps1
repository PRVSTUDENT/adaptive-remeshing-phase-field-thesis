# Focused regression test suite for COMPLETED checkpoint worker PID reconciliation.
# Tests:
# 1. COMPLETED checkpoint with dead worker PID reconciles to PID 0 and preserves next_instruction.
# 2. Checkpoint with active worker PID is rejected (fail-closed).
# 3. Checkpoint with active repository session is rejected.
# 4. Checkpoint with mismatched/changed hash is rejected.
# 5. Exact next_instruction preservation is bitwise verified.
# 6. Mutex contention prevents concurrent reconciliation.

$ErrorActionPreference = 'Stop'
$repo = (Get-Item $PSScriptRoot).Parent.Parent.FullName
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')

$script:testIndex = 0
function Check([bool]$Condition, [string]$Description) {
    $script:testIndex++
    if (-not $Condition) {
        Write-Error ("FAIL $script:testIndex $Description")
        exit 1
    }
    Write-Host ("PASS $script:testIndex $Description")
}

$tmp = Join-Path ([IO.Path]::GetTempPath()) ("worker-rec-" + [Guid]::NewGuid().ToString('n'))
$null = New-Item -ItemType Directory -Path $tmp -Force
$null = New-Item -ItemType Directory -Path (Join-Path $tmp 'project_coordination') -Force
$null = New-Item -ItemType Directory -Path (Join-Path $tmp 'backups') -Force

try {
    # Create mock session
    $sessionPath = Join-Path $tmp 'project_coordination/ACTIVE_SESSION.json'
    $sessionData = [pscustomobject]@{
        active = $false
        agent = 'gemini-antigravity'
        task_id = 'F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION'
    }
    [IO.File]::WriteAllText($sessionPath, ($sessionData | ConvertTo-Json), [Text.UTF8Encoding]::new($false))

    # Generate a dead PID (find an unused PID)
    $deadPid = 99998
    while (Get-Process -Id $deadPid -ErrorAction SilentlyContinue) {
        $deadPid++
    }

    # Helper to create a valid COMPLETED checkpoint fixture
    function New-TestCheckpointFixture {
        param([int]$WorkerPid, [string]$Instr = 'TURN 11 DISPATCH PROMPT: PRESERVE AND AUDIT')
        $cpState = [pscustomobject]@{
            schema = 1
            run_id = 'test-run-158e8df8'
            workspace = $tmp
            turn = 10
            state = 'COMPLETED'
            task_id = 'F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION'
            recovery_count = 0
            operation_id = 'research_preparation'
            scientific_operation = ''
            original_instruction_hash = (Get-ControllerTextHash 'TURN 10 INSTRUCTION')
            next_instruction = $Instr
            process_id = $WorkerPid
            process_exit_code = 0
            conversation_id = ''
            stop_reason = 'PROCESS_EXIT'
            block_reason = ''
            updated_at = ''
        }
        $cpPath = Join-Path $tmp 'controller_turn_checkpoint.json'
        Write-ControllerCheckpoint $cpPath $cpState
        return $cpPath
    }

    $scriptPath = Join-Path $repo 'scripts/controller/Reconcile-CompletedTurnWorkerPid.ps1'

    # Test 1: COMPLETED checkpoint with dead worker PID reconciles successfully
    $cp1 = New-TestCheckpointFixture -WorkerPid $deadPid
    $hash1 = (Get-FileHash -LiteralPath $cp1 -Algorithm SHA256).Hash
    $res1 = & $scriptPath -Workspace $tmp -CheckpointPath $cp1 -ExpectedCheckpointHash $hash1 -ExpectedRunId 'test-run-158e8df8' -ExpectedTurn 10 -BackupDir (Join-Path $tmp 'backups')
    Check ($res1.status -eq 'RECONCILED' -and $res1.reconciled_worker_pid -eq 0) 'Dead worker PID reconciles to 0'
    Check ($res1.next_instruction_preserved -eq $true) 'Next instruction preservation flagged as true'
    Check ($res1.dispatch_checkpoint_assert_pass -eq $true) 'Reconciled checkpoint passes Assert-ControllerDispatchCheckpoint'
    Check (Test-Path -LiteralPath $res1.backup_archive) 'Immutable backup archive exists'

    $read1 = Read-ControllerCheckpoint $cp1
    Check ($read1.process_id -eq 0) 'Read-ControllerCheckpoint confirms process_id is 0 on disk'
    Check ($read1.state -eq 'COMPLETED') 'Checkpoint state remains COMPLETED'
    Check ($read1.reconciliation.status -eq 'COMPLETED_WORKER_PID_RECONCILED') 'Reconciliation record status is COMPLETED_WORKER_PID_RECONCILED'

    # Test 2: Active worker PID is rejected (fail-closed)
    $activePid = $PID # Current PowerShell process is guaranteed active
    $cp2 = New-TestCheckpointFixture -WorkerPid $activePid
    $hash2 = (Get-FileHash -LiteralPath $cp2 -Algorithm SHA256).Hash
    $caught2 = $false
    try {
        & $scriptPath -Workspace $tmp -CheckpointPath $cp2 -ExpectedCheckpointHash $hash2 -ExpectedRunId 'test-run-158e8df8' -ExpectedTurn 10 -BackupDir (Join-Path $tmp 'backups')
    } catch {
        if ($_.Exception.Message -match 'worker process .* is still active') {
            $caught2 = $true
        }
    }
    Check $caught2 'Active worker process blocks reconciliation'
    $read2 = Read-ControllerCheckpoint $cp2
    Check ($read2.process_id -eq $activePid) 'Checkpoint with active worker remains unmodified'

    # Test 3: Active repository session is rejected
    $sessionData.active = $true
    $sessionData.task_id = 'SOME-OTHER-ACTIVE-TASK'
    [IO.File]::WriteAllText($sessionPath, ($sessionData | ConvertTo-Json), [Text.UTF8Encoding]::new($false))

    $cp3 = New-TestCheckpointFixture -WorkerPid $deadPid
    $hash3 = (Get-FileHash -LiteralPath $cp3 -Algorithm SHA256).Hash
    $caught3 = $false
    try {
        & $scriptPath -Workspace $tmp -CheckpointPath $cp3 -ExpectedCheckpointHash $hash3 -ExpectedRunId 'test-run-158e8df8' -ExpectedTurn 10 -BackupDir (Join-Path $tmp 'backups')
    } catch {
        if ($_.Exception.Message -match 'repository session is active') {
            $caught3 = $true
        }
    }
    Check $caught3 'Active repository session blocks reconciliation'

    # Restore session to inactive
    $sessionData.active = $false
    [IO.File]::WriteAllText($sessionPath, ($sessionData | ConvertTo-Json), [Text.UTF8Encoding]::new($false))

    # Test 4: Checkpoint hash mismatch is rejected
    $cp4 = New-TestCheckpointFixture -WorkerPid $deadPid
    $caught4 = $false
    try {
        & $scriptPath -Workspace $tmp -CheckpointPath $cp4 -ExpectedCheckpointHash 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' -ExpectedRunId 'test-run-158e8df8' -ExpectedTurn 10 -BackupDir (Join-Path $tmp 'backups')
    } catch {
        if ($_.Exception.Message -match 'checkpoint hash mismatch') {
            $caught4 = $true
        }
    }
    Check $caught4 'Mismatched checkpoint hash blocks reconciliation'

    # Test 5: Exact instruction preservation verified bitwise
    $complexInstruction = @"
AGY — CONTROLLER TURN 11: PRESERVE AND RECONCILE THE REPORTED R6 HPC SUBMISSION.

HPC STATUS
Job 1419807.mmaster02 was submitted to normal_imfdfkmq with 1 CPU, 16 GB, 8h.
Special characters: $ ` " ' \ / % & ! ^
"@
    $cp5 = New-TestCheckpointFixture -WorkerPid $deadPid -Instr $complexInstruction
    $hash5 = (Get-FileHash -LiteralPath $cp5 -Algorithm SHA256).Hash
    $res5 = & $scriptPath -Workspace $tmp -CheckpointPath $cp5 -ExpectedCheckpointHash $hash5 -ExpectedRunId 'test-run-158e8df8' -ExpectedTurn 10 -BackupDir (Join-Path $tmp 'backups')
    $read5 = Read-ControllerCheckpoint $cp5
    $beforeTextHash = Get-ControllerTextHash $complexInstruction
    $afterTextHash = Get-ControllerTextHash $read5.next_instruction
    Check ($beforeTextHash -eq $afterTextHash) 'Exact next_instruction text hash preserved bitwise'
    Check ($read5.next_instruction -ceq $complexInstruction) 'Exact next_instruction string equality preserved'

    # Test 6: Mutex contention blocks concurrent reconciliation
    $signal = Join-Path $tmp 'mutex_ready.txt'
    $subProc = Start-Process powershell.exe -ArgumentList "-NoProfile", "-Command", "`$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value; `$m = [Threading.Mutex]::new(`$false, ('Global\AdaptiveRemeshing.AgyController.' + `$sid)); if (`$m.WaitOne(10000)) { [IO.File]::WriteAllText('$signal', 'ok'); Start-Sleep -Seconds 5; `$m.ReleaseMutex() }; `$m.Dispose()" -PassThru -WindowStyle Hidden
    $w = 0
    while (-not (Test-Path $signal) -and $w -lt 60) {
        Start-Sleep -Milliseconds 100
        $w++
    }
    $caught6 = $false
    try {
        $cp6 = New-TestCheckpointFixture -WorkerPid $deadPid
        $hash6 = (Get-FileHash -LiteralPath $cp6 -Algorithm SHA256).Hash
        & $scriptPath -Workspace $tmp -CheckpointPath $cp6 -ExpectedCheckpointHash $hash6 -ExpectedRunId 'test-run-158e8df8' -ExpectedTurn 10 -BackupDir (Join-Path $tmp 'backups')
    } catch {
        if ($_.Exception.Message -match 'live autonomous controller owns workspace') {
            $caught6 = $true
        }
    } finally {
        if (-not $subProc.HasExited) {
            $null = $subProc.WaitForExit(6000)
        }
    }
    Check $caught6 'Mutex contention blocks concurrent reconciliation'

    Write-Host "`nAll $script:testIndex tests passed successfully." -ForegroundColor Green
} finally {
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
