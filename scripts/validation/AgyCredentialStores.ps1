function ConvertTo-AgyCredentialToken {
    param([Parameter(Mandatory)][byte[]]$Bytes)
    try {
        $data = [Text.Encoding]::UTF8.GetString($Bytes) | ConvertFrom-Json
        $token = if ($data.token) { $data.token } else { $data }
        $id = if ($token.id_token) { [string]$token.id_token } else { [string]$data.id_token }
        if (-not $id -or -not $token.refresh_token) { throw 'Missing identity or refresh credential' }
        function Get-Subject([string]$jwt) {
            $part = $jwt.Split('.')[1].Replace('-','+').Replace('_','/')
            $part = $part.PadRight($part.Length + ((4-$part.Length%4)%4),'=')
            $claims = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($part)) | ConvertFrom-Json
            if (-not $claims.sub) { throw 'Missing subject' }
            return [string]$claims.sub
        }
        $subject = Get-Subject $id
        if ($token.id_token -and $data.id_token -and (Get-Subject $token.id_token) -ne (Get-Subject $data.id_token)) { throw 'Conflicting identity claims' }
        $token | Add-Member -NotePropertyName id_token -NotePropertyValue $id -Force
        $hash = [Security.Cryptography.SHA256]::Create()
        try { $identity = ([BitConverter]::ToString($hash.ComputeHash([Text.Encoding]::UTF8.GetBytes($subject)))).Replace('-','').ToLowerInvariant().Substring(0,16) }
        finally { $hash.Dispose() }
        return [pscustomobject]@{Identity=$identity; Token=$token; AuthMethod=$(if($data.auth_method){$data.auth_method}else{'consumer'})}
    } catch { throw 'Cannot normalize AGY credential identity safely; credential contents suppressed.' }
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
    $expected = ConvertTo-AgyCredentialToken $ExpectedBytes
    $actual = ConvertTo-AgyCredentialToken (Read-AgyCredentialManagerBytes)
    if (-not (Test-Path -LiteralPath $TokenPath)) { throw 'AGY CLI token file missing; synchronize selected profile before execution.' }
    $file = ConvertTo-AgyCredentialToken ([IO.File]::ReadAllBytes($TokenPath))
    if ($actual.Identity -ne $expected.Identity -or $file.Identity -ne $expected.Identity) { throw 'AGY credential store identity mismatch; refusing model execution.' }
    # Local identity consistency, not a guarantee of provider model capacity.
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
