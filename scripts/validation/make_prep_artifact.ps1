$ErrorActionPreference = 'Stop'

function Get-Sha256([string]$p) {
    return (Get-FileHash -Path $p -Algorithm SHA256).Hash.ToUpperInvariant()
}

$prepPath = "results\validation\preparation-0bcc301f-07a3-42d6-aacd-6d4c2d4fa57b.json"

$evidence = [ordered]@{
    "models/pandey_kumar_mode1/108_r5_c3_multi_increment_continuation/M1_C3_STAGGERED_R5.sta" = Get-Sha256 "models\pandey_kumar_mode1\108_r5_c3_multi_increment_continuation\M1_C3_STAGGERED_R5.sta"
    "models/pandey_kumar_mode1/108_r5_c3_multi_increment_continuation/M1_C3_STAGGERED_R5.dat" = Get-Sha256 "models\pandey_kumar_mode1\108_r5_c3_multi_increment_continuation\M1_C3_STAGGERED_R5.dat"
    "models/pandey_kumar_mode1/108_r5_c3_multi_increment_continuation/uel_energy_balance.csv" = Get-Sha256 "models\pandey_kumar_mode1\108_r5_c3_multi_increment_continuation\uel_energy_balance.csv"
    "models/pandey_kumar_mode1/108_r5_c3_multi_increment_continuation/r5_extracted_telemetry.json" = Get-Sha256 "models\pandey_kumar_mode1\108_r5_c3_multi_increment_continuation\r5_extracted_telemetry.json"
    "models/pandey_kumar_mode1/108_r5_c3_multi_increment_continuation/pbs_execution.log" = Get-Sha256 "models\pandey_kumar_mode1\108_r5_c3_multi_increment_continuation\pbs_execution.log"
    "models/pandey_kumar_mode1/108_r5_c3_multi_increment_continuation/pbs_error.log" = Get-Sha256 "models\pandey_kumar_mode1\108_r5_c3_multi_increment_continuation\pbs_error.log"
    "results/validation/mode1_f1597/r5_evaluation_summary.json" = Get-Sha256 "results\validation\mode1_f1597\r5_evaluation_summary.json"
    "tests/unit/test_mode1_f1597_turn130_package108_r5_evaluation.py" = Get-Sha256 "tests\unit\test_mode1_f1597_turn130_package108_r5_evaluation.py"
}

$prepObj = [ordered]@{
    schema = 1
    run_id = "0bcc301f-07a3-42d6-aacd-6d4c2d4fa57b"
    task_id = "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    status = "PREPARATION_COMPLETE"
    finding = "Package 108 Revision 5 (Job 1417255.mmaster02) completed Exit 0 across all 16 steps. Telemetry evaluation diagnosed that *BOUNDARY, OP=NEW, FIXED on mechanical increment steps froze RP displacement at u=0.001965107 mm, suppressing the five 1 nm forward increments. The stationary alternating cycles underwent cyclic damage escalation (d_max=0.715148, +5.89%) and excessive dissipation (E_frac=0.071065 mJ, +13.88% vs 0.062404 mJ benchmark), failing the +-2% gate tolerance. Gate C1-1 remains UNPROMOTED and Gate C1-2 strictly NOT_QUALIFIED pending syntax correction to separate fixed holding from un-fixed RP boundary conditions."
    verification_passed = $true
    evidence_sources = $evidence
}

$jsonText = $prepObj | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText((Resolve-Path -Path "results\validation").Path + "\preparation-0bcc301f-07a3-42d6-aacd-6d4c2d4fa57b.json", $jsonText)
Write-Host "Created $prepPath successfully."
