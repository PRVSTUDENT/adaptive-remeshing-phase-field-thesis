$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$r3Dir = Join-Path $repo 'models\pandey_kumar_mode1\166_c5_package166_r3_c2_0_nonaccumulating_history'
$frozenUelHash = 'CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6'

# 1. Manifest existence and schema validation
$manifestPath = Join-Path $r3Dir 'PACKAGE_MANIFEST.json'
if (-not (Test-Path $manifestPath)) { throw "PACKAGE_MANIFEST.json missing in $r3Dir" }
$manifest = Get-Content -Path $manifestPath -Raw | ConvertFrom-Json

if ($manifest.schema -ne 1) { throw "Schema version mismatch: expected 1" }
if (-not $manifest.donor_source) { throw "donor_source missing from PACKAGE_MANIFEST.json" }
if ([Math]::Abs([double]$manifest.donor_source.target_uy_mm - 0.0018603125442191958) -gt 1e-12) { throw "target_uy_mm mismatch" }
if ([Math]::Abs([double]$manifest.donor_source.c4_max_history_MPa - 6868.951434128797) -gt 1e-9) { throw "c4_max_history_MPa mismatch" }
if (-not $manifest.non_accumulating_history_contract) { throw "non_accumulating_history_contract missing" }

# 2. File digest integrity
$expectedFiles = @(
    'M1_C5_PACKAGE166_C2_0_REEQUILIBRATION.inp',
    'P166_MECHANICAL_DC.dat',
    'P166_MECHANICAL_DC.inp',
    'P166_PHASE_DC.dat',
    'P166_PHASE_DC.inp',
    'active_set_boundary_cards.inc',
    'd_lower_bounds.csv',
    'f42_mixed_uel.for',
    'initial_conditions_solution.inc',
    'job_notifications.sh',
    'nodal_displacements_initial.csv',
    'nodal_phase_field_initial.csv',
    'run_datacheck.sh',
    'submit_M1_C5_P166_R3_C2_0.pbs'
)

foreach ($fn in $expectedFiles) {
    $fp = Join-Path $r3Dir $fn
    if (-not (Test-Path $fp)) { throw "Missing package file: $fn" }
    $actualHash = (Get-FileHash -Path $fp -Algorithm SHA256).Hash.ToUpper()
    $recordedHash = $manifest.file_digests.$fn
    if ($actualHash -ne $recordedHash) { throw "Digest mismatch for ${fn}: $actualHash vs $recordedHash" }
}

# 3. Frozen production UEL assertion
$uelHash = (Get-FileHash -Path (Join-Path $r3Dir 'f42_mixed_uel.for') -Algorithm SHA256).Hash.ToUpper()
if ($uelHash -ne $frozenUelHash) { throw "Frozen production UEL hash mismatch" }

# 4. Execution manifest validation
$execPath = Join-Path $r3Dir 'EXECUTION_MANIFEST.json'
if (-not (Test-Path $execPath)) { throw "EXECUTION_MANIFEST.json missing" }
$exec = Get-Content -Path $execPath -Raw | ConvertFrom-Json
if ($exec.batch_name -ne 'MODE1_PACKAGE166_R3_M1_C5_P166_R3_C2_0') { throw "Batch name mismatch" }

Write-Output "ALL_R3_SCHEMA_AND_DIGEST_CHECKS_PASS"
