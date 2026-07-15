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
