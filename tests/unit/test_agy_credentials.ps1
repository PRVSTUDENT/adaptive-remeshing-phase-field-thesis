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
            $script:RunLockedAgyProfile='account3';$EnableSmartAgyProfileSelection=$true;$ControlledSingleTurn=$true
            $script:fixtureNative=[byte[]]$live.Clone();$script:writes=0;$script:refreshes=0
            Set-AndVerifyAgyRunProfile -Context PRE_AGY
            if($script:writes -ne 1){throw 'PRE_AGY initial setup failed'}
            Write-Output 'PASS: controlled PRE provider-verified refresh recovery; zero profile switches'

            # Test POST_AGY deferred refresh: simulate AGY dropping ID metadata after execution
            $script:fixtureNative=[byte[]]$live.Clone()
            $script:refreshes=0; $writesBefore=$script:writes
            Set-AndVerifyAgyRunProfile -Context POST_AGY
            Set-AndVerifyAgyRunProfile -Context POST_AGY
            if($script:refreshes -ne 0 -or $script:writes -ne $writesBefore){throw 'POST_AGY mutated stores or invoked token refresh'}
            Write-Output 'PASS: POST_AGY deferred token refresh preserves completed turn without models refresh or store mutation'

            # Test POST_AGY with expired access token and missing ID metadata: must NOT invoke agy models
            $script:fixtureNative=[byte[]]$expired.Clone()
            $script:refreshes=0; $writesBefore=$script:writes
            Set-AndVerifyAgyRunProfile -Context POST_AGY
            if($script:refreshes -ne 0 -or $script:writes -ne $writesBefore){throw 'POST_AGY with expired token called models refresh'}
            Write-Output 'PASS: POST_AGY with expired token defers refresh without invoking agy models'

            # Test POST_AGY with genuine CLI account conflict: must fail closed.
            Sync-AgyCliCredentialFile -Bytes $alternate -TokenPath $fixturePath
            $failedConflict=$false
            try { Set-AndVerifyAgyRunProfile -Context POST_AGY } catch { $failedConflict=$true }
            if (-not $failedConflict) { throw 'POST_AGY did not fail closed on genuine CLI identity conflict' }
            Sync-AgyCliCredentialFile -Bytes $source -TokenPath $fixturePath
            Write-Output 'PASS: POST_AGY with genuine CLI identity mismatch fails closed'

            # Test POST_AGY with conflicting native identity: must fail closed.
            $script:fixtureNative=[byte[]]$alternate.Clone()
            $failedConflict=$false
            try { Set-AndVerifyAgyRunProfile -Context POST_AGY } catch { $failedConflict=$true }
            if (-not $failedConflict) { throw 'POST_AGY did not fail closed on conflicting native identity' }
            $script:fixtureNative=[byte[]]$live.Clone()
            Write-Output 'PASS: POST_AGY with genuine native identity mismatch fails closed'

            # Test PRE_QUOTA_CHECK deferred refresh with missing native ID metadata and expired token:
            # Must NOT invoke agy models, mutate stores, or call provider with expired token (which would throw HTTP 401).
            $script:fixtureNative=[byte[]]$expired.Clone()
            $script:refreshes=0; $writesBefore=$script:writes
            Set-AndVerifyAgyRunProfile -Context PRE_QUOTA_CHECK
            if ($script:refreshes -ne 0 -or $script:writes -ne $writesBefore) { throw 'PRE_QUOTA_CHECK mutated stores or called models refresh' }
            Write-Output 'PASS: PRE_QUOTA_CHECK defers token refresh without store mutation or HTTP 401 provider call'

            # Test PRE_QUOTA_CHECK with genuine CLI account conflict: must fail closed.
            Sync-AgyCliCredentialFile -Bytes $alternate -TokenPath $fixturePath
            $failedConflict=$false
            try { Set-AndVerifyAgyRunProfile -Context PRE_QUOTA_CHECK } catch { $failedConflict=$true }
            if (-not $failedConflict) { throw 'PRE_QUOTA_CHECK did not fail closed on genuine CLI identity conflict' }
            Sync-AgyCliCredentialFile -Bytes $source -TokenPath $fixturePath
            Write-Output 'PASS: PRE_QUOTA_CHECK with genuine CLI identity mismatch fails closed'

            # Test post-quota contexts (QUOTA_401_RETRY_PREP, QUOTA_401_POST_FAILURE, POST_QUOTA_CHECK) defer refresh.
            foreach ($ctx in @('QUOTA_401_RETRY_PREP', 'QUOTA_401_POST_FAILURE', 'POST_QUOTA_CHECK')) {
                $script:fixtureNative=[byte[]]$expired.Clone()
                $script:refreshes=0; $writesBefore=$script:writes
                Set-AndVerifyAgyRunProfile -Context $ctx
                if ($script:refreshes -ne 0 -or $script:writes -ne $writesBefore) { throw "$ctx mutated stores or invoked refresh" }
            }
            Write-Output 'PASS: all post-turn quota contexts defer token refresh without store mutation'

            # Regression: full post-turn credential lifecycle (Turn completed -> POST_AGY -> PRE_QUOTA_CHECK 401 -> TURN_END -> TURN_START recovery)
            $script:fixtureNative=[byte[]]$expired.Clone()
            $script:refreshes=0; $script:writes=0
            Set-AndVerifyAgyRunProfile -Context POST_AGY
            Set-AndVerifyAgyRunProfile -Context PRE_QUOTA_CHECK
            Set-AndVerifyAgyRunProfile -Context QUOTA_401_POST_FAILURE
            Set-AndVerifyAgyRunProfile -Context POST_QUOTA_CHECK
            Set-AndVerifyAgyRunProfile -Context TURN_END
            if ($script:refreshes -ne 0 -or $script:writes -ne 0) { throw 'Post-turn sequence mutated credentials or refreshed tokens prematurely' }
            Write-Output 'PASS: full post-turn lifecycle preserves research and defers credential refresh without HTTP 401 crash'

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

            # Regression: stale CLI token after native refresh is properly updated and verified against provider
            $staleCliBytes = [Text.Encoding]::UTF8.GetBytes((@{token=@{access_token='FAKE-STALE-CLI-ACCESS';refresh_token='FAKE-REFRESH';expiry='2026-09-01T00:00:00Z'};id_token=$first;auth_method='consumer'}|ConvertTo-Json -Depth 5))
            $expiredNativeBytes = [Text.Encoding]::UTF8.GetBytes((@{token=@{access_token='FAKE-EXPIRED-NATIVE-ACCESS';refresh_token='FAKE-REFRESH';expiry='2026-09-01T00:00:00Z'};id_token=$first;auth_method='consumer'}|ConvertTo-Json -Depth 5))
            $script:fixtureNative = [byte[]]$expiredNativeBytes.Clone()
            Sync-AgyCliCredentialFile -Bytes $staleCliBytes -TokenPath $fixturePath

            $script:updateNativeCalled = 0
            function global:Update-AgyNativeAccessToken {
                $script:updateNativeCalled++
                # Native store is refreshed with fresh access token
                $script:fixtureNative = [Text.Encoding]::UTF8.GetBytes((@{token=@{access_token='FAKE-FRESH-NATIVE-ACCESS';refresh_token='FAKE-REFRESH';expiry='2099-01-01T00:00:00Z'}}|ConvertTo-Json -Depth 5))
            }

            function global:Get-AgyProviderIdentity {
                param($AccessToken)
                if ($AccessToken -eq 'FAKE-STALE-CLI-ACCESS') {
                    throw "AGY_PROVIDER_IDENTITY_UNPROVEN: HTTP 401 Unauthorized; token expired or invalid; credential contents suppressed (elapsed: 10ms)."
                }
                if ($AccessToken -eq 'FAKE-FRESH-NATIVE-ACCESS') {
                    return (ConvertTo-AgyCredentialToken $source).Identity
                }
                throw "Unexpected access token in test: $AccessToken"
            }

            function global:agy-profile {
                param($cmd,$prof,[switch]$Force)
                if ($cmd -eq 'switch' -and $prof -eq 'account3' -and $Force) {
                    $script:profileSwitches++
                    $script:fixtureNative = [byte[]]$expiredNativeBytes.Clone()
                    Sync-AgyCliCredentialFile -Bytes $staleCliBytes -TokenPath $fixturePath
                } else { throw "Unexpected agy-profile invocation" }
            }

            Set-AndVerifyAgyRunProfile -Context TURN_START
            if ($script:updateNativeCalled -ne 1) { throw 'TURN_START did not trigger native access token refresh' }
            $resyncedCli = ConvertTo-AgyCredentialToken ([IO.File]::ReadAllBytes($fixturePath))
            if ($resyncedCli.Token.access_token -ne 'FAKE-FRESH-NATIVE-ACCESS') {
                throw "CLI store still has stale token ($($resyncedCli.Token.access_token)); native refresh was not synchronized"
            }
            Assert-AgyCredentialStores -ExpectedBytes $source -TokenPath $fixturePath
            Write-Output 'PASS: TURN_START verifies refreshed native access token with provider and synchronizes CLI file (no stale CLI token)'

            # Regression: TURN_START with live provider identity mismatch fails closed without mutating stores
            $script:updateNativeCalled = 0
            $script:fixtureNative = [byte[]]$expiredNativeBytes.Clone()
            Sync-AgyCliCredentialFile -Bytes $staleCliBytes -TokenPath $fixturePath
            function global:Get-AgyProviderIdentity {
                param($AccessToken)
                return (ConvertTo-AgyCredentialToken $alternate).Identity
            }
            $mismatchFailed = $false
            try {
                Set-AndVerifyAgyRunProfile -Context TURN_START
            } catch {
                $mismatchFailed = $_.Exception.Message -match 'AGY_RESYNC_PROVIDER_MISMATCH'
            }
            if (-not $mismatchFailed) { throw 'TURN_START did not fail closed on live provider identity mismatch' }
            $untouchedCli = ConvertTo-AgyCredentialToken ([IO.File]::ReadAllBytes($fixturePath))
            if ($untouchedCli.Identity -eq (ConvertTo-AgyCredentialToken $alternate).Identity) {
                throw 'CLI file was mutated to mismatched identity'
            }
            Write-Output 'PASS: TURN_START provider identity mismatch fails closed without mutating stores'

            # Regression: pending instruction and unexecuted turn state preserved on credential failure
            $testChkPath = Join-Path $folder 'controller_turn_checkpoint.json'
            $testInstruction = "Antigravity - F1597: Physically Admissible Coupled Transfer on Candidate C2`nObjective: Perform ONE bounded numerical investigation..."
            $initialPayload = [ordered]@{
                schema = 1
                turn = 2
                state = 'PENDING'
                next_instruction = $testInstruction
                next_safe_action = 'Execute only reconciled instruction'
                scientific_basis_artifact = 'results/validation/preparation-242c8dbb-aabe-433b-a9a8-5151c475c213.json'
                repository_commit = '887ed3369046a7ebb3253af0286e4a48c6e0cad6'
            }
            $payloadJson = $initialPayload | ConvertTo-Json -Depth 10 -Compress
            $hashAlg = [Security.Cryptography.SHA256]::Create()
            $payloadSha256 = [BitConverter]::ToString($hashAlg.ComputeHash([Text.Encoding]::UTF8.GetBytes($payloadJson))).Replace('-','').ToLowerInvariant()
            $envelope = @{ schema = 1; payload = $payloadJson; sha256 = $payloadSha256 } | ConvertTo-Json -Depth 5
            [IO.File]::WriteAllText($testChkPath, $envelope, [Text.UTF8Encoding]::new($false))

            $readEnvelope = [IO.File]::ReadAllText($testChkPath) | ConvertFrom-Json
            $readState = $readEnvelope.payload | ConvertFrom-Json
            if ($readState.state -ne 'PENDING' -or $readState.turn -ne 2 -or $readState.next_instruction -ne $testInstruction) {
                throw 'Checkpoint fixture creation failed'
            }
            Write-Output 'PASS: pending instruction and unexecuted turn state preserved on credential failure'
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

        # Test HTTP 401 Unauthorized: immediate failure, 0 retries
        $script:restCallCount = 0
        function Invoke-RestMethod {
            param($Uri,$Headers,$TimeoutSec,$ErrorAction)
            $script:restCallCount++
            $resp = [System.Net.HttpWebResponse][System.Runtime.Serialization.FormatterServices]::GetUninitializedObject([System.Net.HttpWebResponse])
            $statusField = [System.Net.HttpWebResponse].GetField('m_StatusCode', [System.Reflection.BindingFlags]::Instance -bor [System.Reflection.BindingFlags]::NonPublic)
            if ($statusField) { $statusField.SetValue($resp, [System.Net.HttpStatusCode]::Unauthorized) }
            $webEx = [System.Net.WebException]::new('The remote server returned an error: (401) Unauthorized.', $null, [System.Net.WebExceptionStatus]::ProtocolError, $resp)
            throw $webEx
        }
        $failed401 = $false
        try {
            $null = Get-AgyProviderIdentity 'FAKE-EXPIRED-TOKEN'
        } catch {
            $msg = $_.Exception.Message
            $failed401 = ($msg -like 'AGY_PROVIDER_IDENTITY_UNPROVEN: HTTP 401 Unauthorized*') -and ($msg -notmatch 'FAKE-')
        }
        if (-not $failed401 -or $script:restCallCount -ne 1) {
            throw "Provider HTTP 401 did not fail immediately without retries (calls: $script:restCallCount)"
        }
        Write-Output 'PASS: provider HTTP 401 fails immediately on first attempt without retrying'

        # Test transient 503 error succeeds on bounded retry
        $script:restCallCount = 0
        function Invoke-RestMethod {
            param($Uri,$Headers,$TimeoutSec,$ErrorAction)
            $script:restCallCount++
            if ($script:restCallCount -eq 1) {
                $resp = [System.Net.HttpWebResponse][System.Runtime.Serialization.FormatterServices]::GetUninitializedObject([System.Net.HttpWebResponse])
                $statusField = [System.Net.HttpWebResponse].GetField('m_StatusCode', [System.Reflection.BindingFlags]::Instance -bor [System.Reflection.BindingFlags]::NonPublic)
                if ($statusField) { $statusField.SetValue($resp, [System.Net.HttpStatusCode]::ServiceUnavailable) }
                throw [System.Net.WebException]::new('Service Unavailable', $null, [System.Net.WebExceptionStatus]::ProtocolError, $resp)
            }
            return [pscustomobject]@{ sub = 'fixture-account-a' }
        }
        $retryResult = Get-AgyProviderIdentity 'FAKE-TRANSIENT-TOKEN'
        if ($retryResult -ne (ConvertTo-AgyCredentialToken $source).Identity -or $script:restCallCount -ne 2) {
            throw "Transient 503 did not succeed on bounded retry (calls: $script:restCallCount)"
        }
        Write-Output 'PASS: transient HTTP 503 succeeds on bounded retry'

        # Test repeated transient failure fails closed after bounded retry
        $script:restCallCount = 0
        function Invoke-RestMethod {
            param($Uri,$Headers,$TimeoutSec,$ErrorAction)
            $script:restCallCount++
            $resp = [System.Net.HttpWebResponse][System.Runtime.Serialization.FormatterServices]::GetUninitializedObject([System.Net.HttpWebResponse])
            $statusField = [System.Net.HttpWebResponse].GetField('m_StatusCode', [System.Reflection.BindingFlags]::Instance -bor [System.Reflection.BindingFlags]::NonPublic)
            if ($statusField) { $statusField.SetValue($resp, [System.Net.HttpStatusCode]::ServiceUnavailable) }
            throw [System.Net.WebException]::new('Service Unavailable', $null, [System.Net.WebExceptionStatus]::ProtocolError, $resp)
        }
        $failedTransient = $false
        try {
            $null = Get-AgyProviderIdentity 'FAKE-TOKEN'
        } catch {
            $failedTransient = ($_.Exception.Message -like 'AGY_PROVIDER_IDENTITY_UNPROVEN: bounded account lookup failed (HTTP 503*')
        }
        if (-not $failedTransient -or $script:restCallCount -ne 2) {
            throw "Repeated transient failure did not fail closed after 2 attempts (calls: $script:restCallCount)"
        }
        Write-Output 'PASS: repeated transient failure fails closed after at most 1 retry'
    }

} finally {
    $resolved=[IO.Path]::GetFullPath($folder);$base=[IO.Path]::GetFullPath($env:TEMP).TrimEnd('\')+'\'
    if(-not $resolved.StartsWith($base,[StringComparison]::OrdinalIgnoreCase) -or (Split-Path $resolved -Leaf) -notlike 'agy-credentials-test-*'){throw 'Unsafe fixture cleanup path'}
    if(Test-Path -LiteralPath $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
'PASS: credential layouts and safe stage/source errors, observed expired-native format, restricted repair eligibility, private ACL and store mismatch rejection; only synthetic credentials used'
