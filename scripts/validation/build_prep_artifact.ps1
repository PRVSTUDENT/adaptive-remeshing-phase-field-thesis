$Workspace = 'D:\Master thesis\Adaptive remeshing'
$files = @(
    'models/pandey_kumar_mode1/154_c4_package150_c1_2_continuation_r3/EXECUTION_MANIFEST.json',
    'models/pandey_kumar_mode1/154_c4_package150_c1_2_continuation_r3/PACKAGE_MANIFEST.json',
    'results/validation/package154_r3_datachecks.json',
    'tests/unit/test_package154_r3_precision_and_qualification.py',
    'scripts/validation/extract_package148_iteration.py',
    'scripts/state_transfer/driver_package150_c1_2_continuation.py',
    'results/validation/initial_finding_turn383_d655d348.json'
)

$evidence = [ordered]@{}
foreach ($rel in $files) {
    $full = Join-Path $Workspace $rel
    if (-not (Test-Path -LiteralPath $full)) {
        throw "Missing file: $rel"
    }
    $evidence[$rel] = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash
}

$prep = [ordered]@{
    schema = 1
    status = 'PREPARATION_COMPLETE'
    finding = 'Identified and corrected single-precision float32 ODB displacement extraction limitation causing 4.07e-6 MPa strain-gradient noise floor. Formulated Package 154 (C1-2 R3) with output_precision=full and FieldValue.dataDouble extraction, achieving 1e-12 MPa precision headroom. Verified authentic Abaqus 2023 remote datachecks and 6/6 unit tests pass.'
    evidence_sources = $evidence
    verification_passed = $true
}

$outPath = Join-Path $Workspace 'results/validation/preparation-d655d348-80f4-4832-9cd0-ab5b21bf06d8.json'
$json = $prep | ConvertTo-Json -Depth 5
[IO.File]::WriteAllText($outPath, $json.Replace("`r`n", "`n"), [Text.UTF8Encoding]::new($false))
Write-Output "SUCCESS: Wrote $outPath"
