# F43MODEREF-H2-ENDPOINT-RESOLUTION-PREP1

Prepared a new, submission-blocked H2 Mode-II FRACFIX endpoint-resolution package. The user increased the scheduler walltime request from the initially proposed 12 hours to 24 hours. No `qsub` was called and no authorization record was created.

## Frozen execution package

- Package: `models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX_ENDPOINT/`
- Scheduler job name: `M2H2ENDPOINT`
- Historical job: `1386448.mmaster02`
- Input SHA256: `c9a3f496cf2cb0daa455cfae31f5bd699b56f3b410f0a7f2a12014b2718be5b0`
- UEL SHA256: `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
- PBS SHA256: `96854cf7058ecf6d7d571b758aa937bf199ec9b8a5eef90d7578e4d969f5be89`
- Wrapper SHA256: `4293ceaf961b067ea24031d218e303f107984289d0e9434fe1b7adc169066318`
- Manifest SHA256: `2238e1461ef9b7744f2d0b5e8b79c59a49048f465bb77a6d99d769ca2d13296e`
- Resources: 1 CPU, 8 GB, `24:00:00`, `entry_imfdfkmq`, serial Abaqus/Standard.
- Scientific input identity with historical H2: PASS (exact raw-byte identity).
- UEL identity with historical H2: PASS (exact raw-byte identity).
- NPHYS: 33852; five-property U2 declaration and property-slot-5 mapping PASS.

## Qualification

- Rehearsal commit: `195e37d8c4398058c0ff19e0a7d9d78d0c27d529`.
- Rehearsal: 638 unittest cases PASS; 29 focused cases PASS; both pytest-style state-transfer test groups executed explicitly and PASS.
- Exact-P qualification repeated the same suites and checks in a second fresh detached worktree: PASS.
- NPHYS validator, scientific identity validator, raw hashes, PBS grammar/resources, notification contract, output parity, wrapper `bash -n`, manifest consistency, and fail-closed preflight: PASS.
- Immediate natural cleanliness (`status`, unstaged diff, staged diff): PASS for rehearsal and exact P.
- Queue read: `qstat -u pr21vyci` rc=0; rehearsal observed 0 running and 0 queued jobs.
- Submission preflight: `BLOCKED_no_direct_human_authorization`.
- First full-suite attempt used system Python 3.6 and failed on repository Python-version incompatibility. A fresh Python 3.11 run then exposed two missing-`pytest` imports; a temporary external import shim was used because those modules do not call pytest APIs, and their test functions were executed explicitly. No committed files were changed by the shim.

## Immutable P

- Tag: `P43MODEREF-H2END1-FINAL1`
- Commit: `195e37d8c4398058c0ff19e0a7d9d78d0c27d529`
- Local tag object: `9bce2126761584debab79a9cccaf5f70afd2e4dd`
- Remote tag object: `9bce2126761584debab79a9cccaf5f70afd2e4dd`
- Created once and pushed once normally.

## Execution state

- `execution_authorized=false`
- `submission_approved=false`
- `maximum_jobs_now=0`
- `automatic_retry=false`
- `qsub_called=false`
- `HPC_submissions=0`
