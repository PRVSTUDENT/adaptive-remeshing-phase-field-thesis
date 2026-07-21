#!/bin/bash
# Resume Stage C2 from C2B using an existing successful C2A continuum ODB.
# Does not re-run C2A. Fixes afterok cascade after C2B tool failures.
set -euo pipefail

PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
PRESTAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/prestage"
PBS_OUTPUT_ROOT="/scratch/pr21vyci/adaptive-remeshing/pbs_output"
EMAIL="pr21vyci@mailserver.tu-freiberg.de"
QUEUE="entry_imfdfkmq"
STAGE_DIR="scripts/hpc/stage_c2"

# Default: successful C2A ODB from 1376298
C2A_ODB_DEFAULT="/scratch/pr21vyci/adaptive-remeshing/runs/molnar_h0_aux_miseseri_1376298.mmaster02/molnar_h0_aux_miseseri.odb"
C2A_ODB="${C2A_ODB:-$C2A_ODB_DEFAULT}"

REQUIRED_PATHS=(
  "models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension"
  "models/generated/molnar_gravouil_2017/aux_continuum/H0_aux_miseseri"
  "models/generated/molnar_gravouil_2017/h_convergence_lc015/H0_exact"
  "models/generated/molnar_gravouil_2017/unified_preprocessing"
  "configs/preprocessing/molnar_h0_h1_unified.yaml"
  "configs/remeshing/miseseri_h0_to_h1_initial.json"
  "configs/studies/molnar_lc015_h_convergence.yaml"
  "results/processed/molnar_lc015_h_convergence"
  "scripts/preprocessing"
  "scripts/postprocessing"
  "scripts/validation"
  "scripts/remeshing"
  "scripts/model_generation"
  "scripts/hpc/stage_c2"
  "scripts/hpc/validate_pbs_email_notifications.py"
  "runs/hpc/stage_c2"
)

cd "${PROJECT_HOME}"

if [ -n "$(git status --short --untracked-files=no)" ]; then
  echo "tracked_working_tree_not_clean" >&2
  git status --short --untracked-files=no >&2
  exit 2
fi

if [ ! -f "${C2A_ODB}" ]; then
  echo "C2A ODB missing: ${C2A_ODB}" >&2
  exit 5
fi

if qstat -u "${USER}" 2>/dev/null | grep -E 'c2b_gate|c2c_rebuild|c2d_h0|c2e_ref|c2f_ref' >/dev/null 2>&1; then
  echo "duplicate_c2_downstream_active" >&2
  qstat -u "${USER}" >&2 || true
  exit 3
fi

echo "=== using C2A ODB ==="
ls -la "${C2A_ODB}"
# Publish for C2B
printf '%s\n' "${C2A_ODB}" > "${PROJECT_HOME}/runs/hpc/stage_c2/C2A_ODB_PATH.txt"
printf '%s\n' "1376298.mmaster02" > "${PROJECT_HOME}/runs/hpc/stage_c2/C2A_JOB_ID.txt"

REVISION="$(git rev-parse HEAD)"
SHORT_REVISION="${REVISION:0:12}"
TIMESTAMP="$(date +%Y%m%dT%H%M%S%z)"
PRESTAGED_ROOT="${PRESTAGE_ROOT}/stage_c2b_${TIMESTAMP}_${SHORT_REVISION}"
PBS_OUTPUT_DIR="${PBS_OUTPUT_ROOT}/stage_c2b_${TIMESTAMP}_${SHORT_REVISION}"
mkdir -p "${PRESTAGED_ROOT}" "${PBS_OUTPUT_DIR}" "${PROJECT_HOME}/runs/hpc/stage_c2"

git archive "${REVISION}" -- "${REQUIRED_PATHS[@]}" | tar -x -C "${PRESTAGED_ROOT}"
printf '%s\n' "${REVISION}" > "${PRESTAGED_ROOT}/PROJECT_REVISION.txt"

# Also put ODB pointer into prestaged tree copy of stage_c2
mkdir -p "${PRESTAGED_ROOT}/runs/hpc/stage_c2"
printf '%s\n' "${C2A_ODB}" > "${PRESTAGED_ROOT}/runs/hpc/stage_c2/C2A_ODB_PATH.txt"

(cd "${PRESTAGED_ROOT}/models/generated/molnar_gravouil_2017/h_convergence_lc015/H0_exact" && sha256sum -c input_hashes.sha256)
python3 scripts/hpc/validate_pbs_email_notifications.py --email "${EMAIL}" \
  "${STAGE_DIR}/02_gate_remesh_export.pbs" \
  "${STAGE_DIR}/03_rebuild_validate.pbs" \
  "${STAGE_DIR}/04_h0_threads4_qualification.pbs" \
  "${STAGE_DIR}/05_refined_integrity_threads4.pbs" \
  "${STAGE_DIR}/06_refined_final_threads4.pbs"

cd "${PRESTAGED_ROOT}"

J2=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}",C2A_ODB="${C2A_ODB}" \
  -o "${PBS_OUTPUT_DIR}/c2b.out" \
  "${STAGE_DIR}/02_gate_remesh_export.pbs")

J3=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -W depend=afterok:"${J2}" \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}" \
  -o "${PBS_OUTPUT_DIR}/c2c.out" \
  "${STAGE_DIR}/03_rebuild_validate.pbs")

J4=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -W depend=afterok:"${J3}" \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}" \
  -o "${PBS_OUTPUT_DIR}/c2d.out" \
  "${STAGE_DIR}/04_h0_threads4_qualification.pbs")

J5=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -W depend=afterok:"${J4}" \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}" \
  -o "${PBS_OUTPUT_DIR}/c2e.out" \
  "${STAGE_DIR}/05_refined_integrity_threads4.pbs")

J6=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -W depend=afterok:"${J5}" \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}" \
  -o "${PBS_OUTPUT_DIR}/c2f.out" \
  "${STAGE_DIR}/06_refined_final_threads4.pbs")

{
  echo "submission_time=${TIMESTAMP}"
  echo "revision=${REVISION}"
  echo "resume_from=C2B"
  echo "C2A_ODB=${C2A_ODB}"
  echo "C2A_reused=1376298.mmaster02"
  echo "C2B=${J2}"
  echo "C2C=${J3}"
  echo "C2D=${J4}"
  echo "C2E=${J5}"
  echo "C2F=${J6}"
  echo "prior_c2b_failure=1376299_python_annotations"
  echo "fix=cluster_python_no_future_annotations_in_remesh_helper"
} | tee "${PROJECT_HOME}/runs/hpc/stage_c2/C2_RESUME_FROM_C2B_SUBMISSION_RECORD.txt"

printf '%s\n' "C2B=$J2" "C2C=$J3" "C2D=$J4" "C2E=$J5" "C2F=$J6"
qstat -u "${USER}" | head -20 || true
