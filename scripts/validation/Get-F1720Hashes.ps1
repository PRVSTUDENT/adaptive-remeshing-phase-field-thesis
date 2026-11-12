# Get-F1720Hashes.ps1
$files = @(
    "models/pandey_kumar_mode1/212_f1720_diagnostic_patch/f1720_diagnostic_coupling_uel.for",
    "models/pandey_kumar_mode1/212_f1720_diagnostic_patch/f1720_call_order.txt",
    "models/pandey_kumar_mode1/213_f1720_coarse_coupled/PK_F1720_COARSE_COUPLED.inp",
    "models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PHYS.inp",
    "models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PFM.inp",
    "results/validation/f1720_authentic_uel_stress_reference.json",
    "results/validation/f1720_diagnostic_patch_results.json",
    "results/validation/f1720_native_miseseri_evaluation.json",
    "results/validation/f1720_adapted_mesh_metrics.json",
    "results/validation/f1720_adapted_pfm_curves.csv",
    "results/validation/f1720_adapted_pfm_telemetry.json",
    "results/validation/f1720_hole_damage_sequence.json",
    "results/validation/f1720_five_hole_force_displacement_validation.png",
    "docs/validation/F1720_METHOD_A_DIRECT_COUPLING_AUDIT_REPORT.md",
    "docs/validation/F1720_METHOD_A_DIRECT_COUPLING_AND_VALIDATION_REPORT.md",
    "tests/unit/test_f1720_authentic_stress_reference.py",
    "tests/unit/test_f1720_stage2_diagnostic_patch.py",
    "tests/unit/test_f1720_stage3_coarse_coupled_miseseri.py",
    "tests/unit/test_f1720_stage4_adapted_mesh.py",
    "tests/unit/test_f1720_stage5_adapted_simulation.py"
)

$out = @{}
foreach ($f in $files) {
    if (Test-Path $f) {
        $hash = (Get-FileHash -Path $f -Algorithm SHA256).Hash
        $size = (Get-Item $f).Length
        $out[$f] = @{
            exists = $true
            size_bytes = $size
            sha256 = $hash
        }
        Write-Host ("{0,-75} {1,10} bytes  {2}" -f $f, $size, $hash)
    } else {
        $out[$f] = @{
            exists = $false
            size_bytes = 0
            sha256 = "MISSING"
        }
        Write-Host ("{0,-75} MISSING" -f $f)
    }
}

$jsonPath = "results/validation/f1720_artifact_hashes.json"
$out | ConvertTo-Json -Depth 3 | Set-Content -Path $jsonPath -Encoding UTF8
Write-Host "Saved hashes to $jsonPath"
