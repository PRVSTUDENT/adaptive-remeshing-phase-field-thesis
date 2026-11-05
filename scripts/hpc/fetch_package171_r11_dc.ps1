$ErrorActionPreference = 'Stop'
$cfg = Join-Path -Path $env:USERPROFILE -ChildPath '.ssh\codex_config'
$rem = 'tu_freiberg:/scratch9/pr21vyci/runs/mode1_c6_package171_r11_c3_0_adaptive_reequilibration'
$loc = 'models\pandey_kumar_mode1\171_c6_package171_r11_c3_0_adaptive_reequilibration'

Write-Host "Fetching Package 171-R11 datacheck outputs..."
& scp.exe -F $cfg "$rem/P171_MECHANICAL_DC.dat" "$loc\P171_MECHANICAL_DC.dat"
& scp.exe -F $cfg "$rem/P171_MECHANICAL_DC.msg" "$loc\P171_MECHANICAL_DC.msg"
& scp.exe -F $cfg "$rem/P171_PHASE_DC.dat" "$loc\P171_PHASE_DC.dat"
& scp.exe -F $cfg "$rem/P171_PHASE_DC.msg" "$loc\P171_PHASE_DC.msg"
Write-Host "Fetch complete."
