[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$Workspace = 'D:\Master thesis\Adaptive remeshing',
    [string]$BridgeDir = (Join-Path $env:USERPROFILE 'OpenClawPAD\ChatGPTBridge'),
    [switch]$LibraryOnly
)
$ErrorActionPreference = 'Stop'

function Get-MaintenanceRetirementPlan([string]$BridgeRoot) {
    $expected = [ordered]@{
        'fatal-0-ERROR.pending.json'='HND-SUP-a818a6a8255b4e4c95f9bf7f4fd5d389'
        'initial-0-INITIAL.pending.json'='HND-SUP-5c151680eb9d4f27bd5ee3bd9c3d38d5'
        'maintenance-hnd-trigger-fixed-20261101-0-ERROR.pending.json'='HND-SUP-795ada6b0e5e4e11b43e8223d4219b67'
        'maintenance-live-20261101-0-INITIAL.pending.json'='SUP-15ee2535c73d4cfdb4a5848b5435697c'
        'maintenance-live-launch-20261101-0-ERROR.pending.json'='SUP-9e36baf46c1140ce9c5f37458852ff14'
    }
    $supervisor = [IO.Path]::GetFullPath((Join-Path $BridgeRoot 'supervisor'))
    $all = @(Get-ChildItem -LiteralPath $supervisor -Filter '*.pending.json' -File -ErrorAction Stop)
    if(!$all.Count){return}
    if($all.Count -ne 5 -or @($all|Where-Object {$_.Name -notin $expected.Keys}).Count){
        throw 'STOP: pending set differs from the five explicitly named historical transactions'
    }
    foreach($file in $all){
        $meta = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
        $id = $expected[$file.Name]
        if($meta.correlation_id -cne $id){throw "STOP: historical filename/ID mismatch: $($file.Name)"}
        $dir = [IO.Path]::GetFullPath((Join-Path $supervisor $id))
        if([IO.Path]::GetFullPath([string]$meta.archive) -ine $dir -or
           !(Test-Path -LiteralPath $dir -PathType Container)){throw "STOP: original archive mismatch/missing: $id"}
        if(Test-Path -LiteralPath (Join-Path $dir 'decision.json')){throw "STOP: validated planning decision requires separate reconciliation: $id"}
        $request = Join-Path $dir 'request.txt'
        if(Test-Path -LiteralPath $request){
            $text = Get-Content -LiteralPath $request -Raw
            $marker = [regex]::Match($text,'(?m)^\s*\[BRIDGE_HANDOFF_ID=([^\]]+)\]\s*$')
            if(!$marker.Success -or $marker.Groups[1].Value -cne $id){throw "STOP: original request identity mismatch: $id"}
        }
        $evidence = [ordered]@{}
        foreach($name in @('request.txt','evidence.json','transport_error.txt','response.txt')){
            $path=Join-Path $dir $name
            if(Test-Path -LiteralPath $path){$evidence[$path]=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash}
        }
        $archive=Join-Path $BridgeRoot 'archive'
        if(Test-Path -LiteralPath $archive){
            foreach($response in @(Get-ChildItem -LiteralPath $archive -Filter "response_*_$id.json" -File)){
                $evidence[$response.FullName]=(Get-FileHash -LiteralPath $response.FullName -Algorithm SHA256).Hash
            }
        }
        $replyPresent=Test-Path -LiteralPath (Join-Path $dir 'response.txt')
        $errorPresent=Test-Path -LiteralPath (Join-Path $dir 'transport_error.txt')
        [pscustomobject]@{
            name=$file.Name;correlation_id=$id;source=$file.FullName
            sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
            disposition='ABANDONED_OLD_MAINTENANCE_PLANNING_NO_REPLAY'
            uncertainty=$(if($replyPresent){'UNDECIDED_REPLY_PRESERVED'}elseif($errorPresent){'ERROR_RECORDED_UNDECIDED'}else{'NO_ERROR_OR_RESPONSE_UNCERTAIN'})
            evidence_sha256=$evidence
        }
    }
}

function Assert-MaintenanceRetirementPins($Plan){
    foreach($item in $Plan){
        if(!(Test-Path -LiteralPath $item.source) -or (Get-FileHash -LiteralPath $item.source).Hash -cne $item.sha256){throw 'STOP: pending marker changed after preview'}
        $dir=Join-Path (Split-Path $item.source) $item.correlation_id
        if(Test-Path -LiteralPath (Join-Path $dir 'decision.json')){throw 'STOP: decision appeared during recovery'}
        foreach($path in $item.evidence_sha256.Keys){
            if(!(Test-Path -LiteralPath $path) -or (Get-FileHash -LiteralPath $path).Hash -cne $item.evidence_sha256[$path]){throw 'STOP: original evidence changed after preview'}
        }
    }
}

function Write-NewRecoveryJson([string]$Path,$Value){
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 16))
    $stream=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
}

