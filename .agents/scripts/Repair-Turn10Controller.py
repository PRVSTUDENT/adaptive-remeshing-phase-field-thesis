from pathlib import Path
import os

def repair(text):
    old = "$errMsg -match '(?i)\\bstream was interrupted\\b'"
    new = old + " -or\n                $errMsg -match '(?i)(malformed function call|failed to parse function call|improperly formatted function call|function call is empty)'"
    if new not in text:
        if text.count(old) != 1:
            raise RuntimeError("Lifecycle insertion point missing or ambiguous")
        text = text.replace(old, new)
    # Missing helper parameters must throw locally, never ask the terminal.
    start = text.index('function Join-PathStrict {')
    end = text.index('\n}', start) + 2
    helper = text[start:end]
    helper = helper.replace('[Parameter(Mandatory = $true)]', '[Parameter(Mandatory = $false)]')
    text = text[:start] + helper + text[end:]
    marker = '# TURN10_NONINTERACTIVE_GUARD_V1'
    if marker not in text:
        anchor = '    $EffectiveInstruction = $PersistentAgentGuard'
        guard = '    # TURN10_NONINTERACTIVE_GUARD_V1\n    $CurrentInstruction = "Use powershell.exe -NoProfile -NonInteractive for generated shell commands. Always supply explicit -Path and -ChildPath to Join-Path; missing paths are technical errors to diagnose locally. Never wait for a terminal parameter prompt. Do not use timer tools with empty arguments. Recover existing PBS IDs before any submission.`r`n" + $CurrentInstruction\n'
        if text.count(anchor) != 1:
            raise RuntimeError("Instruction insertion point missing or ambiguous")
        text = text.replace(anchor, guard + anchor)
    return text

if __name__ == '__main__':
    targets = [Path(os.environ['USERPROFILE'])/'OpenClawPAD/Antigravity-Autonomous-Loop.ps1', Path('Download_s/AGY-SmartProfile-Patch/Antigravity-Autonomous-Loop.SmartProfiles.ps1')]
    for target in targets:
        source = target.read_text(encoding='utf-8-sig')
        result = repair(source)
        if result != source:
            backup = target.with_name(target.name + '.before-turn10-repair')
            if not backup.exists(): backup.write_bytes(target.read_bytes())
            target.write_text(result, encoding='utf-8-sig')
        print(target)
