# Reliable noninteractive local engine transport for Windows PowerShell 5.1.
$script:Mode1EnginePython=(Get-Command python.exe -ErrorAction Stop).Source
$script:Mode1EnginePath=Join-Path $PSScriptRoot 'mode1_execution_gate.py'
function Invoke-Mode1Engine {
 param([Parameter(Mandatory)][string[]]$Arguments,[string]$InputJson='')
 $valid=($Arguments.Count -eq 1 -and $Arguments[0] -eq '--prepare') -or ($Arguments.Count -eq 2 -and (($Arguments[0] -eq '--status' -and $Arguments[1] -match '^[a-f0-9]{64}$') -or ($Arguments[0] -eq '--command64' -and $Arguments[1] -match '^[A-Za-z0-9+/=]+$')))
 if(-not $valid){throw 'Invalid technical engine arguments'}
 if($Arguments[0] -eq '--prepare' -and [string]::IsNullOrWhiteSpace($InputJson)){throw 'Empty preflight JSON before starting engine'}
 $start=[Diagnostics.ProcessStartInfo]::new($script:Mode1EnginePython)
 $start.Arguments='"'+$script:Mode1EnginePath+'" '+($Arguments -join ' ')
 $start.UseShellExecute=$false;$start.CreateNoWindow=$true
 $start.RedirectStandardInput=$true;$start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
 $process=[Diagnostics.Process]::new();$process.StartInfo=$start
 try {
  if(-not $process.Start()){throw 'Local technical engine did not start'}
  $out=$process.StandardOutput.ReadToEndAsync();$err=$process.StandardError.ReadToEndAsync()
  if($InputJson){$process.StandardInput.WriteLine([Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($InputJson)))}
  $process.StandardInput.Close()
  if(-not $process.WaitForExit(120000)){$process.Kill();throw 'Technical engine timeout; reconcile existing attempts before proceeding'}
  $text=$out.Result.Trim();$errorText=$err.Result.Trim()
  if($process.ExitCode -ne 0 -and -not $text){throw "Technical engine failed: $errorText"}
  if(-not $text){throw 'Technical engine returned no result'}
  $result=$text|ConvertFrom-Json
  if($process.ExitCode -ne 0 -and $result.decision -ne 'deny'){throw 'Technical engine exited unsuccessfully; no submission allowed'}
  return $result
 } finally {$process.Dispose()}
}
