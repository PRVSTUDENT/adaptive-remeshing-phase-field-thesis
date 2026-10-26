"""
Ensure Controller-Preparation.ps1 is dot-sourced inside Invoke-ChatGPTBridge.ps1
so that any running in-memory controller session automatically receives
the BLOCKED_EXTERNAL_AUTHENTICATION plan classification.
"""
import os
import shutil

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
USERPROFILE = os.environ.get("USERPROFILE", r"C:\Users\pruth")

bridge_path = os.path.join(REPO_ROOT, r".agents\scripts\Invoke-ChatGPTBridge.ps1")
with open(bridge_path, "r", encoding="utf-8") as f:
    content = f.read()

target = "# --- 2d. External Authentication Blocker Guard ---"
resourcing_code = """    # Re-source Controller-Preparation to ensure running controller loop has latest plan logic
    $prepScriptCandidates = @(
        "D:\\Master thesis\\Adaptive remeshing\\scripts\\controller\\Controller-Preparation.ps1",
        (Join-Path $PSScriptRoot "..\\..\\scripts\\controller\\Controller-Preparation.ps1")
    )
    foreach ($psc in $prepScriptCandidates) {
        if (Test-Path -LiteralPath $psc) {
            try { . $psc } catch {}
            break
        }
    }

    # --- 2d. External Authentication Blocker Guard ---"""

if "prepScriptCandidates" not in content:
    if "\r\n" in content:
        resourcing_code = resourcing_code.replace("\n", "\r\n")
    assert target in content, "Target not found in Invoke-ChatGPTBridge.ps1"
    content = content.replace(target, resourcing_code, 1)
    with open(bridge_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(content)
    print("Updated Invoke-ChatGPTBridge.ps1 with Controller-Preparation re-sourcing.")
else:
    print("Invoke-ChatGPTBridge.ps1 already has re-sourcing.")

# Deploy to OpenClawPAD
dst_bridge = os.path.join(USERPROFILE, r"OpenClawPAD\ChatGPTBridge\Invoke-ChatGPTBridge.ps1")
if os.path.exists(os.path.dirname(dst_bridge)):
    shutil.copy2(bridge_path, dst_bridge)
    print(f"Deployed {dst_bridge}")
