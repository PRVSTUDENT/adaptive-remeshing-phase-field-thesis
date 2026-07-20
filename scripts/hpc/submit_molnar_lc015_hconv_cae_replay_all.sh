#!/bin/bash
# Login-side wrapper for the single authorized consolidated CAE-only replay.
# DO NOT run until H1 and H2-PUB have left the active queue and the eligibility
# manifest has been rebuilt from final solver evidence.
set -euo pipefail

PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
PRESTAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/prestage"
PBS_OUTPUT_ROOT="/scratch/pr21vyci/adaptive-remeshing/pbs_output"
EMAIL="pr21vyci@mailserver.tu-freiberg.de"
PBS_SCRIPT="scripts/hpc/molnar_lc015_hconv_cae_replay_all.pbs"
MANIFEST_JSON="runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154/CAE_REPLAY_ELIGIBILITY_MANIFEST.json"
MANIFEST_LIST="runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154/CAE_REPLAY_ELIGIBILITY_MANIFEST_eligible_cases.txt"

REQUIRED_PATHS=(
  "scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py"
  "scripts/hpc/molnar_lc015_hconv_cae_replay_all.pbs"
  "scripts/hpc/build_molnar_hconv_cae_replay_manifest.py"
  "runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154"
)

cd "${PROJECT_HOME}"

if [ -n "$(git status --short --untracked-files=no)" ]; then
  echo "tracked_working_tree_not_clean" >&2
  git status --short --untracked-files=no >&2
  exit 2
fi

# Refuse while H1/H2 solver jobs still active
if qstat -u "${USER}" 2>/dev/null | grep -E 'molnar_h1_h0025|molnar_h2_pub_h001' >/dev/null 2>&1; then
  echo "h1_or_h2_still_active_refuse_cae_replay_submit" >&2
  qstat -u "${USER}" >&2 || true
  exit 3
fi

if qstat -u "${USER}" 2>/dev/null | grep -E 'molnar_hconv_cae_all' >/dev/null 2>&1; then
  echo "duplicate_consolidated_cae_job_active" >&2
  exit 4
fi

# Rebuild eligibility from current evidence
python3 scripts/hpc/build_molnar_hconv_cae_replay_manifest.py "${MANIFEST_JSON}"
if [ ! -s "${MANIFEST_LIST}" ]; then
  echo "no_eligible_cases_for_cae_replay" >&2
  cat "${MANIFEST_JSON}" >&2 || true
  exit 5
fi

echo "Eligible cases:"
cat "${MANIFEST_LIST}"

REVISION="$(git rev-parse HEAD)"
SHORT_REVISION="${REVISION:0:12}"
TIMESTAMP="$(date +%Y%m%dT%H%M%S%z)"
PRESTAGED_ROOT="${PRESTAGE_ROOT}/molnar_hconv_cae_all_${TIMESTAMP}_${SHORT_REVISION}"
PBS_OUTPUT_DIR="${PBS_OUTPUT_ROOT}/molnar_hconv_cae_all_${TIMESTAMP}_${SHORT_REVISION}"
mkdir -p "${PRESTAGED_ROOT}" "${PBS_OUTPUT_DIR}"
mkdir -p "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154/cae_replay_all/evidence"

# Ensure latest manifest is committed path content for archive
git archive "${REVISION}" -- "${REQUIRED_PATHS[@]}" | tar -x -C "${PRESTAGED_ROOT}"
# Overlay freshly built eligibility files into prestaged tree
mkdir -p "${PRESTAGED_ROOT}/runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154"
cp "${MANIFEST_JSON}" "${MANIFEST_LIST}" \
  "${PRESTAGED_ROOT}/runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154/"

printf '%s\n' "${REVISION}" > "${PRESTAGED_ROOT}/PROJECT_REVISION.txt"
{
  echo "revision=${REVISION}"
  echo "timestamp=${TIMESTAMP}"
  echo "purpose=consolidated_cae_only_replay"
  echo "abaqus_standard_solves=0"
  echo "eligible_list:"
  cat "${MANIFEST_LIST}"
  echo "sha256:"
  (cd "${PRESTAGED_ROOT}" && find . -type f -print0 | sort -z | xargs -0 sha256sum)
} > "${PRESTAGED_ROOT}/STAGING_MANIFEST.txt"

bash -n "${PRESTAGED_ROOT}/${PBS_SCRIPT}"
python3 scripts/hpc/validate_pbs_email_notifications.py --email "${EMAIL}" "${PBS_SCRIPT}"
if grep -nE '(^|[^A-Za-z_])git([^A-Za-z_]|$)' "${PBS_SCRIPT}" >/dev/null 2>&1; then
  echo "git_found_in_pbs" >&2
  exit 6
fi

# Require env-var path style in prestaged CAE script
if grep -n 'sys.argv' "${PRESTAGED_ROOT}/scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py" | grep -v 'repr(sys.argv)' | grep -v '^#' >/dev/null 2>&1; then
  # allow logging only
  :
fi
grep -q 'MOLNAR_ODB_PATH' "${PRESTAGED_ROOT}/scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py"
grep -q 'MOLNAR_CASE_ID' "${PRESTAGED_ROOT}/scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py"
grep -q 'MOLNAR_OUTPUT_DIR' "${PRESTAGED_ROOT}/scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py"

JOB_ID=$(qsub \
  -M "${EMAIL}" \
  -m abe \
  -v PROJECT_REVISION="${REVISION}",PRESTAGED_ROOT="${PRESTAGED_ROOT}" \
  -o "${PBS_OUTPUT_DIR}/molnar_hconv_cae_all.out" \
  "${PBS_SCRIPT}")

{
  echo "submission_time=${TIMESTAMP}"
  echo "revision=${REVISION}"
  echo "prestaged_root=${PRESTAGED_ROOT}"
  echo "pbs_output_dir=${PBS_OUTPUT_DIR}"
  echo "job_id=${JOB_ID}"
  echo "eligible_cases_file=${MANIFEST_LIST}"
} | tee "${PRESTAGED_ROOT}/SUBMISSION_RECORD.txt"

cp "${PRESTAGED_ROOT}/SUBMISSION_RECORD.txt" \
  "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154/cae_replay_all/SUBMISSION_RECORD.txt"
qstat -f "${JOB_ID}" | tee "${PRESTAGED_ROOT}/QSTAT_INITIAL.txt"
cp "${PRESTAGED_ROOT}/QSTAT_INITIAL.txt" \
  "${PROJECT_HOME}/runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154/cae_replay_all/"
echo "SUBMITTED consolidated_cae_only=${JOB_ID}"
