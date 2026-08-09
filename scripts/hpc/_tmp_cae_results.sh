#!/bin/bash
BASE=/home/pr21vyci/projects/adaptive-remeshing/runs/hpc/molnar_lc015_h_convergence/recovery_after_job_1376154/cae_replay_all/evidence/1376236.mmaster02
echo "case_results:"
cat "$BASE/case_results.txt"
echo "overall:"
cat "$BASE/cae_postprocess_classification.txt"
for c in H0 H1 H2-PUB; do
  echo "==== $c ===="
  d="$BASE/postprocessing/$c"
  echo "cae_rc=$(cat $d/cae_return_code.txt)"
  echo "class=$(cat $d/cae_postprocess_classification.txt)"
  cat "$d/${c}_postprocess_summary.json"
  echo "image_warn=$(cat $d/${c}_image_export_warning.txt)"
  echo "csv_head:"
  head -3 "$d/${c}_RF2_U2.csv"
  echo "csv_n=$(wc -l < $d/${c}_RF2_U2.csv)"
  echo "stdout:"
  cat "$d/postprocess_stdout.log"
done
