#!/bin/bash
# Submit C2E-v2 → C2F-v2 only after C2D.ok and C2C_V2.ok exist.
# Does not resubmit C2D solver. Does not use the 160k mesh.
set -euo pipefail

PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
PRESTAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/prestage"
PBS_OUTPUT_ROOT="/scratch/pr21vyci/adaptive-remeshing/pbs_output"
EMAIL="pr21vyci@mailserver.tu-freiberg.de"
QUEUE="entry_imfdfkmq"
STAGE_DIR="scripts/hpc/stage_c2"
CHAIN_STATE_DIR="${PROJECT_HOME}/runs/hpc/stage_c2/chain_state"

cd "${PROJECT_HOME}"

test -f "${CHAIN_STATE_DIR}/C2D.ok" || { echo "missing C2D.ok" >&2; exit 2; }
test -f "${CHAIN_STATE_DIR}/C2C_V2.ok" || { echo "missing C2C_V2.ok" >&2; exit 2; }
test -f runs/hpc/stage_c2/C2C_V2_DECK_PATH.txt
DECK="$(tr -d '[:space:]' < runs/hpc/stage_c2/C2C_V2_DECK_PATH.txt)"
case "${DECK}" in
  *H0_refined_layered_v2*) ;;
  *) echo "refusing non-v2 deck ${DECK}" >&2; exit 3 ;;
esac

if qstat -u "${USER}" 2>/dev/null | grep -E 'c2e_v2|c2f_v2' >/dev/null 2>&1; then
  echo "duplicate c2e/c2f v2 jobs" >&2
  qstat -u "${USER}" >&2 || true
  exit 4
fi

if [ -n "$(git status --short --untracked-files=no)" ]; then
  echo "tracked_working_tree_not_clean" >&2
  git status --short --untracked-files=no >&2
  exit 5
fi

REVISION="$(git rev-parse HEAD)"
SHORT_REVISION="${REVISION:0:12}"
TIMESTAMP="$(date +%Y%m%dT%H%M%S%z)"
PRESTAGED_ROOT="${PRESTAGE_ROOT}/stage_c2ef_v2_${TIMESTAMP}_${SHORT_REVISION}"
PBS_OUTPUT_DIR="${PBS_OUTPUT_ROOT}/stage_c2ef_v2_${TIMESTAMP}_${SHORT_REVISION}"
mkdir -p "${PRESTAGED_ROOT}" "${PBS_OUTPUT_DIR}"

REQUIRED_PATHS=(
  "models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension"
  "scripts/hpc/stage_c2"
  "scripts/postprocessing"
  "scripts/validation"
  "scripts/hpc/validate_pbs_email_notifications.py"
  "runs/hpc/stage_c2"
)
git archive "${REVISION}" -- "${REQUIRED_PATHS[@]}" | tar -x -C "${PRESTAGED_ROOT}"
# C2C-v2 layered deck is generated offline (may be untracked) — copy from home
V2_SRC="${PROJECT_HOME}/models/generated/molnar_gravouil_2017/unified_preprocessing/H0_refined_layered_v2"
test -d "${V2_SRC}" || { echo "missing C2C-v2 layered dir ${V2_SRC}" >&2; exit 6; }
mkdir -p "${PRESTAGED_ROOT}/models/generated/molnar_gravouil_2017/unified_preprocessing"
cp -a "${V2_SRC}" \
  "${PRESTAGED_ROOT}/models/generated/molnar_gravouil_2017/unified_preprocessing/"
test -f "${PRESTAGED_ROOT}/models/generated/molnar_gravouil_2017/unified_preprocessing/H0_refined_layered_v2/H0_refined_fullgen.inp"

python3 scripts/hpc/validate_pbs_email_notifications.py --email "${EMAIL}" \
  "${STAGE_DIR}/07_c2e_v2_refined_integrity.pbs" \
  "${STAGE_DIR}/08_c2f_v2_refined_final.pbs"

cd "${PRESTAGED_ROOT}"
COMMON_V="PROJECT_REVISION=${REVISION},PRESTAGED_ROOT=${PRESTAGED_ROOT},CHAIN_STATE_DIR=${CHAIN_STATE_DIR}"

J5=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -v "${COMMON_V}" \
  -o "${PBS_OUTPUT_DIR}/c2e_v2.out" \
  "${STAGE_DIR}/07_c2e_v2_refined_integrity.pbs")

J6=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -W depend=afterany:"${J5}" \
  -v "${COMMON_V}" \
  -o "${PBS_OUTPUT_DIR}/c2f_v2.out" \
  "${STAGE_DIR}/08_c2f_v2_refined_final.pbs")

mkdir -p "${PROJECT_HOME}/runs/hpc/stage_c2/recovery"
{
  echo "submission_time=${TIMESTAMP}"
  echo "revision=${REVISION}"
  echo "chain=C2E_V2_C2F_V2"
  echo "C2D_solver_rerun=false"
  echo "C2D_odb_reused=1376411.mmaster02"
  echo "C2C_v1_160400_used=false"
  echo "C2C_V2_deck=${DECK}"
  echo "dependency_mode=afterany_plus_markers"
  echo "queue=${QUEUE}"
  echo "mail=${EMAIL}"
  echo "C2E_V2=${J5}"
  echo "C2F_V2=${J6}"
  echo "mp_mode=threads"
  echo "mpi_for_uel_umat=prohibited"
} | tee "${PROJECT_HOME}/runs/hpc/stage_c2/recovery/C2EF_V2_SUBMISSION_RECORD.txt"

printf '%s\n' "C2E_V2=$J5" "C2F_V2=$J6"
qstat -u "${USER}" | head -20 || true
