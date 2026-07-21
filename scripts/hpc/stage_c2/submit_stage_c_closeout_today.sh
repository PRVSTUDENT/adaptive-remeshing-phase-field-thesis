#!/bin/bash
# Submit Stage C closeout campaign T1–T5 (afterany + markers).
set -euo pipefail
PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
EMAIL="${EMAIL:-Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de}"
QUEUE="${QUEUE:-entry_imfdfkmq}"
PBS_OUT="/scratch/pr21vyci/adaptive-remeshing/pbs_output/stage_c_closeout_$(date +%Y%m%dT%H%M%S)"
STAGE="scripts/hpc/stage_c2"
H1_JOB="1376579.mmaster02"

cd "${PROJECT_HOME}"
mkdir -p "${PBS_OUT}" runs/hpc/stage_c2/closeout

REVISION="$(git rev-parse HEAD)"
if [ -n "$(git status --short --untracked-files=no)" ]; then
  echo "tracked_working_tree_not_clean" >&2
  git status --short --untracked-files=no >&2
  exit 2
fi

for f in \
  t1_h1_threads4_closeout.pbs \
  t2_c2f_v3_repeat.pbs \
  t3_matched_sdv15_extract.pbs \
  t4_crack_path_metrics.pbs \
  t5_h0_automation_smoke.pbs
do
  bash -n "${STAGE}/${f}"
  python3 scripts/hpc/validate_pbs_email_notifications.py --email "${EMAIL}" "${STAGE}/${f}"
done
python3 -m py_compile \
  scripts/hpc/stage_c2/t1_close_h1_threads4.py \
  scripts/postprocessing/crack_path_quantitative_metrics.py \
  scripts/model_generation/build_h0_notch_variation_mesh.py \
  scripts/hpc/telegram_notify.py

# Guard required frozen paths
test -f runs/hpc/stage_c2/C2C_V3_DECK_PATH.txt
test -f models/generated/molnar_gravouil_2017/unified_preprocessing/H0_refined_layered_v3_notchfix/H0_refined_fullgen.inp
test -f /scratch/pr21vyci/adaptive-remeshing/runs/molnar_c2f_v3_refined_final_threads4_1376480.mmaster02/molnar_c2f_v3_refined_final_threads4.odb

notify_sub() {
  local jid="$1" name="$2" msg="$3"
  python3 scripts/hpc/telegram_notify.py \
    --event SUBMITTED --job-id "${jid}" --job-name "${name}" --message "${msg}" || true
}

# T1: if H1 job finished, no depend; if still active, afterany
H1_STATE="$(qstat -f "${H1_JOB}" 2>/dev/null | awk '/job_state/ {print $3; exit}' || true)"
if [ -z "${H1_STATE}" ] || [ "${H1_STATE}" = "F" ]; then
  T1=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
    -o "${PBS_OUT}/t1.out" "${STAGE}/t1_h1_threads4_closeout.pbs")
else
  T1=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
    -W depend=afterany:"${H1_JOB}" \
    -o "${PBS_OUT}/t1.out" "${STAGE}/t1_h1_threads4_closeout.pbs")
fi
notify_sub "${T1}" "t1_h1_close" "Closeout H1 4-thread 1376579; revision=${REVISION}"

T2=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -W depend=afterany:"${T1}" \
  -o "${PBS_OUT}/t2.out" "${STAGE}/t2_c2f_v3_repeat.pbs")
notify_sub "${T2}" "t2_v3_repeat" "C2F-v3 repeatability; afterany T1; revision=${REVISION}"

T3=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -W depend=afterany:"${T2}" \
  -o "${PBS_OUT}/t3.out" "${STAGE}/t3_matched_sdv15_extract.pbs")
notify_sub "${T3}" "t3_sdv_extract" "Matched SDV15 extraction; afterany T2"

T4=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -W depend=afterany:"${T3}" \
  -o "${PBS_OUT}/t4.out" "${STAGE}/t4_crack_path_metrics.pbs")
notify_sub "${T4}" "t4_crack_met" "Crack-path quantitative metrics; afterany T3"

T5=$(qsub -q "${QUEUE}" -M "${EMAIL}" -m abe \
  -W depend=afterany:"${T4}" \
  -o "${PBS_OUT}/t5.out" "${STAGE}/t5_h0_automation_smoke.pbs")
notify_sub "${T5}" "t5_h0_smoke" "H0 notch=0.45 automation smoke; afterany T4"

{
  echo "submission_time=$(date -Is)"
  echo "revision=${REVISION}"
  echo "H1_existing=${H1_JOB}"
  echo "T1=${T1}"
  echo "T2=${T2}"
  echo "T3=${T3}"
  echo "T4=${T4}"
  echo "T5=${T5}"
  echo "dependency_mode=afterany_plus_markers"
  echo "queue=${QUEUE}"
  echo "telegram=primary"
  echo "email=secondary"
  echo "c2f_v3_original=1376480.mmaster02"
} | tee runs/hpc/stage_c2/closeout/STAGE_C_CLOSEOUT_SUBMISSION_RECORD.txt

printf '%s\n' "T1=$T1" "T2=$T2" "T3=$T3" "T4=$T4" "T5=$T5"
qstat -u "${USER}" | head -25 || true
