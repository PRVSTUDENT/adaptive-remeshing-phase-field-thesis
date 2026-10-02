# Apply SSH Non-Interactive Safety Guards to Antigravity-Autonomous-Loop.ps1
$targetFile = "C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"

if (-not (Test-Path -LiteralPath $targetFile)) {
    Write-Error "Target file not found: $targetFile"
    exit 1
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "$targetFile.backup_before_ssh_safety_$timestamp"
Copy-Item -LiteralPath $targetFile -Destination $backupFile -Force
Write-Host "Created backup: $backupFile"

$content = [System.IO.File]::ReadAllText($targetFile, [System.Text.UTF8Encoding]::new($false))

# 1. Inject Rule 16 into $PersistentAgentGuard
$rule15Anchor = "15. A missing temporary brain artifact must never trigger a new PBS submission,`r`n    repeat a completed HPC calculation, or broaden the scientific task. Recover`r`n    locally from existing evidence and continue the current turn."
if (-not $content.Contains($rule15Anchor)) {
    $rule15Anchor = "15. A missing temporary brain artifact must never trigger a new PBS submission,`n    repeat a completed HPC calculation, or broaden the scientific task. Recover`n    locally from existing evidence and continue the current turn."
}

$rule16Block = @'


16. REMOTE COMMAND SAFETY - MANDATORY:
    - All noninteractive SSH commands must use `ssh -n -T` and `-o BatchMode=yes`.
    - The `-n` flag is strictly required to disconnect stdin from null and prevent remote tools
      from hanging indefinitely waiting on console input.
    - Never wrap simple remote inspection commands in nested `bash -c`, `bash -lc`, or `sh -c`.
      Pass the remote command directly to SSH with explicit arguments.
    - Never execute bare `tail`, bare `cat`, bare `grep`, or another program that can wait on stdin.
    - Prefer calling `powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "..."`.
    - Every SSH command must have a bounded execution timeout (default 120s). A timed-out command
      must terminate only its own spawned SSH process, return a tool failure, and allow recovery.
    - For complex multi-command remote logic, use a controlled temporary remote script rather than
      nested shell quoting.
'@

if ($content -notmatch '16\.\s+REMOTE COMMAND SAFETY - MANDATORY') {
    if ($content.Contains($rule15Anchor)) {
        $replacement = $rule15Anchor + $rule16Block
        $content = $content.Replace($rule15Anchor, $replacement)
        Write-Host "Injected Rule 16 into `$PersistentAgentGuard"
    } else {
        Write-Warning "Could not find Rule 15 anchor; searching line by line"
        $idx = $content.IndexOf("15. A missing temporary brain artifact")
        if ($idx -gt 0) {
            $endIdx = $content.IndexOf('"@', $idx)
            if ($endIdx -gt 0) {
                $content = $content.Substring(0, $endIdx) + $rule16Block + "`r`n" + $content.Substring($endIdx)
                Write-Host "Injected Rule 16 before closing quote of `$PersistentAgentGuard"
            }
        }
    }
} else {
    Write-Host "Rule 16 already present in `$PersistentAgentGuard"
}

# 2. Add -n -T -o BatchMode=yes -o ConnectTimeout=20 to Query-Scheduler-Direct (line ~374)
$old374 = '$raw = & $sshPath -F $ConfigPath $HostAlias $remoteCommand 2>&1'
$new374 = '$raw = & $sshPath -n -T -o BatchMode=yes -o ConnectTimeout=20 -F $ConfigPath $HostAlias $remoteCommand 2>&1'
if ($content.Contains($old374)) {
    $content = $content.Replace($old374, $new374)
    Write-Host "Updated Query-Scheduler-Direct ssh call with -n -T"
}

# 3. Add -n -T -o BatchMode=yes -o ConnectTimeout=20 to other controller ssh calls
$oldBlock1 = @'
        $result = & ssh `
            -F $sshConfig `
            tu_freiberg `
            "qstat -u pr21vyci" 2>&1
'@
$newBlock1 = @'
        $result = & ssh `
            -n -T `
            -o BatchMode=yes `
            -o ConnectTimeout=20 `
            -F $sshConfig `
            tu_freiberg `
            "qstat -u pr21vyci" 2>&1
'@
if ($content.Contains($oldBlock1)) {
    $content = $content.Replace($oldBlock1, $newBlock1)
    Write-Host "Updated controller qstat ssh call with -n -T"
}

$oldBlock2 = @'
        $output = & ssh `
            -F $sshConfig `
            tu_freiberg `
            $remoteCommand 2>&1
'@
$newBlock2 = @'
        $output = & ssh `
            -n -T `
            -o BatchMode=yes `
            -o ConnectTimeout=20 `
            -F $sshConfig `
            tu_freiberg `
            $remoteCommand 2>&1
'@
if ($content.Contains($oldBlock2)) {
    $content = $content.Replace($oldBlock2, $newBlock2)
    Write-Host "Updated controller remoteCommand ssh call with -n -T"
}

$oldBlock3 = @'
            $SchedulerResult = & ssh `
                -F $sshConfig `
                tu_freiberg `
                $RemoteCommand 2>&1
'@
$newBlock3 = @'
            $SchedulerResult = & ssh `
                -n -T `
                -o BatchMode=yes `
                -o ConnectTimeout=20 `
                -F $sshConfig `
                tu_freiberg `
                $RemoteCommand 2>&1
'@
if ($content.Contains($oldBlock3)) {
    $content = $content.Replace($oldBlock3, $newBlock3)
    Write-Host "Updated controller SchedulerResult ssh call with -n -T"
}

# 4. Validate AST syntax before writing
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseInput($content, [ref]$tokens, [ref]$errors)
if ($errors -and $errors.Count -gt 0) {
    Write-Error "PowerShell syntax validation failed with $($errors.Count) errors:"
    foreach ($err in $errors) {
        Write-Error "  Line $($err.Extent.StartLineNumber): $($err.Message)"
    }
    exit 1
}

[System.IO.File]::WriteAllText($targetFile, $content, [System.Text.UTF8Encoding]::new($false))
Write-Host "PowerShell syntax validation: PASS (0 errors)."
Write-Host "Successfully patched $targetFile."
