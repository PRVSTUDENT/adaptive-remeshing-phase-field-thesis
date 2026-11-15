#!/usr/bin/env pwsh
# Dispatch script for Task F1766 Review: Unified Method A Framework Development with Full Benchmark Regression Testing Plan
# Correlation ID: HND-F1766-SUITE-PLAN-AUTH-001

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

$repoRoot = "D:\Master thesis\Adaptive remeshing"
$payloadPath = Join-Path $repoRoot ".agents\bridge_history\HND-F1766-SUITE-PLAN-AUTH-001_payload.md"
$correlationId = "HND-F1766-SUITE-PLAN-AUTH-001"
$padInboxDir = "C:\Users\pruth\.openclaw\pad\inbox"

if (-not (Test-Path $payloadPath)) {
    Write-Error "Payload file does not exist: $payloadPath"
    exit 1
}

$payloadContent = Get-Content $payloadPath -Raw

Write-Host "=== Dispathing Review Packet $correlationId ===" -ForegroundColor Cyan
Write-Host "Payload Length: $($payloadContent.Length) characters"

if ($CheckOnly) {
    Write-Host "Check-only mode: Payload verified successfully." -ForegroundColor Green
    exit 0
}

if (-not (Test-Path $padInboxDir)) {
    New-Item -ItemType Directory -Path $padInboxDir -Force | Out-Null
}

$destPath = Join-Path $padInboxDir "$correlationId.md"
Set-Content -Path $destPath -Value $payloadContent -Encoding UTF8

Write-Host "Payload dispatched to OpenClaw PAD inbox: $destPath" -ForegroundColor Green
Write-Host "Awaiting ChatGPT independent review verdict..."
