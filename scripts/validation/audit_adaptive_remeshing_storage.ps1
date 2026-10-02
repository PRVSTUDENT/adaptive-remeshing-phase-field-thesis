$sshConfig = Join-Path $env:USERPROFILE ".ssh\codex_config"

$bashCommands = @'
echo "=========================================================="
echo " 1. ADAPTIVE REMESHING RUNS IN /scratch9"
echo "=========================================================="
if [ -d "/scratch9/pr21vyci/adaptive-remeshing" ]; then
    du -sh /scratch9/pr21vyci/adaptive-remeshing
    du -h --max-depth=2 /scratch9/pr21vyci/adaptive-remeshing 2>/dev/null | sort -h | tail -25
fi

echo ""
echo "=========================================================="
echo " 2. ADAPTIVE REMESHING IN /home/pr21vyci/Adaptive_remeshing_clean"
echo "=========================================================="
if [ -d "/home/pr21vyci/Adaptive_remeshing_clean" ]; then
    du -sh /home/pr21vyci/Adaptive_remeshing_clean
    du -h --max-depth=2 /home/pr21vyci/Adaptive_remeshing_clean/models/generated 2>/dev/null | sort -h | tail -25
fi
'@

$bashCommands | & ssh -F $sshConfig tu_freiberg "bash -s"
