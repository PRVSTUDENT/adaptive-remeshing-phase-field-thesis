#!/bin/bash
set -u
HOME_EV=/home/pr21vyci/projects/adaptive-remeshing/runs/hpc/molnar_lc015_h_convergence
SCR=/scratch/pr21vyci/adaptive-remeshing/runs

echo "=== ACTIVE QUEUE ==="
qstat -u pr21vyci 2>/dev/null || echo "(empty)"

for j in 1376154.mmaster02 1376184.mmaster02 1376185.mmaster02 1376186.mmaster02; do
  echo
  echo "========== $j =========="
  qstat -xf "$j" 2>/dev/null | egrep 'Job Id|Job_Name|job_state|Exit_status|resources_used|Resource_List.mem|Resource_List.ncpus|Resource_List.walltime|Resource_List.select|Mail_Users|Mail_Points|comment|exec_host|stime|obittime|ctime|depend|queue' || echo "qstat history unavailable for $j"
done

echo
echo "========== EVIDENCE / CLASSIFICATIONS =========="

echo
echo "--- H0 solver 1376154 ---"
E0="$HOME_EV/H0_exact/evidence/1376154.mmaster02"
if [ -d "$E0" ]; then
  ls -la "$E0"
  for f in technical_classification.txt failure_class.txt abaqus_return_code.txt postprocess_return_code.txt; do
    [ -f "$E0/$f" ] && echo "$f=$(cat "$E0/$f")"
  done
  if [ -f "$E0/molnar_lc015_h0_exact.sta" ]; then
    grep -E 'SUCCESS|ERROR|FAILED' "$E0/molnar_lc015_h0_exact.sta" | tail -5
  fi
else
  echo "missing $E0"
fi
ls -la "$SCR/molnar_lc015_h0_exact_1376154.mmaster02" 2>/dev/null | head -20
ls -la "$SCR/molnar_lc015_h0_exact_1376154.mmaster02/"*.odb 2>/dev/null || true

echo
echo "--- H0 CAE replay 1376184 ---"
E0c="$HOME_EV/recovery_after_job_1376154/H0_cae_replay/evidence/1376184.mmaster02"
if [ -d "$E0c" ]; then
  ls -la "$E0c"
  for f in technical_classification.txt failure_class.txt cae_return_code.txt cae_postprocess_classification.txt abaqus_return_code.txt; do
    [ -f "$E0c/$f" ] && echo "$f=$(cat "$E0c/$f")"
  done
  echo "--- postprocess log tail ---"
  tail -30 "$E0c/postprocess_stdout.log" 2>/dev/null || true
else
  echo "missing $E0c"
fi

echo
echo "--- H1 1376185 ---"
E1="$HOME_EV/H1_h0025/evidence/1376185.mmaster02"
if [ -d "$E1" ]; then
  ls -la "$E1"
  for f in technical_classification.txt abaqus_technical_classification.txt failure_class.txt abaqus_return_code.txt cae_return_code.txt postprocess_return_code.txt cae_postprocess_classification.txt solver_dependency_status.txt overall_evidence_status.txt pbs_exit_semantics.txt; do
    [ -f "$E1/$f" ] && echo "$f=$(cat "$E1/$f")"
  done
  if [ -f "$E1/molnar_lc015_h1_h0025.sta" ]; then
    grep -E 'SUCCESS|ERROR|FAILED' "$E1/molnar_lc015_h1_h0025.sta" | tail -5
  fi
  ls "$E1"/*RF2* "$E1"/*rf2* 2>/dev/null || echo "no RF2 export in evidence root"
else
  echo "missing $E1"
fi
ls -la "$SCR/molnar_lc015_h1_h0025_1376185.mmaster02" 2>/dev/null | head -25
ls -la "$SCR/molnar_lc015_h1_h0025_1376185.mmaster02/"*.odb 2>/dev/null || true

echo
echo "--- H2 1376186 ---"
E2="$HOME_EV/H2_pub_h0010/evidence/1376186.mmaster02"
if [ -d "$E2" ]; then
  ls -la "$E2"
  for f in technical_classification.txt abaqus_technical_classification.txt failure_class.txt abaqus_return_code.txt cae_return_code.txt postprocess_return_code.txt cae_postprocess_classification.txt solver_dependency_status.txt overall_evidence_status.txt pbs_exit_semantics.txt; do
    [ -f "$E2/$f" ] && echo "$f=$(cat "$E2/$f")"
  done
  if [ -f "$E2/molnar_lc015_h2_pub_h0010.sta" ]; then
    grep -E 'SUCCESS|ERROR|FAILED' "$E2/molnar_lc015_h2_pub_h0010.sta" | tail -5
  fi
  ls "$E2"/*RF2* "$E2"/*rf2* 2>/dev/null || echo "no RF2 export in evidence root"
else
  echo "missing $E2"
fi
ls -la "$SCR/molnar_lc015_h2_pub_h0010_1376186.mmaster02" 2>/dev/null | head -25
ls -la "$SCR/molnar_lc015_h2_pub_h0010_1376186.mmaster02/"*.odb 2>/dev/null || true

echo
echo "=== PBS OUTPUT DIRS ==="
ls -la /scratch/pr21vyci/adaptive-remeshing/pbs_output/ 2>/dev/null | tail -20

echo SUMMARY_DONE
