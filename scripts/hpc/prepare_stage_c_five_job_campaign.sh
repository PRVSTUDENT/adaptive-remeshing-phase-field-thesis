#!/bin/bash
# Prepare / statically validate the Stage C five-job campaign.
# NEVER submits to PBS. There is no qsub in this wrapper.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EMAIL="${EMAIL:-pr21vyci@mailserver.tu-freiberg.de}"
cd "${ROOT}"

PBS_FILES=(
  scripts/hpc/molnar_h0_miseseri_smoke.pbs
  scripts/hpc/molnar_h0_miseseri_preanalysis.pbs
  scripts/hpc/molnar_h0_miseseri_remesh.pbs
  scripts/hpc/molnar_h0_refined_integrity.pbs
  scripts/hpc/molnar_miseseri_refined_final.pbs
)

echo "=== Stage C five-job preparation (no submission) ==="
echo "root=${ROOT}"
echo "submission_authorized=false"

for f in "${PBS_FILES[@]}"; do
  if [ ! -f "${f}" ]; then
    echo "MISSING: ${f}" >&2
    exit 2
  fi
  if command -v bash >/dev/null 2>&1; then
    bash -n "${f}"
    echo "bash -n OK: ${f}"
  fi
done

python3 scripts/hpc/validate_pbs_email_notifications.py --email "${EMAIL}" "${PBS_FILES[@]}"
python3 scripts/hpc/validate_stage_c_five_job_static.py

mkdir -p runs/hpc/stage_c_miseseri
cat > runs/hpc/stage_c_miseseri/CAMPAIGN_PREPARATION_STATUS.md <<EOF
# Stage C five-job campaign preparation

Status: \`prepared_static_only\`
Submission authorized: **false**

| Job | Script | Class | CPUs | Mem | Walltime |
|---|---|---|---:|---|---|
| 1 | molnar_h0_miseseri_smoke.pbs | solver | 1 | 16gb | 01:00:00 |
| 2 | molnar_h0_miseseri_preanalysis.pbs | solver | 1 | 16gb | 02:00:00 |
| 3 | molnar_h0_miseseri_remesh.pbs | CAE | 1 | 16gb | 01:00:00 |
| 4 | molnar_h0_refined_integrity.pbs | solver | 1 | 16gb | 02:00:00 |
| 5 | molnar_miseseri_refined_final.pbs | solver | 1 | 32gb | 06:00:00 |

Do not run \`qsub\` until:

\`\`\`text
full H0 generation passes Gate P1
H1 generation passes structural validation
all layered mappings pass
initial remeshing parameters are frozen
five PBS scripts pass static validation
pre-analysis load mode is decided
exact job count and resources are documented
\`\`\`
EOF

echo "Preparation complete. NO qsub performed."
