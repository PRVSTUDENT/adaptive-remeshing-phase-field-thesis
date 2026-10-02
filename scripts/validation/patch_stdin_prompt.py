import os

target_path = r"C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"

with open(target_path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

has_crlf = "\r\n" in content
content = content.replace("\r\n", "\n")

old_block = '''    $agyArgs += "-p"

    # Always prepend the CLI artifact/tool guard, including on ChatGPT/router
    # follow-up turns. This prevents Turn 2+ from forgetting the restriction.
    $EffectiveInstruction = $PersistentAgentGuard + "`r`n`r`n" + $CurrentInstruction
    $agyArgs += $EffectiveInstruction

    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    $turnStartTime = [DateTimeOffset]::UtcNow
    $agyRawOutput = & $AgyPath @agyArgs 2>&1'''

new_block = '''    # Always prepend the CLI artifact/tool guard, including on ChatGPT/router
    # follow-up turns. This prevents Turn 2+ from forgetting the restriction.
    $EffectiveInstruction = $PersistentAgentGuard + "`r`n`r`n" + $CurrentInstruction

    # Use stdin for long/multiline prompts to avoid CLI argument splitting
    $agyArgs += "-p"

    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    $turnStartTime = [DateTimeOffset]::UtcNow
    $agyRawOutput = $EffectiveInstruction | & $AgyPath @agyArgs 2>&1'''

assert old_block in content, "old_block not found in content"
content = content.replace(old_block, new_block, 1)

if has_crlf:
    content = content.replace("\n", "\r\n")

with open(target_path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print(f"Successfully patched {target_path} for stdin prompt piping.")
