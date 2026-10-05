#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DRY_RUN=false
if [ "$1" == "--dry-run" ]; then
    DRY_RUN=true
fi

echo "=== M2STATE_INGEST_SMOKE1R10 SUBMISSION PREFLIGHT ==="
echo "Directory: $SCRIPT_DIR"
echo "Job Name: M2STATE_INGEST_SMOKE1R10"

REPO_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"

echo "=== PREFLIGHT 1: FlexNet License Readiness Gate ==="
if [ -f "$REPO_ROOT/scripts/hpc/check_license_gate.py" ]; then
    python3 "$REPO_ROOT/scripts/hpc/check_license_gate.py"
fi

echo "=== PREFLIGHT 2: Candidate Qualification & Active-Entity Closure Validator ==="
PYTHONPATH="$REPO_ROOT:$PYTHONPATH" python3 -m unittest -v tests.unit.test_m2state_ingest_smoke1r10

echo "=== PREFLIGHT 3: Package File Hashes ==="
python3 -c "
import json, hashlib, sys
from pathlib import Path

pkg_dir = Path('$SCRIPT_DIR')
manifest_path = pkg_dir / 'PACKAGE_MANIFEST.json'
with open(manifest_path, 'r') as f:
    manifest = json.load(f)

mismatches = []
for filename, expected_hash in manifest['files'].items():
    filepath = pkg_dir / filename
    if not filepath.exists():
        mismatches.append(f'{filename}: missing')
        continue
    actual_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        mismatches.append(f'{filename}: expected {expected_hash}, got {actual_hash}')

if mismatches:
    print('ERROR: Package file hash mismatch!')
    for m in mismatches:
        print('  ' + m)
    sys.exit(1)

print('ALL PACKAGE FILE HASHES VERIFIED MATCH')
"

if [ "$DRY_RUN" = true ]; then
    echo "=== PREFLIGHT DRY-RUN COMPLETE (NO QSUB EXECUTED) ==="
    echo "dry_run = true"
    echo "qsub_called = false"
    echo "HPC_submissions = 0"
    exit 0
fi

echo "=== EXECUTING QSUB ==="
qsub M2STATE_INGEST_SMOKE1R10.pbs
