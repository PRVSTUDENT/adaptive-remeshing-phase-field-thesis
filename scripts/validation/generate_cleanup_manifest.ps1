$sshConfig = Join-Path $env:USERPROFILE ".ssh\codex_config"

$bashCommands = @'
echo "=== 1. GENERATING MANIFEST ==="
find /scratch9/pr21vyci -type f -name "*.stt" -path "*stage16n*" -printf '%s %p\n' | sort -nr > /home/pr21vyci/stage16n_stt_cleanup_candidates.txt
wc -l /home/pr21vyci/stage16n_stt_cleanup_candidates.txt

echo ""
echo "=== 2. TOTAL CANDIDATE SIZE ==="
awk '{sum += $1} END {printf "Total candidate size: %.2f TB (%.2f GB)\n", sum/1024/1024/1024/1024, sum/1024/1024/1024}' /home/pr21vyci/stage16n_stt_cleanup_candidates.txt

echo ""
echo "=== 3. EXCLUSION CHECK (ACTIVE PROJECT NAMES) ==="
MATCH_COUNT=$(grep -Ei "adaptive-remeshing|Adaptive_remeshing_clean" /home/pr21vyci/stage16n_stt_cleanup_candidates.txt | wc -l)
echo "Active project path matches found: $MATCH_COUNT"
if [ "$MATCH_COUNT" -gt 0 ]; then
    echo "WARNING: ACTIVE PROJECT MATCHES DETECTED!"
    grep -Ei "adaptive-remeshing|Adaptive_remeshing_clean" /home/pr21vyci/stage16n_stt_cleanup_candidates.txt
else
    echo "SAFETY PASS: 0 active project files in candidate manifest."
fi

echo ""
echo "=== 4. COMPLETE MANIFEST CONTENT ==="
awk '{printf "%.2f GB  %s\n", $1/1024/1024/1024, $2}' /home/pr21vyci/stage16n_stt_cleanup_candidates.txt
'@

$bashCommands | & ssh -F $sshConfig tu_freiberg "bash -s"
