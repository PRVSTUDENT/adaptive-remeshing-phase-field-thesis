# H0 CAE Replay Manifest

Status: `prepared_not_submitted`

## Why H0 is not solver-rerun

Job `1376154.mmaster02` already achieved Abaqus technical pass with retained ODB.
Only CAE postprocessing failed (f-string parse error). Replaying CAE on the
existing ODB is authorized; re-solving H0 is not.

## Existing ODB

Path:

`/scratch/pr21vyci/adaptive-remeshing/runs/molnar_lc015_h0_exact_1376154.mmaster02/molnar_lc015_h0_exact.odb`

SHA-256 (cluster):

`01601effd2a110dc7124356cb3d9baf6d772d55f4fb344414ad219ba9b78e07b`

## New job

- PBS: `scripts/hpc/molnar_lc015_h0_cae_replay.pbs`
- Job name: `molnar_h0_cae_replay`
- Resources: 1 CPU, 16 GB, 01:00:00
- Classification pass/fail: `molnar_h0_cae_replay_pass` / `molnar_h0_cae_replay_fail`
- No downstream dependency

## Prior classification retained

`solver_pass_cae_postprocess_failure` for job `1376154.mmaster02`
