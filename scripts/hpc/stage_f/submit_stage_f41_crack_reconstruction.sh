#!/bin/bash
set -euo pipefail

PACKAGE_DIR="models/generated/mode_ii/f41_crack_geometry_reconstruction"
PBS_DECK="${PACKAGE_DIR}/M2RMSTITCH1.pbs"
TASK_JSON="project_coordination/ACTIVE_TASK.json"

if [ ! -f "${PBS_DECK}" ]; then
    echo "ERROR: PBS deck not found at ${PBS_DECK}" >&2
    exit 1
fi

if [ ! -f "${TASK_JSON}" ]; then
    echo "ERROR: ACTIVE_TASK.json not found" >&2
    exit 1
fi

EXEC_AUTH=$(python3 -c "import json; data=json.load(open('${TASK_JSON}')); print(str(data.get('execution_authorized', False)).lower())")
SUBM_APP=$(python3 -c "import json; data=json.load(open('${TASK_JSON}')); print(str(data.get('submission_approved', False)).lower())")
MAX_JOBS=$(python3 -c "import json; data=json.load(open('${TASK_JSON}')); print(data.get('maximum_jobs_now', 0))")

if [ "${EXEC_AUTH}" != "true" ] || [ "${SUBM_APP}" != "true" ] || [ "${MAX_JOBS}" -lt 1 ]; then
    echo "SUBMISSION_BLOCKED: Execution authorization missing or maximum_jobs_now=0." >&2
    echo "execution_authorized=${EXEC_AUTH}, submission_approved=${SUBM_APP}, maximum_jobs_now=${MAX_JOBS}" >&2
    exit 1
fi

if command -v qsub >/dev/null 2>&1; then
    JOB_ID=$(qsub "${PBS_DECK}")
    echo "SUBMITTED_JOB_ID: ${JOB_ID}"
else
    echo "ERROR: qsub binary not available in environment" >&2
    exit 1
fi
