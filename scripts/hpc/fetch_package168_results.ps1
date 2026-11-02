$ErrorActionPreference = 'Stop'
$cfg = Join-Path $env:USERPROFILE '.ssh\codex_config'
$rem = 'tu_freiberg:/scratch9/pr21vyci/runs/mode1_c5_package168_companion_miseseri'
$loc = 'models\pandey_kumar_mode1\168_c5_companion_miseseri\evidence\1419573.mmaster02'

New-Item -ItemType Directory -Force -Path $loc | Out-Null

Write-Host "Fetching Package 168 results from $rem to $loc..."
& scp.exe -F $cfg "$rem/pbs_execution.log" "$loc\pbs_execution.log"
& scp.exe -F $cfg "$rem/M1_C5_COMPANION_MISESERI.sta" "$loc\M1_C5_COMPANION_MISESERI.sta"
& scp.exe -F $cfg "$rem/M1_C5_COMPANION_MISESERI.msg" "$loc\M1_C5_COMPANION_MISESERI.msg"
& scp.exe -F $cfg "$rem/M1_C5_COMPANION_MISESERI.dat" "$loc\M1_C5_COMPANION_MISESERI.dat"
& scp.exe -F $cfg "$rem/M1_C5_COMPANION_MISESERI.odb" "$loc\M1_C5_COMPANION_MISESERI.odb"
Copy-Item "$loc\M1_C5_COMPANION_MISESERI.odb" "models\pandey_kumar_mode1\168_c5_companion_miseseri\M1_C5_COMPANION_MISESERI.odb" -Force
Write-Host "Fetch complete."
Get-ChildItem -Path $loc
