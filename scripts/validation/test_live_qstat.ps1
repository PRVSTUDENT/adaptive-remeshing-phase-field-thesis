$sshConfig = Join-Path $env:USERPROFILE ".ssh\codex_config"
$cmds = @(
    "qstat -u pr21vyci",
    "qstat -x -u pr21vyci",
    "qstat -x 1397394.mmaster02",
    "qstat 1397394.mmaster02",
    "qstat -x 1397393.mmaster02"
)

foreach ($cmd in $cmds) {
    Write-Host "=== Running: $cmd ===" -ForegroundColor Cyan
    $out = & ssh -F $sshConfig tu_freiberg $cmd 2>&1
    Write-Host "ExitCode: $LASTEXITCODE"
    $out | ForEach-Object { Write-Host "  [$_]" }
}
