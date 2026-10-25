$ErrorActionPreference = 'Stop'
$remoteDir = "/scratch9/pr21vyci/runs/mode1_c3_staggered_continuation_r5"
$localDir = "models\pandey_kumar_mode1\108_r5_c3_multi_increment_continuation"

$files = @(
    "M1_C3_STAGGERED_R5.sta",
    "M1_C3_STAGGERED_R5.dat",
    "uel_energy_balance.csv",
    "r5_extracted_telemetry.json",
    "pbs_execution.log",
    "pbs_error.log"
)

foreach ($f in $files) {
    Write-Host "Fetching $f..."
    $cmd = "base64 -w 0 $remoteDir/$f"
    $b64 = powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand $cmd
    # Strip any ssh warnings or banner
    $lines = $b64 -split "`r?`n"
    $cleanLines = @()
    foreach ($line in $lines) {
        if ($line -notmatch '^\*\* ' -and $line.Trim().Length -gt 0) {
            $cleanLines += $line.Trim()
        }
    }
    $rawB64 = $cleanLines -join ""
    $bytes = [System.Convert]::FromBase64String($rawB64)
    [System.IO.File]::WriteAllBytes("$localDir\$f", $bytes)
    Write-Host "Saved $localDir\$f ($( $bytes.Length ) bytes)"
}
