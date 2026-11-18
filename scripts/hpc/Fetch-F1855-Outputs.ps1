# Fetch-F1855-Outputs.ps1
$cfg = "$env:USERPROFILE\.ssh\codex_config"
$remoteDir = "/scratch9/pr21vyci/runs/f1855_lpanel_fracture_job1"
$localDir = "D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\284_f1855_lpanel_fracture_job1"

$files = @(
    "PK_F1855_LPANEL_COARSE_JOB1.sta",
    "PK_F1855_LPANEL_COARSE_JOB1.dat",
    "PK_F1855_LPANEL_COARSE_JOB1.msg",
    "PK_F1855_LPANEL_COARSE_JOB1.prt",
    "pbs_execution.log",
    "uel_energy_balance.csv",
    "PK_F1855_LPANEL_COARSE_JOB1.odb"
)

foreach ($file in $files) {
    Write-Output "Downloading $file..."
    & scp -F $cfg -B -o BatchMode=yes "tu_freiberg:$remoteDir/$file" (Join-Path $localDir $file)
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Failed to download $file"
    }
}
Write-Output "All downloads finished."
