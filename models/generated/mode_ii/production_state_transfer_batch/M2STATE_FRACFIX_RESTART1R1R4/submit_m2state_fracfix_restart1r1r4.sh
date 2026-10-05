#!/bin/bash
# Guarded Submission Wrapper for M2STATE_FRACFIX_RESTART1R1R4
# Protocol: Standalone direct-human authorization required before direct qsub.

DRY_RUN=false
if [ "$1" == "--dry-run" ]; then
  DRY_RUN=true
fi

echo "[WRAPPER] Preflight verification for M2STATE_FRACFIX_RESTART1R1R4..."

MANIFEST="PACKAGE_MANIFEST.json"
if [ ! -f "$MANIFEST" ]; then
  echo "[WRAPPER] ERROR: $MANIFEST not found."
  exit 1
fi

python3 -c "
import json, hashlib, sys
from pathlib import Path

m = json.loads(Path('$MANIFEST').read_text())
for f, expected_hash in m['file_hashes'].items():
    p = Path(f)
    if not p.exists():
        print(f'[WRAPPER] ERROR: Missing package file {f}')
        sys.exit(1)
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    if actual != expected_hash:
        print(f'[WRAPPER] ERROR: Hash mismatch for {f}: expected {expected_hash}, got {actual}')
        sys.exit(1)
print('[WRAPPER] ALL PACKAGE FILE HASHES VERIFIED MATCH.')
"
if [ $? -ne 0 ]; then
  echo "[WRAPPER] ERROR: Package manifest hash verification failed."
  exit 1
fi

if [ "$DRY_RUN" = true ]; then
  echo "[WRAPPER] DRY-RUN COMPLETE: Preflight passed cleanly. qsub was NOT called."
  exit 0
fi

echo "[WRAPPER] FAIL-CLOSED: Direct qsub requires explicit human authorization."
exit 1
