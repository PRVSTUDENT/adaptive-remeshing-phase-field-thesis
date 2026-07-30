#!/usr/bin/env bash
# Self-contained Stage F4 replacement batch orchestrator.
# Compute jobs use only files staged below PBS_O_WORKDIR and never invoke Git.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${PROJECT_ROOT_OVERRIDE:-$(cd "${SCRIPT_DIR}/../../.." && pwd)}"
AUTH_FILE="${AUTH_FILE_OVERRIDE:-${REPO_ROOT}/runs/hpc/stage_f/MODE_II_STAGE_F4_REPLACEMENT_AUTHORIZATION.json}"
STATUS_OUT="${STATUS_OUT_OVERRIDE:-${REPO_ROOT}/runs/hpc/stage_f/STAGE_F4_REPLACEMENT_BATCH_STATUS.json}"
CONTRACT_FILE="${REPO_ROOT}/runs/hpc/stage_f/STAGE_F4_REPLACEMENT_RUNTIME_CONTRACT.json"

QSTAT_CMD="${QSTAT_CMD:-qstat}"
QSELECT_CMD="${QSELECT_CMD:-qselect}"
QSUB_CMD="${QSUB_CMD:-qsub}"
PYTHON_CMD="${PYTHON_CMD:-python3}"
SCRATCH_ROOT="${SCRATCH_ROOT_OVERRIDE:-/scratch/pr21vyci/adaptive-remeshing/runs/stage_f4}"

EXPECTED_H2_DECK_SHA="fdcd6ee1b1d6cbfb88d59a3edfb7f1c6b35cecde736a427f6b3030b0443b10bf"
EXPECTED_H2_FOR_SHA="49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37"
EXPECTED_MISESERI_DECK_SHA="a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2"
JOB_A_NAME="M2H2U20R1"
JOB_B_NAME="M2MISER1"

EXECUTE=false
if [[ "${1:-}" == "--execute" ]]; then
    EXECUTE=true
elif [[ -n "${1:-}" ]]; then
    echo "Usage: $0 [--execute]" >&2
    exit 2
fi

CURRENT_SHA=$(git -C "${REPO_ROOT}" rev-parse HEAD)
SOURCE_REVISION="${SOURCE_REVISION_OVERRIDE:-${CURRENT_SHA}}"
git -C "${REPO_ROOT}" cat-file -e "${SOURCE_REVISION}^{commit}"

for spec in \
    "models/generated/mode_ii/h2_uniform_serial_u020_postpeak/ModeII_H2_uniform_serial.inp:${EXPECTED_H2_DECK_SHA}" \
    "models/generated/mode_ii/h2_uniform_serial_u020_postpeak/ModeII_H2_uniform_serial.for:${EXPECTED_H2_FOR_SHA}" \
    "models/generated/mode_ii/miseseri_preanalysis_corrected_pbs/ModeII_MISESERI_preanalysis.inp:${EXPECTED_MISESERI_DECK_SHA}"; do
    path="${spec%%:*}"
    expected="${spec##*:}"
    actual=$(git -C "${REPO_ROOT}" show "${SOURCE_REVISION}:${path}" | sha256sum | awk '{print $1}')
    if [[ "${actual}" != "${expected}" ]]; then
        echo "ERROR: committed input hash mismatch for ${path}" >&2
        exit 1
    fi
done

USER_JOBS=$("${QSELECT_CMD}" -u "${USER:-${LOGNAME:-pr21vyci}}" 2>/dev/null || true)
for job_name in "${JOB_A_NAME}" "${JOB_B_NAME}"; do
    for job_id in ${USER_JOBS}; do
        if "${QSTAT_CMD}" -f "${job_id}" 2>/dev/null | grep -q "Job_Name = ${job_name}"; then
            echo "ERROR: active duplicate job detected: ${job_name}" >&2
            exit 1
        fi
    done
done

UTC_TS=$(date -u +"%Y%m%d_%H%M%S")
SHORT_SHA="${SOURCE_REVISION:0:8}"
RUN_ID="${RUN_ID_OVERRIDE:-F4R1_${UTC_TS}_${SHORT_SHA}}"
FINAL_BASE="${SCRATCH_ROOT}/${RUN_ID}"

