$ErrorActionPreference = 'Stop'
$source = (Get-Content (Join-Path $PSScriptRoot 'Invoke-ChatGPTBridge.ps1') -Raw).Replace("`r`n", "`n")
$t=$null;$e=$null
[void][Management.Automation.Language.Parser]::ParseInput($source,[ref]$t,[ref]$e)
if($e.Count){throw ($e|Out-String)}
$begin=$source.IndexOf('    # --- 3. Lockfile Check & Acquisition ---')
$end=$source.IndexOf('        # --- 4. Clean Stale Handshake Files ---',$begin)
$fin=$source.IndexOf('        # --- 10. Always Release Only Our Lock ---')
$tail=$source.Substring($fin,$source.LastIndexOf("`n    }`n}")-$fin)
$probe=[scriptblock]::Create($source.Substring($begin,$end-$begin)+"`n 'ACQUIRED' `n } finally { `n"+$tail+"`n}")
$BridgeDir=Join-Path ([IO.Path]::GetTempPath()) ('bridge-lock-test-'+[guid]::NewGuid().ToString('N'))
$archiveDir=Join-Path $BridgeDir 'archive';New-Item -ItemType Directory $archiveDir -Force|Out-Null
$lockFile=Join-Path $BridgeDir 'bridge.lock';$requestReady=Join-Path $BridgeDir 'bridge_request.ready';$requestTmp=Join-Path $BridgeDir 'bridge_request.tmp';$responseReady=Join-Path $BridgeDir 'bridge_response.ready';$responseTmp=Join-Path $BridgeDir 'bridge_response.tmp';$HandoffId='TEST'
'{"pid":2147483647}'|Set-Content $lockFile
'evidence'|Set-Content $responseReady
& $probe
if(Test-Path $lockFile){throw 'lock not released'}
if(@(Get-ChildItem $archiveDir).Count -ne 2){throw 'orphan evidence lost'}
Write-Output 'PASS dead owner reclaimed immediately with evidence preservation'
@{pid=$PID;locked_at='2000-01-01'}|ConvertTo-Json|Set-Content $lockFile
try{& $probe;throw 'live owner accepted'}catch{if($_ -notmatch 'live owner'){throw}}
if(-not(Test-Path $lockFile)){throw 'foreign live lock removed'}
Write-Output 'PASS old live owner protected and foreign lock preserved'
Remove-Item $lockFile
& $probe
Write-Output 'PASS normal acquisition and release; parser zero errors'
Write-Output "Test evidence directory: $BridgeDir"

