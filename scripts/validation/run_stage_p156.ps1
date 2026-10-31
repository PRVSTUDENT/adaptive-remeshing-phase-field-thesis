. .\scripts\validation\Invoke-BoundedAgyProcess.ps1
$proc = "C:\Users\pruth\AppData\Local\Programs\Python\Python313\python.exe"
$res = Invoke-BoundedAgyProcess -FilePath $proc -ArgumentList @("scripts/validation/stage_package156_candidate.py") -TimeoutSeconds 600
Write-Output "ExitCode: $($res.ExitCode)"
Write-Output "Duration: $($res.DurationSeconds)"
Write-Output $res.Output
