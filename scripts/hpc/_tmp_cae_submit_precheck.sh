#!/bin/bash
set -euo pipefail
cd /home/pr21vyci/projects/adaptive-remeshing

echo "REV=$(git rev-parse HEAD)"
echo "=== queue ==="
qstat -u pr21vyci 2>/dev/null || echo QUEUE_EMPTY

echo "=== tracked dirt ==="
git status --short --untracked-files=no || true

# stash unrelated dirt if present
if [ -n "$(git status --short --untracked-files=no)" ]; then
  git stash push -m temp_before_cae_all_submit -- \
    runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/evidence/1375028.mmaster02/PROJECT_REVISION.txt \
    runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic_r2/evidence/1375028.mmaster02/STAGING_MANIFEST.txt 2>/dev/null || true
  # if still dirty, report
  if [ -n "$(git status --short --untracked-files=no)" ]; then
    echo "STILL_DIRTY"
    git status --short --untracked-files=no
  fi
fi

echo "=== ODB checks ==="
for p in \
  /scratch/pr21vyci/adaptive-remeshing/runs/molnar_lc015_h0_exact_1376154.mmaster02/molnar_lc015_h0_exact.odb \
  /scratch/pr21vyci/adaptive-remeshing/runs/molnar_lc015_h1_h0025_1376185.mmaster02/molnar_lc015_h1_h0025.odb \
  /scratch/pr21vyci/adaptive-remeshing/runs/molnar_lc015_h2_pub_h0010_1376186.mmaster02/molnar_lc015_h2_pub_h0010.odb
do
  ls -la "$p"
  sha256sum "$p"
done

echo "=== tech classifications ==="
echo -n "H0="; cat runs/hpc/molnar_lc015_h_convergence/H0_exact/evidence/1376154.mmaster02/technical_classification.txt
echo -n "H1="; cat runs/hpc/molnar_lc015_h_convergence/H1_h0025/evidence/1376185.mmaster02/abaqus_technical_classification.txt
echo -n "H2="; cat runs/hpc/molnar_lc015_h_convergence/H2_pub_h0010/evidence/1376186.mmaster02/abaqus_technical_classification.txt

echo "=== rebuild manifest ==="
python3 scripts/hpc/build_molnar_hconv_cae_replay_manifest.py \
  runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154/CAE_REPLAY_ELIGIBILITY_MANIFEST.json
echo "=== eligible list ==="
cat runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154/CAE_REPLAY_ELIGIBILITY_MANIFEST_eligible_cases.txt
echo "=== eligible count ==="
wc -l runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154/CAE_REPLAY_ELIGIBILITY_MANIFEST_eligible_cases.txt

echo "=== abaqus compile ==="
module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023
abaqus python -c 'import py_compile; py_compile.compile("scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py", doraise=True); print("CASE_COMPILE_OK")'

echo "=== no standard solve in PBS ==="
if grep -nE 'abaqus job=|interactive' scripts/hpc/molnar_lc015_hconv_cae_replay_all.pbs; then
  echo "FOUND_SOLVER_COMMAND"
  exit 9
else
  echo "NO_STANDARD_SOLVE_OK"
fi
grep -q MOLNAR_ODB_PATH scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py
grep -q MOLNAR_CASE_ID scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py
grep -q MOLNAR_OUTPUT_DIR scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py
echo ENV_VAR_CONTRACT_OK

bash -n scripts/hpc/molnar_lc015_hconv_cae_replay_all.pbs
bash -n scripts/hpc/submit_molnar_lc015_hconv_cae_replay_all.sh
python3 scripts/hpc/validate_pbs_email_notifications.py --email pr21vyci@mailserver.tu-freiberg.de scripts/hpc/molnar_lc015_hconv_cae_replay_all.pbs
echo PRECHECK_OK
