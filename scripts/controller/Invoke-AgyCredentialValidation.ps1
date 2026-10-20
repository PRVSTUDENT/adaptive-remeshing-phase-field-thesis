[CmdletBinding()]
param([ValidatePattern('^account[1-5]$')][string]$Profile='account3')
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../validation/AgyCredentialStores.ps1')
$expected=Get-AgySavedCredentialBytes -Profile $Profile
$path=Join-Path $env:USERPROFILE '.gemini/antigravity-cli/antigravity-oauth-token'
try {
    Repair-AgyRefreshedNativeCredential -ExpectedBytes $expected -TokenPath $path
    foreach($phase in @('PRE_AGY','POST_AGY','POST_AGY_REPEAT')) {
        Assert-AgyCredentialStores -ExpectedBytes $expected -TokenPath $path
        $nativeBytes=Read-AgyCredentialManagerBytes
        try {
            $native=ConvertTo-AgyCredentialToken $nativeBytes -SourceName native-store
            if((Get-AgyProviderIdentity $native.Token.access_token) -ne (ConvertTo-AgyCredentialToken $expected).Identity){throw 'Provider identity mismatch'}
        } finally {[Array]::Clear($nativeBytes,0,$nativeBytes.Length)}
        Write-Output "$phase PASS (local stores and provider identity; no model invocation)"
    }
} finally {[Array]::Clear($expected,0,$expected.Length)}
