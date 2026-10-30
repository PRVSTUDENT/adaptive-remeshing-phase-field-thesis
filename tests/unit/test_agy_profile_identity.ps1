$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Security
. "$PSScriptRoot/../../scripts/validation/AgyCredentialStores.ps1"
. "$PSScriptRoot/../../scripts/validation/Invoke-BoundedAgyProcess.ps1"
# A managed fixture type with NO P/Invoke. Refuse to run if a real CredMan type
# is already loaded; every profile/native/CLI write below stays in this fixture.
if('CredMan' -as [type]){throw 'Run this fixture in a fresh PowerShell process'}
Add-Type @'
public static class CredMan {
 public static byte[] Blob;
 public static void Write(string target,string user,string comment,uint persist,byte[] bytes) {
  if(target!="fixture-only") throw new System.Exception("Real target forbidden");
  Blob=(byte[])bytes.Clone();
 }
}
'@
$manager=Join-Path $env:LOCALAPPDATA 'agy-profile/agy-profile.ps1'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($manager,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Installed manager syntax failure'}
foreach($fn in @('Test-ProfileName','Get-ProfileDir','Get-BlobHash','Read-ProfileMeta',
                 'Protect-JsonToFile','Protect-ToFile','Unprotect-FromFile','Write-ProfileMeta',
                 'Backup-IfUnsaved','Confirm-Action','Get-CredentialSubject','Invoke-Save','Invoke-Switch',
                 'Get-ByteRange','Test-BytesEqual','Get-PasswordKeys','Protect-WithPassword','Unprotect-WithPassword')) {
    $node=$ast.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $fn},$true)
    if(-not $node){throw "Missing fixture function $fn"}
    . ([scriptblock]::Create($node.Extent.Text))
}
function Get-CurrentCred {return [pscustomobject]@{Blob=[byte[]][CredMan]::Blob.Clone();UserName='fixture';Comment='fixture';Persist=2}}
function Read-AgyCredentialManagerBytes {return ,([byte[]][CredMan]::Blob.Clone())}
function Get-AgyProviderIdentity {param($AccessToken)return Get-AgyCanonicalIdentity 'fixture-a'}
function New-Jwt([string]$sub){$p=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((@{sub=$sub}|ConvertTo-Json -Compress))).TrimEnd('=').Replace('+','-').Replace('/','_');return "fixture.$p.signature"}
function Bytes($obj){return ,([Text.Encoding]::UTF8.GetBytes(($obj|ConvertTo-Json -Depth 8 -Compress)))}
$folder=Join-Path $env:TEMP ('agy-identity-fixture-'+[guid]::NewGuid().ToString('N'))
$PROFILES_DIR=Join-Path $folder 'profiles';$CLI_DIR=Join-Path $folder 'cli';$ACTIVE_FILE=Join-Path $folder 'active'
$CRED_TARGET='fixture-only';$Force=$true;$ReplaceIdentity=$false;$PER_PROFILE_FILES=@()
$null=New-Item -ItemType Directory -Path $PROFILES_DIR,$CLI_DIR
$cli=Bytes @{token=@{refresh_token='FAKE-OLD';access_token='FAKE-OLD'};id_token=(New-Jwt 'fixture-a')}
$native=Bytes @{token=@{refresh_token='FAKE-CURRENT';access_token='FAKE-CURRENT'}}
$other=Bytes @{token=@{refresh_token='FAKE-OTHER'};id_token=(New-Jwt 'fixture-b')}
[CredMan]::Blob=[byte[]]$native.Clone()
$tokenPath=Join-Path $CLI_DIR 'antigravity-oauth-token'
[IO.File]::WriteAllBytes($tokenPath,$cli)
$Name='fixture-a'
Invoke-Save
$saved=Unprotect-FromFile (Join-Path (Get-ProfileDir $Name) 'credential.dpapi')
$savedBytes=[Convert]::FromBase64String($saved.blobB64)
$expected=Get-AgyCanonicalIdentity 'fixture-a'
if((ConvertTo-AgyCredentialToken $savedBytes).Identity -ne $expected){throw 'Save canonical identity failure'}
if((ConvertTo-AgyCredentialToken $savedBytes).Token.refresh_token -ne 'FAKE-CURRENT'){throw 'Current grant was lost'}
# Actual installed quota worker, audit-only, synthetic DPAPI envelope via stdin.
$python=Join-Path $env:APPDATA 'uv/tools/ai-limit-checker/Scripts/python.exe'
$worker=Join-Path $env:USERPROFILE 'OpenClawPAD/agy_profile_quota.py'
$request=@{credential=$saved;audit_only=$true}|ConvertTo-Json -Depth 8 -Compress
$result=Invoke-BoundedAgyProcess -FilePath $python -ArgumentList @($worker) -InputText $request -TimeoutSeconds 20
if($result.ExitCode -ne 0 -or ($result.Output|ConvertFrom-Json).identity -ne $expected){throw 'Save followed by quota identity verification failed'}
'PASS: actual DPAPI fixture save -> nested identity -> installed read-only quota worker'

