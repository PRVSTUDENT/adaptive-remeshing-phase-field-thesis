$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. "$repo/scripts/controller/Controller-Recovery.ps1"
. "$repo/scripts/validation/Invoke-BoundedAgyProcess.ps1"
$n=0
function Check($ok,$why){if(-not $ok){throw $why};$script:n++;"PASS $why"}
$stream='{"event":"init","conversation_id":"x"}'+"`n"+'{"event":"step_update","step_update":{"state":"DONE"}}'
Check ((ConvertFrom-ControllerStream $stream) -eq $stream) 'unrecognized stream preserved'
Check ((Get-ControllerOutputEvidence $stream $stream).classification -eq 'MISSING_TERMINAL_RESPONSE') 'nonempty incomplete stream distinguished'
Check ((Get-ControllerOutputEvidence '' '').classification -eq 'EMPTY_STDOUT') 'empty stdout distinguished'
$complete=$stream+"`n"+'{"event":"result","result":{"status":"SUCCESS","conversation_id":"x","response":"Finished"}}'
$converted=ConvertFrom-ControllerStream $complete
Check (($converted|ConvertFrom-Json).response -eq 'Finished') 'successful stream conversion'
Check ((Get-ControllerOutputEvidence $complete $converted).terminal_response_present) 'terminal evidence found'
Check ((Get-ControllerOutputEvidence $complete '').classification -eq 'STREAM_CONVERSION_FAILURE') 'conversion loss distinguished'
Check ((Get-ControllerOutputEvidence $complete $converted 'pipe failed').classification -eq 'CAPTURE_READ_FAILURE') 'reader error retained'
$root=Join-Path $env:TEMP ('output-evidence-'+[guid]::NewGuid().ToString('N'));[IO.Directory]::CreateDirectory($root)|Out-Null
$cmd="[Console]::Out.WriteLine('"+$complete.Replace("'","''").Replace("`n", "');[Console]::Out.WriteLine('")+"');[Console]::Error.Write('warning');exit 7"
$encoded=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
$r=Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList @('-NoProfile','-EncodedCommand',$encoded) -TimeoutSeconds 20 -OutputLogPath "$root/raw"
Check ($r.ExitCode -eq 7 -and $r.NativeExitCode -eq 7) 'actual native exit retained'
Check ($r.Stdout.Contains('Finished') -and $r.Stderr -eq 'warning') 'exit-tail stdout stderr drained separately'
Check ([IO.File]::ReadAllText("$root/raw.stdout.txt") -eq $r.Stdout) 'stdout durable exact capture'
Check ((Get-Content "$root/raw.process.json" -Raw|ConvertFrom-Json).exit_code -eq 7) 'process evidence durable'
"ALL $n OUTPUT CHECKS PASSED"
# Exercise the capture-exception boundary without AGY, network or science.
$caught=$false
try{Invoke-BoundedAgyProcess -FilePath "$PSHOME/powershell.exe" -ArgumentList @('-NoProfile','-EncodedCommand',$encoded) -TimeoutSeconds 20 -OutputLogPath "$root/failure" -OnOutput {throw 'fixture callback failure'} | Out-Null}catch{$caught=$_.ToString() -match 'fixture callback failure'}
Check ($caught -and (Test-Path "$root/failure.process.json") -and (Test-Path "$root/failure.stdout.txt")) 'exception preserves process and raw evidence before propagation'
Check ((Get-ControllerOutputEvidence $stream (ConvertFrom-ControllerStream $stream)).classification -ne 'TERMINAL_RESPONSE_CAPTURED') 'step DONE cannot become completed result'
"FINAL $n OUTPUT CHECKS PASSED"
