#!/bin/bash
set -euo pipefail

# Storage-compliance guard: reject launching from /home/
if [[ "${SCRIPT_DIR:-$(pwd -P)}" =~ ^/home/ ]]; then
  echo "[STORAGE COMPLIANCE ERROR] Submitting from /home/ is prohibited." >&2
  echo "Please execute/submit from /scratch/pr21vyci/projects/adaptive-remeshing/..." >&2
  exit 88
fi

EXECUTE=false
DRY_RUN=false

for arg in "$@"; do
    case $arg in
        --execute) EXECUTE=true ;;
        --dry-run) DRY_RUN=true ;;
    esac
done

echo "=== M2STATE_FRACFIX_RESTART2R2 PREFLIGHT CHECK ==="
python3 validate_package_manifest.py
echo "PACKAGE_MANIFEST_VERIFICATION: PASS"

if [ "$DRY_RUN" = true ]; then
    echo "DRY_RUN_SUCCESSFUL: qsub_call_count=0"
    exit 0
fi

if [ "$EXECUTE" = true ]; then
    qsub M2STATE_FRACFIX_RESTART2R2.pbs
    exit 0
fi

echo "Usage: submit_m2state_fracfix_restart2r2.sh [--dry-run | --execute]"
exit 1
