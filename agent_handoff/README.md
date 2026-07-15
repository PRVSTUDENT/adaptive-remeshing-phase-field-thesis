# Abaqus/Standard User-Subroutine Smoke Test

## Purpose

This test verifies the HPC Abaqus/Standard user-subroutine toolchain:

- PBS execution;
- Abaqus/Standard license checkout;
- Intel Fortran compilation;
- linker execution;
- loading and invocation of a trivial `UEXTERNALDB`;
- completion of a minimal Abaqus/Standard analysis;
- ODB creation.

## Scientific scope

This test does not verify:

- the Molnar UEL or UMAT;
- phase-field fracture behavior;
- state variables;
- irreversibility;
- benchmark reproduction;
- MISESERI;
- remeshing or state transfer.

A successful result is classified:

```text
hpc_user_subroutine_smoke_pass
```

It is a technical environment result only.

## Job 1374532.mmaster02

The first HPC submission of this smoke test was job `1374532.mmaster02`.
Its overall classification is:

```text
hpc_user_subroutine_smoke_fail
```

Failure category:

```text
callback_invocation
```

Confirmed passes:

- HPC PBS execution;
- Abaqus/Standard license checkout;
- Intel Fortran compilation;
- user-subroutine linking;
- Abaqus/Standard solution completion;
- ODB creation;
- `.sta` contained `THE ANALYSIS HAS COMPLETED SUCCESSFULLY`.

Failed check:

- `uexternaldb_smoke.called` was not found at the expected location.

Follow-up callback investigation:

```text
E. insufficient_retained_evidence
```

The investigation found no marker file in the accessible work directory,
Abaqus scratch directory, stage directory, repository evidence directory, or
PBS submission directory. It also found no retained `.so`, `.o`, or `.obj`
file, so the linked `UEXTERNALDB` symbol and explicit user-library loading
could not be checked after the fact.

The original files remain preserved as the failed-attempt baseline:

```text
tests/hpc/abaqus_standard_user_subroutine_smoke/uexternaldb_smoke.for
scripts/hpc/abaqus_user_subroutine_smoke.pbs
```

Do not rewrite those files when preparing a retry.

## Deterministic callback retry

Retry status:

```text
prepared_not_submitted
```

Retry source:

```text
tests/hpc/abaqus_standard_user_subroutine_smoke/uexternaldb_smoke_getoutdir.for
```

Retry PBS script:

```text
scripts/hpc/abaqus_user_subroutine_smoke_retry.pbs
```

The retry uses two independent callback proofs:

- a unique callback token written to the Abaqus/Standard `.msg` file through
  unit 7;
- an absolute marker path constructed with `GETOUTDIR` and written through
  unit 101.

Rationale:

- `GETOUTDIR` avoids relying on the process working directory, which can be
  ambiguous when Abaqus uses scratch directories.
- Unit 7 provides an Abaqus-managed diagnostic stream for callback-entry
  tokens in the `.msg` file.
- Unit 101 avoids the original unit 99 and follows the safer user-file unit
  range used for Abaqus user files.
- The retry PBS script stages evidence before enforcing acceptance checks, so a
  missing marker or failed token check does not erase the compiler, linker,
  symbol-search, or text-output diagnostics needed to classify the failure.

No pass is claimed for the retry until a separately approved one-CPU HPC
submission produces evidence satisfying every declared acceptance check.
