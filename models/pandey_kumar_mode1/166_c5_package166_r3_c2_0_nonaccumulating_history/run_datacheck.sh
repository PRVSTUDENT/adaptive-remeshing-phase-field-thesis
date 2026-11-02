#!/bin/bash
set -eu
cd "${1:-/scratch9/pr21vyci/runs/mode1_c5_package166_c2_0_nonaccumulating_history}"
if ! type module >/dev/null 2>&1; then
 source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
for role in MECHANICAL PHASE; do
 job="P166_${role}_DC"
 test ! -e "${job}.dat" || rm -f "${job}.dat"
 abaqus job="${job}" input="${job}.inp" user=f42_mixed_uel.for cpus=1 memory="16 gb" datacheck interactive > "${job}.stdout.txt" 2>&1
 test -f "${job}.dat"
 grep -q 'ANALYSIS DATACHECK COMPLETE' "${job}.dat"
 if grep -q '\*\*\*ERROR' "${job}.dat"; then exit 66; fi
done
echo AUTHENTIC_DATACHECK_PASS_BOTH
