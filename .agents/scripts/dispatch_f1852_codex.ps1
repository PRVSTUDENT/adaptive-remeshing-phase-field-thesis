$ErrorActionPreference='Stop'
$repo='D:\Master thesis\Adaptive remeshing'
. (Join-Path $repo '.agents/scripts/Invoke-ChatGPTBridge.ps1')
$prompt=[IO.File]::ReadAllText((Join-Path $repo '.agents/bridge_history/f1852_driver_selection_request.txt'))
$reply=Invoke-ChatGPTBridge -PromptText $prompt -HandoffId 'HND-F1852-DRIVER-SELECTION-001' -TaskId 'F1852-DRIVER-SELECTION' -LaunchPad -TimeoutMinutes 5
[IO.File]::WriteAllText((Join-Path $repo '.agents/bridge_history/f1852_driver_selection_validated_response.json'),$reply,[Text.UTF8Encoding]::new($false))
