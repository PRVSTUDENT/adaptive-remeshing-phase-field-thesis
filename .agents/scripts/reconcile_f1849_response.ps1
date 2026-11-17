# Validate a delayed response for the ORIGINAL transaction without republishing.
$ErrorActionPreference='Stop'
$repo='D:\Master thesis\Adaptive remeshing'
. (Join-Path $repo '.agents/scripts/Bridge-ResearchContract.ps1')
$bridge=Join-Path $env:USERPROFILE 'OpenClawPAD/ChatGPTBridge'
$request=Join-Path $bridge 'bridge_request.ready'
$response=Join-Path $bridge 'bridge_response.ready'
if (-not (Test-Path -LiteralPath $request)) {
    $request=Join-Path $bridge 'archive/request_20261117_232821_HND-F1849-DAMAGE-ENVELOPE-FRAMEWORK-001.txt'
}
if (-not (Test-Path -LiteralPath $request)) { throw 'Original request and exact archive missing. No resend.' }
if (-not (Test-Path -LiteralPath $response)) { throw 'Matching response is not available yet. No resend.' }
$original=[IO.File]::ReadAllText($request)
$packet=New-BridgeCanonicalPrompt -PromptText $original -HandoffId 'HND-F1849-DAMAGE-ENVELOPE-FRAMEWORK-001' -TaskId 'F1849-DAMAGE-ENVELOPE-FRAMEWORK'
$published=[DateTimeOffset](Get-Item -LiteralPath $request).LastWriteTimeUtc
$reply=Read-BridgeValidatedReply -Raw ([IO.File]::ReadAllText($response)) -Packet $packet -PublishedAt $published
[IO.File]::WriteAllText((Join-Path $repo '.agents/bridge_history/f1849_damage_envelope_validated_response.json'),$reply,[Text.UTF8Encoding]::new($false))
$archiveResponse=Join-Path $bridge 'archive/response_20261117_232821_HND-F1849-DAMAGE-ENVELOPE-FRAMEWORK-001.json'
if (Test-Path -LiteralPath $archiveResponse) { throw 'Response archive already exists; reconcile without overwriting.' }
Move-Item -LiteralPath $response -Destination $archiveResponse
Write-Output 'Original F1849 response validated and preserved; inspect next instruction before further work.'
