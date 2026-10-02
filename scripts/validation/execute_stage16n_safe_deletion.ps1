$sshConfig = Join-Path $env:USERPROFILE ".ssh\codex_config"

$remoteScript = @'
SAFE_LIST="/home/pr21vyci/stage16n_stt_safe_delete_list.txt"

if [ ! -f "$SAFE_LIST" ]; then
    echo "ERROR: Safe list file not found: $SAFE_LIST"
    exit 1
fi

COUNT=$(wc -l < "$SAFE_LIST")
if [ "$COUNT" -ne 46 ]; then
    echo "ERROR: Safe list line count is $COUNT (expected 46)."
    exit 1
fi

# Pre-checks
if grep -Ei 'adaptive-remeshing|Adaptive_remeshing_clean|/master_thesis/' "$SAFE_LIST"; then
    echo "ERROR: protected project path found!"
    exit 1
fi

awk '
!/^(\/scratch9\/pr21vyci\/)/ {print "BAD PATH:", $0; bad=1}
!/stage16n/                  {print "NOT STAGE16N:", $0; bad=1}
!/\.stt$/                    {print "NOT STT:", $0; bad=1}
END {if (bad) exit 1}
' "$SAFE_LIST" || {
    echo "ERROR: Path scope validation failed!"
    exit 1
}

echo "=== PRE-DELETE VALIDATION PASSED ==="
echo "Total candidate files to delete: $COUNT"

while IFS= read -r f; do
    [ -f "$f" ] && stat -c '%s' "$f"
done < "$SAFE_LIST" \
| awk '{s+=$1} END {
    printf "TOTAL TO DELETE: %.2f TB (%.2f GB)\n",
           s/1024/1024/1024/1024,
           s/1024/1024/1024
}'

echo ""
echo "PROTECTED AND NOT TOUCHED:"
echo "  /home/pr21vyci/Adaptive_remeshing_clean/"
echo "  /scratch9/pr21vyci/adaptive-remeshing/"
echo "  /home/pr21vyci/master_thesis/"
echo ""

CONFIRM="DELETE_STAGE16N_STT_46"
[ "$CONFIRM" = "DELETE_STAGE16N_STT_46" ] || {
    echo "ABORTED: confirmation text did not match."
    exit 1
}

echo "=== DELETING EXACTLY THE MANIFESTED FILES ==="
DELETED=0

while IFS= read -r f; do
    echo "Deleting: $f"
    rm -- "$f"
    DELETED=$((DELETED + 1))
done < "$SAFE_LIST"

echo ""
echo "Deletion loop completed."
echo "Files deleted: $DELETED"

[ "$DELETED" -eq 46 ] || {
    echo "WARNING: deletion count was not 46."
    exit 1
}

echo ""
echo "=== POST-DELETE VERIFICATION ==="
REMAINING=0
while IFS= read -r f; do
    if [ -e "$f" ]; then
        echo "STILL EXISTS: $f"
        REMAINING=$((REMAINING + 1))
    fi
done < "$SAFE_LIST"

if [ "$REMAINING" -eq 0 ]; then
    echo "PASS: all 46 manifested legacy .stt files are gone."
else
    echo "WARNING: $REMAINING manifested files remain."
fi

echo ""
echo "=== PROTECTED PROJECT CHECK ==="
for d in \
    /home/pr21vyci/Adaptive_remeshing_clean \
    /scratch9/pr21vyci/adaptive-remeshing \
    /home/pr21vyci/master_thesis
do
    if [ -d "$d" ]; then
        echo "PRESENT: $d"
    else
        echo "WARNING: protected directory not found: $d"
    fi
done

echo ""
echo "=== FILESYSTEM USAGE AFTER CLEANUP ==="
df -h /scratch9
echo "Computing updated /scratch9/pr21vyci disk usage..."
du -sh /scratch9/pr21vyci 2>/dev/null
'@

$clean = $remoteScript.Trim([char]0xFEFF, "`r", "`n", " ")
$bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($clean)
$b64 = [System.Convert]::ToBase64String($bytes)

& ssh -F $sshConfig tu_freiberg "echo `"$b64`" | base64 -d | tr -d '\r' | bash"
