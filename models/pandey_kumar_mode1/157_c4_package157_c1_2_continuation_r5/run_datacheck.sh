#!/bin/bash
set -euo pipefail
cd "${1:?exact run directory required}"
for role in MECHANICAL PHASE; do
 job="P157_${role}_DC"
 test ! -e "${job}.dat"
 abaqus job="${job}" input="${job}.inp" user=f42_mixed_uel.for cpus=1 memory="16 gb" datacheck interactive > "${job}.stdout.txt" 2>&1
 test -f "${job}.dat"
 grep -q 'ANALYSIS DATACHECK COMPLETE' "${job}.dat"
 if grep -q '\*\*\*ERROR' "${job}.dat"; then exit 66; fi
done
echo AUTHENTIC_DATACHECK_PASS_BOTH