foreach($label in @('account1','account3','account4','account5')) {
    $Name=$label;$dir=Get-ProfileDir $Name;$null=New-Item -ItemType Directory -Path $dir
    $cred=[pscustomobject]@{Blob=$other;UserName='fixture';Comment='fixture';Persist=2}
    Protect-ToFile $cred (Join-Path $dir 'credential.dpapi')
    $before=[IO.File]::ReadAllBytes((Join-Path $dir 'credential.dpapi'))
    [CredMan]::Blob=[byte[]]$savedBytes.Clone()
    $failed=$false;try{Invoke-Save}catch{$failed=$_.Exception.Message -match 'Identity mismatch'}
    if(-not $failed -or -not(Test-BytesEqual $before ([IO.File]::ReadAllBytes((Join-Path $dir 'credential.dpapi'))))){throw 'Mismatch overwrote fixture profile'}
}
'PASS: Force preserves every mismatched fixture profile; ReplaceIdentity never used'

# Force the formerly failing backup branch before a real fixture switch.
[CredMan]::Blob=[byte[]]$native.Clone()
Invoke-Switch -TargetName 'account3'
Assert-AgyCredentialStores -ExpectedBytes $other -TokenPath $tokenPath
if(@(Get-ChildItem -LiteralPath $PROFILES_DIR -Directory -Filter '_unsaved-*').Count -ne 1){throw 'Unsaved backup branch did not complete'}
if((Get-CredentialSubject ([CredMan]::Blob) 'native-store') -ne (Get-AgyCanonicalIdentity 'fixture-b')){throw 'Switch identity definition differs'}
'PASS: formerly failing Backup-IfUnsaved -> fixture switch -> canonical store verification'
foreach($bad in @($null,([byte[]]@()))) {
    $failed=$false;try{$null=Get-BlobHash $bad}catch{$failed=$_.Exception.Message -match 'AGY_BLOB_HASH_INPUT_MISSING'}
    if(-not $failed){throw 'Null hash input did not fail explicitly'}
}
if((Get-BlobHash ([Text.Encoding]::UTF8.GetBytes('abc'))) -ne 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'){throw 'Blob SHA-256 changed'}
'PASS: explicit overload selection and known SHA-256 vector; null/empty rejected'
$EXPORT_MAGIC='AGYP1';$EXPORT_KDF_ITERS=1000;$EXPORT_HEADER_LEN=69
$plain=[Text.Encoding]::UTF8.GetBytes('fixture portable payload')
$encrypted=Protect-WithPassword $plain 'fixture-password'
$decrypted=Unprotect-WithPassword $encrypted 'fixture-password'
if(-not(Test-BytesEqual $plain $decrypted)){throw 'Typed HMAC compatibility failed'}
'PASS: password export/import round trip retains existing binary format'
# Leave the isolated synthetic fixture for inspection; never recursively clean
# a computed path in a credential-handling test.
