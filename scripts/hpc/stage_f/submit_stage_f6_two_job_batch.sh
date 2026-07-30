#!/usr/bin/env bash
# Guarded Stage F6 two-job orchestrator. This is the only qsub call site.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${PROJECT_ROOT_OVERRIDE:-$(cd "${SCRIPT_DIR}/../../.." && pwd)}"
AUTH_FILE="${AUTH_FILE_OVERRIDE:-${REPO_ROOT}/runs/hpc/stage_f/f6_h2_full_and_miseseri_remesh_api_batch/BATCH_AUTHORIZATION.json}"
SCRATCH_ROOT="${SCRATCH_ROOT_OVERRIDE:-/scratch/pr21vyci/adaptive-remeshing/runs/stage_f6}"
SOURCE_ODB="/scratch/pr21vyci/adaptive-remeshing/runs/stage_f4/F4R1_20260730_065138_86ec6c79/miseseri_corrected/M2MISER1.odb"
EXPECTED_ODB_SHA="bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac"
EXPECTED_DECK_SHA="fdcd6ee1b1d6cbfb88d59a3edfb7f1c6b35cecde736a427f6b3030b0443b10bf"
EXPECTED_FOR_SHA="49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37"
EXPECTED_MIS_DECK_SHA="a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2"
QSUB_CMD="${QSUB_CMD:-qsub}"
MODE="${1:---preflight}"
[[ "${MODE}" == "--preflight" || "${MODE}" == "--execute" ]] || {
  echo "usage: $0 [--preflight|--execute]" >&2; exit 2;
}

SOURCE_REVISION="${SOURCE_REVISION_OVERRIDE:-$(git -C "${REPO_ROOT}" rev-parse HEAD)}"
git -C "${REPO_ROOT}" cat-file -e "${SOURCE_REVISION}^{commit}"
RUN_ID="${RUN_ID_OVERRIDE:-F6_$(date -u +%Y%m%d_%H%M%S)_${SOURCE_REVISION:0:8}}"
BASE="${SCRATCH_ROOT}/${RUN_ID}"

hash_commit_path() {
  git -C "${REPO_ROOT}" show "${SOURCE_REVISION}:$1" | sha256sum | awk '{print $1}'
}
[[ "$(hash_commit_path models/generated/mode_ii/h2_uniform_serial_u020_postpeak/ModeII_H2_uniform_serial.inp)" == "${EXPECTED_DECK_SHA}" ]]
[[ "$(hash_commit_path models/generated/mode_ii/h2_uniform_serial_u020_postpeak/ModeII_H2_uniform_serial.for)" == "${EXPECTED_FOR_SHA}" ]]
[[ "$(hash_commit_path models/generated/mode_ii/miseseri_preanalysis_corrected_pbs/ModeII_MISESERI_preanalysis.inp)" == "${EXPECTED_MIS_DECK_SHA}" ]]
[[ -r "${SOURCE_ODB}" ]]
[[ "$(sha256sum "${SOURCE_ODB}" | awk '{print $1}')" == "${EXPECTED_ODB_SHA}" ]]

module --force purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023
command -v ifort >/dev/null
command -v ifx >/dev/null
command -v abaqus >/dev/null
qstat -u pr21vyci >/dev/null
ACTIVE_COUNT=$(qselect -u pr21vyci 2>/dev/null | wc -l | tr -d ' ')
[[ "${ACTIVE_COUNT}" -eq 0 ]] || {
  echo "ERROR: existing active user jobs prevent a two-job maximum-running batch" >&2
  exit 1
}

