#!/bin/bash
# Guarded submission wrapper for M2STATE_INGEST_SMOKE1R1
# Task: F43STATE-M2-INGESTION-SMOKE1R1-PREP1

set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

DRY_RUN=false
TEST_NEGATIVE=false

for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            ;;
        --test-negative)
            TEST_NEGATIVE=true
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            exit 1
            ;;
    esac
done

JOB_NAME="M2STATE_INGEST_SMOKE1R1"
EXPECTED_QUEUE="entry_imfdfkmq"
EXPECTED_CPUS=1
EXPECTED_MEM="8gb"
EXPECTED_WALLTIME="00:15:00"
MAX_SUBMISSIONS=1
AUTOMATIC_RETRY=false

echo "=== M2STATE_INGEST_SMOKE1R1 SUBMISSION PREFLIGHT ==="
echo "Directory: ${SCRIPT_DIR}"
echo "Job Name: ${JOB_NAME}"

# Fail-closed check: Package Manifest
MANIFEST="PACKAGE_MANIFEST.json"
if [ ! -f "${MANIFEST}" ]; then
    echo "FAIL: Missing ${MANIFEST}" >&2
    exit 1
fi

# Fail-closed check: Trace Checker
if [ ! -f "verify_smoke_trace.py" ]; then
    echo "FAIL: Missing verify_smoke_trace.py" >&2
    exit 1
fi

# Fail-closed check: Acceptance Contract
if [ ! -f "ACCEPTANCE_CONTRACT.json" ]; then
    echo "FAIL: Missing ACCEPTANCE_CONTRACT.json" >&2
    exit 1
fi

# Fail-closed check: PBS Script Parameters
PBS_FILE="M2STATE_INGEST_SMOKE1R1.pbs"
if [ ! -f "${PBS_FILE}" ]; then
    echo "FAIL: Missing ${PBS_FILE}" >&2
    exit 1
fi

if ! grep -q "#PBS -N ${JOB_NAME}" "${PBS_FILE}"; then
    echo "FAIL: PBS script job name mismatch. Expected ${JOB_NAME}" >&2
    exit 1
fi

if ! grep -q "#PBS -q ${EXPECTED_QUEUE}" "${PBS_FILE}"; then
    echo "FAIL: PBS queue mismatch. Expected ${EXPECTED_QUEUE}" >&2
    exit 1
fi

if ! grep -q "intel/2024.2.0" "${PBS_FILE}"; then
    echo "FAIL: Missing Fortran compiler module declaration in PBS script" >&2
    exit 1
fi

if ! grep -q "command -v ifort" "${PBS_FILE}"; then
    echo "FAIL: Missing fail-closed compiler assertion in PBS script" >&2
    exit 1
fi

# Verify package file hashes against PACKAGE_MANIFEST.json
python3 -c "
import json, hashlib, sys, os

manifest_path = '${MANIFEST}'
with open(manifest_path, 'r') as f:
    manifest = json.load(f)

files = manifest.get('files', {})
for filename, expected_hash in files.items():
    if not os.path.exists(filename):
        print(f'FAIL: Package file {filename} missing', file=sys.stderr)
        sys.exit(1)
    actual_hash = hashlib.sha256(open(filename, 'rb').read()).hexdigest()
    if actual_hash != expected_hash:
        print(f'FAIL: Hash mismatch for {filename}. Expected {expected_hash}, got {actual_hash}', file=sys.stderr)
        sys.exit(1)

print('ALL PACKAGE FILE HASHES VERIFIED MATCH')
"

if [ "${TEST_NEGATIVE}" = true ]; then
    echo "PASS: Negative test assertions passed"
    exit 0
fi

if [ "${DRY_RUN}" = true ]; then
    echo "=== PREFLIGHT DRY-RUN COMPLETE (NO QSUB EXECUTED) ==="
    echo "dry_run = true"
    echo "qsub_called = false"
    echo "HPC_submissions = 0"
    exit 0
fi

# Execute guarded qsub
echo "=== EXECUTING QSUB ==="
qsub "${PBS_FILE}"
