function Invoke-BoundedAgyProcess {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [string[]]$ArgumentList = @(),
        [string]$InputText = '',
        [ValidateRange(1,86400)][int]$TimeoutSeconds = 2460,
        [string]$WorkingDirectory = (Get-Location).Path
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
    try {
        [void]$proc.Start()
        $stdout = $proc.StandardOutput.ReadToEndAsync()
        $stderr = $proc.StandardError.ReadToEndAsync()
        $write = $proc.StandardInput.WriteLineAsync($InputText)
        $timedOut = -not $write.Wait($TimeoutSeconds * 1000)
        if (-not $timedOut) {
            $proc.StandardInput.Close()
            while (-not $proc.WaitForExit(250)) {
                if ($clock.Elapsed.TotalSeconds -ge $TimeoutSeconds) { $timedOut = $true; break }
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
    finally { $proc.Dispose() }
}
