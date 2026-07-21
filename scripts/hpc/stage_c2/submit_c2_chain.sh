#!/bin/bash
# Submit Stage C2 unattended afterok chain C2A..C2F exactly once.
set -euo pipefail

PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
PRESTAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/prestage"
PBS_OUTPUT_ROOT="/scratch/pr21vyci/adaptive-remeshing/pbs_output"
EMAIL="${EMAIL:-Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de}"
QUEUE="entry_imfdfkmq"
STAGE_DIR="scripts/hpc/stage_c2"

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

if [ -f "runs/hpc/stage_c2/C2_CHAIN_SUBMISSION_RECORD.txt" ]; then
  echo "c2_chain_already_submitted" >&2
  cat runs/hpc/stage_c2/C2_CHAIN_SUBMISSION_RECORD.txt >&2
  exit 4
fi

if qstat -u "${USER}" 2>/dev/null | grep -E 'c2a_aux|c2b_gate|c2c_rebuild|c2d_h0|c2e_ref|c2f_ref' >/dev/null 2>&1; then
  echo "duplicate_c2_jobs_active" >&2
  qstat -u "${USER}" >&2 || true
  exit 3
fi

echo "=== queue check entry_imfdfkmq ==="
qstat -Qf entry_imfdfkmq | egrep -i 'enabled|started|resources_max|state_count|Queue:' || true
qstat -q | egrep 'entry_imfdfkmq|normal_imfdfkmq|short_imfdfkmq' || true

REVISION="$(git rev-parse HEAD)"
SHORT_REVISION="${REVISION:0:12}"
TIMESTAMP="$(date +%Y%m%dT%H%M%S%z)"
PRESTAGED_ROOT="${PRESTAGE_ROOT}/stage_c2_${TIMESTAMP}_${SHORT_REVISION}"
PBS_OUTPUT_DIR="${PBS_OUTPUT_ROOT}/stage_c2_${TIMESTAMP}_${SHORT_REVISION}"
mkdir -p "${PRESTAGED_ROOT}" "${PBS_OUTPUT_DIR}" "${PROJECT_HOME}/runs/hpc/stage_c2"

git archive "${REVISION}" -- "${REQUIRED_PATHS[@]}" | tar -x -C "${PRESTAGED_ROOT}"
printf '%s\n' "${REVISION}" > "${PRESTAGED_ROOT}/PROJECT_REVISION.txt"

{
  echo "revision=${REVISION}"
  echo "timestamp=${TIMESTAMP}"
  echo "preferred_queue=${QUEUE}"
  echo "prestaged_root=${PRESTAGED_ROOT}"
  echo "chain=C2A-C2F"
  echo "sha256:"
  (cd "${PRESTAGED_ROOT}" && find . -type f -print0 | sort -z | xargs -0 sha256sum)
} > "${PRESTAGED_ROOT}/STAGING_MANIFEST.txt"

(cd "${PRESTAGED_ROOT}/models/generated/molnar_gravouil_2017/aux_continuum/H0_aux_miseseri" && sha256sum -c input_hashes.sha256)
(cd "${PRESTAGED_ROOT}/models/generated/molnar_gravouil_2017/h_convergence_lc015/H0_exact" && sha256sum -c input_hashes.sha256)
bash -n "${PRESTAGED_ROOT}/${STAGE_DIR}/01_aux_continuum_miseseri.pbs"
bash -n "${PRESTAGED_ROOT}/${STAGE_DIR}/02_gate_remesh_export.pbs"
bash -n "${PRESTAGED_ROOT}/${STAGE_DIR}/03_rebuild_validate.pbs"
bash -n "${PRESTAGED_ROOT}/${STAGE_DIR}/04_h0_threads4_qualification.pbs"
bash -n "${PRESTAGED_ROOT}/${STAGE_DIR}/05_refined_integrity_threads4.pbs"
bash -n "${PRESTAGED_ROOT}/${STAGE_DIR}/06_refined_final_threads4.pbs"
python3 scripts/hpc/validate_pbs_email_notifications.py --email "${EMAIL}" \
  "${STAGE_DIR}/01_aux_continuum_miseseri.pbs" \
  "${STAGE_DIR}/02_gate_remesh_export.pbs" \
  "${STAGE_DIR}/03_rebuild_validate.pbs" \
  "${STAGE_DIR}/04_h0_threads4_qualification.pbs" \
  "${STAGE_DIR}/05_refined_integrity_threads4.pbs" \
  "${STAGE_DIR}/06_refined_final_threads4.pbs"

export PROJECT_REVISION="${REVISION}" PRESTAGED_ROOT="${PRESTAGED_ROOT}"

# Submit from prestaged tree so PBS scripts resolve relative paths consistently
cd "${PRESTAGED_ROOT}"

J1=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}" \
  -o "${PBS_OUTPUT_DIR}/c2a.out" \
  "${STAGE_DIR}/01_aux_continuum_miseseri.pbs")

J2=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -W depend=afterok:"${J1}" \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}" \
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
  echo "preferred_queue=${QUEUE}"
  echo "prestaged_root=${PRESTAGED_ROOT}"
  echo "pbs_output_dir=${PBS_OUTPUT_DIR}"
  echo "C2A=${J1}"
  echo "C2B=${J2}"
  echo "C2C=${J3}"
  echo "C2D=${J4}"
  echo "C2E=${J5}"
  echo "C2F=${J6}"
  echo "note=do_not_use_inactive_job2_odb"
  echo "mpi_uel_prohibited=true"
  echo "threads4_uel_after_c2d=true"
} | tee "${PROJECT_HOME}/runs/hpc/stage_c2/C2_CHAIN_SUBMISSION_RECORD.txt" \
  | tee "${PRESTAGED_ROOT}/SUBMISSION_RECORD.txt"

printf '%s\n' "C2A=$J1" "C2B=$J2" "C2C=$J3" "C2D=$J4" "C2E=$J5" "C2F=$J6"
qstat -u "${USER}" | head -20 || true
