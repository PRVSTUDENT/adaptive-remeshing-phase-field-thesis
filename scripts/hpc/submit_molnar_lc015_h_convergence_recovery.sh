#!/bin/bash
set -euo pipefail

PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
PRESTAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/prestage"
PBS_OUTPUT_ROOT="/scratch/pr21vyci/adaptive-remeshing/pbs_output"
EMAIL="pr21vyci@mailserver.tu-freiberg.de"
SCI_INPUT_REV="58d7e3102d76fe0e70e6729457e2c7e90ad131bb"
EXISTING_ODB="/scratch/pr21vyci/adaptive-remeshing/runs/molnar_lc015_h0_exact_1376154.mmaster02/molnar_lc015_h0_exact.odb"

PBS_H0="scripts/hpc/molnar_lc015_h0_cae_replay.pbs"
PBS_H1="scripts/hpc/molnar_lc015_h1_h0025.pbs"
PBS_H2="scripts/hpc/molnar_lc015_h2_pub_h0010.pbs"

REQUIRED_PATHS=(
  "models/generated/molnar_gravouil_2017/h_convergence_lc015"
  "scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py"
  "scripts/hpc/molnar_lc015_h0_cae_replay.pbs"
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

if qstat -u "${USER}" 2>/dev/null | grep -E 'molnar_h0_cae_replay|molnar_h1_h0025|molnar_h2_pub_h001' >/dev/null 2>&1; then
  echo "duplicate_h_convergence_recovery_jobs_active" >&2
  qstat -u "${USER}" >&2 || true
  exit 3
fi

if [ ! -f "${EXISTING_ODB}" ]; then
  echo "existing_h0_odb_missing: ${EXISTING_ODB}" >&2
  exit 4
fi

REVISION="$(git rev-parse HEAD)"
SHORT_REVISION="${REVISION:0:12}"
TIMESTAMP="$(date +%Y%m%dT%H%M%S%z)"
PRESTAGED_ROOT="${PRESTAGE_ROOT}/molnar_lc015_hconv_recovery_${TIMESTAMP}_${SHORT_REVISION}"
PBS_OUTPUT_DIR="${PBS_OUTPUT_ROOT}/molnar_lc015_hconv_recovery_${TIMESTAMP}_${SHORT_REVISION}"
mkdir -p "${PRESTAGED_ROOT}" "${PBS_OUTPUT_DIR}"
mkdir -p \
  "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154/H0_cae_replay/evidence" \
  "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/H1_h0025/evidence" \
  "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/H2_pub_h0010/evidence"

git archive "${REVISION}" -- "${REQUIRED_PATHS[@]}" | tar -x -C "${PRESTAGED_ROOT}"
printf '%s\n' "${REVISION}" > "${PRESTAGED_ROOT}/PROJECT_REVISION.txt"
{
  echo "infrastructure_revision=${REVISION}"
  echo "scientific_input_revision=${SCI_INPUT_REV}"
  echo "existing_h0_odb=${EXISTING_ODB}"
} > "${PRESTAGED_ROOT}/REVISION_IDENTITY.txt"

{
  echo "revision=${REVISION}"
  echo "scientific_input_revision=${SCI_INPUT_REV}"
  echo "timestamp=${TIMESTAMP}"
  echo "source_repository=${PROJECT_HOME}"
  echo "prestaged_root=${PRESTAGED_ROOT}"
  echo "existing_h0_odb=${EXISTING_ODB}"
  echo "submission_user=$(id -un)"
  echo "submission_host=$(hostname)"
  echo "sha256:"
  (cd "${PRESTAGED_ROOT}" && find . -type f -print0 | sort -z | xargs -0 sha256sum)
} > "${PRESTAGED_ROOT}/STAGING_MANIFEST.txt"

# Scientific input hashes must match original study inputs
(cd "${PRESTAGED_ROOT}/models/generated/molnar_gravouil_2017/h_convergence_lc015/H1_h0025" && sha256sum -c input_hashes.sha256)
(cd "${PRESTAGED_ROOT}/models/generated/molnar_gravouil_2017/h_convergence_lc015/H2_pub_h0010" && sha256sum -c input_hashes.sha256)

# Compare to committed 58d7e31 hashes if available
if git cat-file -e "${SCI_INPUT_REV}:models/generated/molnar_gravouil_2017/h_convergence_lc015/H1_h0025/input_hashes.sha256" 2>/dev/null; then
  git show "${SCI_INPUT_REV}:models/generated/molnar_gravouil_2017/h_convergence_lc015/H1_h0025/input_hashes.sha256" > /tmp/h1_hashes_58d7e31.txt
  git show "${SCI_INPUT_REV}:models/generated/molnar_gravouil_2017/h_convergence_lc015/H2_pub_h0010/input_hashes.sha256" > /tmp/h2_hashes_58d7e31.txt
  diff -u /tmp/h1_hashes_58d7e31.txt "${PRESTAGED_ROOT}/models/generated/molnar_gravouil_2017/h_convergence_lc015/H1_h0025/input_hashes.sha256"
  diff -u /tmp/h2_hashes_58d7e31.txt "${PRESTAGED_ROOT}/models/generated/molnar_gravouil_2017/h_convergence_lc015/H2_pub_h0010/input_hashes.sha256"
fi

test "$(tr -d '[:space:]' < "${PRESTAGED_ROOT}/PROJECT_REVISION.txt")" = "${REVISION}"
bash -n "${PRESTAGED_ROOT}/${PBS_H0}"
bash -n "${PRESTAGED_ROOT}/${PBS_H1}"
bash -n "${PRESTAGED_ROOT}/${PBS_H2}"
bash -n "${PROJECT_HOME}/scripts/hpc/submit_molnar_lc015_h_convergence_recovery.sh"
python3 scripts/hpc/validate_pbs_email_notifications.py --email "${EMAIL}" \
  "${PBS_H0}" "${PBS_H1}" "${PBS_H2}"

if grep -nE '(^|[^A-Za-z_])git([^A-Za-z_]|$)' "${PBS_H0}" "${PBS_H1}" "${PBS_H2}" >/dev/null 2>&1; then
  echo "git_found_in_pbs" >&2
  grep -nE '(^|[^A-Za-z_])git([^A-Za-z_]|$)' "${PBS_H0}" "${PBS_H1}" "${PBS_H2}" >&2 || true
  exit 5
fi

# ODB size check
ls -la "${EXISTING_ODB}" | tee "${PRESTAGED_ROOT}/EXISTING_H0_ODB.txt"
sha256sum "${EXISTING_ODB}" | tee -a "${PRESTAGED_ROOT}/EXISTING_H0_ODB.txt"

PBS_OUTPUT_H0="${PBS_OUTPUT_DIR}/molnar_h0_cae_replay.out"
PBS_OUTPUT_H1="${PBS_OUTPUT_DIR}/molnar_h1_h0025.out"
PBS_OUTPUT_H2="${PBS_OUTPUT_DIR}/molnar_h2_pub_h0010.out"

# Independent H0 CAE replay
P0=$(qsub \
  -M "${EMAIL}" \
  -m abe \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}" \
  -o "${PBS_OUTPUT_H0}" \
  "${PBS_H0}")

# H1 is solver-chain head (no dependency on P0)
J1=$(qsub \
  -M "${EMAIL}" \
  -m abe \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}" \
  -o "${PBS_OUTPUT_H1}" \
  "${PBS_H1}")

# H2 depends only on H1 solver-dependency success (PBS exit 0)
J2=$(qsub \
  -W depend=afterok:"${J1}" \
  -M "${EMAIL}" \
  -m abe \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}" \
  -o "${PBS_OUTPUT_H2}" \
  "${PBS_H2}")

{
  echo "submission_time=${TIMESTAMP}"
  echo "infrastructure_revision=${REVISION}"
  echo "scientific_input_revision=${SCI_INPUT_REV}"
  echo "prestaged_root=${PRESTAGED_ROOT}"
  echo "pbs_output_dir=${PBS_OUTPUT_DIR}"
  echo "existing_h0_odb=${EXISTING_ODB}"
  echo "job_H0_CAE=${P0}"
  echo "job_H1=${J1}"
  echo "job_H2=${J2}"
  echo "dependency=H0_CAE independent; H1 head; H2 afterok H1"
  echo "old_H0=1376154.mmaster02"
  echo "old_H1=1376155.mmaster02"
  echo "old_H2=1376156.mmaster02"
} | tee "${PRESTAGED_ROOT}/SUBMISSION_RECORD.txt"

mkdir -p "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154"
cp "${PRESTAGED_ROOT}/SUBMISSION_RECORD.txt" \
  "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154/SUBMISSION_RECORD.txt"
cp "${PRESTAGED_ROOT}/EXISTING_H0_ODB.txt" \
  "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154/EXISTING_H0_ODB.txt" 2>/dev/null || true

qstat -f "${P0}" | tee "${PRESTAGED_ROOT}/QSTAT_H0_CAE_INITIAL.txt"
qstat -f "${J1}" | tee "${PRESTAGED_ROOT}/QSTAT_H1_INITIAL.txt"
qstat -f "${J2}" | tee "${PRESTAGED_ROOT}/QSTAT_H2_INITIAL.txt"

cp "${PRESTAGED_ROOT}/QSTAT_H0_CAE_INITIAL.txt" \
  "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154/"
cp "${PRESTAGED_ROOT}/QSTAT_H1_INITIAL.txt" \
  "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154/"
cp "${PRESTAGED_ROOT}/QSTAT_H2_INITIAL.txt" \
  "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154/"

echo "SUBMITTED H0_CAE=${P0} H1=${J1} H2=${J2}"
