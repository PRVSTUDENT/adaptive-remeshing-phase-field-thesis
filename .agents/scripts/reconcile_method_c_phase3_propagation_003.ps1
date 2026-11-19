# -*- coding: utf-8 -*-
# .agents/scripts/reconcile_method_c_phase3_propagation_003.ps1
# Reconciles and validates the returned bridge_response.ready for HND-METHOD-C-PHASE3-PROPAGATION-003.

$ErrorActionPreference = 'Stop'

$repoRoot = "D:\Master thesis\Adaptive remeshing"
. (Join-Path $repoRoot ".agents\scripts\Bridge-ResearchContract.ps1")

$bridgeDir = "C:\Users\pruth\OpenClawPAD\ChatGPTBridge"
$responseReady = Join-Path $bridgeDir "bridge_response.ready"

if (-not (Test-Path -LiteralPath $responseReady)) {
    throw "bridge_response.ready not found at: $responseReady"
}

$ctx = Get-BridgePolicyContext
$packet = [pscustomobject]@{
    handoff_id = "HND-METHOD-C-PHASE3-PROPAGATION-003"
    protocol   = "INDEPENDENT_STRUCTURED_REVIEW_V1"
    task_id    = "METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON"
    context    = $ctx
}

$raw = [System.IO.File]::ReadAllText($responseReady, [System.Text.UTF8Encoding]::new($false))
$publishedAt = [DateTimeOffset]::UtcNow.AddHours(-1)

$replyText = Read-BridgeValidatedReply -Raw $raw -Packet $packet -PublishedAt $publishedAt
$reply = $replyText | ConvertFrom-Json

Write-Host "=== BRIDGE VALIDATION PASSED ===" -ForegroundColor Green
Write-Host "Verdict: $($reply.verdict)" -ForegroundColor Cyan
Write-Host "Correlation ID: $($reply.correlation_id)"
Write-Host "Task ID: $($reply.task_id)"
Write-Host "Review Summary: $($reply.review_summary)"

# Clean up handshake file after successful validation
Remove-Item -LiteralPath $responseReady -Force
Write-Host "Removed $responseReady successfully." -ForegroundColor Green

# Output the validated inner reply JSON
$replyText
