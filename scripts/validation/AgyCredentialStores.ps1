function ConvertTo-AgyCredentialToken {
    param([Parameter(Mandatory)][byte[]]$Bytes,
          [ValidateSet('unspecified','saved-profile','native-store','cli-file','sync-input','sync-verify')][string]$SourceName='unspecified',
          [switch]$AllowMissingIdentity)
    $stage='JSON_DECODE'
    try {
        function Get-Field($obj,[string]$name) {
            if ($null -eq $obj) { return $null }
            if ($obj -is [Collections.IDictionary]) { return $obj[$name] }
            $property=$obj.PSObject.Properties[$name]
            if ($null -ne $property) { return $property.Value }
            return $null
        }
        $data = [Text.Encoding]::UTF8.GetString($Bytes).TrimStart([char]0xFEFF) | ConvertFrom-Json -ErrorAction Stop
        $stage='TOKEN_SHAPE'
        $nested=Get-Field $data 'token'
        $token=if($nested){$nested}else{$data}
        if ($token -isnot [pscustomobject]) { throw 'Invalid token object' }
        $stage='REFRESH_TOKEN_MISSING'
        if (-not (Get-Field $token 'refresh_token')) { throw 'Refresh credential missing' }
        $nestedId=[string](Get-Field $token 'id_token');$rootId=[string](Get-Field $data 'id_token')
        $id=if($nestedId){$nestedId}else{$rootId}
        $stage='ID_TOKEN_MISSING'
        if (-not $id -and -not $AllowMissingIdentity) { throw 'Identity metadata missing' }
        function Get-Subject([string]$jwt) {
            $part = $jwt.Split('.')[1].Replace('-','+').Replace('_','/')
            $part = $part.PadRight($part.Length + ((4-$part.Length%4)%4),'=')
            $claims = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($part)) | ConvertFrom-Json
            if (-not $claims.sub) { throw 'Missing subject' }
            return [string]$claims.sub
        }
        $identity=$null
        if ($id) {
            $stage='ID_TOKEN_DECODE'
            $subject = Get-Subject $id
            $stage='ID_TOKEN_CONFLICT'
            if ($nestedId -and $rootId -and (Get-Subject $nestedId) -ne (Get-Subject $rootId)) { throw 'Conflicting identity claims' }
            $token | Add-Member -NotePropertyName id_token -NotePropertyValue $id -Force
            $hash = [Security.Cryptography.SHA256]::Create()
            try { $identity = ([BitConverter]::ToString($hash.ComputeHash([Text.Encoding]::UTF8.GetBytes($subject)))).Replace('-','').ToLowerInvariant().Substring(0,16) }
            finally { $hash.Dispose() }
        }
        $method=Get-Field $data 'auth_method'
        return [pscustomobject]@{Identity=$identity; Token=$token; AuthMethod=$(if($method){$method}else{'consumer'})}
    } catch {
        $category=$_.Exception.GetType().Name
        throw "AGY_CREDENTIAL_NORMALIZATION source=$SourceName stage=$stage category=$category; credential contents suppressed."
    }
}

