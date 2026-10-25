$ErrorActionPreference = 'Stop'

function Get-Sha256([string]$p) {
    return (Get-FileHash -Path $p -Algorithm SHA256).Hash.ToUpperInvariant()
}

$prepPath = "results\validation\preparation-f0800f17-a719-4ac2-9fd1-c8bc4958b30d.json"

$evidence = [ordered]@{
    "models/pandey_kumar_mode1/108_r6_c3_multi_increment_continuation/M1_C3_STAGGERED_R6_AUTHORIZATION.json" = Get-Sha256 "models\pandey_kumar_mode1\108_r6_c3_multi_increment_continuation\M1_C3_STAGGERED_R6_AUTHORIZATION.json"
    "models/pandey_kumar_mode1/108_r6_c3_multi_increment_continuation/M1_C3_STAGGERED_R6_CONTINUATION.inp" = Get-Sha256 "models\pandey_kumar_mode1\108_r6_c3_multi_increment_continuation\M1_C3_STAGGERED_R6_CONTINUATION.inp"
    "models/pandey_kumar_mode1/108_r6_c3_multi_increment_continuation/submit_M1_C3_STAGGERED_R6.pbs" = Get-Sha256 "models\pandey_kumar_mode1\108_r6_c3_multi_increment_continuation\submit_M1_C3_STAGGERED_R6.pbs"
    "models/pandey_kumar_mode1/108_r6_c3_multi_increment_continuation/diagnostic_motion_results.json" = Get-Sha256 "models\pandey_kumar_mode1\108_r6_c3_multi_increment_continuation\diagnostic_motion_results.json"
    "tests/unit/test_mode1_f1597_turn131_package108_r6_kinematics.py" = Get-Sha256 "tests\unit\test_mode1_f1597_turn131_package108_r6_kinematics.py"
    "scripts/validation/create_package108_r6.py" = Get-Sha256 "scripts\validation\create_package108_r6.py"
    "scripts/validation/run_kinematic_diagnostic_solve.py" = Get-Sha256 "scripts\validation\run_kinematic_diagnostic_solve.py"
}

$prepObj = [ordered]@{
    schema = 1
    run_id = "f0800f17-a719-4ac2-9fd1-c8bc4958b30d"
    task_id = "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    status = "PREPARATION_COMPLETE"
    finding = "Package 108 Revision 6 successfully corrected the Abaqus boundary syntax defect by eliminating OP=NEW / OP=MOD mixing and separating fixed phase constraints from un-fixed RP displacement boundary cards. Kinematic solve diagnostic empirically verified true physical reference point advancement from u=0.001965107 mm to u=0.001966107 mm (+1.0 nm). Preflight datacheck passed with zero errors, and PBS Job 1417256.mmaster02 was submitted under governed once-only execution."
    verification_passed = $true
    evidence_sources = $evidence
}

$jsonText = $prepObj | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText((Resolve-Path -Path "results\validation").Path + "\preparation-f0800f17-a719-4ac2-9fd1-c8bc4958b30d.json", $jsonText)
Write-Host "Created $prepPath successfully."
