# Consolidated CAE-Only Replay Plan

Status: `prepared_not_submitted`

## Decision

Do **not** submit another H0-only CAE replay while H1/H2 are still using the
old prestage CAE invocation. Prepare the parser repair now; after H1 and H2
finish, submit **exactly one** consolidated CAE-only job for every technical
pass that lacks a valid CAE package.

## Authorization boundary

```text
Abaqus/Standard solves: 0
CAE-only PBS submissions: maximum 1
Cases: H0 plus technically successful H1/H2 lacking valid CAE output
Solver retries: not authorized
Additional meshes: not authorized
Submit only after H1 and H2 leave the active queue
```

## Parser repair

`scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py` reads:

- `MOLNAR_CASE_ID`
- `MOLNAR_ODB_PATH`
- `MOLNAR_OUTPUT_DIR`

It logs `sys.argv` but does not use argv for paths.

## Artifacts

| Artifact | Path |
|---|---|
| Consolidated PBS | `scripts/hpc/molnar_lc015_hconv_cae_replay_all.pbs` |
| Login submit wrapper | `scripts/hpc/submit_molnar_lc015_hconv_cae_replay_all.sh` |
| Eligibility builder | `scripts/hpc/build_molnar_hconv_cae_replay_manifest.py` |
| Eligibility JSON | `CAE_REPLAY_ELIGIBILITY_MANIFEST.json` (rebuild before submit) |

## Submission gate (future)

1. Confirm `qstat` has no `molnar_h1_h0025` / `molnar_h2_pub_h001` active.
2. Rebuild eligibility manifest from final evidence/ODBs.
3. Validate env-var CAE script under `abaqus python`.
4. Submit wrapper once.
5. Record job ID; no automatic second CAE submission.

## Current solver chain (context)

| Case | Job | Note |
|---|---|---|
| H0 solver | 1376154 | technical pass; ODB retained |
| H0 CAE 1376184 | fail | argv `-cae` path bug |
| H1 | 1376185 | first solve (may still be active) |
| H2-PUB | 1376186 | afterok H1 |