function Get-AgyProfileSaveBytes {
    param([Parameter(Mandatory)][byte[]]$Bytes,
          [Parameter(Mandatory)][string]$TokenPath)
    # Save preparation only: no native/CLI/profile writes and no token refresh.
    # AGY can legitimately drop ID metadata while retaining a live OAuth grant.
    $native=ConvertTo-AgyCredentialToken -Bytes $Bytes -SourceName native-store -AllowMissingIdentity
    if ($native.Identity) { return ,([byte[]]$Bytes.Clone()) }
    $stage='CLI_IDENTITY_METADATA'
    $cliBytes=$null
    try {
        if (-not (Test-Path -LiteralPath $TokenPath -PathType Leaf)) { throw 'Missing CLI metadata' }
        $cliBytes=[IO.File]::ReadAllBytes($TokenPath)
        $cli=ConvertTo-AgyCredentialToken -Bytes $cliBytes -SourceName cli-file
        $stage='ACCESS_TOKEN_MISSING'
        if ([string]::IsNullOrWhiteSpace([string]$native.Token.access_token)) { throw 'No live grant' }
        $stage='AUTH_METHOD_CONFLICT'
        if ($native.AuthMethod -ne $cli.AuthMethod) { throw 'Authentication methods differ' }
        $stage='PROVIDER_IDENTITY_UNPROVEN'
        # Do not infer identity from active markers, quota, refresh-token equality
        # or a possibly stale CLI account. Prove the native access grant at Google.
        $providerIdentity=Get-AgyProviderIdentity -AccessToken $native.Token.access_token
        $stage='PROVIDER_IDENTITY_CONFLICT'
        if (-not $providerIdentity -or $providerIdentity -ne $cli.Identity) { throw 'Account mismatch' }
        $stage='CLI_CONCURRENT_CHANGE'
        if ([Convert]::ToBase64String([IO.File]::ReadAllBytes($TokenPath)) -cne
            [Convert]::ToBase64String($cliBytes)) { throw 'CLI changed during verification' }
        $native.Token | Add-Member -NotePropertyName id_token -NotePropertyValue $cli.Token.id_token -Force
        $candidate=[Text.Encoding]::UTF8.GetBytes((@{token=$native.Token;auth_method=$native.AuthMethod}|ConvertTo-Json -Depth 12 -Compress))
        $stage='CANDIDATE_VERIFICATION'
        $verified=ConvertTo-AgyCredentialToken -Bytes $candidate -SourceName sync-verify
        if ($verified.Identity -ne $providerIdentity) { throw 'Candidate identity mismatch' }
        return ,$candidate
    } catch {
        # Provider/JSON exceptions can contain HTTP context; do not relay their text.
        throw "AGY_PROFILE_SAVE_IDENTITY source=native-store stage=$stage; profile not written; credential contents suppressed."
    } finally {
        if ($cliBytes) { [Array]::Clear($cliBytes,0,$cliBytes.Length) }
    }
}

