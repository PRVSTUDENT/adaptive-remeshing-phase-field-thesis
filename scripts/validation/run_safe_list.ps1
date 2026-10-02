$sshConfig = Join-Path $env:USERPROFILE ".ssh\codex_config"

$remoteScript = @'
MANIFEST="/home/pr21vyci/stage16n_stt_cleanup_candidates.txt"
SAFE_LIST="/home/pr21vyci/stage16n_stt_safe_delete_list.txt"

echo "=== 1. FILTERING CONSERVATIVE SAFE-DELETE LIST ==="
sed -n 's#^[^/]*\(/scratch9/pr21vyci/.*\.stt\)$#\1#p' "$MANIFEST" \
  | grep '/stage16n' \
  | grep -Ev 'adaptive-remeshing|Adaptive_remeshing_clean|/master_thesis/' \
  > "$SAFE_LIST"

echo "File count in safe delete list:"
wc -l "$SAFE_LIST"

echo ""
echo "=== 2. FAIL-CLOSED PROTECTED-PATH CHECK ==="
if grep -Ei 'adaptive-remeshing|Adaptive_remeshing_clean|/master_thesis/' "$SAFE_LIST"; then
    echo "ERROR: protected project path found!"
    exit 1
else
    echo "PASS: zero protected project paths found."
fi

echo ""
echo "=== 3. FAIL-CLOSED PATH-SCOPE CHECK ==="
awk '
!/^(\/scratch9\/pr21vyci\/)/ {print "BAD PATH:", $0; bad=1}
!/stage16n/                  {print "NOT STAGE16N:", $0; bad=1}
!/\.stt$/                    {print "NOT STT:", $0; bad=1}
END {if (bad) exit 1}
' "$SAFE_LIST"

if [ $? -eq 0 ]; then
    echo "PASS: all candidate paths are valid /scratch9/pr21vyci/*stage16n*.stt files."
else
    echo "FAIL: invalid paths detected in safe delete list!"
    exit 1
fi

echo ""
echo "=== 4. RECLAIMABLE CAPACITY CALCULATION ==="
while IFS= read -r f; do
    [ -f "$f" ] && stat -c '%s' "$f"
done < "$SAFE_LIST" \
| awk '{s+=$1} END {printf "Reclaimable: %.2f TB (%.2f GB)\n", s/1024/1024/1024/1024, s/1024/1024/1024}'

echo ""
echo "=== 5. COMPLETE SAFE-DELETE LIST WITH SIZES ==="
while IFS= read -r f; do
    if [ -f "$f" ]; then
        SZ=$(stat -c '%s' "$f")
        awk -v s="$SZ" -v p="$f" 'BEGIN {printf "%.2f GB  %s\n", s/1024/1024/1024, p}'
    fi
done < "$SAFE_LIST"
'@

$clean = $remoteScript.Trim([char]0xFEFF, "`r", "`n", " ")
$bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($clean)
$b64 = [System.Convert]::ToBase64String($bytes)

& ssh -F $sshConfig tu_freiberg "echo `"$b64`" | base64 -d | tr -d '\r' | bash"
