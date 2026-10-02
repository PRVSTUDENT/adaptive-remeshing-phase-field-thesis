$sshConfig = Join-Path $env:USERPROFILE ".ssh\codex_config"

$bashCommands = @'
echo "=========================================================="
echo " 1. CLUSTER MOUNTS & OVERALL CAPACITY"
echo "=========================================================="
df -h /home /scratch /scratch* /projects 2>/dev/null

echo ""
echo "=========================================================="
echo " 2. pr21vyci USAGE ACROSS ALL SCRATCH & PROJECT VOLUMES"
echo "=========================================================="
for d in /scratch /scratch0 /scratch1 /scratch2 /scratch3 /scratch4 /scratch5 /scratch6 /scratch7 /scratch8 /scratch9 /projects /local; do
    if [ -d "$d/pr21vyci" ]; then
        echo "Found: $d/pr21vyci"
        du -sh "$d/pr21vyci" 2>/dev/null
    fi
done

echo ""
echo "=========================================================="
echo " 3. TOP-LEVEL BREAKDOWN IN /scratch/pr21vyci"
echo "=========================================================="
if [ -d "/scratch/pr21vyci" ]; then
    du -h --max-depth=2 /scratch/pr21vyci 2>/dev/null | sort -h | tail -40
fi

echo ""
echo "=========================================================="
echo " 4. /home/pr21vyci TOP-LEVEL BREAKDOWN"
echo "=========================================================="
du -sh /home/pr21vyci/* /home/pr21vyci/.* 2>/dev/null | sort -h | tail -30

echo ""
echo "=========================================================="
echo " 5. /home/pr21vyci/Adaptive_remeshing_clean BREAKDOWN"
echo "=========================================================="
if [ -d "/home/pr21vyci/Adaptive_remeshing_clean" ]; then
    du -h --max-depth=2 /home/pr21vyci/Adaptive_remeshing_clean 2>/dev/null | sort -h | tail -40
fi
'@

$bashCommands | & ssh -F $sshConfig tu_freiberg "bash -s"