function Read-AgyCredentialManagerBytes {
    if (-not ('AgyLocalCredentialReader' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class AgyLocalCredentialReader {
 [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] struct CRED {
  public UInt32 Flags,Type; public string TargetName,Comment; public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
  public UInt32 Size; public IntPtr Blob; public UInt32 Persist,Count; public IntPtr Attributes; public string Alias,User;
 }
 [DllImport("advapi32.dll",EntryPoint="CredReadW",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool Read(string target,UInt32 type,UInt32 flags,out IntPtr ptr);
 [DllImport("advapi32.dll")] static extern void CredFree(IntPtr ptr);
 public static byte[] Get() { IntPtr ptr; if(!Read("gemini:antigravity",1,0,out ptr)) throw new Exception("AGY credential unavailable");
  try { var c=(CRED)Marshal.PtrToStructure(ptr,typeof(CRED)); var b=new byte[c.Size]; Marshal.Copy(c.Blob,b,0,b.Length); return b; } finally { CredFree(ptr); }
 }
}
'@
    }
    return ,([AgyLocalCredentialReader]::Get())
}

function Assert-AgyCredentialStores {
    param([Parameter(Mandatory)][byte[]]$ExpectedBytes, [Parameter(Mandatory)][string]$TokenPath)
    $expected = ConvertTo-AgyCredentialToken $ExpectedBytes -SourceName saved-profile
    $actual = ConvertTo-AgyCredentialToken (Read-AgyCredentialManagerBytes) -SourceName native-store
    if (-not (Test-Path -LiteralPath $TokenPath)) { throw 'AGY CLI token file missing; synchronize selected profile before execution.' }
    $file = ConvertTo-AgyCredentialToken ([IO.File]::ReadAllBytes($TokenPath)) -SourceName cli-file
    if ($actual.Identity -ne $expected.Identity -or $file.Identity -ne $expected.Identity) { throw 'AGY credential store identity mismatch; refusing model execution.' }
    # Local identity consistency, not a guarantee of provider model capacity.
}

function Test-AgyExpiredNativeRepair {
    param([byte[]]$ExpectedBytes,[byte[]]$NativeBytes,[byte[]]$CliBytes,[datetimeoffset]$Now=[datetimeoffset]::UtcNow)
    # This is an eligibility check only. It never establishes native identity or bypasses Assert.
    try {
        $expected=ConvertTo-AgyCredentialToken $ExpectedBytes -SourceName saved-profile
        $file=ConvertTo-AgyCredentialToken $CliBytes -SourceName cli-file
        if ($file.Identity -ne $expected.Identity) { return $false }
        $native=ConvertTo-AgyCredentialToken $NativeBytes -SourceName native-store -AllowMissingIdentity
        if ($native.Identity -and $native.Identity -ne $expected.Identity) { return $false }
        $expiry=[datetimeoffset]::MinValue
        $field=$native.Token.PSObject.Properties['expiry']
        if ($null -eq $field -or -not [datetimeoffset]::TryParse([string]$field.Value,[ref]$expiry)) { return $false }
        return ($expiry -lt $Now)
    } catch { return $false }
}

function Get-AgySavedCredentialBytes {
    param([Parameter(Mandatory)][ValidatePattern('^account[1-5]$')][string]$Profile)
    Add-Type -AssemblyName System.Security
    $path = Join-Path $env:USERPROFILE ".gemini/agy-profiles/$Profile/credential.dpapi"
    if (-not (Test-Path -LiteralPath $path)) { throw 'Selected saved AGY credential is missing.' }
    $plain = $null
    try {
        $plain = [Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($path),$null,'CurrentUser')
        $envelope = [Text.Encoding]::UTF8.GetString($plain) | ConvertFrom-Json
        return ,([Convert]::FromBase64String($envelope.blobB64))
    } finally { if ($plain) { [Array]::Clear($plain,0,$plain.Length) } }
}

function Sync-AgyCliCredentialFile {
    param([Parameter(Mandatory)][byte[]]$Bytes, [Parameter(Mandatory)][string]$TokenPath)
    $value = ConvertTo-AgyCredentialToken $Bytes
    $wrapper = @{token=$value.Token;auth_method=$value.AuthMethod} | ConvertTo-Json -Depth 12 -Compress
    $folder = Split-Path $TokenPath -Parent
    if (-not (Test-Path -LiteralPath $folder)) { $null=New-Item -ItemType Directory -Path $folder -Force }
    if (-not (Test-Path -LiteralPath $TokenPath)) { [IO.File]::WriteAllBytes($TokenPath,[byte[]]@()) }
    $fileInfo = New-Object System.IO.FileInfo($TokenPath)
    $acl = $fileInfo.GetAccessControl([System.Security.AccessControl.AccessControlSections]::Access)
    $acl.SetAccessRuleProtection($true,$false)
    foreach ($rule in @($acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]))) {
        $acl.RemoveAccessRule($rule) | Out-Null
    }
    $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User
    $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($sid,'FullControl','Allow')))
    $fileInfo.SetAccessControl($acl)
    [IO.File]::WriteAllText($TokenPath,$wrapper,[Text.UTF8Encoding]::new($false))
    $verified = ConvertTo-AgyCredentialToken ([IO.File]::ReadAllBytes($TokenPath))
    if ($verified.Identity -ne $value.Identity) { throw 'AGY CLI credential synchronization failed.' }
}

function Get-AgyProviderIdentity {
    param([Parameter(Mandatory)][string]$AccessToken)
    # Fixed HTTPS origin, bearer header only: no credentials in URLs or diagnostics.
    $maxAttempts = 2
    $attempt = 0
    $uri = 'https://openidconnect.googleapis.com/v1/userinfo'
    $headers = @{ Authorization = ('Bearer ' + $AccessToken) }

    while ($attempt -lt $maxAttempts) {
        $attempt++
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            $reply = Invoke-RestMethod -Uri $uri -Headers $headers -TimeoutSec 15 -ErrorAction Stop
            $stopwatch.Stop()
            if (-not $reply.sub) { throw 'Missing provider subject' }
            $hash = [Security.Cryptography.SHA256]::Create()
            try { return ([BitConverter]::ToString($hash.ComputeHash([Text.Encoding]::UTF8.GetBytes([string]$reply.sub)))).Replace('-','').ToLowerInvariant().Substring(0,16) }
            finally { $hash.Dispose() }
        } catch {
            $stopwatch.Stop()
            $elapsedMs = [int]$stopwatch.ElapsedMilliseconds
            $ex = $_.Exception
            $inner = if ($ex.InnerException) { $ex.InnerException } else { $ex }
            $category = $inner.GetType().Name
            $statusCode = $null

            if ($inner -is [System.Net.WebException] -and $inner.Response) {
                try { $statusCode = [int](([System.Net.HttpWebResponse]$inner.Response).StatusCode) } catch {}
            } elseif ($inner.PSObject.Properties['StatusCode']) {
                try { $statusCode = [int]$inner.StatusCode } catch {}
            }

            if ($statusCode -eq 401) {
                throw "AGY_PROVIDER_IDENTITY_UNPROVEN: HTTP 401 Unauthorized; token expired or invalid; credential contents suppressed (elapsed: ${elapsedMs}ms)."
            }

            $isTransient = $false
            if ($statusCode) {
                if ($statusCode -ge 500 -or $statusCode -eq 408 -or $statusCode -eq 429) { $isTransient = $true }
            } else {
                if ($category -in @('WebException', 'TimeoutException', 'IOException', 'HttpRequestException', 'SocketException')) {
                    $isTransient = $true
                }
            }

            if ($attempt -lt $maxAttempts -and $isTransient) {
                Start-Sleep -Seconds 1
                continue
            }

            $detail = if ($statusCode) { "HTTP $statusCode ($category, elapsed: ${elapsedMs}ms)" } else { "$category, elapsed: ${elapsedMs}ms" }
            throw "AGY_PROVIDER_IDENTITY_UNPROVEN: bounded account lookup failed ($detail); credential contents suppressed."
        }
    }
}

