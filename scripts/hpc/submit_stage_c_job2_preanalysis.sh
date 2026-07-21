#!/bin/bash
# Submit Stage C Job 2 (H0 elastic pre-analysis) exactly once.
# Preferred queue: entry_imfdfkmq (route; do not hard-code normal for this job).
set -euo pipefail

PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
PRESTAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/prestage"
PBS_OUTPUT_ROOT="/scratch/pr21vyci/adaptive-remeshing/pbs_output"
EMAIL="pr21vyci@mailserver.tu-freiberg.de"
PBS_SCRIPT="scripts/hpc/molnar_h0_miseseri_preanalysis.pbs"
JOB_LABEL="molnar_h0_miseseri_preanalysis"
PREFERRED_QUEUE="entry_imfdfkmq"

REQUIRED_PATHS=(
  "models/generated/molnar_gravouil_2017/unified_preprocessing/H0_fullgen_elastic_preanalysis"
  "configs/remeshing/miseseri_h0_to_h1_initial.json"
  "configs/preprocessing/molnar_h0_h1_unified.yaml"
  "scripts/hpc/molnar_h0_miseseri_preanalysis.pbs"
  "scripts/hpc/validate_pbs_email_notifications.py"
  "runs/hpc/stage_c_miseseri"
)

cd "${PROJECT_HOME}"

if [ -n "$(git status --short --untracked-files=no)" ]; then
  echo "tracked_working_tree_not_clean" >&2
  git status --short --untracked-files=no >&2
  exit 2
fi

if [ ! -f "runs/hpc/stage_c_miseseri/JOB1_GATE_REPORT.md" ] && [ ! -f "runs/hpc/stage_c_miseseri/JOB1_SUBMISSION_RECORD.txt" ]; then
  echo "job1_evidence_missing" >&2
  exit 5
fi

if [ -f "runs/hpc/stage_c_miseseri/JOB2_SUBMISSION_RECORD.txt" ]; then
  echo "job2_already_submitted_see_JOB2_SUBMISSION_RECORD.txt" >&2
  exit 4
fi

if qstat -u "${USER}" 2>/dev/null | grep -E 'molnar_h0_miseseri_pre' >/dev/null 2>&1; then
  echo "duplicate_job2_active" >&2
  qstat -u "${USER}" >&2 || true
  exit 3
fi

# Live queue check (entry route)
echo "=== preferred queue status: ${PREFERRED_QUEUE} ==="
qstat -Qf "${PREFERRED_QUEUE}" | egrep -i 'enabled|started|resources_max|state_count|Queue:' || true
echo "=== qstat -q (imfd/kfm excerpt) ==="
qstat -q | egrep 'entry_imfdfkmq|normal_imfdfkmq|short_imfdfkmq' || qstat -q | head -40

REVISION="$(git rev-parse HEAD)"
SHORT_REVISION="${REVISION:0:12}"
TIMESTAMP="$(date +%Y%m%dT%H%M%S%z)"
PRESTAGED_ROOT="${PRESTAGE_ROOT}/stage_c_job2_${TIMESTAMP}_${SHORT_REVISION}"
PBS_OUTPUT_DIR="${PBS_OUTPUT_ROOT}/stage_c_job2_${TIMESTAMP}_${SHORT_REVISION}"
mkdir -p "${PRESTAGED_ROOT}" "${PBS_OUTPUT_DIR}"
mkdir -p "${PROJECT_HOME}/runs/hpc/stage_c_miseseri/molnar_h0_miseseri_preanalysis/evidence"

git archive "${REVISION}" -- "${REQUIRED_PATHS[@]}" | tar -x -C "${PRESTAGED_ROOT}"
printf '%s\n' "${REVISION}" > "${PRESTAGED_ROOT}/PROJECT_REVISION.txt"

{
  echo "revision=${REVISION}"
  echo "timestamp=${TIMESTAMP}"
  echo "job=${JOB_LABEL}"
  echo "preferred_queue=${PREFERRED_QUEUE}"
  echo "resources=1cpu_16gb_02h"
  echo "u_pre_mm=0.00464"
  echo "prestaged_root=${PRESTAGED_ROOT}"
  echo "paths:"
  for path in "${REQUIRED_PATHS[@]}"; do
    echo "  ${path}"
  done
  echo "sha256:"
  (cd "${PRESTAGED_ROOT}" && find . -type f -print0 | sort -z | xargs -0 sha256sum)
} > "${PRESTAGED_ROOT}/STAGING_MANIFEST.txt"

(cd "${PRESTAGED_ROOT}/models/generated/molnar_gravouil_2017/unified_preprocessing/H0_fullgen_elastic_preanalysis" && sha256sum -c input_hashes.sha256)
test "$(tr -d '[:space:]' < "${PRESTAGED_ROOT}/PROJECT_REVISION.txt")" = "${REVISION}"
bash -n "${PRESTAGED_ROOT}/${PBS_SCRIPT}"
python3 scripts/hpc/validate_pbs_email_notifications.py --email "${EMAIL}" "${PBS_SCRIPT}"

# Explicit -q entry_imfdfkmq; do not default to normal for this small pre-analysis job.
JOB_ID="$(qsub \
  -q "${PREFERRED_QUEUE}" \
  -M "${EMAIL}" \
  -m abe \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}" \
  -o "${PBS_OUTPUT_DIR}/molnar_h0_miseseri_preanalysis.out" \
  "${PBS_SCRIPT}")"

{
  echo "submission_time=${TIMESTAMP}"
  echo "revision=${REVISION}"
  echo "preferred_queue=${PREFERRED_QUEUE}"
  echo "prestaged_root=${PRESTAGED_ROOT}"
  echo "pbs_output_dir=${PBS_OUTPUT_DIR}"
  echo "job_id=${JOB_ID}"
  echo "job_label=${JOB_LABEL}"
  echo "u_pre_mm=0.00464"
  echo "authorization=stage_c_five_job_campaign_user_message"
  echo "job1_predecessor=1376292.mmaster02"
} | tee "${PRESTAGED_ROOT}/SUBMISSION_RECORD.txt" \
  | tee "runs/hpc/stage_c_miseseri/JOB2_SUBMISSION_RECORD.txt"

qstat -f "${JOB_ID}" | tee "${PRESTAGED_ROOT}/QSTAT_INITIAL.txt" \
  | tee "runs/hpc/stage_c_miseseri/JOB2_QSTAT_INITIAL.txt"
