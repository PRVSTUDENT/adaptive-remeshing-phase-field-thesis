# Bounded authentication transition; callbacks use the existing profile/credential APIs.
function Get-ControllerPendingAuthResumePlan {
    param($State,[string]$Instruction,[switch]$ProviderVerified,[switch]$NonExecuting)
    if($State.state -ne 'PENDING' -or $State.next_instruction -or $State.process_id -ne 0 -or $State.owned_session_fingerprint){throw 'AUTH_RESUME_NOT_UNSTARTED_PENDING'}
    if(-not $Instruction -or (Get-ControllerTextHash $Instruction) -cne $State.original_instruction_hash){throw 'AUTH_RESUME_INSTRUCTION_MISMATCH'}
    if(-not $NonExecuting -and -not $ProviderVerified){throw 'AUTH_RESUME_PROVIDER_NOT_VERIFIED'}
    [pscustomobject]@{turn=[int]$State.turn;instruction=$Instruction;conversation_id='';non_executing=[bool]$NonExecuting}
}

function New-ControllerAuthResumeReservation {
    param([string]$CheckpointPath,[string]$ExpectedHash,[string]$ReservationPath,[scriptblock]$Verify,[scriptblock]$AssertOwnerFree)
    & $AssertOwnerFree
    if((Get-FileHash $CheckpointPath).Hash -cne $ExpectedHash){throw 'AUTH_RESUME_CHECKPOINT_CHANGED'}
    if(-not (& $Verify)){throw 'AUTH_RESUME_NOT_VERIFIED'}
    & $AssertOwnerFree
    if((Get-FileHash $CheckpointPath).Hash -cne $ExpectedHash){throw 'AUTH_RESUME_CHECKPOINT_CHANGED'}
    $f=[IO.File]::Open($ReservationPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try{$b=[Text.Encoding]::UTF8.GetBytes((@{status='CHECKPOINT_RESUME_RESERVED';checkpoint_sha256=$ExpectedHash;reserved_at=[DateTimeOffset]::Now.ToString('o')}|ConvertTo-Json));$f.Write($b,0,$b.Length);$f.Flush($true)}finally{$f.Dispose()}
}

function Invoke-ControllerAuthRecovery {
    param([Parameter(Mandatory)][string]$StatePath,[Parameter(Mandatory)][string]$CheckpointHash,
          [Parameter(Mandatory)][AllowEmptyCollection()][string[]]$Profiles,[Parameter(Mandatory)][scriptblock]$Identity,
          [Parameter(Mandatory)][scriptblock]$Activate,[Parameter(Mandatory)][scriptblock]$Verify,
          [Parameter(Mandatory)][scriptblock]$Refresh)
    $state=if(Test-Path $StatePath){Get-Content $StatePath -Raw|ConvertFrom-Json}else{
        [pscustomobject]@{schema=1;checkpoint_sha256=$CheckpointHash;status='AUTH_FAILED';safety_blocked=$true;selected_profile='';attempts=@()}
    }
    if($state.checkpoint_sha256 -cne $CheckpointHash){throw 'AUTH_RECOVERY_CHECKPOINT_CHANGED'}
    function Save-AuthState {
        $tmp=$StatePath+'.tmp';[IO.File]::WriteAllText($tmp,($state|ConvertTo-Json -Depth 15),[Text.UTF8Encoding]::new($false))
        if(Test-Path $StatePath){[IO.File]::Replace($tmp,$StatePath,($StatePath+'.bak'))}else{[IO.File]::Move($tmp,$StatePath)}
    }
    if($state.status -eq 'VERIFIED_PROFILE' -and $state.selected_profile -in $Profiles){
        try{
            $actual=& $Verify $state.selected_profile
            $expected=& $Identity $state.selected_profile
            if($actual -cne $expected){throw 'AUTH_IDENTITY_MISMATCH'}
            return $state
        }catch{$state.status='AUTH_FAILED';$state.safety_blocked=$true;Save-AuthState}
    }
    # Persist intent BEFORE every external action. Interrupted attempts are not repeated.
    foreach($p in @($Profiles|Select-Object -Unique)){
        if($p -notmatch '^account[1-5]$'){throw 'UNREGISTERED_AUTH_PROFILE'}
        $prevAttempt = @($state.attempts|Where-Object {$_.profile -ceq $p})
        if($prevAttempt.Count -gt 0){
            $isStale = $false
            try {
                $expected = & $Identity $p
                if ($expected) {
                    $actual = & $Verify $p
                    if ($actual -ceq $expected) { $isStale = $true }
                }
            } catch {}
            if ($isStale) {
                $prevAttempt[0].outcome = 'VERIFIED_PROFILE'
                $state.status = 'VERIFIED_PROFILE'
                $state.selected_profile = $p
                $state.safety_blocked = $false
                Save-AuthState
                return $state
            }
            continue
        }
        $a=[pscustomobject]@{profile=$p;stage='AUTH_RECOVERY';refresh_attempted=$false;outcome='IN_PROGRESS';identity=''}
        $state.attempts+=@($a);$state.status='AUTH_RECOVERY';Save-AuthState
        try{
            $expected=& $Identity $p
            if(-not $expected){throw 'AUTH_IDENTITY_MISSING'}
            $a.identity=[string]$expected;Save-AuthState
            & $Activate $p|Out-Null
            try{$actual=& $Verify $p}catch{
                if($_.Exception.Message -notmatch '401|AGY_CREDENTIAL_EXPIRED'){throw}
                $a.refresh_attempted=$true;Save-AuthState
                & $Refresh $p|Out-Null
                $actual=& $Verify $p
            }
            if($actual -cne $expected){throw 'AUTH_IDENTITY_MISMATCH'}
            $a.outcome='VERIFIED_PROFILE';$state.status='VERIFIED_PROFILE';$state.selected_profile=$p;$state.safety_blocked=$false;Save-AuthState
            return $state
        }catch{
            # Persist categories only, never exception payloads that might contain secrets.
            $a.outcome=if($_.Exception.Message -match 'MISMATCH|CONFLICT'){'IDENTITY_MISMATCH'}else{'AUTHENTICATION_FAILED'}
            Save-AuthState
        }
    }
    $state.status='AUTH_RECOVERY_REQUIRED';$state.safety_blocked=$true;Save-AuthState
    return $state
}

function Invoke-AgyAuthenticationFailover {
    $marker=(Get-Content (Join-Path $env:USERPROFILE '.gemini/agy-profiles/_active.txt') -Raw).Trim()
    $profiles=@($AgyProfileRotationOrder|Where-Object {-not(Get-AgySmartCooldownActive -Profile $_)})
    $current=$marker
    if(-not (Get-Process agy -ErrorAction SilentlyContinue) -and $script:RunLockedAgyProfile -in $profiles){$current=$script:RunLockedAgyProfile}
    if($current -notin $profiles){$current=if($marker -in $profiles){$marker}elseif($profiles.Count -gt 0){$profiles[0]}else{''}}
    $r=Invoke-ControllerExistingProfileRecovery -CheckpointPath $controllerCheckpointPath -Profiles $profiles -CurrentProfile $current
    if($r.safety_blocked){throw 'AUTH_RECOVERY_REQUIRED: eligible existing profiles exhausted; legitimate interactive sign-in required'}
    $script:RunLockedAgyProfile=$r.selected_profile
    $script:AuthoritativeAgyProfile=$r.selected_profile
    $script:SelectedAgyProfile=$r.selected_profile
    $script:PinnedAgyProfile=$r.selected_profile
    $script:ControllerAuthVerifiedForCheckpoint=(Get-FileHash $controllerCheckpointPath).Hash
    $script:ConversationId='';$script:ConversationIdSource='auth-recovery-fresh-conversation'
    [IO.File]::WriteAllText($SelectionFile,(@{selected_profile=$r.selected_profile;source='verified-auth-recovery';switched_at_utc=[DateTimeOffset]::UtcNow.ToString('o')}|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
    Write-Host ('[AUTH] VERIFIED_PROFILE '+$r.selected_profile+'; preserved checkpoint; fresh conversation required')
    return [pscustomobject]@{new_profile=$r.selected_profile;new_conversation_policy='agy-create-on-first-turn'}
}

function Assert-ControllerBackgroundHubsOnly {
    param([string]$CheckpointPath)
    $state=Read-ControllerCheckpoint $CheckpointPath
    $workspace=[string]$state.workspace
    if(-not $workspace){throw 'AUTH_RECOVERY_OWNER_UNRESOLVED'}
    $session=Get-Content -LiteralPath (Join-Path $workspace 'project_coordination/ACTIVE_SESSION.json') -Raw|ConvertFrom-Json
    $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $validPaths=@(
        [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE '.gemini/bin/agy.exe')),
        [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'agy/bin/agy.exe')),
        [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE 'AppData/Local/agy/bin/agy.exe'))
    )
    $workerLive = $false
    if($state.process_id){
        $wp = Get-CimInstance Win32_Process -Filter ("ProcessId = " + [int]$state.process_id) -ErrorAction SilentlyContinue
        if($wp){
            $exeFull = try{if($wp.ExecutablePath){[IO.Path]::GetFullPath($wp.ExecutablePath)}else{''}}catch{''}
            $isAgy = ($wp.Name -ieq 'agy.exe') -or ($exeFull -in $validPaths)
            $isMockTest = ($wp.ProcessId -eq $state.process_id) -and (-not $wp.ExecutablePath)
            if($isAgy -or $isMockTest){
                $workerLive = $true
            }
        }
    }
    if($session.active -or $workerLive){throw 'AUTH_RECOVERY_LIVE_AGY'}
    foreach($p in @(Get-CimInstance Win32_Process -Filter "Name = 'agy.exe'" -ErrorAction Stop)){
        $parent=Get-CimInstance Win32_Process -Filter ("ProcessId = "+$p.ParentProcessId) -ErrorAction Stop
        $owner=Invoke-CimMethod -InputObject $p -MethodName GetOwnerSid -ErrorAction Stop
        $exeFull=try{[IO.Path]::GetFullPath($p.ExecutablePath)}catch{''}
        if($exeFull -notin $validPaths -or $owner.ReturnValue -ne 0 -or $owner.Sid -cne $sid){throw 'AUTH_RECOVERY_LIVE_AGY'}
        if($p.CommandLine -match '(?:^|\s)--(?:print|conversation|input-format|output-format)' -or ($workerLive -and $p.ProcessId -eq $state.process_id)){throw 'AUTH_RECOVERY_LIVE_AGY'}
        $isHub=($p.CommandLine -match '(?:^|\s)--hub(?:\s|$)') -and ($parent -and $parent.Name -ieq 'Code.exe' -and $parent.CreationDate -le $p.CreationDate)
        $isInteractive=($p.CommandLine -notmatch '(?:^|\s)--hub(?:\s|$)') -and ($parent -and $parent.Name -match '^(?:powershell|pwsh|cmd|wt|Code)\.exe$' -and $parent.CreationDate -le $p.CreationDate)
        if(-not $isHub -and -not $isInteractive){throw 'AUTH_RECOVERY_LIVE_AGY'}
    }
}