function Write-AgyCredentialManagerBytes {
    param([Parameter(Mandatory)][byte[]]$Bytes)
    # Preserve the native entry metadata; replace only its blob. Never switch profiles.
    if (-not ('AgyLocalCredentialWriter' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class AgyLocalCredentialWriter {
 [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] struct CRED {
  public UInt32 Flags,Type; public string TargetName,Comment; public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
  public UInt32 Size; public IntPtr Blob; public UInt32 Persist,Count; public IntPtr Attributes; public string Alias,User;
 }
 [DllImport("advapi32.dll",EntryPoint="CredReadW",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool Read(string target,UInt32 type,UInt32 flags,out IntPtr ptr);
 [DllImport("advapi32.dll",EntryPoint="CredWriteW",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool Write(ref CRED value,UInt32 flags);
 [DllImport("advapi32.dll")] static extern void CredFree(IntPtr ptr);
 public static void Put(byte[] bytes) {
  IntPtr ptr; if(!Read("gemini:antigravity",1,0,out ptr)) throw new Exception("AGY native entry missing");
  IntPtr blob=IntPtr.Zero;
  try { var c=(CRED)Marshal.PtrToStructure(ptr,typeof(CRED)); blob=Marshal.AllocHGlobal(bytes.Length);
   Marshal.Copy(bytes,0,blob,bytes.Length); c.Blob=blob; c.Size=(UInt32)bytes.Length;
   if(!Write(ref c,0)) throw new Exception("AGY native credential write failed");
  } finally { if(blob!=IntPtr.Zero) { for(int i=0;i<bytes.Length;i++) Marshal.WriteByte(blob,i,0); Marshal.FreeHGlobal(blob); } CredFree(ptr); }
 }
}
'@
    }
    [AgyLocalCredentialWriter]::Put($Bytes)
}

function Update-AgyNativeAccessToken {
    # Account discovery only; this command does not invoke a generative model.
    . (Join-Path $PSScriptRoot 'Invoke-BoundedAgyProcess.ps1')
    $exe=Join-Path $env:LOCALAPPDATA 'agy/bin/agy.exe'
    $result=Invoke-BoundedAgyProcess -FilePath $exe -ArgumentList @('models') -TimeoutSeconds 30 -WorkingDirectory $env:USERPROFILE
    if($result.TimedOut -or $result.ExitCode -ne 0){throw 'AGY_CREDENTIAL_REFRESH_FAILED: non-generative account discovery failed.'}
}

function Repair-AgyRefreshedNativeCredential {
    param([Parameter(Mandatory)][byte[]]$ExpectedBytes,[Parameter(Mandatory)][string]$TokenPath,[switch]$SkipTokenRefresh)
    $cliBytes=$null;$nativeBytes=$null;$candidate=$null;$readback=$null
    try {
        if (Get-Process -Name agy -ErrorAction SilentlyContinue) { throw 'AGY_CREDENTIAL_REPAIR_BUSY' }
        $expected=ConvertTo-AgyCredentialToken $ExpectedBytes -SourceName saved-profile
        $cliBytes=[IO.File]::ReadAllBytes($TokenPath)
        $cli=ConvertTo-AgyCredentialToken $cliBytes -SourceName cli-file
        $nativeBytes=Read-AgyCredentialManagerBytes
        $native=ConvertTo-AgyCredentialToken $nativeBytes -SourceName native-store -AllowMissingIdentity
        if ($cli.Identity -ne $expected.Identity -or ($native.Identity -and $native.Identity -ne $expected.Identity)) {
            Write-Warning ("[PROFILE-GUARD] Identity conflict detected before repair: expected '{0}', CLI '{1}', native '{2}'." -f $expected.Identity, $cli.Identity, $native.Identity)
            throw 'AGY_CREDENTIAL_REPAIR_IDENTITY_CONFLICT'
        }
        $expiry=[datetimeoffset]::MinValue
        if (-not $SkipTokenRefresh -and [datetimeoffset]::TryParse([string]$native.Token.expiry,[ref]$expiry) -and $expiry -le [datetimeoffset]::UtcNow) {
            Update-AgyNativeAccessToken
            [Array]::Clear($nativeBytes,0,$nativeBytes.Length)
            $nativeBytes=Read-AgyCredentialManagerBytes
            $native=ConvertTo-AgyCredentialToken $nativeBytes -SourceName native-store -AllowMissingIdentity
        }
        if ($native.Identity -and $native.Identity -ne $expected.Identity) {
            Write-Warning ("[PROFILE-GUARD] Conflicting identity detected after token refresh: expected '{0}', actual '{1}'." -f $expected.Identity, $native.Identity)
            throw 'AGY_CREDENTIAL_REPAIR_IDENTITY_CONFLICT'
        }
        if (-not $native.Token.access_token) { throw 'AGY_CREDENTIAL_REPAIR_ACCESS_MISSING' }
        if ((Get-AgyProviderIdentity -AccessToken $native.Token.access_token) -ne $expected.Identity) { throw 'AGY_CREDENTIAL_REPAIR_PROVIDER_MISMATCH' }
        # Provider proved this live grant. Restore missing metadata only after that proof.
        if (-not $native.Identity) { $native.Token | Add-Member -NotePropertyName id_token -NotePropertyValue $expected.Token.id_token -Force }
        $candidate=[Text.Encoding]::UTF8.GetBytes((@{token=$native.Token;auth_method=$native.AuthMethod}|ConvertTo-Json -Depth 12 -Compress))
        if ([Convert]::ToBase64String([IO.File]::ReadAllBytes($TokenPath)) -cne [Convert]::ToBase64String($cliBytes) -or
            [Convert]::ToBase64String((Read-AgyCredentialManagerBytes)) -cne [Convert]::ToBase64String($nativeBytes)) { throw 'AGY_CREDENTIAL_REPAIR_CONCURRENT_CHANGE' }
        if ([Convert]::ToBase64String($nativeBytes) -cne [Convert]::ToBase64String($candidate)) { Write-AgyCredentialManagerBytes -Bytes $candidate }
        $readback=Read-AgyCredentialManagerBytes
        if ([Convert]::ToBase64String($readback) -cne [Convert]::ToBase64String($candidate)) { throw 'AGY_CREDENTIAL_REPAIR_READBACK_FAILED' }
        $cliNormalized=[Text.Encoding]::UTF8.GetBytes((@{token=$cli.Token;auth_method=$cli.AuthMethod}|ConvertTo-Json -Depth 12 -Compress))
        try {
            if ([Convert]::ToBase64String($cliNormalized) -cne [Convert]::ToBase64String($candidate)) { Sync-AgyCliCredentialFile -Bytes $candidate -TokenPath $TokenPath }
        } finally { [Array]::Clear($cliNormalized,0,$cliNormalized.Length) }
        Assert-AgyCredentialStores -ExpectedBytes $ExpectedBytes -TokenPath $TokenPath
    } finally {
        foreach($buffer in @($cliBytes,$nativeBytes,$candidate,$readback)) { if($buffer){[Array]::Clear($buffer,0,$buffer.Length)} }
    }
}
