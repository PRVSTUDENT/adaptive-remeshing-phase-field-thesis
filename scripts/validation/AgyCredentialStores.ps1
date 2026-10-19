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
    $acl = New-Object Security.AccessControl.FileSecurity
    $acl.SetAccessRuleProtection($true,$false)
    $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User
    $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($sid,'FullControl','Allow')))
    Set-Acl -LiteralPath $TokenPath -AclObject $acl
    [IO.File]::WriteAllText($TokenPath,$wrapper,[Text.UTF8Encoding]::new($false))
    $verified = ConvertTo-AgyCredentialToken ([IO.File]::ReadAllBytes($TokenPath))
    if ($verified.Identity -ne $value.Identity) { throw 'AGY CLI credential synchronization failed.' }
}
