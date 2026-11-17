$ErrorActionPreference='Stop'
$repo='D:\Master thesis\Adaptive remeshing'
. (Join-Path $repo '.agents/scripts/Invoke-ChatGPTBridge.ps1')
$prompt=[IO.File]::ReadAllText((Join-Path $repo '.agents/bridge_history/f1850_donor_recovery_request.txt'))
$reply=Invoke-ChatGPTBridge -PromptText $prompt -HandoffId 'HND-F1850-DONOR-RECOVERY-001' -TaskId 'F1850-DONOR-RECOVERY' -LaunchPad -TimeoutMinutes 10
[IO.File]::WriteAllText((Join-Path $repo '.agents/bridge_history/f1850_donor_recovery_validated_response.json'),$reply,[Text.UTF8Encoding]::new($false))
Write-Output 'F1850_MATCHING_RESPONSE_VALIDATED'
