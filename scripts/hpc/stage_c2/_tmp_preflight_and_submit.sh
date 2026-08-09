#!/bin/bash
# Preflight + one-shot C2C–C2F recovery submission (login node only).
set -euo pipefail
PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
cd "${PROJECT_HOME}"
git pull --ff-only origin main
REVISION="$(git rev-parse HEAD)"
echo "REVISION=${REVISION}"

# Clean tracked tree required by submit script
if [ -n "$(git status --short --untracked-files=no)" ]; then
  echo "tracked_working_tree_not_clean" >&2
  git status --short --untracked-files=no >&2
  exit 2
fi

echo "=== bash -n PBS scripts ==="
bash -n scripts/hpc/stage_c2/03_rebuild_validate.pbs
bash -n scripts/hpc/stage_c2/04_h0_threads4_qualification.pbs
bash -n scripts/hpc/stage_c2/05_refined_integrity_threads4.pbs
bash -n scripts/hpc/stage_c2/06_refined_final_threads4.pbs
bash -n scripts/hpc/stage_c2/submit_c2_from_c2c.sh
bash -n scripts/hpc/stage_c2/verify_c2b_and_write_marker.sh

echo "=== no qsub/git inside PBS ==="
if grep -nE '^\s*qsub\b|^\s*git\s' scripts/hpc/stage_c2/0{3,4,5,6}_*.pbs; then
  echo "forbidden command in PBS" >&2
  exit 3
fi
echo "pbs_forbidden_commands_ok"

echo "=== threads policy ==="
grep -n 'mp_mode=threads\|OMP_NUM_THREADS\|ncpus=4' \
  scripts/hpc/stage_c2/04_h0_threads4_qualification.pbs \
  scripts/hpc/stage_c2/05_refined_integrity_threads4.pbs \
  scripts/hpc/stage_c2/06_refined_final_threads4.pbs | head -40
if grep -nE 'mp_mode=mpi|mpirun' scripts/hpc/stage_c2/0{4,5,6}_*.pbs; then
  echo "MPI forbidden for UEL stages" >&2
  exit 4
fi
echo "threads_no_mpi_ok"

echo "=== python compile ==="
module load gcc/11.4.0 >/dev/null 2>&1 || true
module load python/gcc/11.4.0/3.11.7 >/dev/null 2>&1 || true
python3 -m py_compile \
  scripts/preprocessing/build_molnar_unified_deck.py \
  scripts/validation/validate_molnar_unified_deck.py
python3 -c "import yaml; print('yaml_ok', __import__('sys').version)"

echo "=== C2B verify + marker ==="
bash scripts/hpc/stage_c2/verify_c2b_and_write_marker.sh
test -f runs/hpc/stage_c2/chain_state/C2B.ok
test -f runs/hpc/stage_c2/recovery/C2B_REUSE_VERIFICATION.json
cat runs/hpc/stage_c2/recovery/C2B_REUSE_VERIFICATION.json | head -40

echo "=== C2C revalidate existing dry rebuild ==="
DECK_DIR="/scratch/pr21vyci/adaptive-remeshing/prestage/c2c_dryrun_20260721T095828/models/generated/molnar_gravouil_2017/unified_preprocessing/H0_refined_layered_dryrun"
if [ -f "${DECK_DIR}/H0_refined_fullgen.inp" ]; then
  OUT="/scratch/pr21vyci/adaptive-remeshing/runs/c2c_revalidate_preflight"
  mkdir -p "${OUT}"
  python3 scripts/validation/validate_molnar_unified_deck.py \
    --config configs/preprocessing/molnar_h0_h1_unified.yaml \
    --deck "${DECK_DIR}/H0_refined_fullgen.inp" \
    --fortran "${DECK_DIR}/H0_refined_fullgen.for" \
    --role H0_refined \
    --out-dir "${OUT}/static_validation" | tee "${OUT}/validate_stdout.log"
  (cd "${DECK_DIR}" && sha256sum -c input_hashes.sha256) | tee "${OUT}/input_hash_check.txt"
  echo "revalidate_ok"
else
  echo "no_existing_dry_deck_running_full_dryrun"
  bash /tmp/c2c_dryrun.sh
fi

echo "=== duplicate job guard ==="
if qstat -u "${USER}" 2>/dev/null | grep -E 'c2c_rebuild|c2d_h0|c2e_ref|c2f_ref' >/dev/null 2>&1; then
  echo "duplicate recovery jobs already active" >&2
  qstat -u "${USER}" >&2 || true
  exit 5
fi

echo "=== submit recovery chain once ==="
bash scripts/hpc/stage_c2/submit_c2_from_c2c.sh
echo "=== post-submit qstat ==="
qstat -u "${USER}" || true
echo "=== submission record ==="
cat runs/hpc/stage_c2/recovery/C2_RECOVERY_SUBMISSION_RECORD.txt
echo "PREFLIGHT_AND_SUBMIT_DONE revision=${REVISION}"
