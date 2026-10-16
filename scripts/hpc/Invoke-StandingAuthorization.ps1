[CmdletBinding()]
param([switch]$EnrollStandingGrant,[switch]$VerifyOnly,[switch]$DryRun)
$ErrorActionPreference='Stop'
$repo='D:\Master thesis\Adaptive remeshing'
$package=Join-Path $repo 'models/pandey_kumar_mode1/48_method_c_stage_c1_0_restart_positive_control'
$manifestPath=Join-Path $package 'METHOD_C_RESTART_RECOVERY_AUTHORIZATION.json'
$servicePath=Join-Path $repo 'scripts/hpc/standing_authorization_service.py'
$service=[IO.File]::ReadAllBytes($servicePath)
$serviceHash=(Get-FileHash $servicePath).Hash.ToLowerInvariant()
if($EnrollStandingGrant -and $VerifyOnly){throw 'Enrollment and verification are separate modes'}
$request=@{mode='enroll'}
if(-not $EnrollStandingGrant){
 $batch=Get-Content $manifestPath -Raw|ConvertFrom-Json
 $manifestHash=(Get-FileHash $manifestPath).Hash.ToLowerInvariant()
 foreach($property in $batch.files.PSObject.Properties){
  if([IO.Path]::GetFileName($property.Name) -cne $property.Name){throw 'Unsafe manifest filename'}
  if((Get-FileHash (Join-Path $package $property.Name)).Hash.ToLowerInvariant() -cne $property.Value){throw "Candidate hash mismatch: $($property.Name)"}
 }
 if($DryRun){Write-Output "DRY_RUN: $($batch.batch_name); two exact commands; one replacement per failed parent; no credentials changed; no submissions.";return}
 $payload=@{files=$batch.files;manifest_sha256=$manifestHash;command_sha256=$batch.jobs[0].command_sha256;submission_queue='entry_imfdfkmq';batch=$batch}|ConvertTo-Json -Depth 20 -Compress
 $preflight=[IO.File]::ReadAllBytes((Join-Path $repo 'scripts/hpc/preflight_package48_authorization.py'))
 function Compress64([byte[]]$data){$b=New-Object IO.MemoryStream;$g=New-Object IO.Compression.GZipStream($b,[IO.Compression.CompressionMode]::Compress,$true);try{$g.Write($data,0,$data.Length)}finally{$g.Dispose()};$v=[Convert]::ToBase64String($b.ToArray());$b.Dispose();return $v}
 $code64=Compress64 $preflight
 $payload64=Compress64 ([Text.Encoding]::UTF8.GetBytes($payload))
 $remote="python3 -c 'import base64,gzip,sys;exec(gzip.decompress(base64.b64decode(sys.argv.pop(1))))' $code64 $payload64"
 Push-Location $repo
 try{$output=& powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand $remote;if($LASTEXITCODE -ne 0){throw "Actual preflight failed: $output"}}finally{Pop-Location}
 $evidence=($output|Out-String)|ConvertFrom-Json
 if(-not $evidence.passed){throw 'Actual notification/checkpoint/datacheck preflight failed'}
 Write-Output "PREFLIGHT_VERIFIED: restart datacheck=$($evidence.restart_datacheck); Telegram=$($evidence.telegram_notification_contract); compute delivery=$($evidence.compute_node_delivery)"
 if($VerifyOnly){Write-Output 'VERIFY_ONLY: no credentials changed';return}
 $request=@{mode='issue';batch_spec=$batch;manifest=$manifestHash;manifest_path=$manifestPath;package_path=$package;evidence=$evidence}
}elseif($DryRun){Write-Output 'DRY_RUN: human enrollment only; no grant or credentials changed';return}
# Enrollment is HUMAN ONLY. Controller mode can only derive bounded permits from an existing enrolled grant.
$request64=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(($request|ConvertTo-Json -Depth 24 -Compress)))
$source64=[Convert]::ToBase64String($service)
$result=& wsl.exe -d OpenClawGateway -u openclaw -- python3 -c "import base64,sys,hashlib;source=base64.b64decode(sys.argv.pop(1));expected=sys.argv[2];assert hashlib.sha256(source).hexdigest()==expected;exec(compile(source,'standing_authorization_service.py','exec'))" $source64 $request64 $serviceHash
if($LASTEXITCODE -ne 0){throw "Standing authorization refused: $result"}
Write-Output $result
