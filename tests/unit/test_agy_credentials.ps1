$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/validation/AgyCredentialStores.ps1"
function New-TestToken([string]$subject) {
    $part=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((@{sub=$subject}|ConvertTo-Json -Compress))).TrimEnd('=').Replace('+','-').Replace('/','_')
    return "test.$part.fake-signature"
}
$first=New-TestToken 'fixture-account-a'
$second=New-TestToken 'fixture-account-b'
$source=[Text.Encoding]::UTF8.GetBytes((@{token=@{access_token='FAKE-ACCESS';refresh_token='FAKE-REFRESH'};id_token=$first;auth_method='consumer'}|ConvertTo-Json -Depth 5))
$alternate=[Text.Encoding]::UTF8.GetBytes((@{token=@{refresh_token='FAKE-OTHER';id_token=$second};auth_method='consumer'}|ConvertTo-Json -Depth 5))
$bad=[Text.Encoding]::UTF8.GetBytes((@{token=@{refresh_token='FAKE';id_token=$second};id_token=$first}|ConvertTo-Json -Depth 5))
$failed=$false;try{$null=ConvertTo-AgyCredentialToken $bad}catch{$failed=$true};if(-not $failed){throw 'Conflicting identity accepted'}
# Observed native-store format after AGY: no ID token, unrelated refresh value, expired cache.
$expired=[Text.Encoding]::UTF8.GetBytes((@{token=@{access_token='FAKE-OLD-ACCESS';refresh_token='FAKE-UNRELATED-REFRESH';expiry='2026-09-03T15:53:10Z'};auth_method='consumer'}|ConvertTo-Json -Depth 5))
$failed=$false
try{$null=ConvertTo-AgyCredentialToken -Bytes $expired -SourceName native-store}catch{
    $failed=$true
    if($_.Exception.Message -notmatch 'source=native-store stage=ID_TOKEN_MISSING' -or $_.Exception.Message -match 'FAKE-UNRELATED'){throw 'Unsafe or unidentified normalization error'}
}
if(-not $failed){throw 'Missing native identity bypassed guard'}
$now=[datetimeoffset]'2026-10-19T14:00:00Z'
if(-not (Test-AgyExpiredNativeRepair -ExpectedBytes $source -NativeBytes $expired -CliBytes $source -Now $now)){throw 'Observed expired-cache repair not qualified'}
if(Test-AgyExpiredNativeRepair -ExpectedBytes $source -NativeBytes $expired -CliBytes $alternate -Now $now){throw 'Wrong CLI identity qualified for repair'}
if(Test-AgyExpiredNativeRepair -ExpectedBytes $source -NativeBytes $alternate -CliBytes $source -Now $now){throw 'Conflicting native identity qualified for repair'}
$live=[Text.Encoding]::UTF8.GetBytes(([Text.Encoding]::UTF8.GetString($expired)).Replace('2026-09-03T15:53:10Z','2026-10-20T15:53:10Z'))
if(Test-AgyExpiredNativeRepair -ExpectedBytes $source -NativeBytes $live -CliBytes $source -Now $now){throw 'Unverified live native identity qualified for repair'}
$folder=Join-Path $env:TEMP ('agy-credentials-test-'+[guid]::NewGuid().ToString('N'))
try {
    $null=New-Item -ItemType Directory -Path $folder
    $path=Join-Path $folder 'token-fixture.json'
    Sync-AgyCliCredentialFile -Bytes $source -TokenPath $path
    $written=ConvertTo-AgyCredentialToken ([IO.File]::ReadAllBytes($path))
    if($written.Identity -ne (ConvertTo-AgyCredentialToken $source).Identity){throw 'Nested token normalization failed'}
    if(-not (Get-Acl -LiteralPath $path).AreAccessRulesProtected){throw 'Credential file inherited access rules'}
    function Read-AgyCredentialManagerBytes {return ,$script:fakeManagerBytes}
    $script:fakeManagerBytes=$source
    Assert-AgyCredentialStores -ExpectedBytes $source -TokenPath $path
    Sync-AgyCliCredentialFile -Bytes $alternate -TokenPath $path
    $failed=$false;try{Assert-AgyCredentialStores -ExpectedBytes $source -TokenPath $path}catch{$failed=$true};if(-not $failed){throw 'Observed stale CLI file mismatch accepted'}
    Sync-AgyCliCredentialFile -Bytes $source -TokenPath $path
    $script:fakeManagerBytes=$alternate
    $failed=$false;try{Assert-AgyCredentialStores -ExpectedBytes $source -TokenPath $path}catch{$failed=$true};if(-not $failed){throw 'Wrong Credential Manager identity accepted'}
    # Execute the installed PRE/POST guard with synthetic stores and a mocked profile switch.
    & {
        $originalUserProfile=$env:USERPROFILE
        try {
            $env:USERPROFILE=$folder
            $fixturePath=Join-Path $folder '.gemini/antigravity-cli/antigravity-oauth-token'
            Sync-AgyCliCredentialFile -Bytes $source -TokenPath $fixturePath
            $tokens=$null;$errors=$null
            $ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $originalUserProfile 'OpenClawPAD/Antigravity-Autonomous-Loop.ps1'),[ref]$tokens,[ref]$errors)
            if($errors.Count){throw 'Controller parse regression'}
            $node=$ast.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Set-AndVerifyAgyRunProfile'},$true)
            . ([scriptblock]::Create($node.Extent.Text))
            $script:testRepairDone=$false;$script:testSwitchCalls=0
            function Get-AgySavedCredentialBytes {param($Profile) return ,([byte[]]$source.Clone())}
            function Read-AgyCredentialManagerBytes {if($script:testRepairDone){return ,([byte[]]$source.Clone())}else{return ,([byte[]]$expired.Clone())}}
            function Get-AgyProfileState {return [pscustomobject]@{ActiveProfile='account3';ActiveFile='account3';LastSwitch='account3';Raw='fixture'}}
            function agy-profile {param($Command,$Name,[switch]$Force) $script:testRepairDone=$true;$script:testSwitchCalls++}
            $script:RunLockedAgyProfile='account3';$EnableSmartAgyProfileSelection=$true
            $global:LASTEXITCODE=3 # A successful PS script must not inherit this stale native failure.
            Set-AndVerifyAgyRunProfile -Context PRE_AGY
            Set-AndVerifyAgyRunProfile -Context POST_AGY
            if($script:testSwitchCalls -ne 1){throw 'Expired native repair was repeated or skipped'}
        } finally {$env:USERPROFILE=$originalUserProfile}
    }
} finally {
    $resolved=[IO.Path]::GetFullPath($folder);$base=[IO.Path]::GetFullPath($env:TEMP).TrimEnd('\')+'\'
    if(-not $resolved.StartsWith($base,[StringComparison]::OrdinalIgnoreCase) -or (Split-Path $resolved -Leaf) -notlike 'agy-credentials-test-*'){throw 'Unsafe fixture cleanup path'}
    if(Test-Path -LiteralPath $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
'PASS: credential layouts and safe stage/source errors, observed expired-native format, restricted repair eligibility, private ACL and store mismatch rejection; only synthetic credentials used'
