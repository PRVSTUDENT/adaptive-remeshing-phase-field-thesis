[CmdletBinding()]
param(
 [string]$Recovery='C:\Users\pruth\PAD-Recovery-20261101-173631',
 [string]$Destination='C:\Users\pruth\PAD-Canary-R1-20261101'
)
$ErrorActionPreference='Stop'
$source=Join-Path $Recovery 'pad_flow_workspace'
$original=Join-Path $source 'script.robin'
if(!(Test-Path -LiteralPath $original) -or (Get-FileHash $original).Hash -cne 'EB6EDAB27B20703714674D33A5DD50E8F7357208B10FD963C9E584BF5107BAC2'){throw 'Recovered PAD source hash mismatch'}
foreach($name in @('original_flow','flow_copy_r1','Invoke-PadCanaryGuard.ps1','Main.repaired.robin')){if(Test-Path (Join-Path $Destination $name)){throw 'R1 already built; do not overwrite its evidence'}}
New-Item -ItemType Directory -Path $Destination -Force|Out-Null
Copy-Item -LiteralPath $source -Destination (Join-Path $Destination 'original_flow') -Recurse
$copy=Join-Path $Destination 'flow_copy_r1';New-Item -ItemType Directory -Path $copy|Out-Null
foreach($name in @('controlRepo.appmask','imageRepo.imgrepo','flow.dependencies','flow.manifest')){Copy-Item -LiteralPath (Join-Path $source $name) -Destination $copy}
# Never copy the original compiled package/pData into a repaired execution copy.
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Invoke-PadCanaryGuard.ps1') -Destination $Destination
$guard=Join-Path $Destination 'Invoke-PadCanaryGuard.ps1'
$state=Join-Path $Destination 'canary-state'
$header=(Get-Content -LiteralPath $original -TotalCount 7)-join "`r`n"
$main=@"
$header
Scripting.RunPowershellScript.RunPowershellScript Script: `$'''& '$guard' -Mode Claim''' ScriptOutput=> ClaimOutput
IF Contains(ClaimOutput, `$'''CLAIMED''', False) THEN
    File.ReadTextFromFile.ReadText File: `$'''$state\bridge_request.ready''' Encoding: File.TextFileEncoding.UTF8 Content=> FileContents
    Clipboard.SetText Text: FileContents
    MouseAndKeyboard.MoveMouse X: 2126 Y: 1341 RelativeTo: MouseAndKeyboard.PositionRelativeTo.Screen MovementStyle: MouseAndKeyboard.MovementStyle.Instant
    WAIT 2
    MouseAndKeyboard.SendMouseClick.Click ClickType: MouseAndKeyboard.MouseClickType.LeftClick MillisecondsDelay: 1
    WAIT 1
    MouseAndKeyboard.SendKeys.FocusAndSendKeys TextToSend: `$'''{Control}({V})''' DelayBetweenKeystrokes: 10 SendTextAsHardwareKeys: False
    WAIT (UIAutomation.WaitForImage.ToAppearOnScreen Images: [imgrepo['Bridge_response_copied'], imgrepo['BRidge_error'], imgrepo['bridge response copied 3']] FindAllImages: False Tolerance: 10 SearchAlgorithm: UIAutomation.ImageFinderAlgorithm.Legacy X=> X5 Y=> Y5) FOR 900
    ON ERROR WaitForImageError
        CALL CANARY_TIMEOUT
        GOTO 'canary_end'
    ON ERROR TimeoutError
        CALL CANARY_TIMEOUT
        GOTO 'canary_end'
    END
    Clipboard.GetText Text=> ClipboardText2
    File.WriteText File: `$'''$state\clipboard_candidate.json''' TextToWrite: ClipboardText2 AppendNewLine: False IfFileExists: File.IfFileExists.Overwrite Encoding: File.FileEncoding.Unicode
    Scripting.RunPowershellScript.RunPowershellScript Script: `$'''& '$guard' -Mode Validate''' ScriptOutput=> ValidationOutput
END
LABEL 'canary_end'
FUNCTION CANARY_TIMEOUT GLOBAL
    Scripting.RunPowershellScript.RunPowershellScript Script: `$'''& '$guard' -Mode Timeout''' ScriptOutput=> TimeoutOutput
END FUNCTION
"@
if($main -match 'File.Delete|LOOP WHILE|always_proceed|main_backup_failed|OpenClawPAD\\ChatGPTBridge'){throw 'Repaired flow retained unsafe production or replay action'}
if($main.IndexOf('-Mode Claim') -gt $main.IndexOf('Clipboard.SetText')){throw 'Reservation is not before paste'}
[IO.File]::WriteAllText((Join-Path $copy 'script.robin'),$main,[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText((Join-Path $Destination 'Main.repaired.robin'),$main,[Text.UTF8Encoding]::new($false))
Write-Output 'PAD_R1_SOURCE_BUILT_OFFLINE: not imported, run or native-PAD-qualified'
