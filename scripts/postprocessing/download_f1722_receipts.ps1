$ErrorActionPreference = 'Stop'
$config = Join-Path $env:USERPROFILE '.ssh\codex_config'
$destDir = 'results\validation\f1722_solver_receipts'
if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force }

& scp.exe -o BatchMode=yes -F $config tu_freiberg:/scratch9/pr21vyci/runs/mode1_pk_f1722_causal_pilot/f1722_causal_pilot_curves.csv results/validation/f1722_causal_pilot_curves.csv
& scp.exe -o BatchMode=yes -F $config tu_freiberg:/scratch9/pr21vyci/runs/mode1_pk_f1722_causal_pilot/f1722_causal_pilot_telemetry.json results/validation/f1722_causal_pilot_telemetry.json

& scp.exe -o BatchMode=yes -F $config tu_freiberg:/scratch9/pr21vyci/runs/mode1_pk_f1722_causal_pilot/M1_PK_F1722_CAUSAL_PILOT.sta "$destDir\M1_PK_F1722_CAUSAL_PILOT.sta"
& scp.exe -o BatchMode=yes -F $config tu_freiberg:/scratch9/pr21vyci/runs/mode1_pk_f1722_causal_pilot/M1_PK_F1722_CAUSAL_PILOT.msg "$destDir\M1_PK_F1722_CAUSAL_PILOT.msg"
& scp.exe -o BatchMode=yes -F $config tu_freiberg:/scratch9/pr21vyci/runs/mode1_pk_f1722_causal_pilot/M1_PK_F1722_CAUSAL_PILOT.dat "$destDir\M1_PK_F1722_CAUSAL_PILOT.dat"
& scp.exe -o BatchMode=yes -F $config tu_freiberg:/scratch9/pr21vyci/runs/mode1_pk_f1722_causal_pilot/pbs_execution.log "$destDir\pbs_execution.log"
& scp.exe -o BatchMode=yes -F $config tu_freiberg:/scratch9/pr21vyci/runs/mode1_pk_f1722_causal_pilot/f1720_call_order.txt "$destDir\f1720_call_order.txt"

Write-Output "Downloaded files:"
Get-ChildItem -Path results/validation/f1722* | Select-Object Name, Length
Get-ChildItem -Path $destDir | Select-Object Name, Length
