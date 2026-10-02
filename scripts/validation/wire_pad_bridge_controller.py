# wire_pad_bridge_controller.py
# Configures persistent worker mode ($ChatGPTBridgeLaunchPad = $false) and heartbeat support.

import sys
import os

CONTROLLER_PATH = r"C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"

def patch_controller():
    if not os.path.exists(CONTROLLER_PATH):
        print(f"ERROR: Controller not found at {CONTROLLER_PATH}")
        sys.exit(1)

    with open(CONTROLLER_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # --- Edit 1: Set $ChatGPTBridgeLaunchPad = $false and add $ChatGPTBridgeRequireHeartbeat ---
    param_target = """    # Launch Power Automate Desktop via shortcut/URL per turn (set $false if PAD runs persistent worker loop)
    [bool]$ChatGPTBridgeLaunchPad = $true,"""

    param_replacement = """    # Launch Power Automate Desktop via shortcut/URL per turn (set $false if PAD runs persistent worker loop)
    [bool]$ChatGPTBridgeLaunchPad = $false,

    # Fail quickly if PAD bridge worker heartbeat is missing or stale (>120s)
    [bool]$ChatGPTBridgeRequireHeartbeat = $false,"""

    if param_target not in content:
        print("ERROR: param_target not found in controller script.")
        sys.exit(1)

    content = content.replace(param_target, param_replacement, 1)

    # --- Edit 2: Pass -RequireHeartbeat to Invoke-ChatGPTBridge ---
    call_target = """            $Reply = Invoke-ChatGPTBridge `
                -PromptText $Prompt `
                -HandoffId $persistentHandoffId `
                -LaunchPad:$ChatGPTBridgeLaunchPad `
                -TimeoutMinutes $timeoutMinutes"""

    call_replacement = """            $Reply = Invoke-ChatGPTBridge `
                -PromptText $Prompt `
                -HandoffId $persistentHandoffId `
                -LaunchPad:$ChatGPTBridgeLaunchPad `
                -RequireHeartbeat:$ChatGPTBridgeRequireHeartbeat `
                -TimeoutMinutes $timeoutMinutes"""

    if call_target not in content:
        print("ERROR: call_target not found in controller script.")
        sys.exit(1)

    content = content.replace(call_target, call_replacement, 1)

    with open(CONTROLLER_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("SUCCESS: Controller patched successfully with persistent worker mode and heartbeat support.")

if __name__ == "__main__":
    patch_controller()
