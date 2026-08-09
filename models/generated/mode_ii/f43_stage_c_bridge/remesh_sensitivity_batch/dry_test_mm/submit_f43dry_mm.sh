#!/bin/bash
set -euo pipefail

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
cd "${PACKAGE_DIR}"

if [ "${F43DRY_MM_AUTHORIZED:-0}" -ne 1 ]; then
    echo "ERROR: Submission unauthorized. Must explicitly set F43DRY_MM_AUTHORIZED=1" >&2
    exit 1
fi

qsub -v F43DRY_MM_WRAPPER_AUTHORIZED=1 F43DRY_MM.pbs
