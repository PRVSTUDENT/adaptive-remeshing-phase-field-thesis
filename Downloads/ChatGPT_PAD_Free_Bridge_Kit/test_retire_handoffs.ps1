$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Retire-OldSupervisorMaintenanceHandoffs.ps1') -LibraryOnly
$root=Join-Path ([IO.Path]::GetTempPath()) ('retire-handoffs-test-'+[guid]::NewGuid().ToString('N'))
$supervisor=Join-Path $root 'supervisor'
New-Item -ItemType Directory -Path $supervisor|Out-Null
$entries=[ordered]@{
 'fatal-0-ERROR.pending.json'='HND-SUP-a818a6a8255b4e4c95f9bf7f4fd5d389'
 'initial-0-INITIAL.pending.json'='HND-SUP-5c151680eb9d4f27bd5ee3bd9c3d38d5'
 'maintenance-hnd-trigger-fixed-20261101-0-ERROR.pending.json'='HND-SUP-795ada6b0e5e4e11b43e8223d4219b67'
 'maintenance-live-20261101-0-INITIAL.pending.json'='SUP-15ee2535c73d4cfdb4a5848b5435697c'
 'maintenance-live-launch-20261101-0-ERROR.pending.json'='SUP-9e36baf46c1140ce9c5f37458852ff14'
}
$script:count=0
function Check($ok,$message){if(!$ok){throw $message};$script:count++;Write-Output "PASS: $message"}
function Reject($action,$message){$failed=$false;try{&$action|Out-Null}catch{$failed=$true};Check $failed $message}
foreach($name in $entries.Keys){
 $id=$entries[$name];$dir=Join-Path $supervisor $id;New-Item -ItemType Directory -Path $dir|Out-Null
 [IO.File]::WriteAllText((Join-Path $dir 'request.txt'),"[BRIDGE_HANDOFF_ID=$id]`nMaintenance only")
 Write-NewRecoveryJson (Join-Path $supervisor $name) @{correlation_id=$id;archive=$dir}
}
$before=@{};foreach($f in Get-ChildItem $supervisor -Filter '*.pending.json'){$before[$f.Name]=(Get-FileHash $f.FullName).Hash}
$plan=@(Get-MaintenanceRetirementPlan $root)
Check ($plan.Count -eq 5 -and @($plan|Where-Object uncertainty -eq 'NO_ERROR_OR_RESPONSE_UNCERTAIN').Count -eq 5) 'Both old prefixes retain uncertain outcomes without inventing timeouts'
Check (@(Get-ChildItem $supervisor -Filter '*.pending.json').Count -eq 5) 'Preview preserves all original pending markers'
$extra=Join-Path $supervisor 'unexpected.pending.json';[IO.File]::WriteAllText($extra,'{}')
Reject {Get-MaintenanceRetirementPlan $root} 'An unexpected sixth transaction blocks retirement'
Move-Item -LiteralPath $extra -Destination (Join-Path $root 'extra-preserved.json')
$decision=Join-Path (Join-Path $supervisor $entries['fatal-0-ERROR.pending.json']) 'decision.json';[IO.File]::WriteAllText($decision,'{}')
Reject {Get-MaintenanceRetirementPlan $root} 'Existing decision blocks abandonment'
Move-Item -LiteralPath $decision -Destination (Join-Path $root 'decision-preserved.json')
$first=$plan[0];$original=[IO.File]::ReadAllBytes($first.source);[IO.File]::AppendAllText($first.source,' ')
Reject {Assert-MaintenanceRetirementPins $plan} 'Changed marker fails the preview checksum'
[IO.File]::WriteAllBytes($first.source,$original)
$evidencePath=Join-Path (Join-Path $supervisor $first.correlation_id) 'request.txt';$originalRequest=[IO.File]::ReadAllBytes($evidencePath)
[IO.File]::AppendAllText($evidencePath,' changed')
Reject {Assert-MaintenanceRetirementPins $plan} 'Changed original evidence blocks application'
[IO.File]::WriteAllBytes($evidencePath,$originalRequest)
$batch=Move-MaintenanceRetirementPlan $root $plan 'COMPLETED'
$same=$true;foreach($name in $before.Keys){if((Get-FileHash (Join-Path $batch $name)).Hash -cne $before[$name]){$same=$false}}
Check ($same -and @(Get-ChildItem $supervisor -Filter '*.pending.json').Count -eq 0 -and (Test-Path (Join-Path $batch 'completed.json'))) 'Apply preserves exact marker bytes under an immutable recovery manifest'
Check (@(Get-MaintenanceRetirementPlan $root).Count -eq 0) 'Restart finds no transactions to replay or retire again'
Write-Output "ALL $count RETIREMENT CHECKS PASS (TEMPORARY FIXTURES ONLY)."
