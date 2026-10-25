$ErrorActionPreference = 'Stop'

function Get-Sha256File([string]$path) {
    return (Get-FileHash -Path $path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$r5Dir = "models\pandey_kumar_mode1\108_r5_c3_multi_increment_continuation"
$telemetryPath = Join-Path $r5Dir "r5_extracted_telemetry.json"
$energyPath = Join-Path $r5Dir "uel_energy_balance.csv"
$staPath = Join-Path $r5Dir "M1_C3_STAGGERED_R5.sta"
$datPath = Join-Path $r5Dir "M1_C3_STAGGERED_R5.dat"
$execLogPath = Join-Path $r5Dir "pbs_execution.log"
$errLogPath = Join-Path $r5Dir "pbs_error.log"

$telemetryRaw = Get-Content $telemetryPath -Raw | ConvertFrom-Json
$energyLines = Get-Content $energyPath
# Parse CSV
$energyRecords = @()
for ($i = 1; $i -lt $energyLines.Count; $i++) {
    $line = $energyLines[$i].Trim()
    if ($line.Length -gt 0) {
        $parts = $line -split ','
        if ($parts.Count -ge 7) {
            $energyRecords += [PSCustomObject]@{
                Step = [int]$parts[0].Trim()
                Increment = [int]$parts[1].Trim()
                TotalTime = [double]$parts[2].Trim()
                StepTime = [double]$parts[3].Trim()
                E_elastic_mJ = [double]$parts[4].Trim() * 1000.0
                E_fracture_mJ = [double]$parts[5].Trim() * 1000.0
                E_total_mJ = [double]$parts[6].Trim() * 1000.0
            }
        }
    }
}

$ref_rf2 = 179.2976
$ref_efrac = 0.062404
$ref_efrac_min = 0.06115592
$ref_efrac_max = 0.06365208
$ref_dmax = 0.675399

$stageA_energy = $energyRecords[0]
$final_energy = $energyRecords[-1]

$final_step_data = $telemetryRaw.steps.'Inc5-Mech2'
$final_rf2 = [double]$final_step_data.rp_rf2_N
$final_dmax = [double]$final_step_data.d_max
$final_u2 = [double]$final_step_data.rp_u2
$final_efrac = [double]$final_energy.E_fracture_mJ

$rf2_err_pct = (($final_rf2 - $ref_rf2) / $ref_rf2) * 100.0
$efrac_err_pct = (($final_efrac - $ref_efrac) / $ref_efrac) * 100.0
$dmax_err_pct = (($final_dmax - $ref_dmax) / $ref_dmax) * 100.0

$pass_rf2 = [Math]::Abs($rf2_err_pct) -le 5.0
$pass_efrac = ($final_efrac -ge $ref_efrac_min) -and ($final_efrac -le $ref_efrac_max)
$pass_dmax = [Math]::Abs($dmax_err_pct) -le 2.0
$pass_u2 = [Math]::Abs($final_u2 - 0.00197010735) -lt 1e-7

$summaryOutDir = "results\validation\mode1_f1597"
if (-not (Test-Path $summaryOutDir)) {
    New-Item -ItemType Directory -Path $summaryOutDir -Force | Out-Null
}
$summaryOutFile = Join-Path $summaryOutDir "r5_evaluation_summary.json"

$stepEvalList = @()
foreach ($name in $telemetryRaw.step_order) {
    $sd = $telemetryRaw.steps.$name
    $stepEvalList += [PSCustomObject]@{
        step_name = $name
        rp_u2_mm = [double]$sd.rp_u2
        rp_rf2_N = [double]$sd.rp_rf2_N
        d_max = [double]$sd.d_max
        d_min = [double]$sd.d_min
        h_max = [double]$sd.h_max
        num_interior_rf_gt_1uN = [int]$sd.num_interior_rf_nodes_gt_1uN
    }
}

$evidenceSources = [ordered]@{
    "models/pandey_kumar_mode1/108_r5_c3_multi_increment_continuation/M1_C3_STAGGERED_R5.sta" = Get-Sha256File $staPath
    "models/pandey_kumar_mode1/108_r5_c3_multi_increment_continuation/M1_C3_STAGGERED_R5.dat" = Get-Sha256File $datPath
    "models/pandey_kumar_mode1/108_r5_c3_multi_increment_continuation/uel_energy_balance.csv" = Get-Sha256File $energyPath
    "models/pandey_kumar_mode1/108_r5_c3_multi_increment_continuation/r5_extracted_telemetry.json" = Get-Sha256File $telemetryPath
    "models/pandey_kumar_mode1/108_r5_c3_multi_increment_continuation/pbs_execution.log" = Get-Sha256File $execLogPath
    "models/pandey_kumar_mode1/108_r5_c3_multi_increment_continuation/pbs_error.log" = Get-Sha256File $errLogPath
}

$summaryObj = [ordered]@{
    pbs_job_id = "1417255.mmaster02"
    package = "models/pandey_kumar_mode1/108_r5_c3_multi_increment_continuation"
    model = "Candidate C3 (2,650 quads, 2,769 nodes)"
    solver_exit_status = 0
    walltime_seconds = 102
    acceptance_status = "REJECTED_NUMERICAL_FAILURE"
    gate_decision = "GATE_C1_1_UNPROMOTED"
    initial_state_stage_A = [ordered]@{
        step_name = "Stage-A"
        u_rp_mm = [double]$telemetryRaw.steps.'Stage-A'.rp_u2
        rf2_N = [double]$telemetryRaw.steps.'Stage-A'.rp_rf2_N
        d_max = [double]$telemetryRaw.steps.'Stage-A'.d_max
        e_frac_mJ = [double]$stageA_energy.E_fracture_mJ
        e_total_mJ = [double]$stageA_energy.E_total_mJ
    }
    terminal_state_inc5_mech2 = [ordered]@{
        step_name = "Inc5-Mech2"
        u_rp_mm = $final_u2
        prescribed_target_u_mm = 0.00197010735
        u_error_mm = ($final_u2 - 0.00197010735)
        rf2_N = $final_rf2
        rf2_ref_N = $ref_rf2
        rf2_error_pct = $rf2_err_pct
        rf2_pass = $pass_rf2
        e_frac_mJ = $final_efrac
        e_frac_ref_mJ = $ref_efrac
        e_frac_allowed_interval_mJ = @($ref_efrac_min, $ref_efrac_max)
        e_frac_error_pct = $efrac_err_pct
        e_frac_pass = $pass_efrac
        d_max = $final_dmax
        d_max_ref = $ref_dmax
        d_max_error_pct = $dmax_err_pct
        d_max_pass = $pass_dmax
        healing_detected = $false
        d_min = [double]$final_step_data.d_min
        interior_holding_rf_nodes = ([int]$final_step_data.num_interior_rf_nodes_gt_1uN - 108)
    }
    root_cause_diagnosis = [ordered]@{
        identified_mechanism = "Abaqus *BOUNDARY, OP=NEW, FIXED keyword parameter override"
        detail = "In steps 2, 5, 8, 11, and 14, the input deck specified '*Boundary, op=NEW, fixed' with data line 'N_RP, 2, 2, <prescribed_disp>'. In Abaqus keyword syntax, the 'fixed' parameter explicitly freezes degrees of freedom at the values from the start of the step, causing Abaqus to ignore the numeric magnitude on the data line. Consequently, displacement u_RP remained locked at u = 0.00196510735 mm throughout all 16 steps."
        consequence = "The alternating minimization cycles operated at zero displacement advancement. Cyclic alternation between phase relaxation and mechanical re-equilibration under stationary boundaries caused progressive unzipping: peak damage escalated from 0.6397 to 0.7151 (+11.8%), crack-tip tensile history climbed from 5.209 MPa to 7.653 MPa (+46.9%), and fracture energy reached 0.071065 mJ (+13.88% above reference), violating the +-2.0% gate window."
        first_violating_step = "Step 2 (Inc1-Mech1): displacement failed to advance; Step 3 (Inc1-Phase1): E_frac jumped to 0.064924 mJ exceeding upper bound 0.063652 mJ."
        falsifiable_hypothesis = "Replacing '*Boundary, op=NEW, fixed' with separate '*Boundary, op=NEW, fixed' for holding sets and explicit un-fixed '*Boundary' for N_RP (exactly as correctly implemented in R4 Stage-B-Mech) will restore actual forward displacement incrementation (1 nm per cycle), enabling true multi-increment crack progression without spurious static damage escalation."
    }
    step_evolution = $stepEvalList
    evidence_sources = $evidenceSources
}

$summaryJson = $summaryObj | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText($summaryOutFile, $summaryJson)
Write-Host "Evaluation written to $summaryOutFile"
Write-Host "Acceptance: $($summaryObj.acceptance_status)"
Write-Host "E_frac: $final_efrac mJ (error: $($efrac_err_pct.ToString('+0.00;-0.00'))%)"
Write-Host "RF2: $final_rf2 N (error: $($rf2_err_pct.ToString('+0.00;-0.00'))%)"
Write-Host "d_max: $final_dmax (error: $($dmax_err_pct.ToString('+0.00;-0.00'))%)"
Write-Host "u_RP: $final_u2 mm (target: 0.00197010735 mm)"
