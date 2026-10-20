function Invoke-BoundedAgyProcess {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [string[]]$ArgumentList = @(),
        [string]$InputText = '',
        [ValidateRange(1,86400)][int]$TimeoutSeconds = 2460,
        [string]$WorkingDirectory = (Get-Location).Path,
        [scriptblock]$Checkpoint = {},
        [scriptblock]$OnStarted = {},
        [int]$CheckpointIntervalSeconds = 15
    )
    # Windows CommandLineToArgvW quoting, including trailing backslashes.
    $quoted = foreach ($arg in $ArgumentList) {
        '"' + ([regex]::Replace(([regex]::Replace($arg, '(\\*)"', '$1$1\"')), '(\\+)$', '$1$1')) + '"'
    }
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $FilePath
    $info.Arguments = $quoted -join ' '
    $info.WorkingDirectory = $WorkingDirectory
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardInput = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $info
    $clock = [Diagnostics.Stopwatch]::StartNew()
    $nextCheckpoint = $CheckpointIntervalSeconds
    $started = $false
    try {
        [void]$proc.Start()
        $started = $true
        & $OnStarted $proc.Id | Out-Null
        & $Checkpoint | Out-Null
        $stdout = $proc.StandardOutput.ReadToEndAsync()
        $stderr = $proc.StandardError.ReadToEndAsync()
        $write = $proc.StandardInput.WriteLineAsync($InputText)
        $timedOut = $false
        try {
            while (-not $write.Wait(250)) {
                if ($clock.Elapsed.TotalSeconds -ge $TimeoutSeconds) { $timedOut=$true; break }
                if ($clock.Elapsed.TotalSeconds -ge $nextCheckpoint) {
                    & $Checkpoint | Out-Null
                    $nextCheckpoint = $clock.Elapsed.TotalSeconds + $CheckpointIntervalSeconds
                }
            }
        }
        catch {
            # A CLI may exit before consuming stdin; still collect its real exit/output.
            $cause=$_.Exception.GetBaseException()
            if ($cause -isnot [IO.IOException] -and $cause -isnot [ObjectDisposedException]) { throw }
        }
        if (-not $timedOut) {
            try { $proc.StandardInput.Close() } catch [IO.IOException] { }
            while (-not $proc.WaitForExit(250)) {
                if ($clock.Elapsed.TotalSeconds -ge $TimeoutSeconds) { $timedOut = $true; break }
                if ($clock.Elapsed.TotalSeconds -ge $nextCheckpoint) {
                    & $Checkpoint | Out-Null
                    $nextCheckpoint = $clock.Elapsed.TotalSeconds + $CheckpointIntervalSeconds
                }
            }
        }
        if ($timedOut) {
            # Target only this invocation's process tree; never a shared server or scheduler.
            $killer = Start-Process -FilePath "$env:SystemRoot/System32/taskkill.exe" -ArgumentList @('/PID', $proc.Id, '/T', '/F') -WindowStyle Hidden -PassThru
            if (-not $killer.WaitForExit(5000)) { $killer.Kill() }
            if (-not $proc.WaitForExit(2000)) { throw "Watchdog could not terminate owned CLI PID $($proc.Id)" }
        }
        # Descendants may inherit pipe handles: never wait indefinitely on EOF.
        $outText = if ($stdout.Wait(2000)) { $stdout.Result } else { '[stdout pipe did not close]' }
        $errText = if ($stderr.Wait(2000)) { $stderr.Result } else { '[stderr pipe did not close]' }
        [pscustomobject]@{
            ExitCode = $(if ($timedOut) {124} else {$proc.ExitCode})
            TimedOut = $timedOut
            Output = "$outText`r`n$errText"
            DurationSeconds = $clock.Elapsed.TotalSeconds
        }
    }
    finally {
        # Also clean up on checkpoint callback/pipe errors, targeting this invocation only.
        if ($started -and -not $proc.HasExited) {
            $killer = Start-Process -FilePath "$env:SystemRoot/System32/taskkill.exe" -ArgumentList @('/PID', $proc.Id, '/T', '/F') -WindowStyle Hidden -PassThru
            if (-not $killer.WaitForExit(5000)) { $killer.Kill() }
            $killer.Dispose()
        }
        $proc.Dispose()
    }
}