stage_bundle() {
    local base="$1"
    local h2="${base}/h2_u020"
    local mis="${base}/miseseri_corrected"
    if [[ -e "${base}" ]]; then
        echo "ERROR: immutable run directory already exists: ${base}" >&2
        return 1
    fi
    mkdir "${base}"
    mkdir "${h2}" "${mis}"

    for target in "${h2}" "${mis}"; do
        mkdir "${target}/runtime"
        git -C "${REPO_ROOT}" archive "${SOURCE_REVISION}" \
            scripts configs \
            models/generated/mode_ii/h2_uniform_serial_u020_postpeak \
            models/generated/mode_ii/miseseri_preanalysis_corrected_pbs |
            tar -x -C "${target}/runtime"
    done

    cp "${h2}/runtime/models/generated/mode_ii/h2_uniform_serial_u020_postpeak/ModeII_H2_uniform_serial.inp" "${h2}/"
    cp "${h2}/runtime/models/generated/mode_ii/h2_uniform_serial_u020_postpeak/ModeII_H2_uniform_serial.for" "${h2}/"
    cp "${h2}/runtime/scripts/hpc/stage_f/05_mode_ii_h2_u020_postpeak.pbs" "${h2}/"
    cp "${mis}/runtime/models/generated/mode_ii/miseseri_preanalysis_corrected_pbs/ModeII_MISESERI_preanalysis.inp" "${mis}/"
    cp "${mis}/runtime/scripts/hpc/stage_f/06_mode_ii_miseseri_corrected_pbs.pbs" "${mis}/"

    for target in "${h2}" "${mis}"; do
        (
            cd "${target}"
            {
                find runtime -type f -print0 | sort -z | xargs -0 sha256sum
                if [[ "${target}" == "${h2}" ]]; then
                    sha256sum ModeII_H2_uniform_serial.inp ModeII_H2_uniform_serial.for 05_mode_ii_h2_u020_postpeak.pbs
                else
                    sha256sum ModeII_MISESERI_preanalysis.inp 06_mode_ii_miseseri_corrected_pbs.pbs
                fi
            } > SHA256SUMS
        )
        bundle_sha=$(sha256sum "${target}/SHA256SUMS" | awk '{print $1}')
        job_name="${JOB_B_NAME}"
        target_u1="0.001"
        elements="3930"
        walltime="01:00:00"
        if [[ "${target}" == "${h2}" ]]; then
            job_name="${JOB_A_NAME}"
            target_u1="0.020"
            elements="33852"
            walltime="12:00:00"
        fi
        "${PYTHON_CMD}" - "${target}" "${SOURCE_REVISION}" "${bundle_sha}" "${job_name}" "${target_u1}" "${elements}" "${walltime}" "${RUN_ID}" <<'PY'
import hashlib, json, pathlib, sys
target = pathlib.Path(sys.argv[1])
def sha(name):
    return hashlib.sha256((target / name).read_bytes()).hexdigest()
job = sys.argv[4]
is_h2 = job == "M2H2U20R1"
data = {
    "source_git_revision": sys.argv[2],
    "generation_timestamp_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    "bundle_sha256": sys.argv[3],
    "run_id": sys.argv[8],
    "job_name": job,
    "queue": "entry_imfdfkmq",
    "resources": {"cpus": 1, "memory_gb": 16, "walltime": sys.argv[7]},
    "target_displacement_mm": float(sys.argv[5]),
    "expected_physical_element_count": int(sys.argv[6]),
    "h2_deck_sha256": sha("ModeII_H2_uniform_serial.inp") if is_h2 else None,
    "h2_fortran_sha256": sha("ModeII_H2_uniform_serial.for") if is_h2 else None,
    "miseseri_deck_sha256": sha("ModeII_MISESERI_preanalysis.inp") if not is_h2 else None,
    "pbs_script_sha256": sha("05_mode_ii_h2_u020_postpeak.pbs" if is_h2 else "06_mode_ii_miseseri_corrected_pbs.pbs"),
    "extractor_sha256": sha("runtime/scripts/postprocessing/extract_mode_ii_uniform_reference.py" if is_h2 else "runtime/scripts/postprocessing/export_miseseri_preanalysis_csv.py"),
    "validator_sha256": sha("runtime/scripts/validation/validate_mode_ii_h2_results.py" if is_h2 else "runtime/scripts/validation/validate_mode_ii_miseseri_preanalysis_results.py"),
}
(target / "RUNTIME_MANIFEST.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
(target / "SUBMISSION_MANIFEST.json").write_text(json.dumps({
    "run_id": sys.argv[8], "job_name": job, "source_git_revision": sys.argv[2],
    "qsub_attempted": False, "pbs_job_id": None
}, indent=2, sort_keys=True) + "\n")
PY
        (cd "${target}" && sha256sum -c SHA256SUMS >/dev/null)
    done
}

if [[ "${EXECUTE}" == "false" ]]; then
    temp_base=$(mktemp -d "${TMPDIR:-/tmp}/stage_f4_preflight.XXXXXX")
    trap 'rm -rf -- "${temp_base}"' EXIT
    stage_bundle "${temp_base}/bundle"
    "${PYTHON_CMD}" - "${STATUS_OUT}" "${RUN_ID}" <<'PY'
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
    "batch_status": "preflight_passed_zero_submitted", "run_id": sys.argv[2],
    "qsub_attempts": 0, "successful_submissions": 0, "failed_qsub_attempts": 0
}, indent=2, sort_keys=True) + "\n")
PY
    echo "Preflight check PASSED cleanly. Runtime bundles verified; zero qsub calls."
    echo "Preflight mode complete. Zero jobs submitted."
    exit 0
