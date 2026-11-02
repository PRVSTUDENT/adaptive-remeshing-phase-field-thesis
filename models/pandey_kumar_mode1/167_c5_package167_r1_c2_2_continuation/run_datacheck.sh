#!/bin/bash
set -euo pipefail
cd "/scratch9/pr21vyci/runs/mode1_c5_package167_r1_c2_2_continuation"

case "${1:-}" in
  mechanical) job=P167_MECHANICAL_DC ;;
  phase) job=P167_PHASE_DC ;;
  *) echo 'Exact mechanical or phase role required' >&2; exit 64 ;;
esac

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

abaqus job="${job}" input="${job}.inp" user=f42_mixed_uel.for cpus=1 memory="16 gb" datacheck interactive > "${job}.stdout.txt" 2>&1
test -f "${job}.dat"
grep -q 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' "${job}.dat" || grep -q 'ANALYSIS DATACHECK COMPLETE' "${job}.dat"
if grep -q '\*\*\*ERROR' "${job}.dat"; then exit 66; fi
echo "${job}: AUTHENTIC_DATACHECK_PASS"