stage_bundle() {
  target="$1"
  [[ ! -e "${target}" ]]
  mkdir -p "${target}/h2_u020_full/runtime" "${target}/miseseri_remesh_api/runtime"
  paths=(
    configs/stage_f/mode_ii_miseseri_native_remesh.yaml
    models/generated/mode_ii/h2_uniform_serial_u020_postpeak
    models/generated/mode_ii/miseseri_preanalysis_corrected_pbs
    scripts/hpc/stage_f/write_status_json.py
    scripts/postprocessing/extract_mode_ii_uniform_reference.py
    scripts/remeshing/qualify_mode_ii_native_miseseri_api.py
    scripts/validation/validate_mode_ii_h2_results.py
  )
  for lane in h2_u020_full miseseri_remesh_api; do
    git -C "${REPO_ROOT}" archive "${SOURCE_REVISION}" "${paths[@]}" |
      tar -x -C "${target}/${lane}/runtime"
  done
  cp "${target}/h2_u020_full/runtime/models/generated/mode_ii/h2_uniform_serial_u020_postpeak/ModeII_H2_uniform_serial.inp" "${target}/h2_u020_full/"
  cp "${target}/h2_u020_full/runtime/models/generated/mode_ii/h2_uniform_serial_u020_postpeak/ModeII_H2_uniform_serial.for" "${target}/h2_u020_full/"
  git -C "${REPO_ROOT}" show "${SOURCE_REVISION}:scripts/hpc/stage_f/08_mode_ii_h2_u020_full_f6.pbs" > "${target}/h2_u020_full/M2H2U20F1.pbs"
  git -C "${REPO_ROOT}" show "${SOURCE_REVISION}:scripts/hpc/stage_f/09_mode_ii_miseseri_remesh_api_f6.pbs" > "${target}/miseseri_remesh_api/M2RMAPI1.pbs"
  for lane in h2_u020_full miseseri_remesh_api; do
    (
      cd "${target}/${lane}"
      find runtime -type f -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
      if [[ "${lane}" == "h2_u020_full" ]]; then
        sha256sum ModeII_H2_uniform_serial.inp ModeII_H2_uniform_serial.for M2H2U20F1.pbs >> SHA256SUMS
      else
        sha256sum M2RMAPI1.pbs >> SHA256SUMS
      fi
      python3 runtime/scripts/hpc/stage_f/write_status_json.py --output RUNTIME_MANIFEST.json \
        --set "run_id=str:${RUN_ID}" --set "source_git_revision=str:${SOURCE_REVISION}" \
        --set "lane=str:${lane}" --set "hash_audit_passed=bool:true" \
        --set "automatic_retry_authorized=bool:false"
      python3 -m json.tool RUNTIME_MANIFEST.json >/dev/null
      sha256sum -c SHA256SUMS >/dev/null
    )
  done
  python3 "${target}/h2_u020_full/runtime/scripts/hpc/stage_f/write_status_json.py" \
    --output "${target}/BATCH_RUNTIME_MANIFEST.json" \
    --set "run_id=str:${RUN_ID}" --set "source_git_revision=str:${SOURCE_REVISION}" \
    --set "job_a=str:M2H2U20F1" --set "job_b=str:M2RMAPI1"
  (cd "${target}" && find . -type f ! -name BATCH_SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > BATCH_SHA256SUMS)
}

if [[ "${MODE}" == "--preflight" ]]; then
  TEMP_BASE="$(mktemp -d "${TMPDIR:-/tmp}/f6_batch_preflight.XXXXXX")"
  trap 'rm -rf -- "${TEMP_BASE}"' EXIT
  stage_bundle "${TEMP_BASE}/runtime"
  echo "F6_BATCH_PREFLIGHT_PASS RUN_ID=${RUN_ID} SOURCE_REVISION=${SOURCE_REVISION}"
  exit 0
fi

python3 - "${AUTH_FILE}" <<'PY'
import json, sys
d=json.load(open(sys.argv[1]))
assert d["execution_authorized"] is True
assert d["submission_approved"] is True
assert d["solver_authorized_job_a"] is True
assert d["preprocessing_authorized_job_b"] is True
assert d["solver_authorized_job_b"] is False
assert d["approved_submissions"] == 2
assert d["qsub_attempts"] == 0
assert d["retry_authorized"] is False
assert d["replacement_authorized"] is False
PY
stage_bundle "${BASE}"

ATTEMPTS=0; SUCCESS=0; FAILED=0; JOB_A_ID=""; JOB_B_ID=""
ATTEMPTS=$((ATTEMPTS+1))
if JOB_A_ID=$(cd "${BASE}/h2_u020_full" && "${QSUB_CMD}" M2H2U20F1.pbs); then SUCCESS=$((SUCCESS+1)); else FAILED=$((FAILED+1)); fi
ATTEMPTS=$((ATTEMPTS+1))
if JOB_B_ID=$(cd "${BASE}/miseseri_remesh_api" && "${QSUB_CMD}" -v "SOURCE_ODB_PATH=${SOURCE_ODB}" M2RMAPI1.pbs); then SUCCESS=$((SUCCESS+1)); else FAILED=$((FAILED+1)); fi

python3 "${BASE}/h2_u020_full/runtime/scripts/hpc/stage_f/write_status_json.py" \
  --output "${BASE}/BATCH_STATUS.json" \
  --set "run_id=str:${RUN_ID}" --set "source_git_revision=str:${SOURCE_REVISION}" \
  --set "qsub_attempts=int:${ATTEMPTS}" --set "successful_submissions=int:${SUCCESS}" \
  --set "failed_qsub_attempts=int:${FAILED}" --set "job_a_id=str:${JOB_A_ID}" \
  --set "job_b_id=str:${JOB_B_ID}" --set "execution_authorized=bool:false" \
  --set "submission_approved=bool:false" --set "maximum_jobs_now=int:0" \
  --set "retry_authorized=bool:false" --set "replacement_authorized=bool:false" \
  --set "direct_manual_qsub_calls=int:0"
python3 -m json.tool "${BASE}/BATCH_STATUS.json" >/dev/null
echo "RUN_ID=${RUN_ID}"
echo "JOB_A_ID=${JOB_A_ID}"
echo "JOB_B_ID=${JOB_B_ID}"
echo "QSUB_ATTEMPTS=${ATTEMPTS}"
echo "SUCCESSFUL_SUBMISSIONS=${SUCCESS}"
[[ "${SUCCESS}" -eq 2 ]]
