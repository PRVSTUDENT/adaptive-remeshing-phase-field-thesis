#!/bin/bash
set -euo pipefail

PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
PRESTAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/prestage"
PBS_OUTPUT_ROOT="/scratch/pr21vyci/adaptive-remeshing/pbs_output"
EMAIL="pr21vyci@mailserver.tu-freiberg.de"
PBS_SCRIPT="scripts/hpc/molnar_paper_matched_single_notch_v2_sdv15_diagnostic_r2.pbs"

REQUIRED_PATHS=(
  "models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2_sdv15_diagnostic"
  "scripts/postprocessing/analyze_molnar_sdv15_targeted_diagnostic.py"
  "scripts/hpc/molnar_paper_matched_single_notch_v2_sdv15_diagnostic_r2.pbs"
  "runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv15_mapping_resolution/sdv15_unresolved_event_mapping.csv"
  "runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv15_detailed_review/sdv15_equivalent_state_comparison.csv"
  "runs/hpc/paper_matched_single_notch_v2/scientific_review/rf_u_verified.csv"
  "runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/RUN_MANIFEST.md"
)

cd "${PROJECT_HOME}"

if [ -n "$(git status --short --untracked-files=no)" ]; then
  echo "tracked_working_tree_not_clean" >&2
  git status --short --untracked-files=no >&2
  exit 2
fi

REVISION="$(git rev-parse HEAD)"
SHORT_REVISION="${REVISION:0:12}"
TIMESTAMP="$(date +%Y%m%dT%H%M%S%z)"
PRESTAGED_ROOT="${PRESTAGE_ROOT}/molnar_v2_sdv15_diag_r2_${TIMESTAMP}_${SHORT_REVISION}"
PBS_OUTPUT_DIR="${PBS_OUTPUT_ROOT}/molnar_v2_sdv15_diag_r2_${TIMESTAMP}_${SHORT_REVISION}"
mkdir -p "${PRESTAGED_ROOT}" "${PBS_OUTPUT_DIR}"

git archive "${REVISION}" -- "${REQUIRED_PATHS[@]}" | tar -x -C "${PRESTAGED_ROOT}"
printf '%s\n' "${REVISION}" > "${PRESTAGED_ROOT}/PROJECT_REVISION.txt"

{
  echo "revision=${REVISION}"
  echo "timestamp=${TIMESTAMP}"
  echo "source_repository=${PROJECT_HOME}"
  echo "prestaged_root=${PRESTAGED_ROOT}"
  echo "submission_user=$(id -un)"
  echo "submission_host=$(hostname)"
  echo "paths:"
  for path in "${REQUIRED_PATHS[@]}"; do
    echo "  ${path}"
  done
  echo "sha256:"
  (cd "${PRESTAGED_ROOT}" && find . -type f -print0 | sort -z | xargs -0 sha256sum)
} > "${PRESTAGED_ROOT}/STAGING_MANIFEST.txt"

(cd "${PRESTAGED_ROOT}" && sha256sum -c models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2_sdv15_diagnostic/input_hashes.sha256)
test "$(tr -d '[:space:]' < "${PRESTAGED_ROOT}/PROJECT_REVISION.txt")" = "${REVISION}"
bash -n "${PRESTAGED_ROOT}/${PBS_SCRIPT}"
python3 scripts/hpc/validate_pbs_email_notifications.py --email "${EMAIL}" "${PBS_SCRIPT}"

JOB_ID="$(qsub \
  -M "${EMAIL}" \
  -m abe \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}" \
  -o "${PBS_OUTPUT_DIR}/molnar_v2_sdv15_diag_r2.out" \
  "${PBS_SCRIPT}")"

{
  echo "submission_time=${TIMESTAMP}"
  echo "revision=${REVISION}"
  echo "prestaged_root=${PRESTAGED_ROOT}"
  echo "pbs_output_dir=${PBS_OUTPUT_DIR}"
  echo "job_id=${JOB_ID}"
} | tee "${PRESTAGED_ROOT}/SUBMISSION_RECORD.txt"

qstat -f "${JOB_ID}" | tee "${PRESTAGED_ROOT}/QSTAT_INITIAL.txt"
