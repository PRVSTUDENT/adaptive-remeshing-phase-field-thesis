$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
. (Join-Path $repo '.agents/scripts/Invoke-ChatGPTBridge.ps1')
$prompt = [IO.File]::ReadAllText((Join-Path $repo '.agents/bridge_history/f1849_damage_envelope_request.txt'))
$reply = Invoke-ChatGPTBridge -PromptText $prompt -HandoffId 'HND-F1849-DAMAGE-ENVELOPE-FRAMEWORK-001' -TaskId 'F1849-DAMAGE-ENVELOPE-FRAMEWORK' -LaunchPad -TimeoutMinutes 3
[IO.File]::WriteAllText((Join-Path $repo '.agents/bridge_history/f1849_damage_envelope_validated_response.json'),$reply,[Text.UTF8Encoding]::new($false))
Write-Output 'F1849_MATCHING_RESPONSE_VALIDATED'
