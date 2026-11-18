$proc = Get-CimInstance Win32_Process -Filter "Name='PAD.RobotV2.exe'"
foreach ($p in $proc) {
    Write-Host "PID: $($p.ProcessId)"
    Write-Host "CommandLine: $($p.CommandLine)"
}
