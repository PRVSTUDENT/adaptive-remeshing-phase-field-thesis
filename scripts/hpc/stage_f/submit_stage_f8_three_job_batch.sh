#!/bin/bash
set -euo pipefail
: "${F8_RUN_ROOT:?}"
: "${F8_AUTHORIZATION:?}"
: "${F8_MAIL:?}"
python3 - "$F8_AUTHORIZATION" <<'PY'
import json,sys
a=json.load(open(sys.argv[1]))
assert a["execution_authorized"] is True
assert a["submission_approved"] is True
assert a["approved_submissions"] == 3
assert a["maximum_running_jobs"] == 2
assert a["authorized_jobs"] == ["M2IRRBAS1","M2IRRCAN1","M2RMTYPE1"]
assert a["qsub_attempts"] == 0
assert not a["retry_authorized"] and not a["replacement_authorized"]
PY
for d in baseline candidate remesh_type; do
  (cd "$F8_RUN_ROOT/$d" && sha256sum -c SHA256SUMS)
done
test "$(qstat -u "$USER" | awk 'NR>5 && ($5=="Q" || $5=="R"){n++} END{print n+0}')" -eq 0
attempts=0
submit() {
  attempts=$((attempts+1))
  test "$attempts" -le 3
  qsub "$@"
}
cd "$F8_RUN_ROOT/baseline"
job_a=$(submit -M "$F8_MAIL" -m abe M2IRRBAS1.pbs)
cd "$F8_RUN_ROOT/candidate"
job_b=$(submit -M "$F8_MAIL" -m abe M2IRRCAN1.pbs)
cd "$F8_RUN_ROOT/remesh_type"
job_c=$(submit -W "depend=afterany:${job_a}" -M "$F8_MAIL" -m abe M2RMTYPE1.pbs)
printf '{"qsub_attempts":3,"successful_submissions":3,"job_a":"%s","job_b":"%s","job_c":"%s","maximum_running_jobs":2}\n' \
  "$job_a" "$job_b" "$job_c" > "$F8_RUN_ROOT/SUBMISSION_RESULT.json"
printf '%s\n%s\n%s\n' "$job_a" "$job_b" "$job_c"