fi

"${PYTHON_CMD}" - "${AUTH_FILE}" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["execution_authorized"] is True
assert d["submission_approved"] is True
assert d["solver_authorized"] is True
assert d["approved_submissions"] == 2
assert d["submissions_used"] == 0
assert d["qsub_attempts"] == 0
assert d["automatic_retry_authorized"] is False
assert d["retry_authorized"] is False
PY

stage_bundle "${FINAL_BASE}"
QSUB_ATTEMPTS=0
SUCCESSFUL=0
FAILED=0
JOB_A_ID=""
JOB_B_ID=""

consume_authority() {
    "${PYTHON_CMD}" - "${AUTH_FILE}" "${QSUB_ATTEMPTS}" "${SUCCESSFUL}" "${FAILED}" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
d.update({
    "execution_authorized": False, "submission_approved": False,
    "solver_authorized": False, "maximum_jobs_now": 0,
    "retry_authorized": False, "automatic_retry_authorized": False,
    "qsub_attempts": int(sys.argv[2]), "actual_qsub_calls": int(sys.argv[2]),
    "successful_submissions": int(sys.argv[3]), "submissions_used": int(sys.argv[3]),
    "failed_qsub_attempts": int(sys.argv[4]),
})
open(p, "w").write(json.dumps(d, indent=2, sort_keys=True) + "\n")
PY
}

QSUB_ATTEMPTS=1
if JOB_A_ID=$(cd "${FINAL_BASE}/h2_u020" && "${QSUB_CMD}" 05_mode_ii_h2_u020_postpeak.pbs); then
    SUCCESSFUL=1
    "${PYTHON_CMD}" - "${FINAL_BASE}/h2_u020/SUBMISSION_MANIFEST.json" "${JOB_A_ID}" <<'PY'
import json, sys
p=sys.argv[1]; d=json.load(open(p)); d.update(qsub_attempted=True,pbs_job_id=sys.argv[2]); open(p,"w").write(json.dumps(d,indent=2,sort_keys=True)+"\n")
PY
else
    FAILED=1
    consume_authority
fi

if [[ "${SUCCESSFUL}" -eq 1 ]]; then
    QSUB_ATTEMPTS=2
    if JOB_B_ID=$(cd "${FINAL_BASE}/miseseri_corrected" && "${QSUB_CMD}" 06_mode_ii_miseseri_corrected_pbs.pbs); then
        SUCCESSFUL=2
        "${PYTHON_CMD}" - "${FINAL_BASE}/miseseri_corrected/SUBMISSION_MANIFEST.json" "${JOB_B_ID}" <<'PY'
import json, sys
p=sys.argv[1]; d=json.load(open(p)); d.update(qsub_attempted=True,pbs_job_id=sys.argv[2]); open(p,"w").write(json.dumps(d,indent=2,sort_keys=True)+"\n")
PY
    else
        FAILED=1
    fi
fi
consume_authority

BATCH_STATUS="zero_submitted"
[[ "${SUCCESSFUL}" -eq 1 ]] && BATCH_STATUS="partial_batch_submitted"
[[ "${SUCCESSFUL}" -eq 2 ]] && BATCH_STATUS="full_batch_submitted"
"${PYTHON_CMD}" - "${STATUS_OUT}" "${RUN_ID}" "${BATCH_STATUS}" "${QSUB_ATTEMPTS}" "${SUCCESSFUL}" "${FAILED}" "${JOB_A_ID}" "${JOB_B_ID}" <<'PY'
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
    "run_id": sys.argv[2], "batch_status": sys.argv[3], "qsub_attempts": int(sys.argv[4]),
    "successful_submissions": int(sys.argv[5]), "failed_qsub_attempts": int(sys.argv[6]),
    "job_a_id": sys.argv[7] or None, "job_b_id": sys.argv[8] or None
}, indent=2, sort_keys=True) + "\n")
PY

echo "RUN_ID=${RUN_ID}"
echo "JOB_A_ID=${JOB_A_ID}"
echo "JOB_B_ID=${JOB_B_ID}"
echo "BATCH_STATUS=${BATCH_STATUS}"
[[ "${BATCH_STATUS}" == "full_batch_submitted" ]]
