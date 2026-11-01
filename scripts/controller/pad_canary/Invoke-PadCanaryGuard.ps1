[CmdletBinding()]
param(
    [ValidateSet('Prepare','Claim','Validate','Timeout','Receive')][string]$Mode,
    [string]$Root = (Join-Path $PSScriptRoot 'canary-state'),
    [switch]$LibraryOnly
)
$ErrorActionPreference='Stop'
function Write-PadNewBytes([string]$Path,[byte[]]$Bytes){
    $f=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try{$f.Write($Bytes,0,$Bytes.Length);$f.Flush($true)}finally{$f.Dispose()}
}
function Write-PadNewJson([string]$Path,$Data){
    Write-PadNewBytes $Path ([Text.UTF8Encoding]::new($false).GetBytes(($Data|ConvertTo-Json -Depth 12)))
}
function Get-PadHash([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash}
function Assert-PadCanaryRoot([string]$Path){
    $full=[IO.Path]::GetFullPath($Path).TrimEnd('\')
    $private=[IO.Path]::GetFullPath((Join-Path $env:USERPROFILE 'PAD-Canary-R1-20261101')).TrimEnd('\')+'\'
    $temporary=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')+'\'
    if(!$full.StartsWith($private,[StringComparison]::OrdinalIgnoreCase) -and !$full.StartsWith($temporary,[StringComparison]::OrdinalIgnoreCase)){
        throw 'CANARY_ROOT_BLOCKED: use only the private R1 bundle or temporary offline fixtures'
    }
}
function New-PadCanary([string]$Path){
    Assert-PadCanaryRoot $Path
    if(Test-Path -LiteralPath $Path){throw 'CANARY_ALREADY_PREPARED: preserve this single authorized transaction; never reinitialize it'}
    New-Item -ItemType Directory -Path $Path -ErrorAction Stop|Out-Null
    New-Item -ItemType Directory -Path (Join-Path $Path 'archive')|Out-Null
    $id='HND-PAD-CANARY-'+[guid]::NewGuid().ToString('N')
    $prompt="[BRIDGE_HANDOFF_ID=$id]`r`nPAD_AUTONOMOUS_LOOP_CANARY`r`nThis is a communication test only. Do not execute commands, access scientific files, submit jobs, or change any project state. Reply exactly: PAD_CANARY_PASS"
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes($prompt)
    # Archive bytes first; a ready file is never the only recoverable copy.
    Write-PadNewBytes (Join-Path $Path 'archive/request.txt') $bytes
    Write-PadNewJson (Join-Path $Path 'transaction.json') @{schema=1;handoff_id=$id;request_sha256=(Get-PadHash (Join-Path $Path 'archive/request.txt'));expected_response='PAD_CANARY_PASS';prepared_utc=[DateTimeOffset]::UtcNow.ToString('o');max_attempts=1}
    Write-PadNewBytes (Join-Path $Path 'bridge_request.ready') $bytes
    return $id
}
function Read-PadTransaction([string]$Path){
    Assert-PadCanaryRoot $Path
    $m=Get-Content -LiteralPath (Join-Path $Path 'transaction.json') -Raw|ConvertFrom-Json
    if($m.handoff_id -cnotmatch '^HND-PAD-CANARY-[a-f0-9]{32}$' -or $m.expected_response -cne 'PAD_CANARY_PASS' -or $m.max_attempts -ne 1){throw 'INVALID_CANARY_MANIFEST'}
    foreach($name in @('bridge_request.ready','archive/request.txt')){
        $p=Join-Path $Path $name
        if(!(Test-Path -LiteralPath $p) -or (Get-PadHash $p) -cne $m.request_sha256){throw 'CANARY_REQUEST_CHANGED: no execution or resend permitted'}
    }
    return $m
}
function Claim-PadCanary([string]$Path){
    $m=Read-PadTransaction $Path
    if((Test-Path (Join-Path $Path 'failure.json')) -or (Test-Path (Join-Path $Path 'response_receipt.json'))){throw 'TERMINAL_CANARY_NO_REPLAY'}
    # CreateNew is exclusive across PAD instances. Reserve BEFORE clipboard/paste.
    Write-PadNewJson (Join-Path $Path 'paste_attempt.json') @{handoff_id=$m.handoff_id;request_sha256=$m.request_sha256;attempt=1;reserved_utc=[DateTimeOffset]::UtcNow.ToString('o');meaning='Reserved paste attempt, NOT proof of successful paste or send'}
    return 'CLAIMED'
}
function Fail-PadCanary([string]$Path,[string]$Reason){
    $m=Read-PadTransaction $Path
    if(!(Test-Path (Join-Path $Path 'response_receipt.json')) -and !(Test-Path (Join-Path $Path 'failure.json'))){
        Write-PadNewJson (Join-Path $Path 'failure.json') @{handoff_id=$m.handoff_id;status='STOPPED';reason=$Reason;utc=[DateTimeOffset]::UtcNow.ToString('o');request_retained=$true;retry_allowed=$false}
    }
}
function Validate-PadCanary([string]$Path){
    $m=Read-PadTransaction $Path
    if(Test-Path (Join-Path $Path 'failure.json')){throw 'FAILED_CANARY_NO_RETRY'}
    if(Test-Path (Join-Path $Path 'response_receipt.json')){throw 'RESPONSE_ALREADY_VALIDATED_NO_REPLAY'}
    $attempt=Get-Content -LiteralPath (Join-Path $Path 'paste_attempt.json') -Raw|ConvertFrom-Json
    if($attempt.handoff_id -cne $m.handoff_id -or $attempt.request_sha256 -cne $m.request_sha256 -or $attempt.attempt -ne 1){throw 'INVALID_PASTE_RESERVATION'}
    $candidate=Join-Path $Path 'clipboard_candidate.json'
    if(!(Test-Path -LiteralPath $candidate)){throw 'MISSING_CLIPBOARD_CANDIDATE'}
    # Archive exact PAD bytes before interpreting JSON; Unicode BOMs are detected.
    Write-PadNewBytes (Join-Path $Path 'archive/clipboard_candidate.json') ([IO.File]::ReadAllBytes($candidate))
    try{
        $r=([IO.File]::ReadAllText($candidate)|ConvertFrom-Json -ErrorAction Stop)
        if($r.bridge_handoff_id -cne $m.handoff_id){throw 'MISMATCHED_HANDOFF_ID'}
        if($r.status -cne 'OK'){throw 'NON_OK_CLIPBOARD_STATUS'}
        if($r.response -isnot [string] -or $r.response -cne 'PAD_CANARY_PASS'){throw 'UNEXPECTED_CANARY_RESPONSE'}
        if($r.response_chars -ne $r.response.Length){throw 'RESPONSE_LENGTH_MISMATCH'}
        $stamp=[DateTimeOffset]::Parse([string]$r.copied_at)
        $start=[DateTimeOffset]::Parse([string]$attempt.reserved_utc)
        if($stamp -lt $start.AddSeconds(15) -or $stamp -gt [DateTimeOffset]::UtcNow.AddSeconds(30)){throw 'RESPONSE_TIME_NOT_FRESH_OR_MINIMUM_WAIT_NOT_MET'}
        # This is publication of validated transport data, not browser-count proof.
        Write-PadNewJson (Join-Path $Path 'response_publish_intent.json') @{handoff_id=$m.handoff_id;candidate_sha256=(Get-PadHash $candidate)}
        Write-PadNewJson (Join-Path $Path 'bridge_response.tmp') $r
        [IO.File]::Move((Join-Path $Path 'bridge_response.tmp'),(Join-Path $Path 'bridge_response.ready'))
        Write-PadNewJson (Join-Path $Path 'response_receipt.json') @{handoff_id=$m.handoff_id;status='PAD_RESPONSE_VALIDATED';response_sha256=(Get-PadHash (Join-Path $Path 'bridge_response.ready'));candidate_sha256=(Get-PadHash $candidate);request_retained=$true;browser_single_send_and_new_turn_observation='REQUIRED_SEPARATELY'}
    }catch{
        Fail-PadCanary $Path $_.Exception.Message
        throw
    }
    return 'VALIDATED'
}
function Receive-PadCanary([string]$Path){
    $m=Read-PadTransaction $Path
    if(Test-Path (Join-Path $Path 'failure.json')){throw 'FAILED_CANARY_CANNOT_PASS'}
    $receipt=Get-Content -LiteralPath (Join-Path $Path 'response_receipt.json') -Raw|ConvertFrom-Json
    $file=Join-Path $Path 'bridge_response.ready'
    if($receipt.handoff_id -cne $m.handoff_id -or (Get-PadHash $file) -cne $receipt.response_sha256){throw 'RESPONSE_RECEIPT_CHANGED'}
    $r=[IO.File]::ReadAllText($file)|ConvertFrom-Json
    if($r.bridge_handoff_id -cne $m.handoff_id -or $r.status -cne 'OK' -or $r.response -cne 'PAD_CANARY_PASS'){throw 'INVALID_RETURNED_RESPONSE'}
    [pscustomobject]@{status='PAD_RESPONSE_RETURNED_TO_CONTROLLER';bridge_handoff_id=$m.handoff_id;response=$r.response;full_single_handoff_pass='AWAITING_ACTUAL_BROWSER_OBSERVATIONS'}|ConvertTo-Json
}
if($LibraryOnly){return}
if(!$Mode){throw 'Specify Prepare, Claim, Validate, Timeout or Receive'}
switch($Mode){
 'Prepare' {New-PadCanary $Root}
 'Claim' {Claim-PadCanary $Root}
 'Validate' {Validate-PadCanary $Root}
 'Timeout' {Fail-PadCanary $Root 'PAD_PASTE_OR_RESPONSE_TIMEOUT';Write-Output 'STOPPED_NO_RETRY'}
 'Receive' {Receive-PadCanary $Root}
}
