$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../scripts/validation/Invoke-BoundedAgyProcess.ps1"
$shell = "$env:SystemRoot/System32/WindowsPowerShell/v1.0/powershell.exe"
$r = Invoke-BoundedAgyProcess -FilePath $shell -ArgumentList @('-NoProfile','-Command', '$x=[Console]::In.ReadToEnd(); [Console]::Out.Write($x); [Console]::Error.Write("stderr-ok"); exit 7') -InputText 'input with "quotes" and spaces' -TimeoutSeconds 10
if ($r.ExitCode -ne 7 -or $r.TimedOut -or $r.Output -notmatch 'stderr-ok' -or $r.Output -notmatch 'input with "quotes" and spaces') { throw "Exit/input/output regression: $($r|ConvertTo-Json)" }
$r = Invoke-BoundedAgyProcess -FilePath $shell -ArgumentList @('-NoProfile','-Command','Start-Sleep -Seconds 60') -TimeoutSeconds 1
if (-not $r.TimedOut -or $r.ExitCode -ne 124 -or $r.DurationSeconds -gt 12) { throw 'Timeout regression' }
'PASS: quoted stdin, stdout/stderr, nonzero exit, bounded timeout and termination'
