$ErrorActionPreference = 'Stop'
$cfg = Join-Path $env:USERPROFILE '.ssh\codex_config'
$rem = 'tu_freiberg:/scratch9/pr21vyci/runs/mode1_c6_package170_stage_c3_0'
$loc = 'models\pandey_kumar_mode1\170_c6_stage_c3_0_reequilibration\evidence\1419586.mmaster02'

New-Item -ItemType Directory -Force -Path $loc | Out-Null

Write-Host "Fetching Package 170 results from $rem to $loc..."
& scp.exe -F $cfg "$rem/pbs_execution.log" "$loc\pbs_execution.log"
& scp.exe -F $cfg "$rem/M1_C6_STAGE_C3_0_REEQUILIBRATION.sta" "$loc\M1_C6_STAGE_C3_0_REEQUILIBRATION.sta"
& scp.exe -F $cfg "$rem/M1_C6_STAGE_C3_0_REEQUILIBRATION.msg" "$loc\M1_C6_STAGE_C3_0_REEQUILIBRATION.msg"
& scp.exe -F $cfg "$rem/M1_C6_STAGE_C3_0_REEQUILIBRATION.dat" "$loc\M1_C6_STAGE_C3_0_REEQUILIBRATION.dat"
& scp.exe -F $cfg "$rem/uel_energy_balance.csv" "$loc\uel_energy_balance.csv"
& scp.exe -F $cfg "$rem/M1_C6_STAGE_C3_0_REEQUILIBRATION.odb" "$loc\M1_C6_STAGE_C3_0_REEQUILIBRATION.odb"

Write-Host "Fetch complete."
Get-ChildItem -Path $loc
