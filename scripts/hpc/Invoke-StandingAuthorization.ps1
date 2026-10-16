[CmdletBinding()]
param([switch]$EnrollStandingGrant,[switch]$UpgradeStandingGrant,[switch]$VerifyOnly,[switch]$DryRun,
      [switch]$SubmitReady,[string]$ManifestPath='')
$ErrorActionPreference='Stop'
$repo='D:\Master thesis\Adaptive remeshing'
if(-not $ManifestPath){$ManifestPath=Join-Path $repo 'models/pandey_kumar_mode1/49_method_c_stage_c1_1_nonmatching_transfer/METHOD_C_STAGE_C1_1_AUTHORIZATION.json'}
$ManifestPath=[IO.Path]::GetFullPath($ManifestPath)
$modelsRoot=Join-Path $repo 'models/pandey_kumar_mode1/'
if(-not $ManifestPath.StartsWith($modelsRoot,[StringComparison]::OrdinalIgnoreCase)){throw 'Manifest outside Mode-I models'}
$package=Split-Path -Parent $ManifestPath
$servicePath=Join-Path $repo 'scripts/hpc/standing_authorization_service.py'
$service=[IO.File]::ReadAllBytes($servicePath)
$serviceHash=(Get-FileHash $servicePath).Hash.ToLowerInvariant()
if(($EnrollStandingGrant -or $UpgradeStandingGrant) -and $VerifyOnly){throw 'Human trust changes and verification are separate modes'}
if($EnrollStandingGrant -and $UpgradeStandingGrant){throw 'Choose enrollment or upgrade, never both'}
function Compress64([byte[]]$data){$b=New-Object IO.MemoryStream;$g=New-Object IO.Compression.GZipStream($b,[IO.Compression.CompressionMode]::Compress,$true);try{$g.Write($data,0,$data.Length)}finally{$g.Dispose()};$v=[Convert]::ToBase64String($b.ToArray());$b.Dispose();return $v}
function Invoke-Issuer($Request){
 $request64=Compress64 ([Text.Encoding]::UTF8.GetBytes(($Request|ConvertTo-Json -Depth 30 -Compress)))
 $source64=Compress64 $service
 $output=& wsl.exe -d OpenClawGateway -u openclaw -- python3 -c "import base64,gzip,sys,hashlib;source=gzip.decompress(base64.b64decode(sys.argv.pop(1)));expected=sys.argv[2];assert hashlib.sha256(source).hexdigest()==expected;exec(compile(source,'standing_authorization_service.py','exec'))" $source64 $request64 $serviceHash
 if($LASTEXITCODE -ne 0){throw 'Standing issuer refused; no bypass or counter reset permitted'}
 Write-Output $output
}
if($EnrollStandingGrant -or $UpgradeStandingGrant){
 # HUMAN ONLY. The controller may derive permits, but never enroll or upgrade trust.
 if($DryRun){Write-Output 'DRY_RUN: human trust upgrade/enrollment; preserved grant identity, resources and consumed counters; no live state change';return}
 $mode=if($UpgradeStandingGrant){'upgrade'}else{'enroll'}
 Invoke-Issuer @{mode=$mode}
 if(-not $SubmitReady){return}
}
$batch=Get-Content $ManifestPath -Raw|ConvertFrom-Json
$manifestHash=(Get-FileHash $ManifestPath).Hash.ToLowerInvariant()
foreach($property in $batch.files.PSObject.Properties){
 if([IO.Path]::GetFileName($property.Name) -cne $property.Name){throw 'Unsafe manifest filename'}
 if((Get-FileHash (Join-Path $package $property.Name)).Hash.ToLowerInvariant() -cne $property.Value){throw "Candidate hash mismatch: $($property.Name)"}
}
if($DryRun){Write-Output "DRY_RUN: $($batch.batch_name); exact immutable commands; resource/dependency gates; no credential mutation or submission";return}

$payload=@{files=$batch.files;manifest_sha256=$manifestHash;command_sha256=$batch.jobs[0].command_sha256;submission_queue='entry_imfdfkmq';batch=$batch}|ConvertTo-Json -Depth 30 -Compress
$preflightRel=if($batch.adapter -eq 'mode1-qualified-batch-v2'){'scripts/hpc/preflight_package49_authorization.py'}else{'scripts/hpc/preflight_package48_authorization.py'}
$code64=Compress64 ([IO.File]::ReadAllBytes((Join-Path $repo $preflightRel)))
$payload64=Compress64 ([Text.Encoding]::UTF8.GetBytes($payload))
$remote="python3 -c 'import base64,gzip,sys;exec(gzip.decompress(base64.b64decode(sys.argv.pop(1))))' $code64 $payload64"
Push-Location $repo
try{$output=& powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand $remote;if($LASTEXITCODE -ne 0){throw "Actual qualification failed: $output"}}finally{Pop-Location}
$evidence=($output|Out-String)|ConvertFrom-Json
if(-not $evidence.passed){throw 'Qualification failed'}
Write-Output "PREFLIGHT_VERIFIED: $($evidence.datacheck_verified); login Telegram=$($evidence.telegram_notification_contract); compute delivery=$($evidence.compute_node_delivery)"
if($VerifyOnly){Write-Output 'VERIFY_ONLY: no credentials changed';return}
Invoke-Issuer @{mode='issue';batch_spec=$batch;manifest=$manifestHash;manifest_path=$ManifestPath;package_path=$package;evidence=$evidence}
if($SubmitReady){
 $countCode="import json; s=json.load(open('/home/openclaw/.openclaw/workspace-antigravity-controller/controller-state.json')); print(json.dumps(s['submission_authorization'].get('command_consumption',{})))"
 $count64=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($countCode))
 $countsRaw=& wsl.exe -d OpenClawGateway -u openclaw -- python3 -c "import base64;exec(base64.b64decode('$count64'))"
 if($LASTEXITCODE -ne 0){throw 'Cannot verify consumed slots; no submission attempted'}
 $counts=($countsRaw|Out-String)|ConvertFrom-Json
 $reviewReady=$false
 if($batch.dependency_review_path){
  $reviewPath=Join-Path $repo $batch.dependency_review_path
  if(Test-Path -LiteralPath $reviewPath){$review=Get-Content $reviewPath -Raw|ConvertFrom-Json;$reviewReady=($review.batch_manifest_sha256 -ceq $manifestHash -and $review.scientific_review -ceq 'PASS')}
 }
 $ready=@($batch.jobs|Where-Object {(-not $counts.PSObject.Properties[$_.command_sha256] -or $counts.PSObject.Properties[$_.command_sha256].Value -eq 0) -and ((-not $_.depends_on.Count) -or $reviewReady)})
 if(-not $ready.Count){Write-Output 'NO_JOB_READY: slots consumed or predecessor scientific review pending; no new human research approval required'}
 foreach($job in $ready){& (Join-Path $repo 'scripts/hpc/Submit-Mode1Batch.ps1') -ManifestPath $ManifestPath -Job $job.id}
}
