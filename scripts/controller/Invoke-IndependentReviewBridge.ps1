[CmdletBinding()]
param([Parameter(Mandatory)][string]$RequestPath,[Parameter(Mandatory)][string]$ResponsePath)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$request=Get-Content -LiteralPath $RequestPath -Raw|ConvertFrom-Json
if($request.operation_id -notmatch '^[a-z][a-z0-9_]{5,140}$'){throw 'Invalid review operation'}
if(Test-Path -LiteralPath $ResponsePath){throw 'Preserve existing archived review'}
. (Join-Path $root '.agents/scripts/Invoke-ChatGPTBridge.ps1')
$prompt=@"
INDEPENDENT_STRUCTURED_REVIEW_V1
Review the attached exact scientific evidence. Do not infer PASS from summaries or scheduler Exit0.
Return a JSON decision with reviewer=ChatGPT-independent-review, author=gemini-antigravity,
operation_id, correlation_id, fingerprint, reviewed_hashes (exact packet values),
decision=APPROVE|REJECT|INSUFFICIENT_EVIDENCE, rationale, assistant_message_id and conversation_url.
Do not sign or invent provenance. The independently controlled bridge worker must archive
the assistant response and attest its origin in an Ed25519 envelope {decision, signature}.
If evidence is incomplete use INSUFFICIENT_EVIDENCE. No scientific jobs in this review.

$(Get-Content -LiteralPath $RequestPath -Raw)
"@
$reply=Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $request.correlation_id -TimeoutMinutes 2 -RequireHeartbeat
# This archive is untrusted until the dispatcher verifies the worker signature.
$null=$reply|ConvertFrom-Json
$tmp=$ResponsePath+'.tmp'
[IO.File]::WriteAllText($tmp,$reply,[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $tmp -Destination $ResponsePath
