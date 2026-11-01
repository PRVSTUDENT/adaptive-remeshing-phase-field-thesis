#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_c4_exact_load_reference"
cd "${RUN_DIR}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

case "${1:-both}" in
  mechanical)
    jobs=("P160_MECHANICAL_DC")
    ;;
  phase)
    jobs=("P160_PHASE_DC")
    ;;
  coupled)
    jobs=("M1_C4_EXACT_REF_DC")
    ;;
  both|all)
    jobs=("P160_MECHANICAL_DC" "P160_PHASE_DC")
    ;;
  *)
    echo "Unknown target: ${1:-}" >&2
    exit 64
    ;;
esac

for job in "${jobs[@]}"; do
  if [ "${job}" = "M1_C4_EXACT_REF_DC" ]; then
    inp="M1_C4_EXACT_LOAD_REF.inp"
  else
    inp="${job}.inp"
  fi
  echo "Running Abaqus 2023 datacheck for ${job} (input=${inp})..."
  rm -f "${job}.dat" "${job}.log" "${job}.msg" "${job}.sta" "${job}.prt" "${job}.com"
  abaqus job="${job}" input="${inp}" user=f42_mixed_uel.for cpus=1 memory="16 gb" datacheck interactive > "${job}.stdout.txt" 2>&1
  test -f "${job}.dat"
  grep -q 'ANALYSIS DATACHECK COMPLETE' "${job}.dat"
  if grep -q '\*\*\*ERROR' "${job}.dat"; then
    echo "ERROR: Datacheck failed for ${job}" >&2
    exit 66
  fi
  echo "${job}: AUTHENTIC_DATACHECK_PASS"
done

echo "AUTHENTIC_DATACHECK_PASS_BOTH"
