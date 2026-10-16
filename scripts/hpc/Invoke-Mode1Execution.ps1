[CmdletBinding()]
param([string]$ManifestPath='', [switch]$VerifyOnly, [switch]$DryRun, [switch]$PrepareOnly)
$ErrorActionPreference='Stop'
$repo='D:\Master thesis\Adaptive remeshing'
if(-not $ManifestPath){$ManifestPath=Join-Path $repo 'models/pandey_kumar_mode1/49_method_c_stage_c1_1_nonmatching_transfer/METHOD_C_STAGE_C1_1_AUTHORIZATION.json'}
$ManifestPath=[IO.Path]::GetFullPath($ManifestPath)
if(-not $ManifestPath.StartsWith((Join-Path $repo 'models/pandey_kumar_mode1/'),[StringComparison]::OrdinalIgnoreCase)){throw 'Manifest outside active Mode-I scope'}
$batch=Get-Content $ManifestPath -Raw|ConvertFrom-Json
foreach($property in $batch.files.PSObject.Properties){
 if([IO.Path]::GetFileName($property.Name) -cne $property.Name){throw 'Unsafe filename'}
 if((Get-FileHash (Join-Path (Split-Path -Parent $ManifestPath) $property.Name)).Hash.ToLowerInvariant() -cne $property.Value){throw "Candidate hash mismatch: $($property.Name)"}
}
if($DryRun){Write-Output "DRY_RUN: technical preflight then once-only execution of ready jobs; no human authorization, issuer, grant pin or permit activation";return}
function Compress64([byte[]]$data){$b=New-Object IO.MemoryStream;$g=New-Object IO.Compression.GZipStream($b,[IO.Compression.CompressionMode]::Compress,$true);try{$g.Write($data,0,$data.Length)}finally{$g.Dispose()};$v=[Convert]::ToBase64String($b.ToArray());$b.Dispose();return $v}
$manifestHash=(Get-FileHash $ManifestPath).Hash.ToLowerInvariant()
$payload=@{files=$batch.files;manifest_sha256=$manifestHash;command_sha256=$batch.jobs[0].command_sha256;submission_queue='entry_imfdfkmq';batch=$batch}|ConvertTo-Json -Depth 30 -Compress
$code64=Compress64 ([IO.File]::ReadAllBytes((Join-Path $repo 'scripts/hpc/preflight_package49_authorization.py')))
$data64=Compress64 ([Text.Encoding]::UTF8.GetBytes($payload))
$remote="python3 -c 'import base64,gzip,sys;exec(gzip.decompress(base64.b64decode(sys.argv.pop(1))))' $code64 $data64"
Push-Location $repo
try {
 $output=& powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand $remote
 if($LASTEXITCODE -ne 0){throw "Technical preflight failed: $output"}
 $proof=($output|Out-String)|ConvertFrom-Json
 if(-not $proof.passed){throw 'Technical qualification did not pass'}
 Write-Output "TECHNICAL_PREFLIGHT_PASS: datachecks=$($proof.datacheck_verified); active jobs=$($proof.active_job_count); login notifications verified; compute delivery=$($proof.compute_node_delivery)"
 if($VerifyOnly){Write-Output 'VERIFY_ONLY: no submission or execution-state change';return}
 . (Join-Path $repo 'scripts/hpc/Invoke-Mode1Engine.ps1')
 $request=@{manifest_path=$ManifestPath;preflight=$proof}|ConvertTo-Json -Depth 30 -Compress
 $prepared=Invoke-Mode1Engine -Arguments @('--prepare') -InputJson $request
 if($prepared.decision -eq 'deny'){throw $prepared.reason}
 $key=$prepared.manifest_sha256
 Write-Output 'QUALIFIED_EXECUTION_READY: no human authorization required; prior submissions preserved'
 if($PrepareOnly){return}
 $status=Invoke-Mode1Engine -Arguments @('--status',$key)
 if($status.decision -eq 'deny'){throw $status.reason}
 foreach($blocked in $status.blocked_jobs){Write-Output "SCIENTIFIC_DEPENDENCY: $($blocked.job): $($blocked.reason)"}
 if(-not @($status.ready_jobs).Count){Write-Output 'NO_NEW_JOB_READY: previously submitted jobs preserved; evaluate scientific dependencies';return}
 foreach($job in $status.ready_jobs){& (Join-Path $repo 'scripts/hpc/Submit-Mode1Batch.ps1') -ManifestPath $ManifestPath -Job $job}
} finally {Pop-Location}
