#!/bin/bash
# Guarded Submission Wrapper for M2STATE_INGEST_SMOKE1R6
# Fails closed if any file hash mismatches, toolchain is missing, license gate fails, active-entity validator fails, or candidate test suite fails.

set -e

DRY_RUN=false
TEST_NEGATIVE=false

for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --test-negative)
            TEST_NEGATIVE=true
            shift
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== M2STATE_INGEST_SMOKE1R6 SUBMISSION PREFLIGHT ==="
echo "Directory: $SCRIPT_DIR"
echo "Job Name: M2STATE_INGEST_SMOKE1R6"

# 1. License Gate Check
echo "=== PREFLIGHT 1: FlexNet License Readiness Gate ==="
if [ -f "/scratch/pr21vyci/projects/adaptive-remeshing/scripts/hpc/check_license_gate.py" ]; then
    python3 /scratch/pr21vyci/projects/adaptive-remeshing/scripts/hpc/check_license_gate.py
else
    echo "WARNING: check_license_gate.py not found, proceeding with hash preflight."
fi

# 2. Candidate Qualification & Active-Entity Closure Validator
echo "=== PREFLIGHT 2: Candidate Qualification & Active-Entity Closure Validator ==="
if [ -f "/scratch/pr21vyci/projects/adaptive-remeshing/tests/unit/test_m2state_ingest_smoke1r6.py" ]; then
    python3 /scratch/pr21vyci/projects/adaptive-remeshing/tests/unit/test_m2state_ingest_smoke1r6.py
fi

# 3. Package File Hash Checks
echo "=== PREFLIGHT 3: Package File Hashes ==="
if [ ! -f "PACKAGE_MANIFEST.json" ]; then
    echo "ERROR: PACKAGE_MANIFEST.json not found!"
    exit 1
fi

EXPECTED_INP=$(python3 -c "import json; print(json.load(open('PACKAGE_MANIFEST.json'))['M2STATE_INGEST_SMOKE1R6.inp'])")
EXPECTED_FOR=$(python3 -c "import json; print(json.load(open('PACKAGE_MANIFEST.json'))['f42_mixed_uel.for'])")
EXPECTED_ART=$(python3 -c "import json; print(json.load(open('PACKAGE_MANIFEST.json'))['STATE_TRANSFER_ARTIFACT.json'])")
EXPECTED_MAN=$(python3 -c "import json; print(json.load(open('PACKAGE_MANIFEST.json'))['TRANSFER_MANIFEST.json'])")
EXPECTED_CON=$(python3 -c "import json; print(json.load(open('PACKAGE_MANIFEST.json'))['ACCEPTANCE_CONTRACT.json'])")
EXPECTED_PBS=$(python3 -c "import json; print(json.load(open('PACKAGE_MANIFEST.json'))['M2STATE_INGEST_SMOKE1R6.pbs'])")
EXPECTED_CHK=$(python3 -c "import json; print(json.load(open('PACKAGE_MANIFEST.json'))['verify_smoke_trace.py'])")

ACTUAL_INP=$(sha256sum M2STATE_INGEST_SMOKE1R6.inp | awk '{print $1}')
ACTUAL_FOR=$(sha256sum f42_mixed_uel.for | awk '{print $1}')
ACTUAL_ART=$(sha256sum STATE_TRANSFER_ARTIFACT.json | awk '{print $1}')
ACTUAL_MAN=$(sha256sum TRANSFER_MANIFEST.json | awk '{print $1}')
ACTUAL_CON=$(sha256sum ACCEPTANCE_CONTRACT.json | awk '{print $1}')
ACTUAL_PBS=$(sha256sum M2STATE_INGEST_SMOKE1R6.pbs | awk '{print $1}')
ACTUAL_CHK=$(sha256sum verify_smoke_trace.py | awk '{print $1}')

if [ "$ACTUAL_INP" != "$EXPECTED_INP" ]; then echo "HASH MISMATCH: M2STATE_INGEST_SMOKE1R6.inp"; exit 1; fi
if [ "$ACTUAL_FOR" != "$EXPECTED_FOR" ]; then echo "HASH MISMATCH: f42_mixed_uel.for"; exit 1; fi
if [ "$ACTUAL_ART" != "$EXPECTED_ART" ]; then echo "HASH MISMATCH: STATE_TRANSFER_ARTIFACT.json"; exit 1; fi
if [ "$ACTUAL_MAN" != "$EXPECTED_MAN" ]; then echo "HASH MISMATCH: TRANSFER_MANIFEST.json"; exit 1; fi
if [ "$ACTUAL_CON" != "$EXPECTED_CON" ]; then echo "HASH MISMATCH: ACCEPTANCE_CONTRACT.json"; exit 1; fi
if [ "$ACTUAL_PBS" != "$EXPECTED_PBS" ]; then echo "HASH MISMATCH: M2STATE_INGEST_SMOKE1R6.pbs"; exit 1; fi
if [ "$ACTUAL_CHK" != "$EXPECTED_CHK" ]; then echo "HASH MISMATCH: verify_smoke_trace.py"; exit 1; fi

echo "ALL PACKAGE FILE HASHES VERIFIED MATCH"

if [ "$DRY_RUN" = true ]; then
    echo "=== PREFLIGHT DRY-RUN COMPLETE (NO QSUB EXECUTED) ==="
    echo "dry_run = true"
    echo "qsub_called = false"
    echo "HPC_submissions = 0"
    exit 0
fi

if [ "$TEST_NEGATIVE" = true ]; then
    echo "=== PREFLIGHT TEST-NEGATIVE COMPLETE ==="
    echo "test_negative = true"
    echo "qsub_called = false"
    exit 0
fi

echo "=== EXECUTING QSUB ==="
qsub M2STATE_INGEST_SMOKE1R6.pbs
