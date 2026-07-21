#!/bin/bash
# Recovery: resubmit C2C–C2F only, reusing frozen successful C2B outputs.
# Uses afterany + explicit success markers (C2C.ok ... C2F.ok).
set -euo pipefail

PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
PRESTAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/prestage"
PBS_OUTPUT_ROOT="/scratch/pr21vyci/adaptive-remeshing/pbs_output"
EMAIL="${EMAIL:-Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de}"
QUEUE="entry_imfdfkmq"
STAGE_DIR="scripts/hpc/stage_c2"
CHAIN_STATE_DIR="${PROJECT_HOME}/runs/hpc/stage_c2/chain_state"
C2B_OUTPUT_DIR="${PROJECT_HOME}/runs/hpc/stage_c2/C2B_REFINED_MESH"

REQUIRED_PATHS=(
  "models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension"
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

if qstat -u "${USER}" 2>/dev/null | grep -E 'c2c_rebuild|c2d_h0|c2e_ref|c2f_ref' >/dev/null 2>&1; then
  echo "duplicate_c2_recovery_jobs_active" >&2
  qstat -u "${USER}" >&2 || true
  exit 3
fi

echo "=== verify frozen C2B products (no fabricated markers) ==="
# Linux automated verification + C2B.ok (never invent markers without checks)
bash "${PROJECT_HOME}/scripts/hpc/stage_c2/verify_c2b_and_write_marker.sh"
printf '%s\n' "${C2B_OUTPUT_DIR}" > "${PROJECT_HOME}/runs/hpc/stage_c2/C2B_REFINED_MESH_DIR.txt"

REVISION="$(git rev-parse HEAD)"
SHORT_REVISION="${REVISION:0:12}"
TIMESTAMP="$(date +%Y%m%dT%H%M%S%z)"
PRESTAGED_ROOT="${PRESTAGE_ROOT}/stage_c2c_${TIMESTAMP}_${SHORT_REVISION}"
PBS_OUTPUT_DIR="${PBS_OUTPUT_ROOT}/stage_c2c_${TIMESTAMP}_${SHORT_REVISION}"
mkdir -p "${PRESTAGED_ROOT}" "${PBS_OUTPUT_DIR}"

git archive "${REVISION}" -- "${REQUIRED_PATHS[@]}" | tar -x -C "${PRESTAGED_ROOT}"
printf '%s\n' "${REVISION}" > "${PRESTAGED_ROOT}/PROJECT_REVISION.txt"
# ensure baseline present in prestage (critical C2C fix)
test -f "${PRESTAGED_ROOT}/models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.inp"
test -f "${PRESTAGED_ROOT}/models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.for"

python3 scripts/hpc/validate_pbs_email_notifications.py --email "${EMAIL}" \
  "${STAGE_DIR}/03_rebuild_validate.pbs" \
  "${STAGE_DIR}/04_h0_threads4_qualification.pbs" \
  "${STAGE_DIR}/05_refined_integrity_threads4.pbs" \
  "${STAGE_DIR}/06_refined_final_threads4.pbs"

cd "${PRESTAGED_ROOT}"

COMMON_V="PROJECT_REVISION=${REVISION},PRESTAGED_ROOT=${PRESTAGED_ROOT},C2B_OUTPUT_DIR=${C2B_OUTPUT_DIR},CHAIN_STATE_DIR=${CHAIN_STATE_DIR}"

J3=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -v "${COMMON_V}" \
  -o "${PBS_OUTPUT_DIR}/c2c.out" \
  "${STAGE_DIR}/03_rebuild_validate.pbs")

J4=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -W depend=afterany:"${J3}" \
  -v "${COMMON_V}" \
  -o "${PBS_OUTPUT_DIR}/c2d.out" \
  "${STAGE_DIR}/04_h0_threads4_qualification.pbs")

J5=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -W depend=afterany:"${J4}" \
  -v "${COMMON_V}" \
  -o "${PBS_OUTPUT_DIR}/c2e.out" \
  "${STAGE_DIR}/05_refined_integrity_threads4.pbs")

J6=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -W depend=afterany:"${J5}" \
  -v "${COMMON_V}" \
  -o "${PBS_OUTPUT_DIR}/c2f.out" \
  "${STAGE_DIR}/06_refined_final_threads4.pbs")

mkdir -p "${PROJECT_HOME}/runs/hpc/stage_c2/recovery"
{
  echo "submission_time=${TIMESTAMP}"
  echo "revision=${REVISION}"
  echo "recovery_from=C2C"
  echo "C2A_reused=1376298.mmaster02"
  echo "C2B_reused=1376304.mmaster02"
  echo "C2A_rerun=false"
  echo "C2B_rerun=false"
  echo "C2B_OUTPUT_DIR=${C2B_OUTPUT_DIR}"
  echo "CHAIN_STATE_DIR=${CHAIN_STATE_DIR}"
  echo "PRESTAGED_ROOT=${PRESTAGED_ROOT}"
  echo "PBS_OUTPUT_DIR=${PBS_OUTPUT_DIR}"
  echo "dependency_mode=afterany_plus_markers"
  echo "queue=${QUEUE}"
  echo "mail=${EMAIL}"
  echo "mail_option=abe"
  echo "C2C=${J3}"
  echo "C2D=${J4}"
  echo "C2E=${J5}"
  echo "C2F=${J6}"
  echo "C2D_resources=select=1:ncpus=4:mem=16gb walltime=02:00:00 mp_mode=threads"
  echo "C2E_resources=select=1:ncpus=4:mem=24gb walltime=02:00:00 mp_mode=threads"
  echo "C2F_resources=select=1:ncpus=4:mem=32gb walltime=06:00:00 mp_mode=threads"
  echo "mpi_for_uel_umat=prohibited"
  echo "automatic_retry=false"
  echo "parameter_change=false"
  echo "c2c_prior_failure=1376305_missing_baseline_original_in_prestage"
  echo "c2b_verification_json=${PROJECT_HOME}/runs/hpc/stage_c2/recovery/C2B_REUSE_VERIFICATION.json"
} | tee "${PROJECT_HOME}/runs/hpc/stage_c2/recovery/C2_RECOVERY_SUBMISSION_RECORD.txt" \
  | tee "${PROJECT_HOME}/runs/hpc/stage_c2/C2_RECOVERY_FROM_C2C_SUBMISSION_RECORD.txt"

printf '%s\n' "C2C=$J3" "C2D=$J4" "C2E=$J5" "C2F=$J6"
qstat -u "${USER}" | head -20 || true
