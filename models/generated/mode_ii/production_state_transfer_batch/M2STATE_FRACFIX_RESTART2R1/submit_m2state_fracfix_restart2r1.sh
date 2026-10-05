#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=true
elif [ "${1:-}" = "--execute" ]; then
    DRY_RUN=false
else
    echo "Usage: $0 --dry-run | --execute"
    exit 1
fi

echo "=== M2STATE_FRACFIX_RESTART2R1 PREFLIGHT CHECK ==="
python3 -c "
import json, hashlib, sys
with open('PACKAGE_MANIFEST.json') as f:
    m = json.load(f)
files = m.get('files', m.get('file_hashes', {}))
for f, h in files.items():
    actual = hashlib.sha256(open(f, 'rb').read()).hexdigest()
    if actual != h:
        print('HASH MISMATCH:', f, actual, h)
        sys.exit(1)
print('PACKAGE_MANIFEST_VERIFICATION: PASS')
"

if [ "$DRY_RUN" = true ]; then
    echo "DRY RUN PASSED: qsub will NOT be called."
    exit 0
fi

qsub M2STATE_FRACFIX_RESTART2R1.pbs
