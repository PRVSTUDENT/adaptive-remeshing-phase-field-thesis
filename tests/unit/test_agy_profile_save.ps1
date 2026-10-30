$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/validation/AgyCredentialStores.ps1"
function New-TestJwt([string]$subject) {
    $part=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((@{sub=$subject}|ConvertTo-Json -Compress))).TrimEnd('=').Replace('+','-').Replace('/','_')
    return "fixture.$part.signature"
}
function Bytes($obj) { return ,([Text.Encoding]::UTF8.GetBytes(($obj|ConvertTo-Json -Depth 8 -Compress))) }
$first=New-TestJwt 'fixture-a';$second=New-TestJwt 'fixture-b'
$native=Bytes @{token=@{access_token='FAKE-NATIVE';refresh_token='FAKE-ROTATED';expiry='2099-01-01T00:00:00Z'};auth_method='consumer'}
$cli=Bytes @{token=@{access_token='FAKE-STALE';refresh_token='FAKE-OLD';id_token=$first};auth_method='consumer'}
$other=Bytes @{token=@{refresh_token='FAKE-OTHER';id_token=$second};auth_method='consumer'}
$identity=(ConvertTo-AgyCredentialToken $cli).Identity
$folder=Join-Path $env:TEMP ('agy-save-test-'+[guid]::NewGuid().ToString('N'))
$null=New-Item -ItemType Directory -Path $folder
$tokenPath=Join-Path $folder 'cli.json'
function Get-AgyProviderIdentity {param($AccessToken)
    $script:providerCalls++
    if($AccessToken -ne 'FAKE-NATIVE'){throw 'Unexpected grant'}
    if($script:providerFails){throw 'FAKE-SECRET should never reach diagnostics'}
    if($script:changeCli){[IO.File]::WriteAllBytes($tokenPath,$other)}
    return $script:providerResult
}
function Write-AgyCredentialManagerBytes {throw 'Real native write forbidden in save preparation'}
function Sync-AgyCliCredentialFile {throw 'CLI mutation forbidden in save preparation'}
function Update-AgyNativeAccessToken {throw 'Refresh forbidden in save preparation'}
try {
    $script:providerCalls=0;$script:providerFails=$false;$script:changeCli=$false;$script:providerResult=$identity
    [IO.File]::WriteAllBytes($tokenPath,$cli)
    $before=[Convert]::ToBase64String($native)
    $candidate=Get-AgyProfileSaveBytes -Bytes $native -TokenPath $tokenPath
    $parsed=ConvertTo-AgyCredentialToken $candidate -SourceName sync-verify
    if($parsed.Identity -ne $identity -or $parsed.Token.refresh_token -ne 'FAKE-ROTATED' -or $parsed.Token.access_token -ne 'FAKE-NATIVE'){throw 'Current OAuth grant lost'}
    if($script:providerCalls -ne 1 -or [Convert]::ToBase64String($native) -cne $before){throw 'Native input changed or proof skipped'}
    if([Convert]::ToBase64String([IO.File]::ReadAllBytes($tokenPath)) -cne [Convert]::ToBase64String($cli)){throw 'CLI mutated'}
    'PASS: provider-proven metadata recovery preserves current grant; no store writes'
    $script:providerCalls=0
    $unchanged=Get-AgyProfileSaveBytes -Bytes $cli -TokenPath (Join-Path $folder 'absent.json')
    if($script:providerCalls -or [Convert]::ToBase64String($unchanged) -cne [Convert]::ToBase64String($cli)){throw 'Existing-ID path changed'}
    foreach($scenario in @('provider-failure','provider-conflict','cli-change','cli-missing','cli-no-id')) {
        [IO.File]::WriteAllBytes($tokenPath,$cli)
        $script:providerFails=$scenario -eq 'provider-failure';$script:changeCli=$scenario -eq 'cli-change'
        $script:providerResult=if($scenario -eq 'provider-conflict'){'wrong-identity'}else{$identity}
        $testPath=if($scenario -eq 'cli-missing'){Join-Path $folder 'missing.json'}else{$tokenPath}
        if($scenario -eq 'cli-no-id'){[IO.File]::WriteAllBytes($tokenPath,$native)}
        $failed=$false
        try{$null=Get-AgyProfileSaveBytes -Bytes $native -TokenPath $testPath}catch{
            $failed=$true
            if($_.Exception.Message -notmatch 'source=native-store stage=' -or $_.Exception.Message -match 'FAKE-'){throw 'Unsafe or unidentified diagnostic'}
        }
        if(-not $failed){throw "Unsafe save candidate: $scenario"}
    }
    'PASS: provider, metadata and concurrent-file failures reject without credential leaks'

    # Parse ONLY the installed Invoke-Save function; never dispatch the manager.
    $manager=Join-Path $env:LOCALAPPDATA 'agy-profile/agy-profile.ps1'
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseFile($manager,[ref]$tokens,[ref]$errors)
    if($errors.Count){throw 'Installed manager parse failure'}
    foreach($functionName in @('Get-CredentialSubject','Invoke-Save')) {
        $node=$ast.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $functionName},$true)
        if(-not $node){throw 'Installed save function missing'}
        . ([scriptblock]::Create($node.Extent.Text))
    }
    $Name='fixture';$Force=$true;$ReplaceIdentity=$false;$CLI_DIR=$folder
    $CRED_TARGET='fixture';$PER_PROFILE_FILES=@();$ACTIVE_FILE=Join-Path $folder 'marker'
    $profileDir=Join-Path $folder 'profile';$null=New-Item -ItemType Directory -Path $profileDir
    [IO.File]::WriteAllText((Join-Path $profileDir 'credential.dpapi'),'synthetic placeholder, not a credential')
    $realTokenPath=Join-Path $folder 'antigravity-oauth-token'
    function Test-ProfileName {param($n)}
    function Get-ProfileDir {param($n) return $profileDir}
    function Get-BlobHash([byte[]]$bytes){return [Convert]::ToBase64String($bytes)}
    function Get-CurrentCred {
        $script:reads++
        $b=if($script:nativeChange -and $script:reads -gt 1){$other}else{$native}
        return [pscustomobject]@{Blob=[byte[]]$b.Clone()}
    }
    function Unprotect-FromFile {param($p)return @{blobB64=[Convert]::ToBase64String($script:saved)}}
    function Confirm-Action {param($prompt)return $true}
    function Protect-ToFile {param($cred,$p)$script:writes++;$script:savedResult=[byte[]]$cred.Blob.Clone()}
    function Write-ProfileMeta {param($dir,$n,$cred)}
    function Set-Content {param($Encoding,$Path,$Value)$script:markers++}
    $script:providerFails=$false;$script:changeCli=$false;$script:providerResult=$identity
    [IO.File]::WriteAllBytes($tokenPath,$cli);[IO.File]::WriteAllBytes($realTokenPath,$cli)
    foreach($scenario in @('success','saved-identity-conflict','native-change')) {
        $script:saved=if($scenario -eq 'saved-identity-conflict'){$other}else{$cli}
        $script:reads=0;$script:writes=0;$script:markers=0;$script:nativeChange=$scenario -eq 'native-change'
        $failed=$false
        try{Invoke-Save}catch{$failed=$true}
        if($scenario -eq 'success') {
            if($failed -or $script:writes -ne 1 -or $script:markers -ne 1){throw 'Installed save did not complete with synthetic stores'}
            if((ConvertTo-AgyCredentialToken $script:savedResult).Token.refresh_token -ne 'FAKE-ROTATED'){throw 'Save lost native grant'}
        }elseif(-not $failed -or $script:writes -or $script:markers){throw "Installed save overwrote protected state: $scenario"}
    }
    'PASS: installed save function works with synthetic stores; Force cannot bypass identity conflict; concurrent native changes prevent writes'
} finally {
    $resolved=[IO.Path]::GetFullPath($folder);$base=[IO.Path]::GetFullPath($env:TEMP).TrimEnd('\')+'\'
    if(-not $resolved.StartsWith($base,[StringComparison]::OrdinalIgnoreCase) -or (Split-Path $resolved -Leaf) -notlike 'agy-save-test-*'){throw 'Unsafe fixture cleanup path'}
    if(Test-Path -LiteralPath $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
