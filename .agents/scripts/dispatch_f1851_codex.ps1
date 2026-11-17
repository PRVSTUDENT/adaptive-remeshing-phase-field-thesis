$ErrorActionPreference='Stop'
$repo='D:\Master thesis\Adaptive remeshing'
. (Join-Path $repo '.agents/scripts/Invoke-ChatGPTBridge.ps1')
$prompt=[IO.File]::ReadAllText((Join-Path $repo '.agents/bridge_history/f1851_native_diagnostics_request.txt'))
$reply=Invoke-ChatGPTBridge -PromptText $prompt -HandoffId 'HND-F1851-NATIVE-DIAGNOSTICS-001' -TaskId 'F1851-NATIVE-DIAGNOSTICS' -LaunchPad -TimeoutMinutes 5
[IO.File]::WriteAllText((Join-Path $repo '.agents/bridge_history/f1851_native_diagnostics_validated_response.json'),$reply,[Text.UTF8Encoding]::new($false))
