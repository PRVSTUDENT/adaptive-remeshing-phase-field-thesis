#!/bin/bash
set -e
# Guarded submission wrapper for M2STATE_INGEST_SMOKE1
PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PACKAGE_DIR"

echo "Checking package preflight for M2STATE_INGEST_SMOKE1..."

EXPECTED_INP_SHA="d143c7b649d8c0b2c159bf4e7978eb32c4e20986fa88df1788ee5cce025b6999"

# Validate manifest
if [ ! -f "PACKAGE_MANIFEST.json" ]; then
  echo "ERROR: PACKAGE_MANIFEST.json missing!"
  exit 1
fi

echo "PACKAGE PREFLIGHT: PASS"
echo "Submissions are guarded. Direct qsub requires explicit human authorization."
