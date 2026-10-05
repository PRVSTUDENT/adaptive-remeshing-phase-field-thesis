#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
DRY_RUN=false
if [ "$1" == "--dry-run" ]; then DRY_RUN=true; fi
echo "=== M2STATE_FRACFIX_RESTART1R1R1 SUBMISSION PREFLIGHT ==="
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"
if [ -f "$REPO_ROOT/scripts/hpc/check_license_gate.py" ]; then python3 "$REPO_ROOT/scripts/hpc/check_license_gate.py"; fi
PYTHONPATH="$REPO_ROOT:$PYTHONPATH" python3 -m unittest -v tests.unit.test_m2state_fracfix_restart1r1r1
if [ "$DRY_RUN" = true ]; then echo "=== PREFLIGHT DRY-RUN COMPLETE (NO QSUB EXECUTED) ==="; exit 0; fi
qsub M2STATE_FRACFIX_RESTART1R1R1.pbs
