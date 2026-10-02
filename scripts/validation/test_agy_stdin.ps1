$multilinePrompt = @"
You are operating the PRV_ADAPTIVE_REMESHING project autonomous HPC workflow controller.

Follow the project governance rules strictly.

Report:
1. Confirm you received this multiline prompt.
2. Reply with the exact word: "READY".

Finished
"@

$agy = "C:\Users\pruth\AppData\Local\agy\bin\agy.exe"
$out = $multilinePrompt | & $agy --input-format text --dangerously-skip-permissions --output-format json 2>&1
$exitCode = $LASTEXITCODE
$text = ($out | Out-String).Trim()
Write-Host "Exit code: $exitCode"
Write-Host "Output:"
Write-Host $text
Write-Host "Exit code: $LASTEXITCODE"
Write-Host "Output type: $($out.GetType().FullName)"
Write-Host "Output snippet: $(($out | Out-String).Substring(0, [Math]::Min(120, ($out | Out-String).Length)))"
