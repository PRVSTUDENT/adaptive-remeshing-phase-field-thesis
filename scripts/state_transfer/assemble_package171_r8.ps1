# assemble_package171_r8.ps1
$ErrorActionPreference = "Stop"

$repoRoot = (Get-Item .).FullName
$src = Join-Path $repoRoot "models/pandey_kumar_mode1/171_c6_package171_r7_c3_0_adaptive_reequilibration"
$dst = Join-Path $repoRoot "models/pandey_kumar_mode1/171_c6_package171_r8_c3_0_adaptive_reequilibration"

if (-not (Test-Path -LiteralPath $dst)) {
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
}

$filesToCopy = @(
    "active_set_boundary_cards.inc",
    "d_lower_bounds.csv",
    "f42_mixed_uel.for",
    "initial_conditions_solution.inc",
    "job_notifications.sh",
    "nodal_displacements_initial.csv",
    "nodal_phase_field_initial.csv",
    "P171_MECHANICAL_DC.inp",
    "P171_PHASE_DC.inp",
    "P171_MECHANICAL_DC.dat",
    "P171_MECHANICAL_DC.msg",
    "P171_PHASE_DC.dat",
    "P171_PHASE_DC.msg",
    "smoke_import.py"
)

foreach ($f in $filesToCopy) {
    Copy-Item -LiteralPath (Join-Path $src $f) -Destination (Join-Path $dst $f) -Force
}

Copy-Item -LiteralPath (Join-Path $src "M1_C6_PACKAGE171_C3_0_REEQUILIBRATION.inp") -Destination (Join-Path $dst "M1_C6_PACKAGE171_R8_C3_0_ADAPTIVE_REEQUILIBRATION.inp") -Force
Copy-Item -LiteralPath (Join-Path $src "M1_C6_PACKAGE171_C3_0_REEQUILIBRATION.inp") -Destination (Join-Path $dst "M1_C6_PACKAGE171_C3_0_REEQUILIBRATION.inp") -Force

$mDat = Get-Content (Join-Path $dst "P171_MECHANICAL_DC.dat") -Raw
$pDat = Get-Content (Join-Path $dst "P171_PHASE_DC.dat") -Raw

$mechPass = ($mDat -match "ANALYSIS DATACHECK COMPLETE" -or $mDat -match "THE ANALYSIS HAS COMPLETED SUCCESSFULLY") -and ($mDat -notmatch "\*\*\*ERROR")
$phasePass = ($pDat -match "ANALYSIS DATACHECK COMPLETE" -or $pDat -match "THE ANALYSIS HAS COMPLETED SUCCESSFULLY") -and ($pDat -notmatch "\*\*\*ERROR")

Write-Host "Mechanical Datacheck Complete:" $mechPass
Write-Host "Phase Datacheck Complete:" $phasePass
Write-Host "Package 171-R8 files copied successfully."
