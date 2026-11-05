$ErrorActionPreference = 'Stop'
$cfg = Join-Path $env:USERPROFILE '.ssh\codex_config'
$rem = 'tu_freiberg:/scratch9/pr21vyci/runs/mode1_c6_package171_r9_c3_0_adaptive_reequilibration'
$loc = 'models\pandey_kumar_mode1\171_c6_package171_r9_c3_0_adaptive_reequilibration\evidence\1420215.mmaster02'

New-Item -ItemType Directory -Force -Path $loc | Out-Null

Write-Host "Fetching Package 171-R9 telemetry from $rem to $loc..."
& scp.exe -F $cfg "$rem/pbs_execution.log" "$loc\pbs_execution.log"
& scp.exe -F $cfg "$rem/equilibration_1420215.mmaster02/re_equilibration_summary.json" "$loc\re_equilibration_summary.json"
& scp.exe -F $cfg "$rem/equilibration_1420215.mmaster02/live_iteration_telemetry.json" "$loc\live_iteration_telemetry.json"

Write-Host "Fetch complete."
Get-ChildItem -Path $loc
