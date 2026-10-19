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
} finally {
    $resolved=[IO.Path]::GetFullPath($folder);$base=[IO.Path]::GetFullPath($env:TEMP).TrimEnd('\')+'\'
    if(-not $resolved.StartsWith($base,[StringComparison]::OrdinalIgnoreCase) -or (Split-Path $resolved -Leaf) -notlike 'agy-credentials-test-*'){throw 'Unsafe fixture cleanup path'}
    if(Test-Path -LiteralPath $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
'PASS: root/nested credential normalization, conflicting identity rejection, private ACL, stale CLI token file rejection, and wrong native-store identity rejection; only synthetic credentials used'
