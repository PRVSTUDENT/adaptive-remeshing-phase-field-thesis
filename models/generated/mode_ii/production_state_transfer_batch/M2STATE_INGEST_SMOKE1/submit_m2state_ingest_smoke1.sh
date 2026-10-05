#!/bin/bash
set -e
# Guarded submission wrapper for M2STATE_INGEST_SMOKE1
# Supports --dry-run / --preflight flag for safe non-submitting validation

DRY_RUN=0
if [ "$1" == "--dry-run" ] || [ "$1" == "--preflight" ]; then
  DRY_RUN=1
fi

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PACKAGE_DIR"

echo "Checking package preflight for M2STATE_INGEST_SMOKE1..."

# 1. Validate manifest file existence
if [ ! -f "PACKAGE_MANIFEST.json" ]; then
  echo "ERROR: PACKAGE_MANIFEST.json missing!"
  exit 1
fi

# 2. Validate PBS parameter constraints
grep -q "#PBS -N M2STATE_INGEST_SMOKE1" M2STATE_INGEST_SMOKE1.pbs || { echo "ERROR: Invalid job name"; exit 1; }
grep -q "#PBS -q entry_imfdfkmq" M2STATE_INGEST_SMOKE1.pbs || { echo "ERROR: Invalid queue"; exit 1; }
grep -q "select=1:ncpus=1:mem=8gb" M2STATE_INGEST_SMOKE1.pbs || { echo "ERROR: Invalid resources"; exit 1; }
grep -q "#PBS -l walltime=00:15:00" M2STATE_INGEST_SMOKE1.pbs || { echo "ERROR: Invalid walltime"; exit 1; }

# Determine python command
PYTHON_CMD="python3"
if command -v python &> /dev/null; then
  PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
  PYTHON_CMD="python3"
elif [ -f "C:/Users/pruth/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" ]; then
  PYTHON_CMD="C:/Users/pruth/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe"
fi

# 3. Fail-closed hash validation of every execution-critical package file against PACKAGE_MANIFEST.json
$PYTHON_CMD -c '
import json, hashlib, sys, os

manifest_path = "PACKAGE_MANIFEST.json"
if not os.path.exists(manifest_path):
    print("ERROR: PACKAGE_MANIFEST.json not found")
    sys.exit(1)

with open(manifest_path, "r") as f:
    manifest = json.load(f)

file_hashes = manifest.get("file_hashes", {})
if not file_hashes:
    print("ERROR: Empty file_hashes in manifest")
    sys.exit(1)

for fname, expected_hash in file_hashes.items():
    if not os.path.exists(fname):
        print(f"ERROR: Package file missing: {fname}")
        sys.exit(1)
    with open(fname, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest().lower()
    if actual_hash != expected_hash.lower():
        print(f"ERROR: Hash mismatch for {fname}! Expected {expected_hash}, got {actual_hash}")
        sys.exit(1)

print("ALL PACKAGE FILE HASHES VERIFIED MATCH")
' || { echo "PREFLIGHT HASH VERIFICATION FAILED"; exit 1; }

echo "PACKAGE PREFLIGHT: PASS"

if [ $DRY_RUN -eq 1 ]; then
  echo "PREFLIGHT DRY-RUN SUCCESSFUL: NO QSUB CALLED (qsub_called=false, HPC_submissions=0)"
  exit 0
fi

echo "Guarded submit mode: Submissions require explicit human authorization."
