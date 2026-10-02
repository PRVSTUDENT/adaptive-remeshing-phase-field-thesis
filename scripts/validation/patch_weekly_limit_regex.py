import os

target_path = r"C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"

with open(target_path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

has_crlf = "\r\n" in content
content = content.replace("\r\n", "\n")

old_block = '''function Test-IsAgyQuotaLimitError {
    param(
        [string]$Message
    )

    if ([string]::IsNullOrWhiteSpace($Message)) {
        return $false
    }

    return (
        $Message -match '(?i)HTTP\\s*429' -or
        $Message -match '(?i)status\\s*429' -or
        $Message -match '(?i)RESOURCE_EXHAUSTED' -or
        $Message -match '(?i)quota\\s+(?:exceeded|exhausted|reached)' -or
        $Message -match '(?i)individual\\s+quota' -or
        $Message -match '(?i)quota\\s+limit' -or
        $Message -match '(?i)upgrade your subscription' -or
        $Message -match '(?i)rate.?limit(?:ed| exceeded)?' -or
        $Message -match '(?i)too many requests' -or
        $Message -match '(?i)usage\\s+limit' -or
        $Message -match '(?i)plan.?limit'
    )
}'''

new_block = '''function Test-IsAgyQuotaLimitError {
    param(
        [string]$Message
    )

    if ([string]::IsNullOrWhiteSpace($Message)) {
        return $false
    }

    return (
        $Message -match '(?i)HTTP\\s*429' -or
        $Message -match '(?i)status\\s*429' -or
        $Message -match '(?i)RESOURCE_EXHAUSTED' -or
        $Message -match '(?i)quota\\s+(?:exceeded|exhausted|reached)' -or
        $Message -match '(?i)individual\\s+quota' -or
        $Message -match '(?i)weekly\\s+(?:limit|quota)' -or
        $Message -match '(?i)hit your weekly limit' -or
        $Message -match '(?i)quota\\s+limit' -or
        $Message -match '(?i)upgrade your subscription' -or
        $Message -match '(?i)rate.?limit(?:ed| exceeded)?' -or
        $Message -match '(?i)too many requests' -or
        $Message -match '(?i)usage\\s+limit' -or
        $Message -match '(?i)plan.?limit'
    )
}'''

assert old_block in content, "old_block not found in content"
content = content.replace(old_block, new_block, 1)

if has_crlf:
    content = content.replace("\n", "\r\n")

with open(target_path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print(f"Successfully updated Test-IsAgyQuotaLimitError in {target_path}")
