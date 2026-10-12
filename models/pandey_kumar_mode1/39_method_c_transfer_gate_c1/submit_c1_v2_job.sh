#!/bin/bash
set -euo pipefail

RUN_DIR="/scratch9/pr21vyci/runs/mode1_method_c_gate_c1_v2"
cd "${RUN_DIR}"

if [ -f "${RUN_DIR}/job_notifications.sh" ]; then
    source "${RUN_DIR}/job_notifications.sh"
    notification_load_config || true
fi

echo "Submitting Method C Gate C1 V2 Continuation Job..."
JOB_ID=$(qsub submit_M1_RECIP_2906_CONTINUATION_V2.pbs)
echo "Submitted Job ID: ${JOB_ID}"

if type notify_submitted >/dev/null 2>&1; then
    notify_submitted "${JOB_ID}" "M1_MC_C1_V2" "entry_imfdfkmq" "1" "16gb" "04:00:00" || true
fi
