#!/bin/bash
# Guarded Submission Wrapper for F42TRI1_CORE
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [ "${1:-}" != "--authorize-execution" ]; then
    echo "ERROR: Submission not authorized. Requires explicit --authorize-execution flag." >&2
    echo "Current authorization status: execution_authorized = false" >&2
    exit 1
fi

export F42TRI1_CORE_WRAPPER_AUTHORIZED=1
qsub F42TRI1_CORE.pbs
