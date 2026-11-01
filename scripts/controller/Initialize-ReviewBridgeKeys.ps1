[CmdletBinding()]
param(
    [string]$Workspace = '',
    [string]$KeyDir = (Join-Path $env:USERPROFILE '.config\adaptive-remeshing'),
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($Workspace)) {
    $Workspace = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)
}

if (-not (Test-Path -LiteralPath $KeyDir)) {
    $null = New-Item -ItemType Directory -Path $KeyDir -Force
}

$privateKeyPath = (Join-Path $KeyDir 'review_bridge_ed25519.key').Replace('\', '/')
$publicConfigDir = Join-Path $Workspace 'configs/controller'
if (-not (Test-Path -LiteralPath $publicConfigDir)) {
    $null = New-Item -ItemType Directory -Path $publicConfigDir -Force
}
$publicKeyPath = (Join-Path $publicConfigDir 'review_bridge_public.pem').Replace('\', '/')

$forcePy = if ($Force.IsPresent) { "True" } else { "False" }

$pyCode = @"
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption

priv_path = Path(r'$privateKeyPath')
pub_path = Path(r'$publicKeyPath')
force = $forcePy

if priv_path.is_file() and not force:
    print('KEY_EXISTS: ' + str(priv_path))
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    priv = load_pem_private_key(priv_path.read_bytes(), password=None)
else:
    priv = Ed25519PrivateKey.generate()
    priv_bytes = priv.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    priv_path.write_bytes(priv_bytes)
    print('KEY_GENERATED: ' + str(priv_path))

pub_bytes = priv.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
pub_path.write_bytes(pub_bytes)
print('PUBLIC_KEY_WRITTEN: ' + str(pub_path))
"@

& py -3 -c $pyCode
if ($LASTEXITCODE -ne 0) { throw 'Key generation failed' }

$pubHash = (Get-FileHash -LiteralPath $publicKeyPath -Algorithm SHA256).Hash
Write-Host "Review bridge Ed25519 keys initialized." -ForegroundColor Green
Write-Host "Private Key: $privateKeyPath (Protected user directory)"
Write-Host "Public Key:  $publicKeyPath (SHA256: $pubHash)"
