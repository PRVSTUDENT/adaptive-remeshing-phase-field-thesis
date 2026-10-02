# -*- coding: utf-8 -*-
# apply_model_selection_controller_patch.ps1

$ErrorActionPreference = "Stop"

$loopScriptPath = "$env:USERPROFILE\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"
if (-not (Test-Path $loopScriptPath)) {
    throw "Controller loop script not found at '$loopScriptPath'"
}

$lines = [System.IO.File]::ReadAllLines($loopScriptPath)

# 1. Check if param block already has $Model
$hasModelParam = $false
for ($i = 0; $i -lt 30; $i++) {
    if ($lines[$i] -match '\[string\]\$Model\s*=') {
        $hasModelParam = $true
        break
    }
}

if (-not $hasModelParam) {
    for ($i = 0; $i -lt 30; $i++) {
        if ($lines[$i] -match '\[string\]\$AgyPath\s*=') {
            $lines[$i] = $lines[$i] + "`r`n    [string]`$Model          = `"gemini-3.7-flash-high`","
            Write-Host "[PATCHED] Param block updated with `$Model = 'gemini-3.7-flash-high'" -ForegroundColor Green
            break
        }
    }
}

# 2. Check if startup banner has Model
$hasBannerModel = $false
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match 'Write-Host " Model:') {
        $hasBannerModel = $true
        break
    }
}

if (-not $hasBannerModel) {
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match 'Write-Host " agy Executable:\s*\$AgyPath"') {
            $lines[$i] = $lines[$i] + "`r`nWrite-Host `" Model:           `$Model`""
            Write-Host "[PATCHED] Startup banner updated with Model display" -ForegroundColor Green
            break
        }
    }
}

# 3. Check if agyArgs has --model
$hasArgsModel = $false
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '\$agyArgs\s*\+=\s*"--model"') {
        $hasArgsModel = $true
        break
    }
}

if (-not $hasArgsModel) {
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '\$agyArgs\s*\+=\s*\$ConversationId') {
            # Find the closing brace of this if block
            for ($j = $i + 1; $j -lt $i + 5; $j++) {
                if ($lines[$j].Trim() -eq "}") {
                    $modelArgsBlock = @(
                        "",
                        "    if (-not [string]::IsNullOrWhiteSpace(`$Model)) {",
                        "        `$agyArgs += `"--model`"",
                        "        `$agyArgs += `$Model",
                        "    }"
                    ) -join "`r`n"
                    $lines[$j] = $lines[$j] + "`r`n" + $modelArgsBlock
                    Write-Host "[PATCHED] `$agyArgs construction block updated with --model" -ForegroundColor Green
                    break
                }
            }
            break
        }
    }
}

$newContent = ($lines -join "`r`n")

# 4. AST Validation
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseInput($newContent, [ref]$tokens, [ref]$errors)

if ($errors -and $errors.Count -gt 0) {
    Write-Host "AST validation FAILED with $($errors.Count) error(s):" -ForegroundColor Red
    foreach ($err in $errors) {
        Write-Host "  $($err.Message) at line $($err.Extent.StartLineNumber)" -ForegroundColor Red
    }
    throw "Aborting patch: modified script failed syntax validation."
}

Write-Host "[VALIDATED] AST syntax check passed with 0 errors." -ForegroundColor Green

# 5. Save
[System.IO.File]::WriteAllText($loopScriptPath, $newContent, [System.Text.Encoding]::UTF8)
Write-Host "[SUCCESS] Controller loop script successfully patched and verified." -ForegroundColor Green