function Move-MaintenanceRetirementPlan([string]$BridgeRoot,$Plan,$CheckpointState){
    Assert-MaintenanceRetirementPins $Plan
    $supervisor=[IO.Path]::GetFullPath((Join-Path $BridgeRoot 'supervisor'))
    $batch=Join-Path (Join-Path $supervisor 'retired_planning_handoffs') ('explicit_abandon_'+[guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $batch -ErrorAction Stop|Out-Null
    Write-NewRecoveryJson (Join-Path $batch 'manifest.json') ([ordered]@{
        classification='USER_DIRECTED_ABANDONMENT_UNCERTAIN_MAINTENANCE_ONLY'
        reason='Explicit user instruction 1 November 2026: retire these five old planning transactions without executing their instructions; not certified timeouts or success.'
        created_utc=[DateTimeOffset]::UtcNow.ToString('o');checkpoint_state=$CheckpointState
        original_handoffs=$Plan
    })
    foreach($item in $Plan){
        $source=[IO.Path]::GetFullPath($item.source)
        $destination=Join-Path $batch $item.name
        if((Split-Path $source) -ine $supervisor -or (Split-Path ([IO.Path]::GetFullPath($destination))) -ine $batch){throw 'STOP: archive path escaped intended directory'}
        if((Get-FileHash -LiteralPath $source).Hash -cne $item.sha256){throw 'STOP: marker changed before move'}
        Move-Item -LiteralPath $source -Destination $destination -ErrorAction Stop
        if((Get-FileHash -LiteralPath $destination).Hash -cne $item.sha256){throw 'STOP: archived marker checksum mismatch'}
    }
    foreach($item in $Plan){foreach($path in $item.evidence_sha256.Keys){if((Get-FileHash -LiteralPath $path).Hash -cne $item.evidence_sha256[$path]){throw 'STOP: original evidence changed'}}}
    Write-NewRecoveryJson (Join-Path $batch 'completed.json') @{archived_count=@($Plan).Count;manifest_sha256=(Get-FileHash (Join-Path $batch 'manifest.json')).Hash;no_replay=$true}
    return $batch
}

if($LibraryOnly){return}
. (Join-Path $Workspace 'scripts/controller/Controller-Recovery.ps1')
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$mutex=[Threading.Mutex]::new($false,('Global\AdaptiveRemeshing.AgyController.'+$sid))
$held=$false;$bridgeHeld=$false;$bridgeMutex=$null
try{
    try{$held=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true}
    if(!$held){throw 'STOP: controller instance owns the project execution mutex'}
    $bridgeKey=[BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes([IO.Path]::GetFullPath($BridgeDir).ToLowerInvariant()))).Replace('-','')
    $bridgeMutex=[Threading.Mutex]::new($false,('Global\AdaptiveRemeshing.Bridge.'+$bridgeKey))
    try{$bridgeHeld=$bridgeMutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$bridgeHeld=$true}
    if(!$bridgeHeld){throw 'STOP: bridge transaction is active'}
    function Assert-RetirementIdle {
        $session=Get-Content -LiteralPath (Join-Path $Workspace 'project_coordination/ACTIVE_SESSION.json') -Raw|ConvertFrom-Json
        if($session.active){throw 'STOP: project session is active'}
        $processes=@(Get-CimInstance Win32_Process|Where-Object {$_.ProcessId -ne $PID -and ($_.Name -eq 'agy.exe' -or ($_.Name -in @('powershell.exe','pwsh.exe') -and $_.CommandLine -match 'Antigravity-Autonomous-Loop.ps1|Invoke-ChatGPTBridge.ps1'))})
        if($processes.Count){throw 'STOP: Gemini/controller process exists; no ownership override'}
        foreach($name in @('bridge.lock','bridge_request.ready','bridge_request.tmp','bridge_response.ready','bridge_response.tmp')){
            if(Test-Path -LiteralPath (Join-Path $BridgeDir $name)){throw "STOP: conflicting handshake $name"}
        }
    }
    Assert-RetirementIdle
    $checkpointPath=Join-Path $env:USERPROFILE 'OpenClawPAD/controller_turn_checkpoint.json'
    $cp=Read-ControllerCheckpoint $checkpointPath
    if(!$cp -or $cp.state -notin @('COMPLETED','PENDING')){throw 'STOP: absent or incompatible controller checkpoint'}
    Assert-ControllerDispatchCheckpoint $Workspace $cp
    $checkpointHash=(Get-FileHash $checkpointPath).Hash
    $ledgerPath=Join-Path $Workspace 'project_coordination/HPC_JOB_LEDGER.csv'
    $ledgerHash=(Get-FileHash $ledgerPath).Hash
    $plan=@(Get-MaintenanceRetirementPlan $BridgeDir)
    if(!$plan.Count){Write-Output 'No historical pending handoffs remain.';return}
    $plan|Select-Object name,correlation_id,uncertainty|Format-Table -AutoSize
    if(!$Apply){Write-Output 'PREVIEW ONLY: no changes. Abandonment retains uncertainty; it is not completion or a proven timeout.';return}
    Assert-RetirementIdle
    $batch=Move-MaintenanceRetirementPlan $BridgeDir $plan $cp.state
    if((Get-FileHash $checkpointPath).Hash -cne $checkpointHash -or (Get-FileHash $ledgerPath).Hash -cne $ledgerHash){throw 'STOP: checkpoint or HPC ledger changed concurrently'}
    Write-Output "RETIRED_FIVE_WITHOUT_REPLAY: $batch"
}finally{
    if($bridgeHeld){$bridgeMutex.ReleaseMutex()};if($bridgeMutex){$bridgeMutex.Dispose()}
    if($held){$mutex.ReleaseMutex()};$mutex.Dispose()
}
