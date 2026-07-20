# Abaqus/CAE Path Passing via Environment Variables

## Failure mode

Job `1376184.mmaster02` (H0 CAE replay) failed after the f-string repair with:

```text
OdbError: Cannot open file .../-cae
```

Abaqus/CAE inserts internal argv tokens such as `-cae`. Positional parsing of
`sys.argv` after `--` is therefore unsafe for mandatory ODB/output paths.

## Required interface

Mandatory I/O for `postprocess_molnar_h_convergence_case.py` must come only from:

```text
MOLNAR_CASE_ID
MOLNAR_ODB_PATH
MOLNAR_OUTPUT_DIR
```

Invocation pattern:

```bash
export MOLNAR_CASE_ID="H0"
export MOLNAR_ODB_PATH="/scratch/.../case.odb"
export MOLNAR_OUTPUT_DIR="/scratch/.../postprocessing/H0"
abaqus cae noGUI=scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py
```

`sys.argv` is logged for diagnostics only and is not used for paths.

## Consolidated CAE replay authorization

Exactly one future PBS job `molnar_lc015_hconv_cae_replay_all.pbs` may process
all technically successful ODBs that still lack a valid CAE package, after H1
and H2 leave the active queue. No Abaqus/Standard solves in that job.
