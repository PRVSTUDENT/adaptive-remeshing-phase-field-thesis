$files = @(
    'results/validation/initial_finding_turn383_d655d348.json',
    'results/validation/package154_r3_datachecks.json',
    'tests/unit/test_package154_r3_precision_and_qualification.py',
    'models/pandey_kumar_mode1/154_c4_package150_c1_2_continuation_r3/PACKAGE_MANIFEST.json',
    'models/pandey_kumar_mode1/154_c4_package150_c1_2_continuation_r3/EXECUTION_MANIFEST.json',
    'results/validation/preparation-d655d348-80f4-4832-9cd0-ab5b21bf06d8.json',
    'project_coordination/sessions/2026-10-31_gemini-antigravity_F1597_d655d348-80f4-4832-9cd0-ab5b21bf06d8.md',
    'project_coordination/controller/turn-d655d348-80f4-4832-9cd0-ab5b21bf06d8.json'
)
foreach ($f in $files) {
    $h = (Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash
    Write-Output "$f : $h"
}
