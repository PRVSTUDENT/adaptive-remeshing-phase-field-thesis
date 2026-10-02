$sshConfig = Join-Path $env:USERPROFILE ".ssh\codex_config"

$bashCommands = @'
echo "=========================================================="
echo " 1. /scratch9/pr21vyci DEPTH-2 DIRECTORY USAGE"
echo "=========================================================="
du -h --max-depth=2 /scratch9/pr21vyci 2>/dev/null | sort -h | tail -40

echo ""
echo "=========================================================="
echo " 2. /scratch9/pr21vyci LARGEST 50 FILES"
echo "=========================================================="
find /scratch9/pr21vyci -type f -printf '%s %p\n' 2>/dev/null | sort -nr | head -50 | awk '{printf "%.2f GB  %s\n", $1/1024/1024/1024, $2}'

echo ""
echo "=========================================================="
echo " 3. /scratch9/pr21vyci FILE TYPE SUMMARY (COUNT & SIZE)"
echo "=========================================================="
find /scratch9/pr21vyci -type f 2>/dev/null | sed -n 's/..*\.//p' | sort | uniq -c | sort -nr | head -30

echo ""
echo "=========================================================="
echo " 4. /home/pr21vyci/master_thesis & projects BREAKDOWN"
echo "=========================================================="
du -h --max-depth=2 /home/pr21vyci/master_thesis /home/pr21vyci/projects /home/pr21vyci/Adaptive_remeshing_clean 2>/dev/null | sort -h | tail -40
'@

$bashCommands | & ssh -F $sshConfig tu_freiberg "bash -s"
