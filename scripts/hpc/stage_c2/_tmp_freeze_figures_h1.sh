#!/bin/bash
set -euo pipefail
cd /home/pr21vyci/projects/adaptive-remeshing
module load gcc/11.4.0 >/dev/null 2>&1 || true
module load python/gcc/11.4.0/3.11.7 >/dev/null 2>&1 || true
module load intel/2024.2.0 >/dev/null 2>&1 || true
module load abaqus/2023 >/dev/null 2>&1 || true

python3 - <<'PY'
import json, hashlib
from pathlib import Path
from datetime import datetime, timezone

def sha(p):
    p = Path(p)
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

paths = {
    "deck": "models/generated/molnar_gravouil_2017/unified_preprocessing/H0_refined_layered_v3_notchfix/H0_refined_fullgen.inp",
    "fortran": "models/generated/molnar_gravouil_2017/unified_preprocessing/H0_refined_layered_v3_notchfix/H0_refined_fullgen.for",
    "odb": "/scratch/pr21vyci/adaptive-remeshing/runs/molnar_c2f_v3_refined_final_threads4_1376480.mmaster02/molnar_c2f_v3_refined_final_threads4.odb",
    "rfu_csv": "runs/hpc/stage_c2/recovery/c2f_v3_vs_h1/C2F_V3_RF_U.csv",
    "vs_h1_status": "runs/hpc/stage_c2/recovery/c2f_v3_vs_h1/C2F_V3_VS_H1_STATUS.json",
}
rev = Path(".git/refs/heads/main").read_text().strip() if Path(".git/refs/heads/main").is_file() else None
freeze = {
    "freeze_id": "stage_c_v3_refined_response",
    "classification": "stage_c_refined_response_supported",
    "job_id": "1376480.mmaster02",
    "commit_sha": rev,
    "sha256": {k: sha(v) for k, v in paths.items()},
    "paths": paths,
    "metrics": {
        "peak_rf_diff_pct": 0.24,
        "stiffness_diff_pct": 0.061,
        "prepeak_nrmse_pct": 0.089,
        "peak_u_mm": 0.0058,
        "element_reduction_pct": 14.7,
        "n_physical": 10290,
        "n_H1": 12064,
        "postpeak_nrmse_pct": 24.3,
    },
    "h1_production_reference": True,
    "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
}
Path("runs/hpc/stage_c2/diagnostics").mkdir(parents=True, exist_ok=True)
Path("runs/hpc/stage_c2/diagnostics/STAGE_C_V3_FREEZE.json").write_text(
    json.dumps(freeze, indent=2, sort_keys=True) + "\n"
)
print("freeze_sha256", json.dumps(freeze["sha256"], indent=2))
PY

python3 scripts/postprocessing/plot_stage_c_final_figures.py \
  --h0 results/processed/molnar_lc015_h_convergence/source_csv/H0_RF2_U2.csv \
  --h1 results/processed/molnar_lc015_h_convergence/source_csv/H1_RF2_U2.csv \
  --h2 results/processed/molnar_lc015_h_convergence/source_csv/H2-PUB_RF2_U2.csv \
  --refined runs/hpc/stage_c2/recovery/c2f_v3_vs_h1/C2F_V3_RF_U.csv \
  --out-dir results/figures/stage_c_final

H1ODB=/scratch/pr21vyci/adaptive-remeshing/runs/molnar_lc015_h1_h0025_1376185.mmaster02/molnar_lc015_h1_h0025.odb
R3ODB=/scratch/pr21vyci/adaptive-remeshing/runs/molnar_c2f_v3_refined_final_threads4_1376480.mmaster02/molnar_c2f_v3_refined_final_threads4.odb
mkdir -p runs/hpc/stage_c2/recovery/c2f_v3_vs_h1
if [ -f "$H1ODB" ] && [ -f "$R3ODB" ]; then
  abaqus python scripts/postprocessing/assess_matched_state_crack_path.py \
    --odb-h1 "$H1ODB" \
    --odb-refined "$R3ODB" \
    --out-json runs/hpc/stage_c2/recovery/c2f_v3_vs_h1/CRACK_PATH_MATCHED_STATE.json \
    > runs/hpc/stage_c2/recovery/c2f_v3_vs_h1/crack_path_stdout.log 2>&1 || true
  tail -40 runs/hpc/stage_c2/recovery/c2f_v3_vs_h1/crack_path_stdout.log || true
else
  echo "missing_odb_for_crack_path H1=$H1ODB R3=$R3ODB"
fi

# mail smoke test to student inbox
echo "Stage C freeze complete on $(hostname) at $(date)" | mailx -s "PBS mail smoke: Stage C freeze" \
  Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de 2>&1 || true

bash scripts/hpc/stage_c2/submit_h1_threads4_baseline.sh
echo DONE
