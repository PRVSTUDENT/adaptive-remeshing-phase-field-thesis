"""
Add external institutional authentication blocker check to scripts/controller/Controller-Preparation.ps1
"""
import os

path = r"D:\Master thesis\Adaptive remeshing\scripts\controller\Controller-Preparation.ps1"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

target = """    # Unsafe proposal rejection
    if($Instruction -match '(?i)(change formulation and execute arbitrary|arbitrary commands|destructive|bypass qualification|qdel|qmove|rm -rf)'){
        return [pscustomobject]@{status='DEFINITION_REJECTED';dispatch_ready=$false;task_type='REJECTED';operation_id='';path='';blocked_on=@('Unreviewed proposal rejected; safety guard enforced');recipe=''}
    }"""

addition = """    # External institutional authentication blocker rejection
    if($Instruction -match '(?i)(BLOCKED_EXTERNAL_AUTHENTICATION|INTERACTIVE_SSO_REQUIRED|OFFLINE_QUALIFIED__INTERACTIVE_SSO_REQUIRED)'){
        return [pscustomobject]@{status='BLOCKED_EXTERNAL_AUTHENTICATION';dispatch_ready=$false;task_type='BLOCKED_ON_SSO';operation_id='';path='';blocked_on=@('University eduVPN interactive browser SSO required on workstation');recipe=''}
    }"""

if "BLOCKED_EXTERNAL_AUTHENTICATION" not in content:
    if target not in content:
        target = target.replace("\n", "\r\n")
        addition = addition.replace("\n", "\r\n")
    assert target in content, "Target not found in Controller-Preparation.ps1"
    new_content = content.replace(target, target + ("\r\n" if "\r\n" in target else "\n") + addition, 1)
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(new_content)
    print("Updated Controller-Preparation.ps1 successfully.")
else:
    print("Controller-Preparation.ps1 already contains blocker check.")