function Invoke-ControllerReadOnlyProfileCheck {
    param([string]$CheckpointPath,[string]$CurrentProfile,[scriptblock]$AssertOwnerFree,[scriptblock]$Verify)
    if($CurrentProfile -notmatch '^account[1-5]$'){throw 'AUTH_RECOVERY_LIVE_AGY'}
    $hash=(Get-FileHash -LiteralPath $CheckpointPath).Hash
    & $AssertOwnerFree
    try{if(-not (& $Verify $CurrentProfile)){throw 'Unverified'}}catch{throw 'AUTH_RECOVERY_LIVE_AGY: current profile needs recovery; credential mutation remains blocked'}
    & $AssertOwnerFree
    if((Get-FileHash -LiteralPath $CheckpointPath).Hash -cne $hash){throw 'AUTH_RECOVERY_CHECKPOINT_CHANGED'}
    [pscustomobject]@{status='VERIFIED_PROFILE';selected_profile=$CurrentProfile;safety_blocked=$false;read_only=$true}
}

function Invoke-ControllerExistingProfileRecovery {
    param([string]$CheckpointPath,[string[]]$Profiles,[string]$CurrentProfile)
    $backgroundHub=[bool](Get-Process agy -ErrorAction SilentlyContinue)
    if($backgroundHub){
        # Prefer read-only proof. A verified idle sidebar permits recovery of
        # its current account, but never profile rotation or a live worker.
        $marker=(Get-Content (Join-Path $env:USERPROFILE '.gemini/agy-profiles/_active.txt') -Raw).Trim()
        $candidateProfile = if ($marker -in $Profiles) { $marker } elseif ($CurrentProfile -in $Profiles) { $CurrentProfile } else { '' }
        if ($candidateProfile) {
            try{return Invoke-ControllerReadOnlyProfileCheck -CheckpointPath $CheckpointPath -CurrentProfile $candidateProfile -AssertOwnerFree {
                Assert-ControllerBackgroundHubsOnly $CheckpointPath
            } -Verify {
                param($profile)
                $activeMarker=(Get-Content (Join-Path $env:USERPROFILE '.gemini/agy-profiles/_active.txt') -Raw).Trim()
                if($activeMarker -cne $profile){return $false}
                $saved=$null;$cli=$null;$native=$null
                try{
                    $saved=Get-AgySavedCredentialBytes $profile
                    $tokenPath=Join-Path $env:USERPROFILE '.gemini/antigravity-cli/antigravity-oauth-token'
                    if (-not (Test-Path -LiteralPath $tokenPath)) { return $false }
                    $expected=ConvertTo-AgyCredentialToken $saved -SourceName saved-profile
                    $cli=[IO.File]::ReadAllBytes($tokenPath);$native=Read-AgyCredentialManagerBytes
                    if (-not $cli -or -not $native) { return $false }
                    foreach($bytes in @($cli,$native)){
                        $token=ConvertTo-AgyCredentialToken $bytes -SourceName unspecified -AllowMissingIdentity
                        $expiry=[datetimeoffset]::MinValue
                        if(-not $token.Token.access_token -or -not [datetimeoffset]::TryParse([string]$token.Token.expiry,[ref]$expiry) -or $expiry -le [datetimeoffset]::UtcNow){return $false}
                        if((Get-AgyProviderIdentity -AccessToken $token.Token.access_token) -cne $expected.Identity){return $false}
                    }
                    if (-not (ConvertTo-AgyCredentialToken $native -SourceName native-store -AllowMissingIdentity).Identity) {
                        Repair-AgyRefreshedNativeCredential -ExpectedBytes $saved -TokenPath $tokenPath -SkipTokenRefresh -CheckpointPath $CheckpointPath
                    }
                    Assert-AgyCredentialStores -ExpectedBytes $saved -TokenPath $tokenPath
                    return $true
                }finally{foreach($bytes in @($saved,$cli,$native)){if($bytes){[Array]::Clear($bytes,0,$bytes.Length)}}}
            }}catch{
                if($_.Exception.Message -notmatch 'current profile needs recovery'){throw}
                # The idle sidebar is not a research worker. Recover only the SAME
                # selected account; never rotate credentials underneath the sidebar.
                Assert-ControllerBackgroundHubsOnly $CheckpointPath
                if($candidateProfile -notmatch '^account[1-5]$'){throw 'AUTH_RECOVERY_LIVE_AGY'}
                $Profiles=@($candidateProfile)
            }
        }
    }
    $hash=(Get-FileHash -LiteralPath $CheckpointPath).Hash
    $root=Join-Path $env:USERPROFILE 'OpenClawPAD/auth_recovery';[IO.Directory]::CreateDirectory($root)|Out-Null
    $eligible=@(@($CurrentProfile)+$Profiles|Where-Object {$_ -match '^account[1-5]$' -and (Test-Path (Join-Path $env:USERPROFILE ".gemini/agy-profiles/$_/credential.dpapi"))}|Select-Object -Unique)
    # A newly saved legitimate interactive login starts a new generation while
    # preserving exhausted attempt history. Automatic native refresh does not.
    $generation=(@('account1','account2','account3','account4','account5')|ForEach-Object {$f=Join-Path $env:USERPROFILE ".gemini/agy-profiles/$_/credential.dpapi";if(Test-Path $f){(Get-FileHash $f).Hash}}) -join ':'
    $sha=[Security.Cryptography.SHA256]::Create()
    try{$revision=([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($generation)))).Replace('-','').Substring(0,16)}finally{$sha.Dispose()}
    $path=Join-Path $root ($hash+'-'+$revision+'.json')
    $tokenPath=Join-Path $env:USERPROFILE '.gemini/antigravity-cli/antigravity-oauth-token'
    $identity={param($p) $b=Get-AgySavedCredentialBytes $p;try{(ConvertTo-AgyCredentialToken $b -SourceName saved-profile).Identity}finally{[Array]::Clear($b,0,$b.Length)}}
    $activate={param($p)
        $marker=(Get-Content (Join-Path $env:USERPROFILE '.gemini/agy-profiles/_active.txt') -Raw).Trim()
        if($marker -ceq $p){return} # Never restore an old saved access token over a freshly verified one.
        if($backgroundHub){throw 'AUTH_RECOVERY_HUB_PROFILE_SWITCH_FORBIDDEN'}
        $null=& agy-profile switch $p -Force *>&1;if($LASTEXITCODE -ne 0){throw 'AUTH_PROFILE_SWITCH_FAILED'}
    }
    $verify={param($p) $b=Get-AgySavedCredentialBytes $p;try{Repair-AgyRefreshedNativeCredential -ExpectedBytes $b -TokenPath $tokenPath -SkipTokenRefresh -CheckpointPath $CheckpointPath; (ConvertTo-AgyCredentialToken $b -SourceName saved-profile).Identity}finally{[Array]::Clear($b,0,$b.Length)}}
    $result=Invoke-ControllerAuthRecovery -StatePath $path -CheckpointHash $hash -Profiles $eligible -Identity $identity -Activate $activate -Verify $verify -Refresh {
        param($p)
        if($backgroundHub){Assert-ControllerBackgroundHubsOnly $CheckpointPath}
        Update-AgyNativeAccessToken
        if($backgroundHub){Assert-ControllerBackgroundHubsOnly $CheckpointPath}
    }
    if((Get-FileHash -LiteralPath $CheckpointPath).Hash -cne $hash){throw 'AUTH_RECOVERY_CHECKPOINT_CHANGED'}
    return $result
}
