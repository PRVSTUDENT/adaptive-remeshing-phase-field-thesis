#!/bin/bash
set -euo pipefail

PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
PRESTAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/prestage"
PBS_OUTPUT_ROOT="/scratch/pr21vyci/adaptive-remeshing/pbs_output"
EMAIL="pr21vyci@mailserver.tu-freiberg.de"

PBS_H0="scripts/hpc/molnar_lc015_h0_exact.pbs"
PBS_H1="scripts/hpc/molnar_lc015_h1_h0025.pbs"
PBS_H2="scripts/hpc/molnar_lc015_h2_pub_h0010.pbs"

REQUIRED_PATHS=(
  "models/generated/molnar_gravouil_2017/h_convergence_lc015"
  "scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py"
  "scripts/hpc/molnar_lc015_h0_exact.pbs"
  "scripts/hpc/molnar_lc015_h1_h0025.pbs"
  "scripts/hpc/molnar_lc015_h2_pub_h0010.pbs"
  "runs/hpc/molnar_lc015_h_convergence"
)

cd "${PROJECT_HOME}"

if [ -n "$(git status --short --untracked-files=no)" ]; then
  echo "tracked_working_tree_not_clean" >&2
  git status --short --untracked-files=no >&2
  exit 2
fi

# No duplicate active h-convergence jobs
if qstat -u "${USER}" 2>/dev/null | grep -E 'molnar_h0_exact|molnar_h1_h0025|molnar_h2_pub_h001' >/dev/null 2>&1; then
  echo "duplicate_h_convergence_jobs_active" >&2
  qstat -u "${USER}" >&2 || true
  exit 3
fi

# Storage check (scratch free space)
df -h /scratch/pr21vyci | tee /tmp/hconv_df_scratch.txt >/dev/null
df -h /home/pr21vyci | tee /tmp/hconv_df_home.txt >/dev/null

REVISION="$(git rev-parse HEAD)"
SHORT_REVISION="${REVISION:0:12}"
TIMESTAMP="$(date +%Y%m%dT%H%M%S%z)"
PRESTAGED_ROOT="${PRESTAGE_ROOT}/molnar_lc015_h_convergence_${TIMESTAMP}_${SHORT_REVISION}"
PBS_OUTPUT_DIR="${PBS_OUTPUT_ROOT}/molnar_lc015_h_convergence_${TIMESTAMP}_${SHORT_REVISION}"
mkdir -p "${PRESTAGED_ROOT}" "${PBS_OUTPUT_DIR}"
mkdir -p \
  "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/H0_exact/evidence" \
  "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/H1_h0025/evidence" \
  "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/H2_pub_h0010/evidence"

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

(cd "${PRESTAGED_ROOT}/models/generated/molnar_gravouil_2017/h_convergence_lc015/H0_exact" && sha256sum -c input_hashes.sha256)
(cd "${PRESTAGED_ROOT}/models/generated/molnar_gravouil_2017/h_convergence_lc015/H1_h0025" && sha256sum -c input_hashes.sha256)
(cd "${PRESTAGED_ROOT}/models/generated/molnar_gravouil_2017/h_convergence_lc015/H2_pub_h0010" && sha256sum -c input_hashes.sha256)
test "$(tr -d '[:space:]' < "${PRESTAGED_ROOT}/PROJECT_REVISION.txt")" = "${REVISION}"

bash -n "${PRESTAGED_ROOT}/${PBS_H0}"
bash -n "${PRESTAGED_ROOT}/${PBS_H1}"
bash -n "${PRESTAGED_ROOT}/${PBS_H2}"
bash -n "${PROJECT_HOME}/scripts/hpc/submit_molnar_lc015_h_convergence.sh"
python3 scripts/hpc/validate_pbs_email_notifications.py --email "${EMAIL}" \
  "${PBS_H0}" "${PBS_H1}" "${PBS_H2}"

# No git in PBS scripts
if grep -nE '(^|[^A-Za-z_])git([^A-Za-z_]|$)' "${PBS_H0}" "${PBS_H1}" "${PBS_H2}" >/dev/null 2>&1; then
  echo "git_found_in_pbs" >&2
  grep -nE '(^|[^A-Za-z_])git([^A-Za-z_]|$)' "${PBS_H0}" "${PBS_H1}" "${PBS_H2}" >&2 || true
  exit 4
fi

PBS_OUTPUT_H0="${PBS_OUTPUT_DIR}/molnar_h0_exact.out"
PBS_OUTPUT_H1="${PBS_OUTPUT_DIR}/molnar_h1_h0025.out"
PBS_OUTPUT_H2="${PBS_OUTPUT_DIR}/molnar_h2_pub_h0010.out"

J0=$(qsub \
  -M "${EMAIL}" \
  -m abe \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}" \
  -o "${PBS_OUTPUT_H0}" \
  "${PBS_H0}")

J1=$(qsub \
  -W depend=afterok:"${J0}" \
  -M "${EMAIL}" \
  -m abe \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}" \
  -o "${PBS_OUTPUT_H1}" \
  "${PBS_H1}")

J2=$(qsub \
  -W depend=afterok:"${J1}" \
  -M "${EMAIL}" \
  -m abe \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}" \
  -o "${PBS_OUTPUT_H2}" \
  "${PBS_H2}")

{
  echo "submission_time=${TIMESTAMP}"
  echo "revision=${REVISION}"
  echo "prestaged_root=${PRESTAGED_ROOT}"
  echo "pbs_output_dir=${PBS_OUTPUT_DIR}"
  echo "job_H0=${J0}"
  echo "job_H1=${J1}"
  echo "job_H2=${J2}"
  echo "dependency=H0->H1->H2 afterok"
} | tee "${PRESTAGED_ROOT}/SUBMISSION_RECORD.txt"

mkdir -p "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence"
cp "${PRESTAGED_ROOT}/SUBMISSION_RECORD.txt" \
  "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/SUBMISSION_RECORD.txt"

qstat -f "${J0}" | tee "${PRESTAGED_ROOT}/QSTAT_H0_INITIAL.txt"
qstat -f "${J1}" | tee "${PRESTAGED_ROOT}/QSTAT_H1_INITIAL.txt"
qstat -f "${J2}" | tee "${PRESTAGED_ROOT}/QSTAT_H2_INITIAL.txt"

cp "${PRESTAGED_ROOT}/QSTAT_H0_INITIAL.txt" "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/H0_exact/"
cp "${PRESTAGED_ROOT}/QSTAT_H1_INITIAL.txt" "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/H1_h0025/"
cp "${PRESTAGED_ROOT}/QSTAT_H2_INITIAL.txt" "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/H2_pub_h0010/"

echo "SUBMITTED H0=${J0} H1=${J1} H2=${J2}"
