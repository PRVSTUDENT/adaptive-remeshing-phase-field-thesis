. .\scripts\validation\Invoke-BoundedAgyProcess.ps1
$proc = "C:\Users\pruth\AppData\Local\Programs\Python\Python313\python.exe"
$res = Invoke-BoundedAgyProcess -FilePath $proc -ArgumentList @("scripts/validation/make_prep_artifact.py") -TimeoutSeconds 60
Write-Output "ExitCode: $($res.ExitCode)"
Write-Output "Duration: $($res.DurationSeconds)"
Write-Output $res.Output
