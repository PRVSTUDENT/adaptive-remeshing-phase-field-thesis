. .\scripts\validation\Invoke-BoundedAgyProcess.ps1
$proc = "C:\Users\pruth\AppData\Local\Programs\Python\Python313\python.exe"
$res = Invoke-BoundedAgyProcess -FilePath $proc -ArgumentList @("-m", "unittest", "tests/unit/test_package156_initialization_recovery.py") -TimeoutSeconds 120
Write-Output "ExitCode: $($res.ExitCode)"
Write-Output "Duration: $($res.DurationSeconds)"
Write-Output $res.Output
