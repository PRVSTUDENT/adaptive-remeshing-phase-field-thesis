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
    # Real lifecycle code, synthetic stores/provider/refresh only; no real credential writes.
    try {
        function global:Read-AgyCredentialManagerBytes {return ,([byte[]]$script:fixtureNative.Clone())}
        function global:Write-AgyCredentialManagerBytes {param([byte[]]$Bytes) $script:writes++;if(-not $script:badWrite){$script:fixtureNative=[byte[]]$Bytes.Clone()}}
        function global:Get-AgyProviderIdentity {param($AccessToken) if($script:providerFails){throw 'AGY_PROVIDER_IDENTITY_UNPROVEN'};return $script:providerIdentity}
        function global:Update-AgyNativeAccessToken {$script:refreshes++;$script:fixtureNative=[Text.Encoding]::UTF8.GetBytes((@{token=@{access_token='FAKE-NEW';refresh_token='FAKE-ROTATED';expiry='2099-01-01T00:00:00Z'}}|ConvertTo-Json -Depth 5))}
        $script:providerIdentity=(ConvertTo-AgyCredentialToken $source).Identity
        $script:providerFails=$false;$script:badWrite=$false;$script:writes=0;$script:refreshes=0
        $script:fixtureNative=[byte[]]$expired.Clone()
        Repair-AgyRefreshedNativeCredential -ExpectedBytes $source -TokenPath $path
        Assert-AgyCredentialStores -ExpectedBytes $source -TokenPath $path
        $current=ConvertTo-AgyCredentialToken ([IO.File]::ReadAllBytes($path))
        if($script:refreshes -ne 1 -or $script:writes -ne 1 -or $current.Token.refresh_token -ne 'FAKE-ROTATED'){throw 'Refreshed grant was lost or refresh was repeated'}
        foreach($scenario in @('provider-failure','provider-mismatch','native-conflict','cli-conflict','concurrent-change','readback-failure')) {
            Sync-AgyCliCredentialFile -Bytes $source -TokenPath $path
            $script:fixtureNative=[byte[]]$live.Clone();$script:writes=0
            $script:providerFails=$scenario -eq 'provider-failure';$script:badWrite=$scenario -eq 'readback-failure'
            $script:providerIdentity=if($scenario -eq 'provider-mismatch'){(ConvertTo-AgyCredentialToken $alternate).Identity}else{(ConvertTo-AgyCredentialToken $source).Identity}
            if($scenario -eq 'native-conflict'){$script:fixtureNative=[byte[]]$alternate.Clone()}
            if($scenario -eq 'cli-conflict'){Sync-AgyCliCredentialFile -Bytes $alternate -TokenPath $path}
            if($scenario -eq 'concurrent-change'){
                function global:Get-AgyProviderIdentity {param($AccessToken) Sync-AgyCliCredentialFile -Bytes $alternate -TokenPath $path;return $script:providerIdentity}
            }
            $failed=$false
            try{Repair-AgyRefreshedNativeCredential -ExpectedBytes $source -TokenPath $path}catch{$failed=$true;if($_.Exception.Message -match 'FAKE-'){throw 'Credential leaked in diagnostic'}}
            if(-not $failed -or ($scenario -ne 'readback-failure' -and $script:writes -ne 0)){throw "Unsafe repair: $scenario"}
            function global:Get-AgyProviderIdentity {param($AccessToken) if($script:providerFails){throw 'AGY_PROVIDER_IDENTITY_UNPROVEN'};return $script:providerIdentity}
        }
        $script:providerFails=$false;$script:badWrite=$false;$script:providerIdentity=(ConvertTo-AgyCredentialToken $source).Identity
        $originalUserProfile=$env:USERPROFILE
        try {
            $env:USERPROFILE=$folder
            $fixturePath=Join-Path $folder '.gemini/antigravity-cli/antigravity-oauth-token'
            Sync-AgyCliCredentialFile -Bytes $source -TokenPath $fixturePath
            $tokens=$null;$errors=$null
            $ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot '../../scripts/controller/Antigravity-Autonomous-Loop.ps1'),[ref]$tokens,[ref]$errors)
            if($errors.Count){throw 'Controller parse regression'}
            $node=$ast.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Set-AndVerifyAgyRunProfile'},$true)
            . ([scriptblock]::Create($node.Extent.Text))
            function global:Get-AgySavedCredentialBytes {param($Profile) return ,([byte[]]$source.Clone())}
            function global:Get-AgyProfileState {return [pscustomobject]@{ActiveProfile='account3';ActiveFile='account3';LastSwitch='account3';Raw='fixture'}}
            function global:agy-profile {throw 'Profile rollback must never occur'}
            $script:RunLockedAgyProfile='account3';$EnableSmartAgyProfileSelection=$true;$ControlledSingleTurn=$true
            $script:fixtureNative=[byte[]]$live.Clone();$script:writes=0
            Set-AndVerifyAgyRunProfile -Context PRE_AGY
            # Simulate AGY dropping ID metadata after a refresh.
            $script:fixtureNative=[byte[]]$live.Clone()
            Set-AndVerifyAgyRunProfile -Context POST_AGY
            Set-AndVerifyAgyRunProfile -Context POST_AGY
            if($script:writes -ne 2){throw 'PRE/POST recovery not idempotent'}
            Write-Output 'PASS: controlled PRE/POST provider-verified refresh recovery; repeated POST is read-only; zero profile switches'

            # Test TURN_END deferred refresh: native ID metadata missing does NOT trigger token refresh at turn end.
            $script:fixtureNative=[byte[]]$live.Clone()
            $script:refreshes=0; $writesBefore=$script:writes
            Set-AndVerifyAgyRunProfile -Context TURN_END
            if ($script:refreshes -ne 0 -or $script:writes -ne $writesBefore) { throw 'TURN_END did not defer token refresh' }
            Write-Output 'PASS: TURN_END deferred token refresh preserves completed turn without models refresh or store mutation'

            # Test TURN_END with genuine CLI account conflict: must fail closed.
            Sync-AgyCliCredentialFile -Bytes $alternate -TokenPath $fixturePath
            $failedConflict=$false
            try { Set-AndVerifyAgyRunProfile -Context TURN_END } catch { $failedConflict=$true }
            if (-not $failedConflict) { throw 'TURN_END did not fail closed on genuine CLI identity conflict' }
            Sync-AgyCliCredentialFile -Bytes $source -TokenPath $fixturePath
            Write-Output 'PASS: TURN_END with genuine CLI identity mismatch fails closed'

            # Test TURN_START bounded resynchronization when stores drifted at between-turn boundary.
            $script:fixtureNative=[byte[]]$alternate.Clone()
            Sync-AgyCliCredentialFile -Bytes $alternate -TokenPath $fixturePath
            $script:profileSwitches=0
            function global:agy-profile {
                param($cmd,$prof,[switch]$Force)
                if ($cmd -eq 'switch' -and $prof -eq 'account3' -and $Force) {
                    $script:profileSwitches++
                    $script:fixtureNative=[byte[]]$source.Clone()
                    Sync-AgyCliCredentialFile -Bytes $source -TokenPath $fixturePath
                } else { throw "Unexpected agy-profile invocation: cmd=$cmd prof=$prof Force=$Force" }
            }
            Set-AndVerifyAgyRunProfile -Context TURN_START
            if ($script:profileSwitches -ne 1) { throw 'TURN_START did not perform bounded profile resynchronization' }
            Write-Output 'PASS: TURN_START bounded resynchronization successfully restores and verifies active profile with provider'

            # Test TURN_START fails closed if an AGY process is active (not a safe between-turn boundary).
            $script:fixtureNative=[byte[]]$alternate.Clone()
            function global:Get-Process {
                param([string]$Name,[System.Management.Automation.ActionPreference]$ErrorAction)
                if ($Name -eq 'agy') { return [pscustomobject]@{Id=99999;ProcessName='agy'} }
                return $null
            }
            $failedBusy=$false
            try { Set-AndVerifyAgyRunProfile -Context TURN_START } catch { $failedBusy=$_.Exception.Message -match 'AGY_CREDENTIAL_RESYNC_BUSY' }
            if (-not $failedBusy) { throw 'TURN_START resync did not fail closed when AGY process was active' }
            Remove-Item Function:\Get-Process
            $script:fixtureNative=[byte[]]$source.Clone()
            Sync-AgyCliCredentialFile -Bytes $source -TokenPath $fixturePath
            Write-Output 'PASS: TURN_START resynchronization fails closed when active AGY process is detected'
        } finally {$env:USERPROFILE=$originalUserProfile}
        # Regression: expired native refresh resulting in conflicting identity fails closed.
        $script:fixtureNative=[byte[]]$expired.Clone()
        $script:refreshes=0;$script:writes=0
        function global:Update-AgyNativeAccessToken {
            $script:refreshes++
            # Simulates refresh using resident refresh token that belonged to another account (account-b)
            $script:fixtureNative=[Text.Encoding]::UTF8.GetBytes((@{token=@{access_token='FAKE-DIFF';refresh_token='FAKE-ALT';expiry='2099-01-01T00:00:00Z'};id_token=$second;auth_method='consumer'}|ConvertTo-Json -Depth 5))
        }
        $conflictFailed=$false
        try {
            Repair-AgyRefreshedNativeCredential -ExpectedBytes $source -TokenPath $path
        } catch {
            $conflictFailed=$_.Exception.Message -eq 'AGY_CREDENTIAL_REPAIR_IDENTITY_CONFLICT'
        }
        if (-not $conflictFailed -or $script:refreshes -ne 1 -or $script:writes -ne 0) {
            throw 'Expired refresh with conflicting identity was not rejected'
        }
        Write-Output 'PASS: expired native refresh producing conflicting provider identity fails closed without store mutation'
        Write-Output 'PASS: missing metadata and rotated refresh preserved; provider failure/mismatch, native/CLI conflict, concurrent change and failed readback rejected'
    } finally {
        . "$PSScriptRoot/../../scripts/validation/AgyCredentialStores.ps1"
    }
    & {
        function Invoke-RestMethod {
            param($Uri,$Headers,$TimeoutSec,$ErrorAction)
            if($Uri -ne 'https://openidconnect.googleapis.com/v1/userinfo' -or $TimeoutSec -ne 15 -or $Headers.Authorization -ne 'Bearer FAKE-ACCESS'){throw 'Unexpected provider request'}
            if($script:lookupFailure){throw 'FAKE-SENSITIVE-RESPONSE'}
            return [pscustomobject]@{sub='fixture-account-a'}
        }
        $script:lookupFailure=$false
        if((Get-AgyProviderIdentity 'FAKE-ACCESS') -ne (ConvertTo-AgyCredentialToken $source).Identity){throw 'Provider subject normalization mismatch'}
        $script:lookupFailure=$true;$failed=$false
        try{$null=Get-AgyProviderIdentity 'FAKE-ACCESS'}catch{$failed=$_.Exception.Message -like 'AGY_PROVIDER_IDENTITY_UNPROVEN:*';if($_.Exception.Message -match 'FAKE-'){throw 'Provider response leaked'}}
        if(-not $failed){throw 'Provider transport failure not closed'}
        Write-Output 'PASS: fixed HTTPS provider request, bounded lookup, subject normalization and credential-safe transport failure'
    }

} finally {
    $resolved=[IO.Path]::GetFullPath($folder);$base=[IO.Path]::GetFullPath($env:TEMP).TrimEnd('\')+'\'
    if(-not $resolved.StartsWith($base,[StringComparison]::OrdinalIgnoreCase) -or (Split-Path $resolved -Leaf) -notlike 'agy-credentials-test-*'){throw 'Unsafe fixture cleanup path'}
    if(Test-Path -LiteralPath $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
'PASS: credential layouts and safe stage/source errors, observed expired-native format, restricted repair eligibility, private ACL and store mismatch rejection; only synthetic credentials used'
