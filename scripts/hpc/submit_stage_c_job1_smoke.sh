#!/bin/bash
# Submit Stage C Job 1 (MISESERI smoke) exactly once.
# Prestages immutable snapshot; never retries.
set -euo pipefail

PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
PRESTAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/prestage"
PBS_OUTPUT_ROOT="/scratch/pr21vyci/adaptive-remeshing/pbs_output"
EMAIL="pr21vyci@mailserver.tu-freiberg.de"
PBS_SCRIPT="scripts/hpc/molnar_h0_miseseri_smoke.pbs"
JOB_LABEL="molnar_h0_miseseri_smoke"

REQUIRED_PATHS=(
  "models/generated/molnar_gravouil_2017/unified_preprocessing/H0_fullgen_elastic_preanalysis_smoke"
  "configs/remeshing/miseseri_h0_to_h1_initial.json"
  "configs/preprocessing/molnar_h0_h1_unified.yaml"
  "scripts/hpc/molnar_h0_miseseri_smoke.pbs"
  "scripts/hpc/validate_pbs_email_notifications.py"
  "runs/hpc/stage_c_miseseri"
)

cd "${PROJECT_HOME}"

if [ -n "$(git status --short --untracked-files=no)" ]; then
  echo "tracked_working_tree_not_clean" >&2
  git status --short --untracked-files=no >&2
  exit 2
fi

if qstat -u "${USER}" 2>/dev/null | grep -E 'molnar_h0_miseseri_smoke|molnar_h0_miseseri_pre' >/dev/null 2>&1; then
  echo "duplicate_stage_c_job_active" >&2
  qstat -u "${USER}" >&2 || true
  exit 3
fi

# Refuse second Job 1 if evidence already exists for a pass
if [ -f "runs/hpc/stage_c_miseseri/JOB1_SUBMISSION_RECORD.txt" ]; then
  echo "job1_already_submitted_see_JOB1_SUBMISSION_RECORD.txt" >&2
  exit 4
fi

REVISION="$(git rev-parse HEAD)"
SHORT_REVISION="${REVISION:0:12}"
TIMESTAMP="$(date +%Y%m%dT%H%M%S%z)"
PRESTAGED_ROOT="${PRESTAGE_ROOT}/stage_c_job1_${TIMESTAMP}_${SHORT_REVISION}"
PBS_OUTPUT_DIR="${PBS_OUTPUT_ROOT}/stage_c_job1_${TIMESTAMP}_${SHORT_REVISION}"
mkdir -p "${PRESTAGED_ROOT}" "${PBS_OUTPUT_DIR}"
mkdir -p "${PROJECT_HOME}/runs/hpc/stage_c_miseseri/molnar_h0_miseseri_smoke/evidence"

git archive "${REVISION}" -- "${REQUIRED_PATHS[@]}" | tar -x -C "${PRESTAGED_ROOT}"
printf '%s\n' "${REVISION}" > "${PRESTAGED_ROOT}/PROJECT_REVISION.txt"

{
  echo "revision=${REVISION}"
  echo "timestamp=${TIMESTAMP}"
  echo "job=${JOB_LABEL}"
  echo "prestaged_root=${PRESTAGED_ROOT}"
  echo "paths:"
  for path in "${REQUIRED_PATHS[@]}"; do
    echo "  ${path}"
  done
  echo "sha256:"
  (cd "${PRESTAGED_ROOT}" && find . -type f -print0 | sort -z | xargs -0 sha256sum)
} > "${PRESTAGED_ROOT}/STAGING_MANIFEST.txt"

(cd "${PRESTAGED_ROOT}/models/generated/molnar_gravouil_2017/unified_preprocessing/H0_fullgen_elastic_preanalysis_smoke" && sha256sum -c input_hashes.sha256)
test "$(tr -d '[:space:]' < "${PRESTAGED_ROOT}/PROJECT_REVISION.txt")" = "${REVISION}"
bash -n "${PRESTAGED_ROOT}/${PBS_SCRIPT}"
python3 scripts/hpc/validate_pbs_email_notifications.py --email "${EMAIL}" "${PBS_SCRIPT}"

# Prefer entry_imfdfkmq route for small smoke jobs; never hard-code normal.
JOB_ID="$(qsub \
  -q entry_imfdfkmq \
  -M "${EMAIL}" \
  -m abe \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}" \
  -o "${PBS_OUTPUT_DIR}/molnar_h0_miseseri_smoke.out" \
  "${PBS_SCRIPT}")"

{
  echo "submission_time=${TIMESTAMP}"
  echo "revision=${REVISION}"
  echo "prestaged_root=${PRESTAGED_ROOT}"
  echo "pbs_output_dir=${PBS_OUTPUT_DIR}"
  echo "job_id=${JOB_ID}"
  echo "job_label=${JOB_LABEL}"
  echo "authorization=stage_c_five_job_campaign_user_message"
} | tee "${PRESTAGED_ROOT}/SUBMISSION_RECORD.txt" \
  | tee "runs/hpc/stage_c_miseseri/JOB1_SUBMISSION_RECORD.txt"

qstat -f "${JOB_ID}" | tee "${PRESTAGED_ROOT}/QSTAT_INITIAL.txt" \
  | tee "runs/hpc/stage_c_miseseri/JOB1_QSTAT_INITIAL.txt"
