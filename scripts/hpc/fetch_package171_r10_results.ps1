$ErrorActionPreference = 'Stop'
$cfg = Join-Path $env:USERPROFILE '.ssh\codex_config'
$rem = 'tu_freiberg:/scratch9/pr21vyci/runs/mode1_c6_package171_r10_c3_0_adaptive_reequilibration'
$loc = 'models\pandey_kumar_mode1\171_c6_package171_r10_c3_0_adaptive_reequilibration\evidence\1420261.mmaster02'

New-Item -ItemType Directory -Force -Path $loc | Out-Null

Write-Host "Fetching Package 171-R10 telemetry from $rem to $loc..."
& scp.exe -F $cfg "$rem/pbs_execution.log" "$loc\pbs_execution.log"
& scp.exe -F $cfg "$rem/equilibration_1420261.mmaster02/re_equilibration_summary.json" "$loc\re_equilibration_summary.json"
& scp.exe -F $cfg "$rem/equilibration_1420261.mmaster02/live_iteration_telemetry.json" "$loc\live_iteration_telemetry.json"
$ErrorActionPreference = 'Continue'
& scp.exe -F $cfg "$rem/equilibration_1420261.mmaster02/converged_checkpoint_01.json" "$loc\converged_checkpoint_01.json" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "No converged_checkpoint_01.json found (job nonconverged or uncommitted)."
}

Write-Host "Fetch complete."
Get-ChildItem -Path $loc
